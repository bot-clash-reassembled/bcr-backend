import argparse
import logging
import os

from dotenv import load_dotenv
from functools import reduce

from battle.shared import (
    BattleObjectProperty as BOP,
    BattleObject,
    get_bot_name,
    get_part_name,
)
from battle.io import load_bot_designs, store_battle_results
from battle.scene import BattleScene
from battle.state import BattleState, BattleEvent


def calculate_bot_metrics(bot):
    result = {}
    bot_parts = bot.get_property(BOP.BOT_PARTS) or []

    result[BOP.BOT_HIT_POINTS_MAX] = reduce(
        lambda s, p: s + p.get_property(BOP.HIT_POINTS_MAX),
        bot_parts,
        0,
    )

    alive_parts = [p for p in bot_parts if p.get_property(BOP.HIT_POINTS_LEFT) > 0]
    result[BOP.BOT_HIT_POINTS_LEFT] = reduce(
        lambda s, p: s + p.get_property(BOP.HIT_POINTS_LEFT),
        alive_parts,
        0,
    )

    cpu_parts = (
        p
        for p in alive_parts
        if p.has_property(BOP.ACTION_POINTS) and p.get_property(BOP.ACTION_POINTS) > 0
    )
    ap_available = reduce(
        lambda s, p: s + p.get_property(BOP.ACTION_POINTS),
        cpu_parts,
        0,
    )
    result[BOP.BOT_ACTION_POINTS_AVAILABLE] = ap_available

    health_metrics = [
        (BOP.BOT_POWER_AVAILABLE, BOP.POWER),
        (BOP.BOT_WEIGHT_AVAILABLE, BOP.WEIGHT),
    ]
    for bot_metric, part_metric in health_metrics:
        bot_metric_value = reduce(
            lambda s, p: s + p.get_property(part_metric),
            [p for p in alive_parts if p.has_property(part_metric)],
            0,
        )
        result[bot_metric] = bot_metric_value

    actionable_alive_parts = [
        p
        for p in alive_parts
        if p.has_property(BOP.ACTION_POINTS) and p.get_property(BOP.ACTION_POINTS) < 0
    ]
    result[BOP.BOT_PARTS_COUNT_ALIVE_ACTIONABLE] = len(actionable_alive_parts)

    min_ap_cost = 0
    if len(actionable_alive_parts) > 0:
        min_ap_cost = min(
            (abs(p.get_property(BOP.ACTION_POINTS)) for p in actionable_alive_parts)
        )
    result[BOP.BOT_ACTION_POINTS_EXCEEDING_MIN_COST] = ap_available - min_ap_cost

    return result


def check_if_bot_is_defeated(bot, bot_metrics):
    metrics_with_negative_threshold = [
        BOP.BOT_POWER_AVAILABLE,
        BOP.BOT_WEIGHT_AVAILABLE,
        BOP.BOT_ACTION_POINTS_EXCEEDING_MIN_COST,
    ]
    if any(bot_metrics.get(m, -1) < 0 for m in metrics_with_negative_threshold):
        return True

    metrics_with_zero_threshold = [
        BOP.BOT_ACTION_POINTS_AVAILABLE,
        BOP.BOT_PARTS_COUNT_ALIVE_ACTIONABLE,
    ]
    if any(bot_metrics.get(m, 0) <= 0 for m in metrics_with_zero_threshold):
        return True

    return False


def calculate_vitality_gauges(metrics):
    vitality_props_and_thresholds = {
        BOP.BOT_ACTION_POINTS_AVAILABLE: 0,
        BOP.BOT_POWER_AVAILABLE: -1,
        BOP.BOT_WEIGHT_AVAILABLE: -1,
        BOP.BOT_ACTION_POINTS_EXCEEDING_MIN_COST: -1,
        BOP.BOT_PARTS_COUNT_ALIVE_ACTIONABLE: 0,
    }
    gauges = {}
    for prop, threshold in vitality_props_and_thresholds.items():
        gauges[prop] = max(metrics[prop] - threshold, 0)
    return gauges


def update_bot_vitality_gauges(bot, metrics):
    bot_vitality_gauges = bot.get_property(BOP.BOT_VITALITY_GAUGES_CURRENT)
    vitality_gauges_update = calculate_vitality_gauges(metrics)
    for k, v in bot_vitality_gauges.export_properties().items():
        updated_gauge = vitality_gauges_update[k]
        if updated_gauge < v:
            bot_vitality_gauges.set_property(k, updated_gauge)


def calculate_bot_vitality_percentage(bot, metrics):
    current_gauges = bot.get_property(BOP.BOT_VITALITY_GAUGES_CURRENT)
    max_gauges = bot.get_property(BOP.BOT_VITALITY_GAUGES_MAX)
    min_gauge_ratio = 1.0
    for k, v in max_gauges.export_properties().items():
        prop_ratio = current_gauges.get_property(k) / v
        if prop_ratio < min_gauge_ratio:
            min_gauge_ratio = prop_ratio

    hp_ratio = metrics[BOP.BOT_HIT_POINTS_LEFT] / metrics[BOP.BOT_HIT_POINTS_MAX]
    return round(hp_ratio * min_gauge_ratio, 4) * 100


