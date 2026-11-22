class BattleObject:
    def __init__(self, props=None):
        self._props = props or {}

    def get_property(self, property_name):
        return self._props.get(property_name)

    def set_property(self, property_name, property_value):
        self._props[property_name] = property_value

    def update_property(self, property_name, property_modifier):
        prop_value = self.get_property(property_name)
        new_prop_value = property_modifier(prop_value)
        self.set_property(property_name, new_prop_value)

    def has_property(self, property_name):
        return property_name in self._props

    def export_properties(self):
        return dict(self._props)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._props})"


class BattleObjectProperty:
    BOT_ACTION_POINTS_AVAILABLE = "bot.ap.available"
    BOT_ACTION_POINTS_LEFT = "bot.ap.left"
    BOT_POWER_AVAILABLE = "bot.power_available"
    BOT_WEIGHT_AVAILABLE = "bot.weight_available"
    COOLDOWN_ACTION_POINTS_LEFT = "cooldown.ap_left"
    HIT_POINTS_MAX = "hit_points.max"
    HIT_POINTS_LEFT = "hit_points.left"
    BOT_PARTS = "bot.parts"
    POWER = "power"
    WEIGHT = "weight"
    ACTION_POINTS = "action_points"
    PART_NAME_EN = "part.name.en"
    PART_DRAWING_FUNCTION = "part.drawing.function"
    DAMAGE_HP_BASE = "damage.hp.base"
    DAMAGE_HP_AUX = "damage.hp.aux"
    COOLDOWN_TURNS = "cooldown.turns"
    BOT_DESIGN_NAME = "bot.design.name"
    BOT_DESIGN_ID = "bot.design.id"
    BOT_DESIGN_SLOT = "bot.design.slot"
    BOT_DESIGN_COLOR = "bot.design.color"
    # TODO: Remove this property?
    PART_LOCATION = "__part_location"
    DAMAGE_SPLASH_FUNCTION = "damage.splash.function"
    DAMAGE_SPLASH_PARAMS = "damage.splash.params"
    PART_DESCRIPTION_EN = "part.description.en"
    PART_CATEGORY = "part.category"
    BOT_PARTS_COUNT_ALIVE_ACTIONABLE = "bot.parts.count.alive_actionable"
    BOT_ACTION_POINTS_EXCEEDING_MIN_COST = "bot.ap.exceeding_min_cost"
    BOT_HIT_POINTS_MAX = "bot.hit_points.max"
    BOT_HIT_POINTS_LEFT = "bot.hit_points.left"
    BOT_VITALITY_GAUGES_MAX = "bot.vitality.gauges.max"
    BOT_VITALITY_GAUGES_CURRENT = "bot.vitality.gauges.current"
    PART_ID = "part.id"


def get_bot_name(bot):
    return bot.get_property(BattleObjectProperty.BOT_DESIGN_NAME)


def get_part_name(part):
    return part.get_property(BattleObjectProperty.PART_NAME_EN)
