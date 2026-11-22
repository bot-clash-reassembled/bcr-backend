import asyncio
import logging
import random

from core.db import SessionLocal
from services.league import LeagueService
from services.participation import ParticipationService
from services.battle import CreateBattleService


async def _main():
    async with SessionLocal() as session:
        league_service = LeagueService(session)
        participation_service = ParticipationService(session)
        create_battle_service = CreateBattleService(session)

        # Fetch all leagues (and leave a note to split in batches in future)
        leagues = await league_service.list_leagues()

        for league in leagues:
            if league.is_finished:
                logging.debug(f"League with ID={league.id} is finished, skipping")
                continue

            # Fetch participations of that league (here batches also will be needed at some point)
            participations = await participation_service.list_league_participations(
                league.id
            )
            if len(participations) < 2:
                continue

            # Combine in pairs
            part_ids = [p.id for p in participations if p.is_active]
            random.shuffle(part_ids)

            pairs = []
            if len(part_ids) % 2 == 0:
                for i in range(0, len(part_ids), 2):
                    pairs.append((part_ids[i], part_ids[i + 1]))
            else:
                left_out = part_ids.pop()
                for i in range(0, len(part_ids), 2):
                    pairs.append((part_ids[i], part_ids[i + 1]))

                # Pick one randomly among paired and pair with the one who is left out
                random_pair = random.choice(pairs)
                random_player = random.choice(random_pair)
                pairs.append((random_player, left_out))

            # For each battle POST to /api/v1/battles in parallel, control parallelism by semaphore (for now just run each battle sequentially)
            # We call the service directly as we're in a script
            for pair in pairs:
                try:
                    await create_battle_service.create_battle(list(pair))
                    logging.info(
                        f"Battle created for pair {pair} in league {league.name}"
                    )
                except Exception:
                    logging.exception(f"Error creating battle for pair {pair}")

    # The leaderboard can be calculated on the fly from participation records of a particular league, should be fine for now


if __name__ == "__main__":
    # TODO: Make log level configurable
    logging.basicConfig(level=logging.INFO)

    asyncio.run(_main())
