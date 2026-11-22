import asyncio
import logging

import anyio

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from battle.io import build_bot, unbuild_bot
from battle.main import simulate_battle
from battle.shared import BattleObjectProperty as BOP
from battle.state import BattleState
from models.design import Design
from repositories.battle import BattleRepository
from repositories.design import DesignRepository
from repositories.participation import ParticipationRepository
from repositories.notification import NotificationRepository
from repositories.user import UserRepository
from schemas.design import DesignRead


class BattleService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.battles = BattleRepository(session)
        self.designs = DesignRepository(session)

    async def list_battles(
        self, participation_id: int, page: int = 1, page_size: int = 10
    ):
        offset = (page - 1) * page_size
        return await self.battles.list_by_participation(
            participation_id, limit=page_size, offset=offset
        )

    async def simulate_battle(self, raw_bots, event_data_wrapper):
        parsed_bots = []
        designs = []
        for design_id in raw_bots:
            design_model: Design = await self.designs.get_by_id(design_id)
            designs.append(design_model)
            parsed_bots.append(build_bot(design_model.name, design_model.parts))

        max_turns = settings.battle_max_turns
        battle_state = BattleState(parsed_bots, max_turns)
        logging.info(
            f"About to begin battle with {len(parsed_bots)} bots and {max_turns} turns max"
        )

        async def event_generator():
            opponent_design_dict = DesignRead.model_validate(designs[1]).model_dump()
            yield event_data_wrapper(dict(oppenent_design=opponent_design_dict))
            async with anyio.create_task_group() as tg:
                sim_battle_coro = tg.start_soon(
                    anyio.to_thread.run_sync, simulate_battle, battle_state
                )
                battle_event_index = 0
                while (
                    not battle_state.battle_is_over()
                    or len(battle_state.events) > battle_event_index
                ):
                    await asyncio.sleep(1)
                    yield event_data_wrapper(battle_state.events[battle_event_index])
                    battle_event_index += 1
                await sim_battle_coro
            result_designs = []
            for bot_index, bot in enumerate(parsed_bots):
                name, parts, _ = unbuild_bot(bot)
                bot_design = designs[bot_index]
                result_designs.append(
                    dict(
                        id=bot_design.id, name=name, color=bot_design.color, parts=parts
                    )
                )
            yield event_data_wrapper(dict(bots=result_designs))

        return event_generator()

    async def replay_battle(self, battle_id, current_user_id, event_data_wrapper):
        battle = await self.battles.get_by_id(battle_id)
        if battle is None:
            return None

        async def event_generator():
            for event in battle.events:
                await asyncio.sleep(1)
                yield event_data_wrapper(event)
            result_designs = []
            for design in battle.designs:
                design_model = await self.designs.get_by_id(design["id"])
                if design_model.user_id == current_user_id:
                    result_designs.append(design)
            yield event_data_wrapper(dict(bots=result_designs))

        return event_generator()


class CreateBattleService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.battles = BattleRepository(session)
        self.designs = DesignRepository(session)
        self.participations = ParticipationRepository(session)
        self.notifications = NotificationRepository(session)
        self.users = UserRepository(session)

    async def create_battle(self, participation_ids: list[int]):
        if len(participation_ids) != 2:
            raise ValueError("For now battle can only be created with two participants")

        participations = []
        parsed_bots = []
        designs = []
        participation_users = []
        for part_id in participation_ids:
            part = await self.participations.get_by_id(part_id)
            if not part:
                raise ValueError(f"Participation {part_id} not found")
            design_model: Design = await self.designs.get_by_id(part.design_id)
            participations.append(part)
            designs.append(design_model)
            parsed_bots.append(
                build_bot(design_model.name, design_model.parts, design_model.id)
            )
            participation_users.append(await self.users.get_by_id(part.user_id))

        max_turns = settings.battle_max_turns
        battle_state = BattleState(parsed_bots, max_turns)

        await anyio.to_thread.run_sync(simulate_battle, battle_state)

        winner_design_id = (
            battle_state.playable_bots[0].get_property(BOP.BOT_DESIGN_ID)
            if not battle_state.battle_is_tie()
            else None
        )

        result_designs = []
        for bot_index, bot in enumerate(parsed_bots):
            name, parts, _ = unbuild_bot(bot)
            bot_design = designs[bot_index]
            result_designs.append(
                dict(id=bot_design.id, name=name, color=bot_design.color, parts=parts)
            )

        battle = await self.battles.create(
            designs=result_designs,
            events=battle_state.events,
            winner_design_id=winner_design_id,
            participation_ids=participation_ids,
        )

        for i, part in enumerate(participations):
            part.battles_total += 1
            is_winner = part.design_id == winner_design_id
            if is_winner:
                part.battles_won += 1
            part.total_score = max(
                part.battles_won * 2 - (part.battles_total - part.battles_won) * 1, 0
            )

            current_user = participation_users[i]
            # Don't create notifications for system users
            if current_user.is_system:
                continue

            other_user = participation_users[0 if i == 1 else 1]
            message = (
                (
                    f"You won the battle against {other_user.full_name}!"
                    if is_winner
                    else f"You lost the battle with {other_user.full_name}."
                )
                if not battle_state.battle_is_tie()
                else f"Your battle with {other_user.full_name} was a tie."
            )
            await self.notifications.create(part.user_id, message)

        await self.session.commit()
        await self.session.refresh(battle)
        return battle
