import unittest
from unittest.mock import patch

from battle.scene import calculate_weapon_primary_damage
from battle.shared import BattleObject, BattleObjectProperty as BOP


class CalculateWeaponPrimaryDamageTests(unittest.TestCase):
    def setUp(self):
        self.bot = BattleObject()

    def test_base_damage_only_when_no_aux_damage_property(self):
        # ARRANGE
        weapon = BattleObject(
            {
                BOP.DAMAGE_HP_BASE: 10,
            }
        )
        # ACT
        damage = calculate_weapon_primary_damage(self.bot, weapon)
        # ASSERT
        self.assertEqual(10, damage)

    @patch("battle.scene.random.random", return_value=0.0)
    def test_aux_damage_with_min_random_roll(self, mock_random):
        # ARRANGE
        weapon = BattleObject(
            {
                BOP.DAMAGE_HP_BASE: 10,
                BOP.DAMAGE_HP_AUX: 6,
            }
        )
        # ACT
        damage = calculate_weapon_primary_damage(self.bot, weapon)
        # ASSERT
        self.assertEqual(10, damage)
        mock_random.assert_called_once()

    @patch("battle.scene.random.random", return_value=1.0)
    def test_aux_damage_with_max_random_roll(self, mock_random):
        # ARRANGE
        weapon = BattleObject(
            {
                BOP.DAMAGE_HP_BASE: 10,
                BOP.DAMAGE_HP_AUX: 6,
            }
        )
        # ACT
        damage = calculate_weapon_primary_damage(self.bot, weapon)
        # ASSERT
        self.assertEqual(16, damage)
        mock_random.assert_called_once()

    @patch("battle.scene.random.random", return_value=0.5)
    def test_aux_damage_with_half_random_roll(self, mock_random):
        # ARRANGE
        weapon = BattleObject(
            {
                BOP.DAMAGE_HP_BASE: 10,
                BOP.DAMAGE_HP_AUX: 6,
            }
        )
        # ACT
        damage = calculate_weapon_primary_damage(self.bot, weapon)
        # ASSERT
        self.assertEqual(13, damage)
        mock_random.assert_called_once()

    @patch("battle.scene.random.random", return_value=0.4)
    def test_aux_damage_rounds_properly(self, mock_random):
        # ARRANGE
        weapon = BattleObject(
            {
                BOP.DAMAGE_HP_BASE: 15,
                BOP.DAMAGE_HP_AUX: 7,
            }
        )
        # ACT: 7 * 0.4 = 2.8, round(2.8) = 3 -> total 18
        damage = calculate_weapon_primary_damage(self.bot, weapon)
        # ASSERT
        self.assertEqual(18, damage)
        mock_random.assert_called_once()

    @patch("battle.scene.random.random", return_value=0.9)
    def test_aux_damage_zero_returns_base_damage(self, mock_random):
        # ARRANGE
        weapon = BattleObject(
            {
                BOP.DAMAGE_HP_BASE: 25,
                BOP.DAMAGE_HP_AUX: 0,
            }
        )
        # ACT
        damage = calculate_weapon_primary_damage(self.bot, weapon)
        # ASSERT
        self.assertEqual(25, damage)
        mock_random.assert_called_once()

    @patch("battle.scene.random.random", return_value=0.6)
    def test_base_damage_zero_with_aux_damage(self, mock_random):
        # ARRANGE
        weapon = BattleObject(
            {
                BOP.DAMAGE_HP_BASE: 0,
                BOP.DAMAGE_HP_AUX: 10,
            }
        )
        # ACT: 0 + round(10 * 0.6) = 6
        damage = calculate_weapon_primary_damage(self.bot, weapon)
        # ASSERT
        self.assertEqual(6, damage)
        mock_random.assert_called_once()

    def test_damage_is_always_within_expected_bounds(self):
        # ARRANGE
        weapon = BattleObject(
            {
                BOP.DAMAGE_HP_BASE: 10,
                BOP.DAMAGE_HP_AUX: 5,
            }
        )
        # ACT & ASSERT across multiple randomized runs
        for _ in range(50):
            damage = calculate_weapon_primary_damage(self.bot, weapon)
            self.assertIsInstance(damage, int)
            self.assertGreaterEqual(damage, 10)
            self.assertLessEqual(damage, 15)
