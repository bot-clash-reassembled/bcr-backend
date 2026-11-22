import json
import os

from datetime import datetime

from typing_extensions import deprecated

from battle.shared import BattleObjectProperty as BOP, BattleObject, get_bot_name


def build_bot(bot_name, bot_parts_dict, bot_id=None):
    bot_design_parts = []
    # TODO: Rework parts loading to preserve location info properly
    for loc, part in bot_parts_dict.items():
        part_for_list = BattleObject(part)
        part_for_list.set_property(BOP.PART_LOCATION, loc)
        bot_design_parts.append(part_for_list)
    bop_props = {
        BOP.BOT_DESIGN_NAME: bot_name,
        BOP.BOT_PARTS: bot_design_parts,
    }
    if bot_id:
        bop_props[BOP.BOT_DESIGN_ID] = bot_id
    return BattleObject(bop_props)


@deprecated("Remove when CLI battle running won't be used anymore")
def parse_bot_from_dict(bot_design):
    bot_design_name = bot_design[BOP.BOT_DESIGN_NAME]
    loaded_parts = bot_design[BOP.BOT_PARTS]
    return build_bot(bot_design_name, loaded_parts)


def unbuild_bot(bot: BattleObject):
    bot_name = get_bot_name(bot)
    parts_dict = {}
    for part in bot.get_property(BOP.BOT_PARTS):
        part_props = part.export_properties()
        part_location = part_props[BOP.PART_LOCATION]
        del part_props[BOP.PART_LOCATION]
        parts_dict[part_location] = part_props
    bot_id = bot.get_property(BOP.BOT_DESIGN_ID)
    return bot_name, parts_dict, bot_id


@deprecated("Remove when CLI battle running won't be used anymore")
def serialize_bot_to_dict(bot):
    bot_name = get_bot_name(bot)
    parts_dict = {}
    for part in bot.get_property(BOP.BOT_PARTS):
        part_props = part.export_properties()
        part_location = part_props[BOP.PART_LOCATION]
        del part_props[BOP.PART_LOCATION]
        parts_dict[part_location] = part_props
    return bot_name, {
        BOP.BOT_DESIGN_NAME: bot_name,
        BOP.BOT_PARTS: parts_dict,
    }


@deprecated("Remove when CLI battle running won't be used anymore")
def load_bot_designs(designs_folder):
    result = []
    for file_name in [
        fn for fn in os.listdir(designs_folder) if fn.endswith(".bot-design.json")
    ][:2]:
        with open(os.path.join(designs_folder, file_name), "r") as f:
            bot_design = json.load(f)
            loaded_bot = parse_bot_from_dict(bot_design)
            result.append(loaded_bot)
    return result


@deprecated("Remove when CLI battle running won't be used anymore")
def store_battle_results(results_folder, all_bots):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    for bot in all_bots:
        bot_name, bot_content = serialize_bot_to_dict(bot)
        with open(
            os.path.join(results_folder, f"{bot_name}.{timestamp}_battle-result.json"),
            "w",
        ) as f:
            json.dump(bot_content, f)
