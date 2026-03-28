"""Sidebar, HUD, buttons, upgrade panel."""

import pygame
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CANVAS_WIDTH, SIDEBAR_WIDTH,
    NAVY, DARK_NAVY, WHITE, BLACK, GRAY, DARK_GRAY, LIGHT_GRAY,
    RED, GREEN, BLUE, YELLOW, GOLD, TOWER_TYPES, TOTAL_WAVES,
    INFINITE_RANGE_THRESHOLD
)


class Button:
    def __init__(self, x, y, w, h, text, color, text_color=WHITE, font_size=14):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover = False
        self.enabled = True
        self.font = pygame.font.SysFont("arial", font_size, bold=True)

    def draw(self, surface):
        color = self.color if self.enabled else DARK_GRAY
        if self.hover and self.enabled:
            color = tuple(min(255, c + 30) for c in color)
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, BLACK, self.rect, 1, border_radius=4)
        text_surf = self.font.render(self.text, True, self.text_color if self.enabled else GRAY)
        tx = self.rect.centerx - text_surf.get_width() // 2
        ty = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (tx, ty))

    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover

    def check_click(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


class TowerButton:
    def __init__(self, x, y, tower_name, index):
        self.rect = pygame.Rect(x, y, 145, 32)
        self.tower_name = tower_name
        data = TOWER_TYPES[tower_name]
        self.cost = data["cost"]
        self.color = data["color"]
        self.hover = False
        self.affordable = True
        self.font = pygame.font.SysFont("arial", 11, bold=True)
        self.font_small = pygame.font.SysFont("arial", 10)

    def draw(self, surface):
        bg = DARK_NAVY if not self.hover else (40, 45, 80)
        if not self.affordable:
            bg = (30, 30, 40)
        pygame.draw.rect(surface, bg, self.rect, border_radius=3)
        pygame.draw.rect(surface, GRAY if self.affordable else DARK_GRAY, self.rect, 1, border_radius=3)

        pygame.draw.circle(surface, self.color, (self.rect.x + 16, self.rect.centery), 10)
        pygame.draw.circle(surface, WHITE, (self.rect.x + 16, self.rect.centery), 3)

        name_text = self.font.render(self.tower_name, True, WHITE if self.affordable else GRAY)
        surface.blit(name_text, (self.rect.x + 30, self.rect.y + 2))

        cost_color = GOLD if self.affordable else GRAY
        cost_text = self.font_small.render(f"${self.cost}", True, cost_color)
        surface.blit(cost_text, (self.rect.x + 30, self.rect.y + 17))

    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover

    def check_click(self, pos):
        return self.affordable and self.rect.collidepoint(pos)


class UI:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 16, bold=True)
        self.font_small = pygame.font.SysFont("arial", 12)
        self.font_large = pygame.font.SysFont("arial", 28, bold=True)
        self.font_title = pygame.font.SysFont("arial", 48, bold=True)

        # Tower buttons
        self.tower_buttons = []
        tower_names = list(TOWER_TYPES.keys())
        sx = CANVAS_WIDTH + 10
        for i, name in enumerate(tower_names):
            col = i % 2
            row = i // 2
            bx = sx + col * 155
            by = 170 + row * 38
            self.tower_buttons.append(TowerButton(bx, by, name, i))

        # Action buttons
        btn_y = SCREEN_HEIGHT - 55
        self.start_wave_btn = Button(CANVAS_WIDTH + 15, btn_y, 140, 40, "Start Wave", (40, 160, 40), font_size=16)
        self.fast_forward_btn = Button(CANVAS_WIDTH + 165, btn_y, 140, 40, "Fast x1", (40, 80, 180), font_size=16)

        # Upgrade / sell buttons
        self.upgrade1_btn = Button(CANVAS_WIDTH + 15, 480, 290, 32, "", (60, 60, 120))
        self.upgrade2_btn = Button(CANVAS_WIDTH + 15, 520, 290, 32, "", (60, 60, 120))
        self.sell_btn = Button(CANVAS_WIDTH + 15, 565, 290, 30, "Sell", (180, 40, 40))
        self.targeting_btn = Button(CANVAS_WIDTH + 15, 600, 290, 25, "Target: First", (60, 80, 60), font_size=12)

        # State
        self.selected_tower_type = None
        self.placing_tower = False
        self.fast_forward = False

        # Wave banner
        self.banner_text = ""
        self.banner_timer = 0

        # Game over / victory
        self.game_over = False
        self.victory = False
        self.restart_btn = Button(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 60, 160, 50,
                                  "Restart", (40, 160, 40), font_size=20)

    def update_tower_affordability(self, cash):
        for tb in self.tower_buttons:
            tb.affordable = cash >= tb.cost

    def show_banner(self, text, duration=2.0):
        self.banner_text = text
        self.banner_timer = duration

    def update(self, dt):
        if self.banner_timer > 0:
            self.banner_timer -= dt

    def draw_sidebar(self, surface, cash, lives, wave, score, selected_tower=None):
        sidebar_rect = pygame.Rect(CANVAS_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, NAVY, sidebar_rect)
        pygame.draw.line(surface, (60, 70, 120), (CANVAS_WIDTH, 0), (CANVAS_WIDTH, SCREEN_HEIGHT), 2)

        title = self.font.render("BLOONS TD 6", True, GOLD)
        surface.blit(title, (CANVAS_WIDTH + SIDEBAR_WIDTH // 2 - title.get_width() // 2, 8))

        y = 35
        cash_text = self.font.render(f"$ {cash}", True, GOLD)
        surface.blit(cash_text, (CANVAS_WIDTH + 15, y))
        lives_color = RED if lives < 20 else WHITE
        lives_text = self.font.render(f"\u2665 {lives}", True, lives_color)
        surface.blit(lives_text, (CANVAS_WIDTH + 160, y))

        y += 25
        wave_text = self.font_small.render(f"Wave: {wave}/{TOTAL_WAVES}", True, LIGHT_GRAY)
        surface.blit(wave_text, (CANVAS_WIDTH + 15, y))
        score_text = self.font_small.render(f"Score: {score}", True, LIGHT_GRAY)
        surface.blit(score_text, (CANVAS_WIDTH + 160, y))

        y += 22
        pygame.draw.line(surface, (60, 70, 120), (CANVAS_WIDTH + 10, y), (SCREEN_WIDTH - 10, y))

        y += 5
        label = self.font_small.render("TOWERS", True, LIGHT_GRAY)
        surface.blit(label, (CANVAS_WIDTH + SIDEBAR_WIDTH // 2 - label.get_width() // 2, y))

        for tb in self.tower_buttons:
            tb.draw(surface)

        if selected_tower:
            self._draw_tower_info(surface, selected_tower, cash)

        self.start_wave_btn.draw(surface)
        self.fast_forward_btn.text = "Fast x2" if self.fast_forward else "Fast x1"
        self.fast_forward_btn.color = (40, 120, 220) if self.fast_forward else (40, 80, 180)
        self.fast_forward_btn.draw(surface)

    def _draw_tower_info(self, surface, tower, cash):
        y = 430
        pygame.draw.line(surface, (60, 70, 120), (CANVAS_WIDTH + 10, y), (SCREEN_WIDTH - 10, y))
        y += 5

        info = self.font.render(f"{tower.type}", True, WHITE)
        surface.blit(info, (CANVAS_WIDTH + 15, y))
        y += 20

        range_str = "Inf" if tower.range > INFINITE_RANGE_THRESHOLD else str(tower.range)
        stats = self.font_small.render(
            f"Dmg:{tower.damage}  Rate:{tower.fire_rate:.1f}/s  Range:{range_str}",
            True, LIGHT_GRAY
        )
        surface.blit(stats, (CANVAS_WIDTH + 15, y))

        # Path 1 upgrade
        can1, upg1, cost1 = tower.can_upgrade("path1", cash)
        if upg1:
            self.upgrade1_btn.text = f"P1: {upg1['name']} (${cost1})"
            self.upgrade1_btn.enabled = can1
        else:
            self.upgrade1_btn.text = "P1: MAX"
            self.upgrade1_btn.enabled = False
        self.upgrade1_btn.draw(surface)

        # Path 2 upgrade
        can2, upg2, cost2 = tower.can_upgrade("path2", cash)
        if upg2:
            self.upgrade2_btn.text = f"P2: {upg2['name']} (${cost2})"
            self.upgrade2_btn.enabled = can2
        else:
            self.upgrade2_btn.text = "P2: MAX"
            self.upgrade2_btn.enabled = False
        self.upgrade2_btn.draw(surface)

        self.sell_btn.text = f"Sell (${tower.get_sell_value()})"
        self.sell_btn.draw(surface)

        self.targeting_btn.text = f"Target: {tower.targeting_mode}"
        self.targeting_btn.draw(surface)

    def draw_hud(self, surface):
        if self.banner_timer > 0:
            alpha = min(1.0, self.banner_timer * 2) * 255
            text = self.font_large.render(self.banner_text, True, WHITE)
            bar_surf = pygame.Surface((CANVAS_WIDTH, 50), pygame.SRCALPHA)
            bar_surf.fill((0, 0, 0, int(alpha * 0.6)))
            surface.blit(bar_surf, (0, SCREEN_HEIGHT // 2 - 25))
            text.set_alpha(int(alpha))
            surface.blit(text, (CANVAS_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 15))

    def draw_game_over(self, surface, score):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        title = self.font_title.render("GAME OVER", True, RED)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        score_text = self.font_large.render(f"Score: {score}", True, WHITE)
        surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))
        self.restart_btn.draw(surface)

    def draw_victory(self, surface, score):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        title = self.font_title.render("VICTORY!", True, GOLD)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        score_text = self.font_large.render(f"Final Score: {score}", True, WHITE)
        surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))
        self.restart_btn.text = "Play Again"
        self.restart_btn.draw(surface)

    def draw_placement_ghost(self, surface, pos, tower_type, valid):
        """Draw tower placement preview."""
        if not tower_type:
            return
        data = TOWER_TYPES[tower_type]
        color = data["color"] if valid else (200, 50, 50)
        draw_range = data["range"]
        is_infinite = draw_range > INFINITE_RANGE_THRESHOLD

        # Range circle (skip for infinite range towers like Sniper)
        if not is_infinite:
            range_surf = pygame.Surface((draw_range * 2, draw_range * 2), pygame.SRCALPHA)
            range_color = (100, 255, 100, 50) if valid else (255, 100, 100, 50)
            pygame.draw.circle(range_surf, range_color, (draw_range, draw_range), draw_range)
            surface.blit(range_surf, (pos[0] - draw_range, pos[1] - draw_range))
        else:
            # Show "infinite range" text instead
            font = pygame.font.SysFont("arial", 10, bold=True)
            inf_text = font.render("INFINITE RANGE", True, (200, 200, 255))
            surface.blit(inf_text, (pos[0] - inf_text.get_width() // 2, pos[1] - 30))

        # Tower preview
        pygame.draw.circle(surface, color, pos, 14)
        pygame.draw.circle(surface, WHITE, pos, 3)

    def handle_sidebar_click(self, pos, cash, wave_active, selected_tower):
        """Handle clicks in the sidebar. Returns action dict."""
        action = {}

        for tb in self.tower_buttons:
            if tb.check_click(pos):
                if cash >= tb.cost:
                    self.selected_tower_type = tb.tower_name
                    self.placing_tower = True
                    action["place_tower"] = tb.tower_name
                return action

        if self.start_wave_btn.check_click(pos) and not wave_active:
            action["start_wave"] = True
            return action

        if self.fast_forward_btn.check_click(pos):
            self.fast_forward = not self.fast_forward
            action["fast_forward"] = self.fast_forward
            return action

        if selected_tower:
            if self.upgrade1_btn.check_click(pos):
                action["upgrade"] = "path1"
            elif self.upgrade2_btn.check_click(pos):
                action["upgrade"] = "path2"
            elif self.sell_btn.check_click(pos):
                action["sell"] = True
            elif self.targeting_btn.check_click(pos):
                action["cycle_targeting"] = True

        return action

    def handle_hover(self, pos):
        for tb in self.tower_buttons:
            tb.check_hover(pos)
        self.start_wave_btn.check_hover(pos)
        self.fast_forward_btn.check_hover(pos)
        self.upgrade1_btn.check_hover(pos)
        self.upgrade2_btn.check_hover(pos)
        self.sell_btn.check_hover(pos)
        self.targeting_btn.check_hover(pos)
        self.restart_btn.check_hover(pos)
