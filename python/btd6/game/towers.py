"""All tower types, targeting, shooting logic."""

import math
from game.constants import TOWER_TYPES, TARGETING_MODES, SELL_REFUND_RATE
from game.projectiles import Projectile, SniperShot, ExplosionEffect, FreezeEffect
from game.assets import draw_tower


class Tower:
    def __init__(self, tower_type, x, y):
        data = TOWER_TYPES[tower_type]
        self.type = tower_type
        self.x = x
        self.y = y
        self.base_cost = data["cost"]
        self.total_spent = data["cost"]

        # Stats (mutable, affected by upgrades)
        self.range = data["range"]
        self.damage = data["damage"]
        self.fire_rate = data["fire_rate"]
        self.projectile_type = data["projectile"]
        self.damage_type = data.get("damage_type", "normal")
        self.color = data["color"]
        self.barrel_color = data["barrel_color"]

        # Special stats
        self.splash_radius = data.get("splash_radius", 0)
        self.tack_count = data.get("tack_count", 0)
        self.multishot = data.get("multishot", 1)
        self.moab_damage = 0
        self.pierce = data.get("pierce", 1)
        self.freeze_duration = data.get("freeze_duration", 0)
        self.slow_factor = data.get("slow_factor", 1.0)
        self.slow_duration = data.get("slow_duration", 0)
        self.glue_dps = 0
        self.permafrost = False
        self.affects_white = False
        self.affects_moab_glue = False

        # Upgrades
        self.path1_level = 0
        self.path2_level = 0

        # Targeting
        self.targeting_mode = data.get("default_targeting", "First")
        self.target = None
        self.angle = 0
        self.fire_timer = 0
        self.selected = False
        self.radius = 14

    def get_sell_value(self):
        return int(self.total_spent * SELL_REFUND_RATE)

    def can_upgrade(self, path, cash):
        """Check if an upgrade is available and affordable."""
        data = TOWER_TYPES[self.type]
        if path == "path1":
            level = self.path1_level
            other = self.path2_level
        else:
            level = self.path2_level
            other = self.path1_level

        if level >= 4:
            return False, None, 0
        # Can't go beyond 2 on one path if the other is already > 2
        if level >= 2 and other > 2:
            return False, None, 0

        upgrades = data["upgrades"][path]
        if level >= len(upgrades):
            return False, None, 0

        upgrade = upgrades[level]
        cost = upgrade["cost"]
        if cash < cost:
            return False, upgrade, cost

        return True, upgrade, cost

    def apply_upgrade(self, path):
        """Apply the next upgrade on the given path."""
        data = TOWER_TYPES[self.type]
        if path == "path1":
            level = self.path1_level
        else:
            level = self.path2_level

        upgrades = data["upgrades"][path]
        if level >= len(upgrades):
            return 0

        upgrade = upgrades[level]
        cost = upgrade["cost"]
        effects = upgrade["effects"]

        for key, value in effects.items():
            if key == "range":
                self.range += value
            elif key == "damage":
                self.damage += value
            elif key == "fire_rate":
                self.fire_rate += value
            elif key == "multishot":
                self.multishot = value if self.multishot <= 1 else self.multishot + value
            elif key == "splash_radius":
                self.splash_radius += value
            elif key == "tack_count":
                self.tack_count += value
            elif key == "damage_type":
                self.damage_type = value
            elif key == "moab_damage":
                self.moab_damage += value
            elif key == "pierce":
                self.pierce += value
            elif key == "freeze_duration":
                self.freeze_duration += value
            elif key == "slow_factor":
                self.slow_factor += value
            elif key == "slow_duration":
                self.slow_duration += value
            elif key == "glue_damage":
                self.glue_dps = value
            elif key == "permafrost":
                self.permafrost = True
            elif key == "affect_white":
                self.affects_white = True
            elif key == "moab_glue":
                self.affects_moab_glue = True

        if path == "path1":
            self.path1_level += 1
        else:
            self.path2_level += 1

        self.total_spent += cost
        return cost

    def find_target(self, bloons):
        """Find the best target based on targeting mode."""
        in_range = []
        for b in bloons:
            if not b.alive:
                continue
            d = math.hypot(b.x - self.x, b.y - self.y)
            if self.range < 9000 and d > self.range:
                continue
            in_range.append((b, d))

        if not in_range:
            self.target = None
            return

        if self.targeting_mode == "First":
            in_range.sort(key=lambda x: -x[0].dist)
        elif self.targeting_mode == "Last":
            in_range.sort(key=lambda x: x[0].dist)
        elif self.targeting_mode == "Strong":
            in_range.sort(key=lambda x: -x[0].hp)
        elif self.targeting_mode == "Close":
            in_range.sort(key=lambda x: x[1])

        self.target = in_range[0][0]

    def cycle_targeting(self):
        idx = TARGETING_MODES.index(self.targeting_mode)
        self.targeting_mode = TARGETING_MODES[(idx + 1) % len(TARGETING_MODES)]

    def update(self, dt, bloons, projectiles, effects, particles):
        """Update tower: find target, rotate, shoot."""
        self.find_target(bloons)

        if self.target and self.target.alive:
            self.angle = math.atan2(self.target.y - self.y, self.target.x - self.x)

        self.fire_timer += dt
        fire_interval = 1.0 / self.fire_rate if self.fire_rate > 0 else 999
        if self.fire_timer >= fire_interval and self.target and self.target.alive:
            self.fire_timer = 0
            self._shoot(bloons, projectiles, effects, particles)

    def _shoot(self, bloons, projectiles, effects, particles):
        if self.type == "Tack Shooter":
            self._shoot_tacks(projectiles)
        elif self.type == "Ice Monkey":
            self._shoot_ice(bloons, effects, particles)
        elif self.type == "Sniper Monkey":
            self._shoot_sniper(bloons, effects, particles)
        elif self.type == "Glue Gunner":
            self._shoot_glue(projectiles)
        else:
            self._shoot_standard(projectiles)

    def _shoot_standard(self, projectiles):
        for i in range(self.multishot):
            angle_offset = 0
            if self.multishot > 1:
                spread = 0.3
                angle_offset = -spread / 2 + spread * i / (self.multishot - 1)

            proj_angle = self.angle + angle_offset
            proj = Projectile(
                self.x + math.cos(proj_angle) * 16,
                self.y + math.sin(proj_angle) * 16,
                self.target, 500, self.damage, self.projectile_type,
                self.damage_type, self.splash_radius, self.moab_damage, self.pierce
            )
            proj.angle = proj_angle
            projectiles.append(proj)

    def _shoot_tacks(self, projectiles):
        for i in range(self.tack_count):
            angle = (2 * math.pi * i) / self.tack_count
            proj = Projectile(
                self.x + math.cos(angle) * 12,
                self.y + math.sin(angle) * 12,
                None, 350, self.damage, "tack",
                self.damage_type, 0, 0, 1
            )
            proj.angle = angle
            projectiles.append(proj)

    def _shoot_ice(self, bloons, effects, particles):
        freeze_dur = self.freeze_duration if self.freeze_duration > 0 else 1.5
        for b in bloons:
            if not b.alive:
                continue
            d = math.hypot(b.x - self.x, b.y - self.y)
            if d <= self.range:
                b.apply_freeze(freeze_dur, self.permafrost, self.affects_white)
                if self.damage > 0:
                    b.take_damage(self.damage, "freeze")
        effects.append(FreezeEffect(self.x, self.y, self.range))

    def _shoot_sniper(self, bloons, effects, particles):
        if self.target and self.target.alive:
            self.target.take_damage(self.damage, self.damage_type, self.moab_damage)
            effects.append(SniperShot((self.x, self.y), (self.target.x, self.target.y)))

    def _shoot_glue(self, projectiles):
        slow_dur = self.slow_duration if self.slow_duration > 0 else 3.0
        proj = Projectile(
            self.x + math.cos(self.angle) * 16,
            self.y + math.sin(self.angle) * 16,
            self.target, 350, 0, "glue",
            "glue", 0, 0, 1,
            slow_factor=self.slow_factor,
            slow_duration=slow_dur,
            glue_dps=self.glue_dps,
            affects_moab_glue=self.affects_moab_glue
        )
        proj.angle = self.angle
        projectiles.append(proj)

    def draw(self, surface):
        draw_tower(surface, self.x, self.y, self.type, self.color, self.barrel_color,
                   self.angle, self.radius, self.selected, self.range,
                   self.path1_level, self.path2_level)
