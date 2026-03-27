import pygame
import sys
import random
import copy
from collections import deque

GRID_SIZE = 10
CELL_SIZE = 60
MARGIN_TOP = 80
MARGIN_BOTTOM = 60
MARGIN_SIDE = 40
WINDOW_WIDTH = GRID_SIZE * CELL_SIZE + 2 * MARGIN_SIDE
WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + MARGIN_TOP + MARGIN_BOTTOM
FPS = 60

COLOR_DEFS = {
    "red":       ((220,  40,  40), (255, 120, 120)),
    "blue":      (( 50,  80, 220), (130, 160, 255)),
    "green":     (( 30, 180,  50), (120, 230, 130)),
    "yellow":    ((230, 210,  30), (255, 240, 130)),
    "orange":    ((240, 150,  30), (255, 200, 120)),
    "purple":    ((160,  50, 200), (210, 140, 255)),
    "cyan":      (( 30, 200, 210), (130, 240, 245)),
    "maroon":    ((140,  30,  60), (200, 100, 130)),
    "lime":      ((120, 220,  30), (180, 255, 120)),
    "pink":      ((255, 100, 180), (255, 180, 220)),
}

BG_COLOR       = (30, 30, 30)
GRID_COLOR     = (60, 60, 60)
TEXT_COLOR      = (220, 220, 220)
BUTTON_COLOR   = (70, 70, 70)
BUTTON_HOVER   = (100, 100, 100)
BUTTON_TEXT     = (240, 240, 240)
WIN_OVERLAY    = (0, 0, 0, 160)

def _neighbours(r, c):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
            yield nr, nc

def _generate_hamiltonian_path(grid_size):
    """Generate a Hamiltonian path on a grid using Warnsdorff's heuristic"""
    visited = [[False] * grid_size for _ in range(grid_size)]
    total = grid_size * grid_size

    start = (random.randint(0, grid_size - 1), random.randint(0, grid_size - 1))
    path = [start]
    visited[start[0]][start[1]] = True

    while len(path) < total:
        r, c = path[-1]
        neighbors = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < grid_size and 0 <= nc < grid_size and not visited[nr][nc]:
                neighbors.append((nr, nc))

        if not neighbors:
            return None

        def _degree(cell):
            cnt = 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = cell[0] + dr, cell[1] + dc
                if 0 <= nr < grid_size and 0 <= nc < grid_size and not visited[nr][nc]:
                    cnt += 1
            return cnt

        neighbors.sort(key=_degree)
        min_deg = _degree(neighbors[0])
        best = [n for n in neighbors if _degree(n) == min_deg]
        next_cell = random.choice(best)

        path.append(next_cell)
        visited[next_cell[0]][next_cell[1]] = True

    return path

def _cut_path(path, num_segments, min_length):
    """Cut a Hamiltonian path into num_segments pieces, each >= min_length"""
    total = len(path)
    if total < num_segments * min_length:
        return None

    remaining = total - num_segments * min_length
    extra = [0] * num_segments
    for _ in range(remaining):
        extra[random.randint(0, num_segments - 1)] += 1

    segments = []
    idx = 0
    for i in range(num_segments):
        length = min_length + extra[i]
        segments.append(path[idx:idx + length])
        idx += length
    return segments

def generate_level(min_seg_len=4):
    """Generate a puzzle where every cell is occupied

    Returns (level_dict, solution_dict) or (None, None) on failure
    level_dict:    {color_name: (start, end)}
    solution_dict: {color_name: [(r,c), ...]}
    """
    color_names = list(COLOR_DEFS.keys())
    num_colors = len(color_names)

    for _ in range(500):
        ham = _generate_hamiltonian_path(GRID_SIZE)
        if ham is None:
            continue

        segments = _cut_path(ham, num_colors, min_seg_len)
        if segments is None:
            continue

        level = {}
        solution = {}
        for i, seg in enumerate(segments):
            color = color_names[i]
            level[color] = (tuple(seg[0]), tuple(seg[-1]))
            solution[color] = [tuple(c) for c in seg]
        return level, solution

    return None, None

NUM_LEVELS = 10

_DIFFICULTY = [4, 4, 5, 5, 6, 6, 7, 7, 8, 8]

LEVELS = []
SOLUTIONS = []

