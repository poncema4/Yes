"""Projectile movement and hit detection."""

import math
import pygame
from game.assets import draw_projectile, draw_sniper_line, draw_explosion, draw_freeze_ring


class Projectile:
    def __init__(self, x, y, target, speed, damage, proj_type, damage_type="normal",
                 splash_radius=0, moab_damage=0, pierce=1, freeze_duration=0,
                 slow_factor=1.0, slow_duration=0, glue_dps=0, affects_white=False,
                 permafrost=False, affects_moab_glue=False):
        self.x = x
        self.y = y
        self.target = target
        self.speed = speed
        self.damage = damage
        self.proj_type = proj_type
        self.damage_type = damage_type
        self.splash_radius = splash_radius
        self.moab_damage = moab_damage
        self.pierce = pierce
        self.freeze_duration = freeze_duration
        self.slow_factor = slow_factor
        self.slow_duration = slow_duration
        self.glue_dps = glue_dps
        self.affects_white = affects_white
        self.permafrost = permafrost
        self.affects_moab_glue = affects_moab_glue

        self.alive = True
        self.hit_bloons = set()
        self.age = 0.0  # track lifetime for range-limited projectiles
        self.angle = 0
        if target and target.alive:
            self.angle = math.atan2(target.y - y, target.x - x)

    def update(self, dt, bloons, particles):
        if not self.alive:
            return

        self.age += dt

        # Homing: re-aim toward living target
        if self.target and self.target.alive:
            self.angle = math.atan2(self.target.y - self.y, self.target.x - self.x)

        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

        # Kill projectile if out of bounds or too old (prevents infinite travel)
        if self.x < -50 or self.x > 1300 or self.y < -50 or self.y > 770:
            self.alive = False
            return
        if self.age > 3.0:
            self.alive = False
            return

        # Hit detection
        hit_radius = 18 if self.proj_type == "bomb" else 12
        for bloon in bloons:
            if not bloon.alive or id(bloon) in self.hit_bloons:
                continue
            dist = math.hypot(bloon.x - self.x, bloon.y - self.y)
            if dist < hit_radius + bloon.radius:
                self._hit_bloon(bloon, bloons, particles)
                self.hit_bloons.add(id(bloon))
                self.pierce -= 1
                if self.pierce <= 0:
                    self.alive = False
                    return
                break

    def _hit_bloon(self, bloon, all_bloons, particles):
        """Process hitting a bloon."""
        # Apply freeze
        if self.freeze_duration > 0:
            bloon.apply_freeze(self.freeze_duration, self.permafrost, self.affects_white)

        # Apply glue
        if self.slow_duration > 0:
            bloon.apply_glue(self.slow_factor, self.slow_duration, self.glue_dps, self.affects_moab_glue)

        # Apply damage
        if self.damage > 0:
            bloon.take_damage(self.damage, self.damage_type, self.moab_damage)

        # Splash damage
        if self.splash_radius > 0:
            particles.pop_effect(self.x, self.y, (255, 150, 0), count=6)
            for other in all_bloons:
                if other is bloon or not other.alive or id(other) in self.hit_bloons:
                    continue
                d = math.hypot(other.x - self.x, other.y - self.y)
                if d < self.splash_radius:
                    other.take_damage(self.damage, self.damage_type, self.moab_damage)
                    self.hit_bloons.add(id(other))

    def draw(self, surface):
        if self.alive:
            draw_projectile(surface, self.x, self.y, self.proj_type, self.angle)


class SniperShot:
    """Visual-only sniper shot line that fades."""
    def __init__(self, start, end, lifetime=0.15):
        self.start = start
        self.end = end
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if self.alive:
            alpha = self.lifetime / self.max_lifetime
            draw_sniper_line(surface, self.start, self.end, alpha)


class ExplosionEffect:
    """Visual explosion that expands and fades."""
    def __init__(self, x, y, radius, lifetime=0.3):
        self.x = x
        self.y = y
        self.max_radius = radius
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if self.alive:
            progress = 1.0 - (self.lifetime / self.max_lifetime)
            r = int(self.max_radius * progress)
            alpha = self.lifetime / self.max_lifetime
            draw_explosion(surface, self.x, self.y, r, alpha)


class FreezeEffect:
    """Visual freeze ring that expands."""
    def __init__(self, x, y, radius, lifetime=0.4):
        self.x = x
        self.y = y
        self.max_radius = radius
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if self.alive:
            progress = 1.0 - (self.lifetime / self.max_lifetime)
            r = int(self.max_radius * progress)
            alpha = self.lifetime / self.max_lifetime
            draw_freeze_ring(surface, self.x, self.y, r, alpha)