def discover_bot_available_weapons(bot):
    bot_parts = bot.get_property(BOP.BOT_PARTS) or []
    weapon_parts = (
        p
        for p in bot_parts
        if p.has_property(BOP.ACTION_POINTS)
        and p.get_property(BOP.ACTION_POINTS) < 0
        and p.has_property(BOP.DAMAGE_HP_BASE)
    )
    alive_weapons = (w for w in weapon_parts if w.get_property(BOP.HIT_POINTS_LEFT) > 0)
    weapons_not_in_cooldown = (
        w
        for w in alive_weapons
        if not w.has_property(BOP.COOLDOWN_ACTION_POINTS_LEFT)
        or w.get_property(BOP.COOLDOWN_ACTION_POINTS_LEFT) == 0
    )
    weapons_which_can_be_used = (
        w
        for w in weapons_not_in_cooldown
        if bot.get_property(BOP.BOT_ACTION_POINTS_LEFT)
        + w.get_property(BOP.ACTION_POINTS)
        >= 0
    )
    return [*weapons_which_can_be_used]


# TODO: Cover with tests
def calculate_weapon_dpt(weapon):
    return weapon.get_property(BOP.DAMAGE_HP_BASE)


def handle_bot_idle_action(bot, ap_cost=-1):
    if bot.get_property(BOP.BOT_ACTION_POINTS_LEFT) + ap_cost < 0:
        return
    bot.update_property(BOP.BOT_ACTION_POINTS_LEFT, lambda v: v + ap_cost)
    bot_parts = bot.get_property(BOP.BOT_PARTS) or []
    weapons_in_cooldown = (
        w for w in bot_parts if w.has_property(BOP.COOLDOWN_ACTION_POINTS_LEFT)
    )
    for weapon in weapons_in_cooldown:
        cooldown_ap_left = weapon.get_property(BOP.COOLDOWN_ACTION_POINTS_LEFT)
        weapon.set_property(
            BOP.COOLDOWN_ACTION_POINTS_LEFT,
            max(cooldown_ap_left + ap_cost, 0),
        )


def update_state_for_weapon_use(bot, weapon_to_use):
    weapon_ap = weapon_to_use.get_property(BOP.ACTION_POINTS)
    handle_bot_idle_action(bot, weapon_ap)
    weapon_to_use.set_property(
        BOP.COOLDOWN_ACTION_POINTS_LEFT,
        round(
            bot.get_property(BOP.BOT_ACTION_POINTS_AVAILABLE)
            * weapon_to_use.get_property(BOP.COOLDOWN_TURNS)
        ),
    )


def determine_weapon_target(bot, playable_bots, weapon_to_use):
    return next(iter([b for b in playable_bots if b != bot]), None)


def determine_weapon_to_use(available_weapons):
    if len(available_weapons) == 1:
        return available_weapons[0]
    weapons_sorted_by_dpt = sorted(
        available_weapons, key=lambda w: calculate_weapon_dpt(w), reverse=True
    )
    return weapons_sorted_by_dpt[0]


def adjust_bot_parts_hp_after_damage(bot, primary_damage, target_damage_area):
    for dmg_ratio, affected_parts in target_damage_area.items():
        damage_to_parts = round(primary_damage * dmg_ratio)
        for part in affected_parts:
            part.update_property(
                BOP.HIT_POINTS_LEFT,
                lambda v: v - damage_to_parts,
            )


def adjust_bot_apa_after_damage(bot, new_bot_apa):
    current_bot_apa = bot.get_property(BOP.BOT_ACTION_POINTS_AVAILABLE)
    apa_decrease_ratio = new_bot_apa / current_bot_apa
    bot.update_property(
        BOP.BOT_ACTION_POINTS_LEFT,
        lambda v: round(v * apa_decrease_ratio),
    )
    bot_parts = bot.get_property(BOP.BOT_PARTS) or []
    for weapon_in_cooldown in [
        p for p in bot_parts if p.has_property(BOP.COOLDOWN_ACTION_POINTS_LEFT)
    ]:
        weapon_in_cooldown.update_property(
            BOP.COOLDOWN_ACTION_POINTS_LEFT,
            lambda v: round(v * apa_decrease_ratio),
        )


def log_battle_event(battle_state, event_type, event_data=None):
    match event_type:
        case BattleEvent.BATTLE_NEW_TURN:
            msg = f"About to start turn {event_data['current_turn']}"
        case BattleEvent.SHOOT_MISSING:
            msg = f"Bot {event_data['shooter']} missed {event_data['target']} using {event_data['weapon']}"
        case BattleEvent.SHOOT_HIT:
            msg = f"Bot {event_data['shooter']} hit {event_data['target']} into {event_data['part_hit']} using {event_data['weapon']}"
            if event_data["splash_damage"]:
                msg += " with splash damage"
        case BattleEvent.BOT_DEFEATED:
            msg = f"Bot {event_data['defeated']} was defeated"
        case BattleEvent.BATTLE_FINISHED:
            winner_descr = (
                "it's a tie"
                if event_data["is_tie"]
                else f"the winner is {event_data['winner']}"
            )
            msg = f"Battle finished, {winner_descr}"
        case _:
            raise NotImplementedError(f"Unknown battle event type: {event_type}")

    logging.info(f"Battle event: {msg}")
    battle_state.log_event(dict(event_type=event_type, event_data=event_data))


