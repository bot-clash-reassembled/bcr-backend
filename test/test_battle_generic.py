import unittest

from battle.shared import BattleObject, BattleObjectProperty as BOP
from battle.main import (
    calculate_bot_metrics,
    handle_bot_idle_action,
    discover_bot_available_weapons,
    update_state_for_weapon_use,
    determine_weapon_target,
    check_if_bot_is_defeated,
)


class CalculateBotMetricsTests(unittest.TestCase):
    def test_key_metrics_are_present(self):
        # ARRANGE
        bot = BattleObject()
        # ACT
        metrics = calculate_bot_metrics(bot)
        # ASSERT
        key_metrics = [
            BOP.BOT_ACTION_POINTS_AVAILABLE,
            BOP.BOT_POWER_AVAILABLE,
            BOP.BOT_WEIGHT_AVAILABLE,
        ]
        for metric in key_metrics:
            self.assertTrue(metric in metrics, f"{metric} is missing")

    def test_bot_apa_aggregates_only_increases(self):
        # ARRANGE
        bot = BattleObject(
            {
                BOP.BOT_PARTS: [
                    BattleObject(
                        {
                            BOP.ACTION_POINTS: 1,
                            BOP.HIT_POINTS_LEFT: 1,
                            BOP.HIT_POINTS_MAX: 1,
                        }
                    ),
                    BattleObject(
                        {
                            BOP.ACTION_POINTS: -1,
                            BOP.HIT_POINTS_LEFT: 1,
                            BOP.HIT_POINTS_MAX: 1,
                        }
                    ),
                ]
            }
        )
        # ACT
        metrics = calculate_bot_metrics(bot)
        # ASSERT
        self.assertEqual(1, metrics[BOP.BOT_ACTION_POINTS_AVAILABLE])


class HandleBotIdleActionTests(unittest.TestCase):
    def test_ap_left_is_decreased(self):
        # ARRANGE
        bot = BattleObject(
            {
                BOP.BOT_ACTION_POINTS_LEFT: 1,
            }
        )
        # ACT
        handle_bot_idle_action(bot)
        # ASSERT
        self.assertEqual(0, bot.get_property(BOP.BOT_ACTION_POINTS_LEFT))

    def test_ap_left_is_kept_non_negative(self):
        # ARRANGE
        bot = BattleObject(
            {
                BOP.BOT_ACTION_POINTS_LEFT: 0,
            }
        )
        # ACT
        handle_bot_idle_action(bot)
        # ASSERT
        self.assertEqual(0, bot.get_property(BOP.BOT_ACTION_POINTS_LEFT))

    def test_bot_weapons_cooldown_ap_left_decreased(self):
        # ARRANGE
        weapon_in_cooldown = BattleObject(
            {
                BOP.HIT_POINTS_LEFT: 1,
                BOP.ACTION_POINTS: -1,
                BOP.COOLDOWN_ACTION_POINTS_LEFT: 1,
            }
        )
        bot = BattleObject(
            {
                BOP.BOT_ACTION_POINTS_LEFT: 1,
                BOP.BOT_PARTS: [weapon_in_cooldown],
            }
        )
        # ACT
        handle_bot_idle_action(bot)
        # ASSERT
        self.assertEqual(
            0,
            weapon_in_cooldown.get_property(BOP.COOLDOWN_ACTION_POINTS_LEFT),
        )

    def test_bot_weapons_cooldown_ap_left_kept_non_negative(self):
        # ARRANGE
        weapon_in_cooldown = BattleObject(
            {
                BOP.HIT_POINTS_LEFT: 1,
                BOP.ACTION_POINTS: -1,
                BOP.COOLDOWN_ACTION_POINTS_LEFT: 1,
            }
        )
        bot = BattleObject(
            {
                BOP.BOT_ACTION_POINTS_LEFT: 2,
                BOP.BOT_PARTS: [weapon_in_cooldown],
            }
        )
        # ACT
        handle_bot_idle_action(bot, -2)
        # ASSERT
        self.assertEqual(
            0,
            weapon_in_cooldown.get_property(BOP.COOLDOWN_ACTION_POINTS_LEFT),
        )


