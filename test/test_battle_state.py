import unittest

from battle.shared import BattleObject, BattleObjectProperty
from battle.state import BattleState


class BattleStateCurrentTurnIsOverTests(unittest.TestCase):
    def test_returns_true_if_no_playable_bots_left(self):
        # ARRANGE
        battle_state = BattleState([], 0)
        # ACT
        is_over = battle_state.current_turn_is_over()
        # ASSERT
        self.assertTrue(is_over)

    def test_returns_false_if_playable_bots_with_ap_are_left(self):
        # ARRANGE
        battle_state = BattleState(
            [
                BattleObject(
                    {
                        BattleObjectProperty.BOT_ACTION_POINTS_LEFT: 1,
                    }
                )
            ],
            0,
        )
        # ACT
        is_over = battle_state.current_turn_is_over()
        # ASSERT
        self.assertFalse(is_over)

    def test_returns_true_if_playable_bots_have_no_ap_left(self):
        # ARRANGE
        battle_state = BattleState(
            [
                BattleObject(
                    {
                        BattleObjectProperty.BOT_ACTION_POINTS_LEFT: 0,
                    }
                ),
                BattleObject(
                    {
                        BattleObjectProperty.BOT_ACTION_POINTS_LEFT: 0,
                    }
                ),
            ],
            0,
        )
        # ACT
        is_over = battle_state.current_turn_is_over()
        # ASSERT
        self.assertTrue(is_over)


class BattleStateInitializeTurnStateTests(unittest.TestCase):
    def test_bot_ap_left_initialized(self):
        # ARRANGE
        bot = BattleObject()
        battle_state = BattleState([bot], 0)
        # ACT
        battle_state.initialize_turn_state()
        # ASSERT
        self.assertTrue(bot.has_property(BattleObjectProperty.BOT_ACTION_POINTS_LEFT))

    def test_bot_ap_left_equalized_with_apa_for_all_bots(self):
        # ARRANGE
        bot1 = BattleObject(
            {
                BattleObjectProperty.BOT_ACTION_POINTS_AVAILABLE: 1,
            }
        )
        bot2 = BattleObject(
            {
                BattleObjectProperty.BOT_ACTION_POINTS_AVAILABLE: 2,
            }
        )
        battle_state = BattleState([bot1, bot2], 0)
        # ACT
        battle_state.initialize_turn_state()
        # ASSERT
        self.assertEqual(
            1, bot1.get_property(BattleObjectProperty.BOT_ACTION_POINTS_LEFT)
        )
        self.assertEqual(
            2, bot2.get_property(BattleObjectProperty.BOT_ACTION_POINTS_LEFT)
        )


class BattleStateBattleIsOverTests(unittest.TestCase):
    def test_returns_false_when_no_end_condition_holds_true(self):
        # ARRANGE
        battle_state = BattleState([BattleObject(), BattleObject()], 1)
        # ACT
        is_over = battle_state.battle_is_over()
        # ASSERT
        self.assertFalse(is_over)

    def test_returns_true_when_there_are_no_turns_left(self):
        # ARRANGE
        battle_state = BattleState([BattleObject(), BattleObject()], 1)
        # ACT
        battle_state.increment_completed_turns()
        is_over = battle_state.battle_is_over()
        # ASSERT
        self.assertTrue(is_over)

    def test_returns_true_when_there_only_one_bot_left(self):
        # ARRANGE
        battle_state = BattleState([BattleObject()], 1)
        # ACT
        is_over = battle_state.battle_is_over()
        # ASSERT
        self.assertTrue(is_over)
