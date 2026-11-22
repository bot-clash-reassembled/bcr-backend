import logging
import random

from math import sqrt, cos, sin, pi

from battle.shared import BattleObjectProperty as BOP, get_bot_name, get_part_name


logger = logging.getLogger(__name__)


def normalize_vector(vec):
    x, y = vec
    vec_len = sqrt(x * x + y * y)
    return [x / vec_len, y / vec_len]


def points_to_vector(a, b):
    x1, y1 = a
    x2, y2 = b
    return [x2 - x1, y2 - y1]


def rotate_vector(vec, angle):
    x, y = vec
    return [x * cos(angle) - y * sin(angle), x * sin(angle) + y * cos(angle)]


def sum_vectors(vec1, vec2):
    x1, y1 = vec1
    x2, y2 = vec2
    return [x1 + x2, y1 + y2]


def diff_vectors(vec1, vec2):
    x1, y1 = vec1
    x2, y2 = vec2
    return [x1 - x2, y1 - y2]


def dot_product(vec1, vec2):
    x1, y1 = vec1
    x2, y2 = vec2
    return x1 * x2 + y1 * y2


def check_box_intersection(box_coords, line_origin, line_vec):
    line_normal = rotate_vector(line_vec, pi / 2)
    dot_products = [
        dot_product(line_normal, diff_vectors(bv, line_origin)) for bv in box_coords
    ]
    return not (
        all((dp > 0 for dp in dot_products)) or all((dp < 0 for dp in dot_products))
    )


def calculate_weapon_primary_damage(bot, weapon_to_use):
    # TODO: Implement randomization?
    base_damage = weapon_to_use.get_property(BOP.DAMAGE_HP_BASE)
    return base_damage + (
        round(weapon_to_use.get_property(BOP.DAMAGE_HP_AUX) * random.random())
        if weapon_to_use.has_property(BOP.DAMAGE_HP_AUX)
        else 0
    )


