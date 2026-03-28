"""Programmatic sprite drawing with Pygame draw calls — NO external images needed."""

import math
import pygame
from game.constants import (
    WHITE, BLACK, GRAY, DARK_GRAY, BROWN, BLIMP_TYPES, ICE_BLUE, GLUE_GREEN,
    INFINITE_RANGE_THRESHOLD
)


def draw_bloon(surface, x, y, bloon_type, color, radius, frozen=False, glued=False, hp=0, max_hp=0):
    """Draw a bloon at the given position."""
    ix, iy = int(x), int(y)

    if bloon_type in BLIMP_TYPES:
        _draw_blimp(surface, ix, iy, bloon_type, color, hp, max_hp)
        return

    if bloon_type == "Zebra":
        _draw_zebra(surface, ix, iy, radius)
    elif bloon_type == "Rainbow":
        _draw_rainbow(surface, ix, iy, radius)
    elif bloon_type == "Lead":
        pygame.draw.circle(surface, (100, 100, 100), (ix, iy), radius)
        pygame.draw.circle(surface, (140, 140, 140), (ix, iy), radius, 2)
        pygame.draw.circle(surface, (170, 170, 170), (ix - 3, iy - 3), radius // 3)
    else:
        pygame.draw.circle(surface, color, (ix, iy), radius)
        highlight = tuple(min(255, c + 80) for c in color)
        pygame.draw.circle(surface, highlight, (ix - radius // 3, iy - radius // 3), radius // 3)

    # String below bloon
    pygame.draw.line(surface, DARK_GRAY, (ix, iy + radius), (ix - 3, iy + radius + 12), 1)

    # Frozen overlay
    if frozen:
        s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (150, 210, 255, 120), (radius + 2, radius + 2), radius + 2)
        surface.blit(s, (ix - radius - 2, iy - radius - 2))
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            ex = ix + int(math.cos(rad) * (radius - 2))
            ey = iy + int(math.sin(rad) * (radius - 2))
            pygame.draw.line(surface, WHITE, (ix, iy), (ex, ey), 1)

    # Glue overlay
    if glued:
        s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 200, 50, 100), (radius + 2, radius + 2), radius + 2)
        surface.blit(s, (ix - radius - 2, iy - radius - 2))

    # HP bar for Ceramic
    if bloon_type == "Ceramic" and max_hp > 1:
        bar_w = radius * 2
        bar_h = 4
        bx = ix - bar_w // 2
        by = iy - radius - 8
        pygame.draw.rect(surface, DARK_GRAY, (bx, by, bar_w, bar_h))
        fill_w = max(1, int(bar_w * hp / max_hp))
        pygame.draw.rect(surface, (255, 100, 50), (bx, by, fill_w, bar_h))


