"""Main game loop and state manager."""

import math
import pygame
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CANVAS_WIDTH, FPS, STARTING_CASH,
    STARTING_LIVES, TOTAL_WAVES, BLIMP_TYPES, TOWER_TYPES
)
from game.path import draw_map, is_on_path
from game.bloons import Bloon
from game.towers import Tower
from game.waves import WaveSpawner
from game.particles import ParticleSystem
from game.ui import UI


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        self.cash = STARTING_CASH
        self.lives = STARTING_LIVES
        self.score = 0
        self.wave = 0
        self.wave_active = False
        self.game_over = False
        self.victory = False
        self.speed_mult = 1.0

        self.bloons = []
        self.towers = []
        self.projectiles = []
        self.effects = []

        self.spawner = WaveSpawner()
        self.particles = ParticleSystem()
        self.ui = UI()

        self.selected_tower = None
        self.placing_tower = False
        self.place_type = None
        self.mouse_pos = (0, 0)

        # Pre-render map
        self.map_surface = pygame.Surface((CANVAS_WIDTH, SCREEN_HEIGHT))
        draw_map(self.map_surface)

        self._init_sounds()

    def _init_sounds(self):
        """Generate procedural sounds."""
        self.has_sound = False
        try:
            if not pygame.mixer.get_init():
                return
            import numpy as np
            sr = 22050

            t = np.linspace(0, 0.05, int(sr * 0.05), False)
            wave = (np.sin(2 * np.pi * 1200 * t) * 0.3 * np.exp(-t * 40)).astype(np.float32)
            buf = (wave * 32767).astype(np.int16)
            self.pop_sound = pygame.mixer.Sound(buffer=buf.tobytes())
            self.pop_sound.set_volume(0.15)

            t = np.linspace(0, 0.03, int(sr * 0.03), False)
            wave = (np.sin(2 * np.pi * 600 * t) * 0.2 * np.exp(-t * 60)).astype(np.float32)
            buf = (wave * 32767).astype(np.int16)
            self.shoot_sound = pygame.mixer.Sound(buffer=buf.tobytes())
            self.shoot_sound.set_volume(0.08)

            t = np.linspace(0, 0.2, int(sr * 0.2), False)
            wave = (np.sin(2 * np.pi * 100 * t) * 0.5 * np.exp(-t * 10)).astype(np.float32)
            buf = (wave * 32767).astype(np.int16)
            self.moab_sound = pygame.mixer.Sound(buffer=buf.tobytes())
            self.moab_sound.set_volume(0.25)

            t = np.linspace(0, 0.3, int(sr * 0.3), False)
            freq = np.linspace(400, 800, len(t))
            wave = (np.sin(2 * np.pi * freq * t / sr * 50) * 0.3 * np.exp(-t * 5)).astype(np.float32)
            buf = (wave * 32767).astype(np.int16)
            self.wave_sound = pygame.mixer.Sound(buffer=buf.tobytes())
            self.wave_sound.set_volume(0.15)

            t = np.linspace(0, 0.5, int(sr * 0.5), False)
            freq = np.linspace(600, 200, len(t))
            wave = (np.sin(2 * np.pi * freq * t / sr * 50) * 0.4 * np.exp(-t * 3)).astype(np.float32)
            buf = (wave * 32767).astype(np.int16)
            self.gameover_sound = pygame.mixer.Sound(buffer=buf.tobytes())
            self.gameover_sound.set_volume(0.2)

            self.has_sound = True
        except Exception:
            self.has_sound = False

    def play_sound(self, name):
        if not self.has_sound:
            return
        sounds = {
            "pop": "pop_sound", "shoot": "shoot_sound", "moab_pop": "moab_sound",
            "wave_start": "wave_sound", "game_over": "gameover_sound"
        }
        snd = getattr(self, sounds.get(name, ""), None)
        if snd:
            snd.play()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt *= self.speed_mult
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_click(event)
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_pos = event.pos
                    self.ui.handle_hover(event.pos)

            if not self.game_over and not self.victory:
                self._update(dt)

            self._draw()
            pygame.display.flip()

        pygame.quit()

    def _handle_click(self, event):
        mx, my = event.pos

        if self.game_over or self.victory:
            if self.ui.restart_btn.check_click(event.pos):
                self.reset()
            return

        # Right click: cancel placement or cycle targeting
        if event.button == 3:
            if self.placing_tower:
                self.placing_tower = False
                self.place_type = None
                self.ui.placing_tower = False
                self.ui.selected_tower_type = None
            elif self.selected_tower:
                self.selected_tower.cycle_targeting()
            return

        if event.button == 1:
            # Sidebar click
            if mx >= CANVAS_WIDTH:
                action = self.ui.handle_sidebar_click(
                    event.pos, self.cash, self.wave_active, self.selected_tower
                )
                self._process_action(action)
                return

            # Canvas click: place tower or select existing tower
            if self.placing_tower and self.place_type:
                self._try_place_tower(mx, my)
            else:
                self._try_select_tower(mx, my)

    def _process_action(self, action):
        if "place_tower" in action:
            self.place_type = action["place_tower"]
            self.placing_tower = True
            if self.selected_tower:
                self.selected_tower.selected = False
                self.selected_tower = None

        if action.get("start_wave"):
            self._start_next_wave()

        if "fast_forward" in action:
            self.speed_mult = 2.0 if action["fast_forward"] else 1.0

        if action.get("upgrade") and self.selected_tower:
            path = action["upgrade"]
            can, upg, cost = self.selected_tower.can_upgrade(path, self.cash)
            if can:
                spent = self.selected_tower.apply_upgrade(path)
                self.cash -= spent

        if action.get("sell") and self.selected_tower:
            refund = self.selected_tower.get_sell_value()
            self.cash += refund
            self.towers.remove(self.selected_tower)
            self.selected_tower = None

        if action.get("cycle_targeting") and self.selected_tower:
            self.selected_tower.cycle_targeting()

    def _start_next_wave(self):
        if self.wave >= TOTAL_WAVES:
            return
        self.wave += 1
        self.wave_active = True
        self.cash += 100 + self.wave * 10
        self.spawner.start_wave(self.wave)
        self.ui.show_banner(f"Wave {self.wave} — INCOMING!")
        self.play_sound("wave_start")

    def _try_place_tower(self, mx, my):
        if mx >= CANVAS_WIDTH:
            return
        if is_on_path(mx, my, margin=10):
            return
        for t in self.towers:
            if math.hypot(t.x - mx, t.y - my) < 30:
                return

        cost = TOWER_TYPES[self.place_type]["cost"]
        if self.cash < cost:
            return

        tower = Tower(self.place_type, mx, my)
        self.towers.append(tower)
        self.cash -= cost
        self.placing_tower = False
        self.place_type = None
        self.ui.placing_tower = False
        self.ui.selected_tower_type = None
        self.play_sound("shoot")

    def _try_select_tower(self, mx, my):
        if self.selected_tower:
            self.selected_tower.selected = False
            self.selected_tower = None

        for t in self.towers:
            if math.hypot(t.x - mx, t.y - my) < t.radius + 5:
                t.selected = True
                self.selected_tower = t
                return

    def _update(self, dt):
        # Spawn bloons
        if self.wave_active:
            new_types = self.spawner.update(dt)
            for bt in new_types:
                self.bloons.append(Bloon(bt))

        # Update bloons
        for b in self.bloons:
            b.update(dt)

        # Update towers
        for t in self.towers:
            old_proj = len(self.projectiles)
            t.update(dt, self.bloons, self.projectiles, self.effects, self.particles)
            if len(self.projectiles) > old_proj:
                self.play_sound("shoot")

        # Update projectiles
        for p in self.projectiles:
            p.update(dt, self.bloons, self.particles)

        # Update effects
        for e in self.effects:
            e.update(dt)

        self.particles.update(dt)
        self.ui.update(dt)

        # Process dead bloons — collect children from popped bloons
        new_bloons = []
        for b in list(self.bloons):
            if not b.alive:
                if b.reached_end:
                    # Escaped — lose lives
                    damage = b.rbe()
                    self.lives -= damage
                else:
                    # Popped by damage — give cash, spawn children
                    self.cash += b.reward
                    self.score += b.reward
                    if b.type in BLIMP_TYPES:
                        self.particles.moab_pop(b.x, b.y, b.color)
                        self.play_sound("moab_pop")
                    else:
                        self.particles.pop_effect(b.x, b.y, b.color)
                        self.play_sound("pop")
                    self.particles.cash_text(b.x, b.y - 15, b.reward)
                    children = b.get_children()
                    new_bloons.extend(children)

        self.bloons = [b for b in self.bloons if b.alive] + new_bloons

        # Clean up
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.effects = [e for e in self.effects if e.alive]

        # Check wave complete
        alive_count = sum(1 for b in self.bloons if b.alive)
        if self.wave_active and self.spawner.is_wave_complete(alive_count):
            self.wave_active = False
            if self.wave >= TOTAL_WAVES:
                self.victory = True
                self.ui.show_banner("VICTORY!")

        # Check game over
        if self.lives <= 0:
            self.lives = 0
            self.game_over = True
            self.play_sound("game_over")

        self.ui.update_tower_affordability(self.cash)

    def _draw(self):
        shake = self.particles.get_shake_offset()
        self.screen.blit(self.map_surface, shake)

        for t in self.towers:
            t.draw(self.screen)

        sorted_bloons = sorted(self.bloons, key=lambda b: b.dist)
        for b in sorted_bloons:
            b.draw(self.screen)

        for p in self.projectiles:
            p.draw(self.screen)

        for e in self.effects:
            e.draw(self.screen)

        self.particles.draw(self.screen)

        # Placement ghost
        if self.placing_tower and self.place_type and self.mouse_pos[0] < CANVAS_WIDTH:
            valid = (not is_on_path(self.mouse_pos[0], self.mouse_pos[1], margin=10) and
                     all(math.hypot(t.x - self.mouse_pos[0], t.y - self.mouse_pos[1]) >= 30
                         for t in self.towers))
            self.ui.draw_placement_ghost(self.screen, self.mouse_pos, self.place_type, valid)

        self.ui.draw_sidebar(self.screen, self.cash, self.lives, self.wave, self.score,
                             self.selected_tower)
        self.ui.draw_hud(self.screen)

        if self.game_over:
            self.ui.draw_game_over(self.screen, self.score)
        elif self.victory:
            self.ui.draw_victory(self.screen, self.score)
