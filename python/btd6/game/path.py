"""Bloon path waypoints and movement logic."""

import math
import pygame
from game.constants import (
    PATH_WAYPOINTS, PATH_WIDTH, TAN, DARK_TAN, GRASS_GREEN, DARK_GREEN,
    CANVAS_WIDTH, SCREEN_HEIGHT, WHITE, RED, BLACK
)


def compute_path_segments():
    """Precompute cumulative distances along the path."""
    segments = []
    total = 0.0
    for i in range(len(PATH_WAYPOINTS) - 1):
        x1, y1 = PATH_WAYPOINTS[i]
        x2, y2 = PATH_WAYPOINTS[i + 1]
        length = math.hypot(x2 - x1, y2 - y1)
        segments.append((x1, y1, x2, y2, total, total + length))
        total += length
    return segments, total


PATH_SEGMENTS, PATH_TOTAL_LENGTH = compute_path_segments()


def get_position_at_dist(dist):
    """Get (x, y) position at a given distance along the path."""
    if dist <= 0:
        return PATH_WAYPOINTS[0]
    if dist >= PATH_TOTAL_LENGTH:
        return PATH_WAYPOINTS[-1]
    for x1, y1, x2, y2, d_start, d_end in PATH_SEGMENTS:
        if d_start <= dist <= d_end:
            t = (dist - d_start) / (d_end - d_start) if d_end > d_start else 0
            return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
    return PATH_WAYPOINTS[-1]


def get_direction_at_dist(dist):
    """Get the direction angle (radians) at a given distance."""
    for x1, y1, x2, y2, d_start, d_end in PATH_SEGMENTS:
        if d_start <= dist <= d_end:
            return math.atan2(y2 - y1, x2 - x1)
    return 0


def is_on_path(x, y, margin=0):
    """Check if a point is on or near the path."""
    half_w = PATH_WIDTH / 2 + margin
    for x1, y1, x2, y2, _, _ in PATH_SEGMENTS:
        dx, dy = x2 - x1, y2 - y1
        seg_len = math.hypot(dx, dy)
        if seg_len == 0:
            continue
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (seg_len * seg_len)))
        px, py = x1 + t * dx, y1 + t * dy
        if math.hypot(x - px, y - py) < half_w:
            return True
    return False


def draw_map(surface):
    """Draw the grass background and dirt path."""
    surface.fill(GRASS_GREEN)
    for i in range(0, CANVAS_WIDTH, 40):
        for j in range(0, SCREEN_HEIGHT, 40):
            if (i + j) % 80 == 0:
                pygame.draw.circle(surface, DARK_GREEN, (i + 20, j + 20), 12)

    # Path shadow / dark edge
    for i in range(len(PATH_WAYPOINTS) - 1):
        pygame.draw.line(surface, DARK_TAN, PATH_WAYPOINTS[i], PATH_WAYPOINTS[i + 1], PATH_WIDTH + 6)

    # Main path
    for i in range(len(PATH_WAYPOINTS) - 1):
        pygame.draw.line(surface, TAN, PATH_WAYPOINTS[i], PATH_WAYPOINTS[i + 1], PATH_WIDTH)

    # Path detail stones
    for seg_i in range(len(PATH_WAYPOINTS) - 1):
        x1, y1 = PATH_WAYPOINTS[seg_i]
        x2, y2 = PATH_WAYPOINTS[seg_i + 1]
        seg_len = math.hypot(x2 - x1, y2 - y1)
        for d in range(0, int(seg_len), 30):
            t = d / seg_len if seg_len > 0 else 0
            px = x1 + (x2 - x1) * t
            py = y1 + (y2 - y1) * t
            offset = ((d * 7 + seg_i * 13) % 20) - 10
            stone_color = (190 + (d % 20), 150 + (d % 15), 90 + (d % 10))
            pygame.draw.circle(surface, stone_color, (int(px) + offset, int(py) + offset // 2), 3)

    # Corner joints
    for wp in PATH_WAYPOINTS[1:-1]:
        pygame.draw.circle(surface, TAN, wp, PATH_WIDTH // 2)

    # START / EXIT labels
    font = pygame.font.SysFont("arial", 16, bold=True)
    start_label = font.render("START", True, WHITE)
    surface.blit(start_label, (5, 300 - 30))
    exit_label = font.render("EXIT", True, RED)
    surface.blit(exit_label, (CANVAS_WIDTH - 50, 250 - 30))