def run_battle(battle_state, battle_scene):
    while not battle_state.battle_is_over():
        log_battle_event(
            battle_state,
            BattleEvent.BATTLE_NEW_TURN,
            dict(current_turn=battle_state.current_turn),
        )
        battle_state.initialize_turn_state()
        while not battle_state.current_turn_is_over():
            for bot in battle_state.get_bots_in_order_of_move():
                if battle_state.battle_is_over():
                    return
                if bot not in battle_state.playable_bots:
                    continue
                logging.info(f"Bot {get_bot_name(bot)} about to make a move")
                logging.debug(f"Bot {get_bot_name(bot)} props={bot}")
                available_weapons = discover_bot_available_weapons(bot)
                if not any(available_weapons):
                    handle_bot_idle_action(bot)
                    continue
                weapon_to_use = determine_weapon_to_use(available_weapons)
                update_state_for_weapon_use(bot, weapon_to_use)
                target = determine_weapon_target(
                    bot, battle_state.playable_bots, weapon_to_use
                )
                logging.info(
                    f"Bot {get_bot_name(bot)} about to shoot {get_bot_name(target)}"
                )
                target_damage_area, primary_damage = (
                    battle_scene.determine_target_damage_area(
                        bot, target, weapon_to_use
                    )
                )
                if not any(target_damage_area):
                    log_battle_event(
                        battle_state,
                        BattleEvent.SHOOT_MISSING,
                        dict(
                            shooter=get_bot_name(bot),
                            target=get_bot_name(target),
                            weapon=get_part_name(weapon_to_use),
                        ),
                    )
                    continue

                adjust_bot_parts_hp_after_damage(
                    target, primary_damage, target_damage_area
                )
                # TODO: Fix this indexing
                original_part_hit = target_damage_area[1.0][0]
                metrics = calculate_bot_metrics(target)
                update_bot_vitality_gauges(target, metrics)
                log_battle_event(
                    battle_state,
                    BattleEvent.SHOOT_HIT,
                    dict(
                        shooter=get_bot_name(bot),
                        target=get_bot_name(target),
                        weapon=get_part_name(weapon_to_use),
                        part_hit=get_part_name(original_part_hit),
                        splash_damage=len(target_damage_area.keys()) > 1,
                        target_vitality_percentage=calculate_bot_vitality_percentage(
                            target, metrics
                        ),
                    ),
                )
                logging.debug(
                    f"Target {get_bot_name(target)} metrics={metrics}, props={target}"
                )
                if check_if_bot_is_defeated(target, metrics):
                    log_battle_event(
                        battle_state,
                        BattleEvent.BOT_DEFEATED,
                        dict(defeated=get_bot_name(target)),
                    )
                    battle_state.remove_playable_bot(target)
                else:
                    new_bot_apa = metrics[BOP.BOT_ACTION_POINTS_AVAILABLE]
                    adjust_bot_apa_after_damage(target, new_bot_apa)
                for name, value in metrics.items():
                    target.set_property(name, value)
        battle_state.increment_completed_turns()


def simulate_battle(battle_state):
    for bot in battle_state.playable_bots:
        metrics = calculate_bot_metrics(bot)
        if check_if_bot_is_defeated(bot, metrics):
            logging.error(f"Bot {get_bot_name(bot)} config is invalid, exiting")
            return
        for name, value in metrics.items():
            bot.set_property(name, value)
        max_gauges = {
            p: v for p, v in calculate_vitality_gauges(metrics).items() if v > 1
        }
        bot.set_property(BOP.BOT_VITALITY_GAUGES_MAX, BattleObject(max_gauges.copy()))
        bot.set_property(
            BOP.BOT_VITALITY_GAUGES_CURRENT, BattleObject(max_gauges.copy())
        )
        logging.info(f"Bot {get_bot_name(bot)} max vitality gauges: {max_gauges}")

    battle_scene = BattleScene(battle_state.playable_bots)
    run_battle(battle_state, battle_scene)

    winner_bot = (
        battle_state.playable_bots[0] if not battle_state.battle_is_tie() else None
    )
    log_battle_event(
        battle_state,
        BattleEvent.BATTLE_FINISHED,
        dict(
            is_tie=battle_state.battle_is_tie(),
            winner=get_bot_name(winner_bot) if winner_bot else None,
        ),
    )


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(prog="BCR Battle PoC")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument("designs_folder", help="Folder to look up bot designs")
    parser.add_argument("results_folder", help="Folder to store battle results")

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logging.info("About to begin battle")

    all_bots = load_bot_designs(args.designs_folder)
    max_turns = int(os.getenv("MAX_TURNS", "10"))

    battle_state = BattleState(all_bots, max_turns)
    simulate_battle(battle_state)

    store_battle_results(args.results_folder, all_bots)


if __name__ == "__main__":
    main()