for _i in range(NUM_LEVELS):
    _min_seg = _DIFFICULTY[_i] if _i < len(_DIFFICULTY) else 8
    _lvl, _sol = generate_level(min_seg_len=_min_seg)
    if _lvl is not None:
        LEVELS.append(_lvl)
        SOLUTIONS.append(_sol)
    else:
        _lvl, _sol = generate_level(min_seg_len=3)
        if _lvl is not None:
            LEVELS.append(_lvl)
            SOLUTIONS.append(_sol)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Connect the Lines")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)

        self.current_level_idx = 0

        self.paths = {}
        self.dragging = None
        self.history = []
        self.won = False
        self.level_data = None
        self.color_list = []

        self._load_level()

    def _load_level(self):
        if self.current_level_idx >= len(LEVELS):
            LEVELS.clear()
            SOLUTIONS.clear()
            for _i in range(NUM_LEVELS):
                _min_seg = _DIFFICULTY[_i] if _i < len(_DIFFICULTY) else 8
                _lvl, _sol = generate_level(min_seg_len=_min_seg)
                if _lvl is not None:
                    LEVELS.append(_lvl)
                    SOLUTIONS.append(_sol)
                else:
                    _lvl, _sol = generate_level(min_seg_len=3)
                    if _lvl is not None:
                        LEVELS.append(_lvl)
                        SOLUTIONS.append(_sol)
            self.current_level_idx = 0
        self.level_data = LEVELS[self.current_level_idx]
        self.color_list = list(self.level_data.keys())
        self.paths = {}
        self.history = []
        self.dragging = None
        self.won = False

    def _cell_from_pixel(self, mx, my):
        """Return (row, col) or None if outside grid"""
        x0 = MARGIN_SIDE
        y0 = MARGIN_TOP
        col = (mx - x0) // CELL_SIZE
        row = (my - y0) // CELL_SIZE
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return (row, col)
        return None

    def _pixel_center(self, row, col):
        x = MARGIN_SIDE + col * CELL_SIZE + CELL_SIZE // 2
        y = MARGIN_TOP + row * CELL_SIZE + CELL_SIZE // 2
        return (x, y)

    def _occupied_by(self, row, col, exclude_color=None):
        """Return the color occupying (row, col), or None."""
        for color, path in self.paths.items():
            if color == exclude_color:
                continue
            if (row, col) in path:
                return color
        return None

    def _endpoint_color(self, row, col):
        """If (row, col) is an endpoint, return its colour."""
        for color, (s, e) in self.level_data.items():
            if (row, col) == s or (row, col) == e:
                return color
        return None

    def _is_adjacent(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def _save_history(self):
        self.history.append(copy.deepcopy(self.paths))

    def _check_win(self):
        for color, (start, end) in self.level_data.items():
            path = self.paths.get(color)
            if not path:
                return False
            if path[0] != start and path[0] != end:
                return False
            if path[-1] != start and path[-1] != end:
                return False
            if len(path) < 2:
                return False
            if path[0] == path[-1]:
                return False
            if start not in path or end not in path:
                return False
        all_cells = []
        for path in self.paths.values():
            all_cells.extend(path)
        if len(all_cells) != len(set(all_cells)):
            return False
        if len(all_cells) != GRID_SIZE * GRID_SIZE:
            return False
        return True

    def _draw_grid(self):
        self.screen.fill(BG_COLOR)

        # Grid lines
        for r in range(GRID_SIZE + 1):
            y = MARGIN_TOP + r * CELL_SIZE
            pygame.draw.line(self.screen, GRID_COLOR,
                             (MARGIN_SIDE, y),
                             (MARGIN_SIDE + GRID_SIZE * CELL_SIZE, y))
        for c in range(GRID_SIZE + 1):
            x = MARGIN_SIDE + c * CELL_SIZE
            pygame.draw.line(self.screen, GRID_COLOR,
                             (x, MARGIN_TOP),
                             (x, MARGIN_TOP + GRID_SIZE * CELL_SIZE))

    def _draw_paths(self):
        for color, path in self.paths.items():
            if len(path) < 2:
                continue
            rgb_light = COLOR_DEFS[color][1]
            points = [self._pixel_center(r, c) for r, c in path]
            pygame.draw.lines(self.screen, rgb_light, False, points, 6)

    def _draw_endpoints(self):
        for color, (start, end) in self.level_data.items():
            rgb = COLOR_DEFS[color][0]
            for (r, c) in (start, end):
                cx, cy = self._pixel_center(r, c)
                pygame.draw.circle(self.screen, rgb, (cx, cy), CELL_SIZE // 3)
                lbl = color[0].upper()
                txt = self.font_small.render(lbl, True, (255, 255, 255))
                tr = txt.get_rect(center=(cx, cy))
                self.screen.blit(txt, tr)

    def _draw_ui(self):
        diff = _DIFFICULTY[self.current_level_idx] if self.current_level_idx < len(_DIFFICULTY) else 8
        title = f"Level {self.current_level_idx + 1}  (Difficulty {diff})"
        txt = self.font_large.render(title, True, TEXT_COLOR)
        self.screen.blit(txt, (MARGIN_SIDE, 15))

        self.btn_reset = pygame.Rect(MARGIN_SIDE, WINDOW_HEIGHT - 50, 120, 38)
        self.btn_undo = pygame.Rect(MARGIN_SIDE + 140, WINDOW_HEIGHT - 50, 120, 38)

        mx, my = pygame.mouse.get_pos()
        for btn, label in [(self.btn_reset, "Reset"), (self.btn_undo, "Undo")]:
            hover = btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, BUTTON_HOVER if hover else BUTTON_COLOR, btn, border_radius=6)
            t = self.font_med.render(label, True, BUTTON_TEXT)
            self.screen.blit(t, t.get_rect(center=btn.center))

    def _draw_win(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(WIN_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        msg = self.font_large.render("Level Complete!  Click to continue", True, (100, 255, 100))
        self.screen.blit(msg, msg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))

    def _handle_mousedown(self, pos):
        cell = self._cell_from_pixel(*pos)
        if cell is None:
            if self.btn_reset.collidepoint(pos):
                self._save_history()
                self.paths = {}
                self.dragging = None
                return
            if self.btn_undo.collidepoint(pos):
                if self.history:
                    self.paths = self.history.pop()
                    self.dragging = None
                return
            return

        r, c = cell
        ep_color = self._endpoint_color(r, c)

        if ep_color:
            self._save_history()
            existing = self.paths.get(ep_color, [])
            if existing and existing[-1] == (r, c):
                self.dragging = ep_color
                return
            if existing and existing[0] == (r, c):
                self.paths[ep_color] = list(reversed(existing))
                self.dragging = ep_color
                return
            self.paths[ep_color] = [(r, c)]
            self.dragging = ep_color
            return

        occ = self._occupied_by(r, c)
        if occ:
            self._save_history()
            path = self.paths[occ]
            idx = path.index((r, c))
            self.paths[occ] = path[:idx + 1]
            self.dragging = occ
            return

    def _handle_mousemotion(self, pos):
        if self.dragging is None:
            return
        cell = self._cell_from_pixel(*pos)
        if cell is None:
            return

        r, c = cell
        path = self.paths.get(self.dragging, [])
        if not path:
            return

        if (r, c) in path:
            idx = path.index((r, c))
            self.paths[self.dragging] = path[:idx + 1]
            return

        last = path[-1]
        if not self._is_adjacent(last, (r, c)):
            return

        ep_color = self._endpoint_color(r, c)
        if ep_color and ep_color != self.dragging:
            return

        occ = self._occupied_by(r, c, exclude_color=self.dragging)
        if occ:
            return

        start, end = self.level_data[self.dragging]
        path.append((r, c))
        self.paths[self.dragging] = path

        if (r, c) in (start, end) and len(path) >= 2 and path[0] != path[-1]:
            endpoints = {start, end}
            if {path[0], path[-1]} == endpoints:
                self.dragging = None
                if self._check_win():
                    self.won = True

    def _handle_mouseup(self, pos):
        self.dragging = None

    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.won:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.current_level_idx += 1
                        self._load_level()
                    continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_mousedown(event.pos)
                elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                    self._handle_mousemotion(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self._handle_mouseup(event.pos)

            self._draw_grid()
            self._draw_paths()
            self._draw_endpoints()
            self._draw_ui()
            if self.won:
                self._draw_win()
            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()