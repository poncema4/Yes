"""Wave definitions and spawn queue."""

WAVE_DEFS = {
    1:  [("Red", 20, 0.5)],
    2:  [("Red", 15, 0.5), ("Blue", 5, 0.5)],
    3:  [("Blue", 15, 0.5), ("Red", 10, 0.4)],
    4:  [("Blue", 20, 0.4), ("Green", 5, 0.5)],
    5:  [("Pink", 12, 0.4), ("Yellow", 8, 0.4)],
    6:  [("Green", 15, 0.35), ("Blue", 20, 0.3), ("Black", 3, 0.8)],
    7:  [("Yellow", 15, 0.35), ("Green", 15, 0.3), ("White", 3, 0.8)],
    8:  [("Pink", 20, 0.3), ("Black", 6, 0.6), ("White", 6, 0.6)],
    9:  [("Zebra", 8, 0.5), ("Lead", 4, 0.8), ("Yellow", 15, 0.3)],
    10: [("Ceramic", 6, 1.0), ("Rainbow", 4, 0.6)],
    11: [("Rainbow", 10, 0.5), ("Zebra", 10, 0.4), ("Lead", 5, 0.6)],
    12: [("MOAB", 1, 2.0), ("Ceramic", 8, 0.8)],
    13: [("Ceramic", 12, 0.6), ("Rainbow", 10, 0.4), ("Lead", 8, 0.5)],
    14: [("MOAB", 2, 3.0), ("Ceramic", 10, 0.6)],
    15: [("MOAB", 3, 2.5), ("Rainbow", 15, 0.3)],
    16: [("Ceramic", 20, 0.4), ("Lead", 10, 0.5), ("MOAB", 2, 3.0)],
    17: [("MOAB", 4, 2.0), ("Ceramic", 15, 0.5)],
    18: [("BFB", 1, 4.0), ("MOAB", 5, 2.0)],
    19: [("BFB", 1, 4.0), ("MOAB", 8, 1.5), ("Ceramic", 20, 0.3)],
    20: [("BFB", 2, 5.0), ("MOAB", 10, 1.5)],
}


class WaveSpawner:
    def __init__(self):
        self.current_wave = 0
        self.spawn_queue = []
        self.spawn_timer = 0.0
        self.wave_active = False
        self.all_waves_done = False

    def start_wave(self, wave_num):
        self.current_wave = wave_num
        self.spawn_queue = []
        self.spawn_timer = 0.0
        self.wave_active = True

        if wave_num not in WAVE_DEFS:
            self.wave_active = False
            self.all_waves_done = True
            return

        time_offset = 0.0
        for bloon_type, count, spacing in WAVE_DEFS[wave_num]:
            for i in range(count):
                self.spawn_queue.append((time_offset, bloon_type))
                time_offset += spacing

        self.spawn_queue.sort(key=lambda x: x[0])

    def update(self, dt):
        if not self.wave_active:
            return []

        self.spawn_timer += dt
        to_spawn = []
        remaining = []

        for spawn_time, bloon_type in self.spawn_queue:
            if spawn_time <= self.spawn_timer:
                to_spawn.append(bloon_type)
            else:
                remaining.append((spawn_time, bloon_type))

        self.spawn_queue = remaining
        return to_spawn

    def is_wave_complete(self, bloons_alive):
        return self.wave_active and len(self.spawn_queue) == 0 and bloons_alive == 0