class DiscoverBotAvailableWeaponsTests(unittest.TestCase):
    def setUp(self):
        self.weapon = BattleObject(
            {
                BOP.HIT_POINTS_LEFT: 1,
                BOP.ACTION_POINTS: -1,
                BOP.DAMAGE_HP_BASE: 1,
            }
        )
        self.properly_setup_bot = BattleObject(
            {
                BOP.BOT_ACTION_POINTS_LEFT: 1,
                BOP.BOT_PARTS: [
                    self.weapon,
                ],
            }
        )

    def test_returns_empty_list_when_no_weapons_in_parts(self):
        # ARRANGE
        bot = BattleObject(
            {
                BOP.BOT_PARTS: [],
            }
        )
        # ACT
        available_weapons = discover_bot_available_weapons(bot)
        # ASSERT
        self.assertEqual(0, len(available_weapons))

    def test_returns_weapon_satisfying_all_conditions(self):
        # ARRANGE
        # ACT
        available_weapons = discover_bot_available_weapons(self.properly_setup_bot)
        # ASSERT
        self.assertEqual(1, len(available_weapons))

    def test_does_not_return_broken_weapon(self):
        # ARRANGE
        self.weapon.set_property(BOP.HIT_POINTS_LEFT, 0)
        # ACT
        available_weapons = discover_bot_available_weapons(self.properly_setup_bot)
        # ASSERT
        self.assertEqual(0, len(available_weapons))

    def test_does_not_return_weapon_in_cooldown(self):
        # ARRANGE
        self.weapon.set_property(BOP.COOLDOWN_ACTION_POINTS_LEFT, 1)
        # ACT
        available_weapons = discover_bot_available_weapons(self.properly_setup_bot)
        # ASSERT
        self.assertEqual(0, len(available_weapons))

    def test_does_not_return_unusable_weapon(self):
        # ARRANGE
        self.weapon.set_property(BOP.ACTION_POINTS, -2)
        # ACT
        available_weapons = discover_bot_available_weapons(self.properly_setup_bot)
        # ASSERT
        self.assertEqual(0, len(available_weapons))


class UpdateStateForWeaponUseTests(unittest.TestCase):
    def setUp(self):
        self.weapon = BattleObject(
            {
                BOP.HIT_POINTS_LEFT: 1,
                BOP.ACTION_POINTS: -2,
                BOP.COOLDOWN_TURNS: 1.0,
            }
        )
        self.bot = BattleObject(
            {
                BOP.BOT_ACTION_POINTS_AVAILABLE: 1,
                BOP.BOT_ACTION_POINTS_LEFT: 3,
                BOP.BOT_PARTS: [
                    self.weapon,
                ],
            }
        )

    def test_bot_ap_left_decreased(self):
        # ARRANGE
        # ACT
        update_state_for_weapon_use(self.bot, self.weapon)
        # ASSERT
        self.assertEqual(1, self.bot.get_property(BOP.BOT_ACTION_POINTS_LEFT))

    def test_weapon_cooldown_ap_left_set_up(self):
        # ARRANGE
        # ACT
        update_state_for_weapon_use(self.bot, self.weapon)
        # ASSERT
        self.assertEqual(
            1,
            self.weapon.get_property(BOP.COOLDOWN_ACTION_POINTS_LEFT),
        )


class DetermineWeaponTargetTests(unittest.TestCase):
    def test_skips_shooter(self):
        # ARRANGE
        shooter = BattleObject()
        # ACT
        target = determine_weapon_target(shooter, [shooter], None)
        # ASSERT
        self.assertIsNone(target)

    def test_returns_first_other_bot(self):
        # ARRANGE
        shooter = BattleObject()
        second = BattleObject()
        # ACT
        target = determine_weapon_target(
            shooter, [shooter, second, BattleObject()], None
        )
        # ASSERT
        self.assertEqual(second, target)


class CheckIfBotIsDefeatedTests(unittest.TestCase):
    def setUp(self):
        self.actionable_item = BattleObject(
            {
                BOP.HIT_POINTS_LEFT: 1,
                BOP.ACTION_POINTS: -1,
            }
        )
        self.bot = BattleObject(
            {
                BOP.BOT_PARTS: [self.actionable_item],
            }
        )
        self.healthy_bot_metrics = {
            BOP.BOT_ACTION_POINTS_AVAILABLE: 1,
            BOP.BOT_POWER_AVAILABLE: 1,
            BOP.BOT_WEIGHT_AVAILABLE: 1,
            BOP.BOT_PARTS_COUNT_ALIVE_ACTIONABLE: 1,
            BOP.BOT_ACTION_POINTS_EXCEEDING_MIN_COST: 0,
        }

    def test_returns_false_if_bot_is_healthy(self):
        # ARRANGE
        # ACT
        result = check_if_bot_is_defeated(self.bot, self.healthy_bot_metrics)
        # ASSERT
        self.assertFalse(result)

    def test_returns_true_if_not_enough_health(self):
        health_metrics = [
            BOP.BOT_ACTION_POINTS_AVAILABLE,
            BOP.BOT_POWER_AVAILABLE,
            BOP.BOT_WEIGHT_AVAILABLE,
            BOP.BOT_PARTS_COUNT_ALIVE_ACTIONABLE,
            BOP.BOT_ACTION_POINTS_EXCEEDING_MIN_COST,
        ]
        for metric in health_metrics:
            with self.subTest(metric=metric):
                # ARRANGE
                del self.healthy_bot_metrics[metric]
                # ACT
                result = check_if_bot_is_defeated(self.bot, self.healthy_bot_metrics)
                # ASSERT
                self.assertTrue(result)


# TODO: Implement
class AdjustBotPartsHPAfterDamageTests(unittest.TestCase):
    pass


# TODO: Implement
class AdjustBotAPAAfterDamageTests(unittest.TestCase):
    pass
