import argparse
import asyncio
import random
import sys

from sqlalchemy import select, delete

from core.db import SessionLocal
from models.design import Design
from models.user import User
from repositories.design import DesignRepository
from repositories.user import UserRepository
from services.design_template import DesignTemplateService


DESIGN_TEMPLATE_NAMES_TO_SYSTEM_USER_NAMES = {
    "Machine Gun Bot v1.1": "Machine Gunner",
    "Nail Gun Bot v1.1": "Nail Technician",
    "Missile Launcher Bot v1.1": "Rocketeer",
}

DESIGN_COLOR_OPTIONS = [
    "#ff4757",
    "#2ed573",
    "#3498db",
    "#cda314",
    "#800080",
    "#00ffff",
    "#ffc0cb",
    "#00ff00",
    "#0000ff",
    "#ffd700",
]


async def _provision_system_users(reset: bool):
    async with SessionLocal() as session:
        try:
            if reset:
                print("Resetting database...")
                design_id_subquery = (
                    select(Design.id).join(User).where(User.is_system).scalar_subquery()
                )
                await session.execute(
                    delete(Design).where(Design.id.in_(design_id_subquery))
                )
                await session.execute(delete(User).where(User.is_system))

            user_repo = UserRepository(session)
            design_repo = DesignRepository(session)
            design_template_service = DesignTemplateService()

            templates = await design_template_service.list_design_templates()
            for template in templates:
                template_name = template["name"]
                if template_name not in DESIGN_TEMPLATE_NAMES_TO_SYSTEM_USER_NAMES:
                    raise ValueError(
                        f"Can't find system user name for template name {template_name}."
                    )

                # 1. Create a system user if not exists
                system_user_name = DESIGN_TEMPLATE_NAMES_TO_SYSTEM_USER_NAMES[
                    template_name
                ]
                user = await user_repo.get_system_user_by_full_name(system_user_name)
                if not user:
                    user = await user_repo.create(
                        full_name=system_user_name, is_system=True
                    )
                    await session.flush()
                    print(
                        f"Created system user with name '{system_user_name}' and ID={user.id}"
                    )

                # 2. Create a design for a template if not exists
                system_user_designs = await design_repo.list_by_user(user.id)
                if not system_user_designs:
                    random_color = random.choice(DESIGN_COLOR_OPTIONS)
                    design = await design_repo.create(
                        user_id=user.id,
                        name=template_name,
                        color=random_color,
                        slot=1,
                        parts=template["parts"],
                    )
                    await session.flush()
                    print(f"Created design for {template_name} with ID={design.id}")

            await session.commit()
            print("Provisioning completed.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await session.rollback()
            sys.exit(1)

        finally:
            await session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Provision system users and designs.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing system users and designs before provisioning.",
    )
    args = parser.parse_args()

    asyncio.run(_provision_system_users(args.reset))
