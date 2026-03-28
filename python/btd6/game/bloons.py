"""All bloon types, stats, child bloons."""

import math
from game.constants import BLOON_TYPES, BLIMP_TYPES
from game.path import get_position_at_dist, PATH_TOTAL_LENGTH
from game.assets import draw_bloon


class Bloon:
    def __init__(self, bloon_type, dist=0.0):
        data = BLOON_TYPES[bloon_type]
        self.type = bloon_type
        self.hp = data["hp"]
        self.max_hp = data["hp"]
        self.base_speed = data["speed"]
        self.speed = data["speed"]
        self.color = data["color"] or (255, 255, 255)
        self.child_type = data["child"]
        self.child_count = data["child_count"]
        self.reward = data["reward"]
        self.immunities = list(data["immunities"])
        self.dist = dist
        self.x, self.y = get_position_at_dist(dist)
        self.alive = True
        self.reached_end = False

        # Status effects
        self.frozen = False
        self.freeze_timer = 0.0
        self.glued = False
        self.glue_timer = 0.0
        self.slow_factor = 1.0
        self.permafrost_slow = 1.0
        self.glue_dps = 0
        self.glue_dps_timer = 0.0

        # Visual radius
        if bloon_type in BLIMP_TYPES:
            self.radius = 25 if bloon_type == "MOAB" else 32
        elif bloon_type == "Ceramic":
            self.radius = 12
        else:
            self.radius = 10

    @property
    def is_blimp(self):
        return self.type in BLIMP_TYPES

    def rbe(self):
        """Red Bloon Equivalent - damage to lives if this escapes."""
        total = self.hp
        if self.child_type:
            child_data = BLOON_TYPES.get(self.child_type)
            if child_data:
                total += self.child_count * 2
        return max(1, total)

    def take_damage(self, damage, damage_type="normal", moab_bonus=0):
        """Apply damage, respecting immunities. Returns True if hit landed."""
        if not self.alive:
            return False

        # Check immunities
        if damage_type == "sharp" and "sharp" in self.immunities:
            return False
        if damage_type == "explosion" and "explosion" in self.immunities:
            return False
        if damage_type == "freeze" and "freeze" in self.immunities:
            return False

        actual_damage = damage
        if self.is_blimp and moab_bonus > 0:
            actual_damage += moab_bonus

        self.hp -= actual_damage

        # >>> FIX: Mark bloon as dead when HP depleted <<<
        if self.hp <= 0:
            self.alive = False

        return True

    def apply_freeze(self, duration, permafrost=False, affects_white=False):
        if "freeze" in self.immunities and not affects_white:
            return
        if self.is_blimp:
            return
        self.frozen = True
        self.freeze_timer = max(self.freeze_timer, duration)
        if permafrost:
            self.permafrost_slow = 0.7

    def apply_glue(self, slow_factor, duration, dps=0, affects_moab=False):
        if self.is_blimp and not affects_moab:
            return
        self.glued = True
        self.slow_factor = min(self.slow_factor, slow_factor)
        self.glue_timer = max(self.glue_timer, duration)
        if dps > self.glue_dps:
            self.glue_dps = dps

    def update(self, dt):
        """Move bloon along path."""
        if not self.alive:
            return

        # Process freeze
        if self.frozen:
            self.freeze_timer -= dt
            if self.freeze_timer <= 0:
                self.frozen = False
                self.freeze_timer = 0

        # Process glue
        if self.glued:
            self.glue_timer -= dt
            if self.glue_dps > 0:
                self.glue_dps_timer += dt
                if self.glue_dps_timer >= 1.0:
                    self.hp -= self.glue_dps
                    self.glue_dps_timer -= 1.0
                    if self.hp <= 0:
                        self.alive = False
                        return
            if self.glue_timer <= 0:
                self.glued = False
                self.slow_factor = 1.0
                self.glue_dps = 0

        # Move if not frozen
        if not self.frozen:
            effective_speed = self.base_speed * 60
            effective_speed *= self.slow_factor * self.permafrost_slow
            self.dist += effective_speed * dt
            self.x, self.y = get_position_at_dist(self.dist)

        # Check if reached end
        if self.dist >= PATH_TOTAL_LENGTH:
            self.reached_end = True
            self.alive = False

    def get_children(self):
        """Return list of child bloons when this one pops."""
        if not self.child_type or self.child_count <= 0:
            return []
        children = []
        for i in range(self.child_count):
            offset = (i - (self.child_count - 1) / 2) * 5
            child = Bloon(self.child_type, max(0, self.dist + offset))
            children.append(child)
        return children

    def draw(self, surface):
        if not self.alive:
            return
        draw_bloon(surface, self.x, self.y, self.type, self.color, self.radius,
                   self.frozen, self.glued, self.hp, self.max_hp)