class BattleScene:
    SCENE_CELL_SIZE = 10
    DESIGN_GRID_SIZE = 9

    def __init__(self, bots):
        self._bot_locations = {
            bots[0]: [0, 0],
            bots[1]: [30 * self.SCENE_CELL_SIZE, 0],
        }
        self._bot_directions = {
            bots[0]: [1, 0],
            bots[1]: [-1, 0],
        }
        self._splash_damage_func_resolver = {
            "explosion": self._extend_target_damage_area_by_explosive_splash_damage,
            "pierce": self._extend_target_damage_area_by_piercing_splash_damage,
        }

    # TODO: Cover with tests
    def determine_target_damage_area(self, bot, target, weapon_to_use):
        weapon_location = weapon_to_use.get_property(BOP.PART_LOCATION)
        shooter_loc = self._part_location_to_scene_coords(bot, weapon_location)
        target_loc = self._bot_locations[target]
        # TODO: Use weapon accuracy for randomization
        randomizer_vec = [
            0,
            (1 if random.random() < 0.5 else -1)
            * random.random()
            * 3
            * self.SCENE_CELL_SIZE,
        ]
        shoot_vec = normalize_vector(
            sum_vectors(points_to_vector(shooter_loc, target_loc), randomizer_vec)
        )
        logger.debug(f"Shooting from {shooter_loc} to {target_loc} via {shoot_vec}")
        if not self._check_target_overall_bbox_hit(target, shooter_loc, shoot_vec):
            return {}, None

        primary_damage = calculate_weapon_primary_damage(bot, weapon_to_use)
        alive_parts = (
            p
            for p in target.get_property(BOP.BOT_PARTS)
            if p.get_property(BOP.HIT_POINTS_LEFT) > 0
        )
        for part in sorted(
            alive_parts,
            key=lambda p: int(p.get_property(BOP.PART_LOCATION)),
        ):
            if self._check_target_part_bbox_hit(target, part, shooter_loc, shoot_vec):
                logger.info(
                    f"Target {get_bot_name(target)} got a hit to {get_part_name(part)}"
                )
                return self._calc_target_damage_area_by_hit_point(
                    target, part, weapon_to_use, shooter_loc, shoot_vec, primary_damage
                ), primary_damage

        return {}, None

    def _calc_target_damage_area_by_hit_point(
        self, target, hit_part, weapon, shooter_loc, shoot_vec, primary_damage
    ):
        result = {
            1.0: [hit_part],
        }
        hit_part_still_alive = (
            hit_part.get_property(BOP.HIT_POINTS_LEFT) - primary_damage > 0
        )
        if hit_part_still_alive or not weapon.has_property(BOP.DAMAGE_SPLASH_FUNCTION):
            return result

        splash_damage_func_name = weapon.get_property(BOP.DAMAGE_SPLASH_FUNCTION)
        if splash_damage_func_name in self._splash_damage_func_resolver:
            splash_func = self._splash_damage_func_resolver[splash_damage_func_name]
            splash_result = splash_func(
                target, hit_part, weapon, shooter_loc, shoot_vec, primary_damage
            )
            result.update(splash_result)
            return result

        raise NotImplementedError

    def _part_location_to_canon_vec(self, part_loc):
        part_loc_int = int(part_loc)
        row_no = part_loc_int // self.DESIGN_GRID_SIZE
        col_no = part_loc_int % self.DESIGN_GRID_SIZE
        center_column = self.DESIGN_GRID_SIZE // 2
        return [
            (col_no - center_column) * self.SCENE_CELL_SIZE,
            (self.DESIGN_GRID_SIZE - row_no - 1) * self.SCENE_CELL_SIZE,
        ]

    # TODO: Make this hull type agnostic
    def _part_location_to_scene_coords(self, bot, part_loc, shift_vec=None):
        part_loc_canon_vec = self._part_location_to_canon_vec(part_loc)
        if shift_vec is not None:
            part_loc_canon_vec = sum_vectors(part_loc_canon_vec, shift_vec)
        bot_dir_x = self._bot_directions[bot][0]
        bot_loc_vec = self._bot_locations[bot]
        rotated_part_loc_vec = rotate_vector(
            part_loc_canon_vec, pi / 2 if bot_dir_x < 0 else -pi / 2
        )
        result = sum_vectors(rotated_part_loc_vec, bot_loc_vec)
        return result

    def _check_target_overall_bbox_hit(self, target, shoot_loc, shoot_vec):
        shift_vec_len = self.SCENE_CELL_SIZE / 2
        left_lower_corner = self._part_location_to_scene_coords(
            target, "156", [-shift_vec_len, -shift_vec_len]
        )
        left_upper_corner = self._part_location_to_scene_coords(
            target, "0", [-shift_vec_len, shift_vec_len]
        )
        right_upper_corner = self._part_location_to_scene_coords(
            target, "12", [shift_vec_len, shift_vec_len]
        )
        right_lower_corner = self._part_location_to_scene_coords(
            target, "168", [shift_vec_len, -shift_vec_len]
        )
        target_bbox_coords = [
            left_lower_corner,
            left_upper_corner,
            right_upper_corner,
            right_lower_corner,
        ]
        logger.debug(f"Target overall bounding box is {target_bbox_coords}")
        return check_box_intersection(target_bbox_coords, shoot_loc, shoot_vec)

    def _check_target_part_bbox_hit(self, target, part, shoot_loc, shoot_vec):
        part_location = self._part_location_to_scene_coords(
            target, part.get_property(BOP.PART_LOCATION)
        )
        half_grid_size = self.SCENE_CELL_SIZE / 2
        part_bbox_coords = [
            sum_vectors(part_location, [-half_grid_size, -half_grid_size]),
            sum_vectors(part_location, [-half_grid_size, half_grid_size]),
            sum_vectors(part_location, [half_grid_size, half_grid_size]),
            sum_vectors(part_location, [half_grid_size, -half_grid_size]),
        ]
        logger.debug(f"Part bounding box is {part_bbox_coords}")
        return check_box_intersection(part_bbox_coords, shoot_loc, shoot_vec)

    def _extend_target_damage_area_by_explosive_splash_damage(
        self, target, hit_part, weapon, shooter_loc, shoot_vec, primary_damage
    ):
        alive_parts_resolver = {
            p.get_property(BOP.PART_LOCATION): p
            for p in target.get_property(BOP.BOT_PARTS)
            if p.get_property(BOP.HIT_POINTS_LEFT) > 0
        }
        splash_radius = int(weapon.get_property(BOP.DAMAGE_SPLASH_PARAMS))
        current_radius = 1
        dissipation_ratio_step = round(1.0 / splash_radius, 1)
        hit_part_loc = hit_part.get_property(BOP.PART_LOCATION)
        locations_to_process_queue = [hit_part_loc]
        affected_area = set()
        affected_area.add(hit_part_loc)
        result = {}
        while current_radius < splash_radius:
            current_step_parts = []
            new_locations_to_process = []
            ratio = 1.0 - dissipation_ratio_step * current_radius
            dissipated_dmg = round(primary_damage * ratio)
            while len(locations_to_process_queue) > 0:
                location = int(locations_to_process_queue.pop(0))
                location_candidates = [
                    str(location - 1),
                    str(location - self.DESIGN_GRID_SIZE),
                    str(location + 1),
                    str(location + self.DESIGN_GRID_SIZE),
                ]
                for loc_candidate in location_candidates:
                    if loc_candidate in affected_area:
                        continue
                    affected_area.add(loc_candidate)
                    loc_candidate_part = None
                    if loc_candidate in alive_parts_resolver:
                        current_step_parts.append(alive_parts_resolver[loc_candidate])
                    if (
                        loc_candidate_part is None
                        or loc_candidate_part.get_property(BOP.HIT_POINTS_LEFT)
                        - dissipated_dmg
                        <= 0
                    ):
                        # Part which got hit but still alive stops splash from propagating further
                        new_locations_to_process.append(loc_candidate)
            result[ratio] = current_step_parts
            locations_to_process_queue.extend(new_locations_to_process)
            current_radius += 1
        logger.debug(f"Calculated explosive damage area={result}.")
        return result

    def _extend_target_damage_area_by_piercing_splash_damage(
        self, target, hit_part, weapon, shooter_loc, shoot_vec, primary_damage
    ):
        alive_parts_resolver = {
            p.get_property(BOP.PART_LOCATION): p
            for p in target.get_property(BOP.BOT_PARTS)
            if p.get_property(BOP.HIT_POINTS_LEFT) > 0
        }
        splash_depth = int(weapon.get_property(BOP.DAMAGE_SPLASH_PARAMS))
        current_depth = 1
        dissipation_ratio_step = round(1.0 / splash_depth, 1)
        hit_part_depth = (
            int(hit_part.get_property(BOP.PART_LOCATION)) // self.DESIGN_GRID_SIZE
        )
        result = {}
        while current_depth < splash_depth:
            current_layer_depth = hit_part_depth + current_depth
            current_layer_parts = (
                p
                for loc, p in alive_parts_resolver.items()
                if (int(loc) // self.DESIGN_GRID_SIZE) == current_layer_depth
            )
            ratio = 1.0 - dissipation_ratio_step * current_depth
            dissipated_dmg = round(primary_damage * ratio)
            layer_hit_part = None
            for part in current_layer_parts:
                if self._check_target_part_bbox_hit(
                    target, part, shooter_loc, shoot_vec
                ):
                    layer_hit_part = part
                    result[ratio] = [part]
                    break
            if (
                layer_hit_part is not None
                and layer_hit_part.get_property(BOP.HIT_POINTS_LEFT) - dissipated_dmg
                > 0
            ):
                # Part which got hit but still alive stops splash from propagating further
                break
            current_depth += 1
        logger.debug(f"Calculated piercing damage area={result}.")
        return result
