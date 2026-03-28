"""Pop effects and visual feedback particles."""

import random
import math
import pygame
from game.constants import GOLD


class Particle:
    def __init__(self, x, y, color, vx, vy, lifetime=0.4, radius=4):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.radius = radius
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 100 * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        alpha = max(0, self.lifetime / self.max_lifetime)
        r = max(1, int(self.radius * alpha))
        color = tuple(min(255, int(c * (0.5 + 0.5 * alpha))) for c in self.color)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r)


class FloatingText:
    def __init__(self, x, y, text, color=GOLD, lifetime=0.8):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
        self.font = pygame.font.SysFont("arial", 14, bold=True)

    def update(self, dt):
        self.y -= 40 * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        alpha = max(0, self.lifetime / self.max_lifetime)
        color = tuple(min(255, int(c * alpha)) for c in self.color)
        text_surf = self.font.render(self.text, True, color)
        surface.blit(text_surf, (int(self.x) - text_surf.get_width() // 2, int(self.y)))


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.texts = []
        self.screen_shake = 0
        self.shake_intensity = 0

    def pop_effect(self, x, y, color, count=8, big=False):
        speed = 200 if big else 120
        r = 6 if big else 4
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(speed * 0.5, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd - 50
            c = tuple(min(255, max(0, v + random.randint(-30, 30))) for v in color)
            lt = random.uniform(0.3, 0.6) if big else random.uniform(0.2, 0.4)
            self.particles.append(Particle(x, y, c, vx, vy, lt, r))

    def moab_pop(self, x, y, color):
        self.pop_effect(x, y, color, count=20, big=True)
        self.screen_shake = 0.3
        self.shake_intensity = 8

    def cash_text(self, x, y, amount):
        self.texts.append(FloatingText(x, y, f"+${amount}"))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.alive]
        if self.screen_shake > 0:
            self.screen_shake -= dt
            if self.screen_shake <= 0:
                self.shake_intensity = 0

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
        for t in self.texts:
            t.draw(surface)

    def get_shake_offset(self):
        if self.screen_shake > 0:
            return (random.randint(-int(self.shake_intensity), int(self.shake_intensity)),
                    random.randint(-int(self.shake_intensity), int(self.shake_intensity)))
        return (0, 0)
