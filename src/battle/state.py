import random

from battle.shared import BattleObjectProperty as BOP


class BattleEvent:
    SHOOT_HIT = "shoot.hit"
    SHOOT_MISSING = "shoot.missing"
    BOT_DEFEATED = "bot.defeated"
    BATTLE_FINISHED = "battle.finished"
    BATTLE_NEW_TURN = "battle.new_turn"


class BattleState:
    def __init__(self, bots, max_turns):
        self.playable_bots = list(bots)
        self.max_turns = max_turns
        self.completed_turns = 0
        self.events = []

    @property
    def current_turn(self):
        return self.completed_turns + 1

    def initialize_turn_state(self):
        for bot in self.playable_bots:
            bot.set_property(
                BOP.BOT_ACTION_POINTS_LEFT,
                bot.get_property(BOP.BOT_ACTION_POINTS_AVAILABLE),
            )

    def get_bots_in_order_of_move(self):
        playable_bots_copy = self.playable_bots.copy()
        # Without this if bots have same amount of AP the last will always move first
        random.shuffle(playable_bots_copy)
        return sorted(
            playable_bots_copy,
            key=lambda b: b.get_property(BOP.BOT_ACTION_POINTS_AVAILABLE),
            reverse=True,
        )

    def battle_is_over(self):
        if self.completed_turns >= self.max_turns:
            return True

        if len(self.playable_bots) == 1:
            return True

        return False

    def current_turn_is_over(self):
        if not any(self.playable_bots):
            return True

        return all(
            (
                b.get_property(BOP.BOT_ACTION_POINTS_LEFT) == 0
                for b in self.playable_bots
            )
        )

    def remove_playable_bot(self, bot):
        self.playable_bots.remove(bot)

    def increment_completed_turns(self):
        self.completed_turns += 1

    def log_event(self, event):
        self.events.append(event)

    def battle_is_tie(self):
        return self.completed_turns >= self.max_turns and len(self.playable_bots) > 1
