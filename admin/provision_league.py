import argparse
import asyncio
import sys

from sqlalchemy import select, func, delete

from core.db import SessionLocal
from repositories.user import UserRepository
from repositories.design import DesignRepository
from repositories.participation import ParticipationRepository
from repositories.league import LeagueRepository
from models.participation import Participation


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


async def provision_league(league_id: int, league_name: str, reset: bool):
    async with SessionLocal() as session:
        try:
            if league_id:
                if reset:
                    print("Resetting database...")
                    await session.execute(
                        delete(Participation).where(
                            Participation.league_id == league_id
                        )
                    )
                else:
                    print("Checking for existing data...")
                    result = await session.execute(
                        select(func.count(Participation.id)).where(
                            Participation.league_id == league_id
                        )
                    )
                    if result.scalar_one() > 0:
                        print(
                            f"Database already contains data for league {league_id}. Skipping provision."
                        )
                        return

            user_repo = UserRepository(session)
            design_repo = DesignRepository(session)
            participation_repo = ParticipationRepository(session)
            league_repo = LeagueRepository(session)

            if league_id:
                league = await league_repo.get_by_id(league_id)
                if not league:
                    raise ValueError(f"League with ID {league_id} not found.")
            else:
                league = await league_repo.create(league_name)

            system_users = await user_repo.list_system_users()
            for su in system_users:
                su_designs = await design_repo.list_by_user(su.id)
                await participation_repo.create(su.id, su_designs[0].id, league.id)
                print(
                    f"Added participation for {su_designs[0].name} in league {league.name}"
                )

            await session.commit()
            print("Provisioning completed.")
            if not league_id:
                print(f"New league ID = {league.id}.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await session.rollback()
            sys.exit(1)

        finally:
            await session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Provision a league with participations of system users` designs."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--league_id", type=int, help="ID of the existing league to provision."
    )
    group.add_argument(
        "--league_name", type=str, help="Name of a league to create & provision."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset league participations before provisioning.",
    )
    args = parser.parse_args()

    asyncio.run(provision_league(args.league_id, args.league_name, args.reset))