def _draw_zebra(surface, x, y, radius):
    pygame.draw.circle(surface, WHITE, (x, y), radius)
    for i in range(-radius, radius, 6):
        if (i // 6) % 2 == 0:
            top = max(-radius, i)
            bot = min(radius, i + 3)
            for row in range(top, bot):
                half = int(math.sqrt(max(0, radius * radius - row * row)))
                pygame.draw.line(surface, BLACK, (x - half, y + row), (x + half, y + row))
    pygame.draw.circle(surface, GRAY, (x, y), radius, 1)


def _draw_rainbow(surface, x, y, radius):
    colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (148, 0, 211)]
    for i, c in enumerate(colors):
        r = radius - i * (radius // len(colors))
        if r > 0:
            pygame.draw.circle(surface, c, (x, y), r)
    pygame.draw.circle(surface, (255, 200, 200), (x - radius // 3, y - radius // 3), radius // 4)


def _draw_blimp(surface, x, y, bloon_type, color, hp, max_hp):
    w = 50 if bloon_type == "MOAB" else 65
    h = 24 if bloon_type == "MOAB" else 30

    rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
    pygame.draw.ellipse(surface, color, rect)
    stripe_rect = pygame.Rect(x - w // 2, y - 3, w, 6)
    darker = tuple(max(0, c - 40) for c in color)
    pygame.draw.ellipse(surface, darker, stripe_rect)
    pygame.draw.ellipse(surface, BLACK, rect, 2)

    font = pygame.font.SysFont("arial", 12, bold=True)
    label = font.render(bloon_type, True, WHITE)
    surface.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))

    # Tail fin
    pygame.draw.polygon(surface, darker, [
        (x - w // 2, y - 6), (x - w // 2 - 10, y - 12),
        (x - w // 2 - 10, y + 12), (x - w // 2, y + 6)
    ])

    # HP bar
    if max_hp > 0:
        bar_w = w
        bar_h = 5
        bx = x - bar_w // 2
        by = y - h // 2 - 8
        pygame.draw.rect(surface, DARK_GRAY, (bx, by, bar_w, bar_h))
        fill_w = max(1, int(bar_w * max(0, hp) / max_hp))
        bar_color = (0, 255, 0) if hp > max_hp * 0.5 else (255, 255, 0) if hp > max_hp * 0.25 else (255, 0, 0)
        pygame.draw.rect(surface, bar_color, (bx, by, fill_w, bar_h))


def draw_tower(surface, x, y, tower_type_name, color, barrel_color, angle, radius,
               selected=False, range_val=0, path1_level=0, path2_level=0):
    """Draw a tower at the given position."""
    ix, iy = int(x), int(y)
    is_infinite = range_val > INFINITE_RANGE_THRESHOLD

    # Range ring when selected (skip for infinite range towers)
    if selected and range_val > 0 and not is_infinite:
        s = pygame.Surface((range_val * 2 + 4, range_val * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 40), (range_val + 2, range_val + 2), range_val)
        for a in range(0, 360, 8):
            if (a // 8) % 2 == 0:
                rad = math.radians(a)
                px = range_val + 2 + int(math.cos(rad) * range_val)
                py = range_val + 2 + int(math.sin(rad) * range_val)
                pygame.draw.circle(s, (255, 255, 255, 150), (px, py), 1)
        surface.blit(s, (ix - range_val - 2, iy - range_val - 2))
    elif selected and is_infinite:
        # For infinite range, just show a small indicator and text
        font = pygame.font.SysFont("arial", 10, bold=True)
        inf_text = font.render("INFINITE RANGE", True, (200, 200, 255))
        surface.blit(inf_text, (ix - inf_text.get_width() // 2, iy - radius - 20))

    # Selection glow
    if selected:
        pygame.draw.circle(surface, (255, 215, 0), (ix, iy), radius + 4, 2)

    # Base circle
    pygame.draw.circle(surface, color, (ix, iy), radius)
    pygame.draw.circle(surface, tuple(max(0, c - 40) for c in color), (ix, iy), radius, 2)

    # Barrel
    barrel_len = radius + 6
    barrel_w = 4
    end_x = ix + int(math.cos(angle) * barrel_len)
    end_y = iy + int(math.sin(angle) * barrel_len)
    pygame.draw.line(surface, barrel_color, (ix, iy), (end_x, end_y), barrel_w)
    pygame.draw.circle(surface, barrel_color, (end_x, end_y), barrel_w // 2 + 1)

    # Center dot
    pygame.draw.circle(surface, WHITE, (ix, iy), 3)

    # Upgrade dots
    dot_y = iy + radius + 6
    for i in range(path1_level):
        pygame.draw.circle(surface, (255, 255, 0), (ix - 8 + i * 5, dot_y), 2)
    for i in range(path2_level):
        pygame.draw.circle(surface, (50, 150, 255), (ix - 8 + i * 5, dot_y + 6), 2)


def draw_projectile(surface, x, y, proj_type, angle=0, radius=3):
    ix, iy = int(x), int(y)
    if proj_type == "dart":
        end_x = ix + int(math.cos(angle) * 6)
        end_y = iy + int(math.sin(angle) * 6)
        pygame.draw.line(surface, BROWN, (ix, iy), (end_x, end_y), 3)
    elif proj_type == "tack":
        pts = [(ix, iy - 3), (ix + 2, iy), (ix, iy + 3), (ix - 2, iy)]
        pygame.draw.polygon(surface, GRAY, pts)
    elif proj_type == "bomb":
        pygame.draw.circle(surface, DARK_GRAY, (ix, iy), 5)
        pygame.draw.circle(surface, (255, 100, 0), (ix - 1, iy - 2), 2)
    elif proj_type == "glue":
        pygame.draw.circle(surface, GLUE_GREEN, (ix, iy), 4)
    elif proj_type == "laser":
        end_x = ix + int(math.cos(angle) * 8)
        end_y = iy + int(math.sin(angle) * 8)
        pygame.draw.line(surface, (255, 50, 50), (ix, iy), (end_x, end_y), 2)
    elif proj_type == "cryo":
        pygame.draw.circle(surface, ICE_BLUE, (ix, iy), 4)
    else:
        pygame.draw.circle(surface, WHITE, (ix, iy), radius)


def draw_sniper_line(surface, start, end, alpha):
    s = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    color = (255, 255, 100, int(alpha * 255))
    pygame.draw.line(s, color, (int(start[0]), int(start[1])), (int(end[0]), int(end[1])), 2)
    surface.blit(s, (0, 0))


def draw_explosion(surface, x, y, radius, alpha):
    if radius <= 0:
        return
    s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(s, (255, 150, 0, int(alpha * 200)), (radius + 2, radius + 2), radius)
    pygame.draw.circle(s, (255, 255, 100, int(alpha * 150)), (radius + 2, radius + 2), max(1, radius // 2))
    surface.blit(s, (int(x) - radius - 2, int(y) - radius - 2))


def draw_freeze_ring(surface, x, y, radius, alpha):
    if radius <= 0:
        return
    s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(s, (150, 210, 255, int(alpha * 120)), (radius + 2, radius + 2), radius)
    surface.blit(s, (int(x) - radius - 2, int(y) - radius - 2))
