"""All game constants in one place."""

# Window
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CANVAS_WIDTH = 960
SIDEBAR_WIDTH = 320
FPS = 60
TITLE = "Bloons TD 6 - Python Edition"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
RED = (255, 50, 50)
BLUE = (50, 100, 255)
GREEN = (50, 200, 50)
YELLOW = (255, 255, 0)
PINK = (255, 150, 200)
ORANGE = (255, 165, 0)
PURPLE = (180, 50, 255)
CYAN = (0, 255, 255)
BROWN = (139, 90, 43)
TAN = (210, 170, 109)
DARK_TAN = (170, 130, 70)
GRASS_GREEN = (80, 160, 50)
DARK_GREEN = (50, 120, 30)
NAVY = (20, 25, 60)
DARK_NAVY = (15, 18, 45)
GOLD = (255, 215, 0)
ICE_BLUE = (150, 210, 255)
GLUE_GREEN = (100, 200, 50)

# Path
PATH_WIDTH = 60
PATH_WAYPOINTS = [
    (0, 300), (200, 300), (200, 150), (500, 150), (500, 450),
    (800, 450), (800, 250), (1050, 250), (1280, 250)
]

# Game defaults
STARTING_CASH = 650
STARTING_LIVES = 100
TOTAL_WAVES = 20
SELL_REFUND_RATE = 0.75

# Range threshold: anything above this is treated as "infinite range"
INFINITE_RANGE_THRESHOLD = 1000

# Bloon types
BLOON_TYPES = {
    "Red":     {"hp": 1,   "speed": 1.0, "color": (255, 50, 50),    "child": None,      "child_count": 0, "reward": 1,   "immunities": []},
    "Blue":    {"hp": 1,   "speed": 1.4, "color": (50, 100, 255),   "child": "Red",     "child_count": 1, "reward": 1,   "immunities": []},
    "Green":   {"hp": 1,   "speed": 1.8, "color": (50, 200, 50),    "child": "Blue",    "child_count": 1, "reward": 1,   "immunities": []},
    "Yellow":  {"hp": 1,   "speed": 3.2, "color": (255, 255, 0),    "child": "Green",   "child_count": 1, "reward": 1,   "immunities": []},
    "Pink":    {"hp": 1,   "speed": 3.5, "color": (255, 150, 200),  "child": "Yellow",  "child_count": 1, "reward": 1,   "immunities": []},
    "Black":   {"hp": 1,   "speed": 1.8, "color": (30, 30, 30),     "child": "Pink",    "child_count": 2, "reward": 1,   "immunities": ["explosion"]},
    "White":   {"hp": 1,   "speed": 2.0, "color": (240, 240, 240),  "child": "Pink",    "child_count": 2, "reward": 1,   "immunities": ["freeze"]},
    "Lead":    {"hp": 1,   "speed": 1.0, "color": (120, 120, 120),  "child": "Black",   "child_count": 2, "reward": 2,   "immunities": ["sharp"]},
    "Zebra":   {"hp": 1,   "speed": 1.8, "color": None,             "child": "Black",   "child_count": 2, "reward": 1,   "immunities": ["explosion", "freeze"]},
    "Rainbow": {"hp": 1,   "speed": 2.2, "color": None,             "child": "Zebra",   "child_count": 2, "reward": 2,   "immunities": []},
    "Ceramic": {"hp": 10,  "speed": 2.5, "color": (220, 140, 50),   "child": "Rainbow", "child_count": 2, "reward": 5,   "immunities": []},
    "MOAB":    {"hp": 200, "speed": 0.6, "color": (40, 80, 200),    "child": "Ceramic", "child_count": 4, "reward": 50,  "immunities": []},
    "BFB":     {"hp": 700, "speed": 0.4, "color": (200, 40, 40),    "child": "MOAB",    "child_count": 4, "reward": 200, "immunities": []},
}

BLIMP_TYPES = {"MOAB", "BFB"}

# Tower definitions
TOWER_TYPES = {
    "Dart Monkey": {
        "cost": 170, "range": 130, "damage": 1, "fire_rate": 1.0,
        "projectile": "dart", "color": (139, 90, 43), "barrel_color": (100, 60, 30),
        "damage_type": "sharp",
        "upgrades": {
            "path1": [
                {"name": "Longer Range", "cost": 90, "effects": {"range": 20}},
                {"name": "Sharper Shots", "cost": 150, "effects": {"damage": 1}},
                {"name": "Triple Shot", "cost": 400, "effects": {"multishot": 3}},
                {"name": "Fan Club", "cost": 8000, "effects": {"fire_rate": 5.0, "damage": 2}},
            ],
            "path2": [
                {"name": "Quick Shots", "cost": 80, "effects": {"fire_rate": 0.5}},
                {"name": "Very Quick", "cost": 150, "effects": {"fire_rate": 0.5}},
                {"name": "Turbo Charge", "cost": 350, "effects": {"fire_rate": 1.0}},
                {"name": "Ultra Jugg", "cost": 6000, "effects": {"damage": 4, "pierce": 20}},
            ],
        },
    },
    "Tack Shooter": {
        "cost": 230, "range": 90, "damage": 1, "fire_rate": 0.8,
        "projectile": "tack", "color": (180, 80, 80), "barrel_color": (140, 50, 50),
        "damage_type": "sharp", "tack_count": 8,
        "upgrades": {
            "path1": [
                {"name": "Fast Shooting", "cost": 100, "effects": {"fire_rate": 0.3}},
                {"name": "Even Faster", "cost": 200, "effects": {"fire_rate": 0.3}},
                {"name": "Hot Shots", "cost": 500, "effects": {"damage_type": "fire", "damage": 1}},
                {"name": "Ring of Fire", "cost": 3000, "effects": {"damage": 3, "range": 20}},
            ],
            "path2": [
                {"name": "More Tacks", "cost": 80, "effects": {"tack_count": 4}},
                {"name": "Even More", "cost": 150, "effects": {"tack_count": 4}},
                {"name": "Tack Sprayer", "cost": 400, "effects": {"tack_count": 4}},
                {"name": "Inferno Ring", "cost": 5000, "effects": {"damage": 5, "range": 30, "damage_type": "fire"}},
            ],
        },
    },
    "Sniper Monkey": {
        "cost": 350, "range": 9999, "damage": 2, "fire_rate": 0.4,
        "projectile": "sniper", "color": (60, 80, 60), "barrel_color": (40, 50, 40),
        "damage_type": "sharp", "default_targeting": "Last",
        "upgrades": {
            "path1": [
                {"name": "Full Metal", "cost": 250, "effects": {"damage_type": "normal"}},
                {"name": "Point Five Oh", "cost": 400, "effects": {"damage": 3}},
                {"name": "Deadly Prec.", "cost": 1500, "effects": {"damage": 10}},
                {"name": "Maim MOAB", "cost": 5000, "effects": {"damage": 10, "moab_slow": True}},
            ],
            "path2": [
                {"name": "Night Vision", "cost": 150, "effects": {"camo": True}},
                {"name": "Shrapnel", "cost": 350, "effects": {"shrapnel": True}},
                {"name": "Bouncing", "cost": 2500, "effects": {"bounce": 3}},
                {"name": "Cripple MOAB", "cost": 8000, "effects": {"moab_damage": 20}},
            ],
        },
    },
    "Bomb Tower": {
        "cost": 500, "range": 140, "damage": 1, "fire_rate": 0.5,
        "projectile": "bomb", "color": (60, 60, 60), "barrel_color": (40, 40, 40),
        "damage_type": "explosion", "splash_radius": 60,
        "upgrades": {
            "path1": [
                {"name": "Bigger Bombs", "cost": 200, "effects": {"splash_radius": 20}},
                {"name": "Extra Range", "cost": 150, "effects": {"range": 30}},
                {"name": "Cluster Bombs", "cost": 600, "effects": {"cluster": True}},
                {"name": "Recursive", "cost": 3000, "effects": {"recursive": True, "damage": 2}},
            ],
            "path2": [
                {"name": "Fuse Time", "cost": 100, "effects": {"fire_rate": 0.2}},
                {"name": "Multi Bombs", "cost": 300, "effects": {"multishot": 2}},
                {"name": "MOAB Mauler", "cost": 800, "effects": {"moab_damage": 10}},
                {"name": "MOAB Assassin", "cost": 3500, "effects": {"moab_damage": 25}},
            ],
        },
    },
    "Ice Monkey": {
        "cost": 400, "range": 120, "damage": 0, "fire_rate": 0.4,
        "projectile": "ice", "color": (100, 180, 255), "barrel_color": (70, 140, 220),
        "damage_type": "freeze", "freeze_duration": 1.5,
        "upgrades": {
            "path1": [
                {"name": "Permafrost", "cost": 100, "effects": {"permafrost": True}},
                {"name": "Cold Snap", "cost": 300, "effects": {"affect_white": True}},
                {"name": "Arctic Wind", "cost": 1500, "effects": {"range": 40, "slow_aura": True}},
                {"name": "Snowstorm", "cost": 4000, "effects": {"global_freeze": True}},
            ],
            "path2": [
                {"name": "Enhanced", "cost": 100, "effects": {"freeze_duration": 0.5}},
                {"name": "Deep Freeze", "cost": 250, "effects": {"damage": 1}},
                {"name": "Cryo Cannon", "cost": 1200, "effects": {"projectile": "cryo", "range": 40}},
                {"name": "Absolute Zero", "cost": 5000, "effects": {"damage": 3, "range": 40}},
            ],
        },
    },
    "Glue Gunner": {
        "cost": 275, "range": 120, "damage": 0, "fire_rate": 0.7,
        "projectile": "glue", "color": (80, 180, 50), "barrel_color": (60, 140, 30),
        "damage_type": "glue", "slow_factor": 0.5, "slow_duration": 3.0,
        "upgrades": {
            "path1": [
                {"name": "Glue Soak", "cost": 100, "effects": {"glue_soak": True}},
                {"name": "Corrosive", "cost": 250, "effects": {"glue_damage": 1}},
                {"name": "Dissolver", "cost": 1500, "effects": {"glue_damage": 2}},
                {"name": "Liquifier", "cost": 4000, "effects": {"glue_damage": 5}},
            ],
            "path2": [
                {"name": "Stickier Glue", "cost": 80, "effects": {"slow_duration": 2.0}},
                {"name": "Stronger Glue", "cost": 200, "effects": {"slow_factor": -0.15}},
                {"name": "MOAB Glue", "cost": 1500, "effects": {"moab_glue": True}},
                {"name": "Super Glue", "cost": 5000, "effects": {"slow_factor": -0.3, "slow_duration": 5.0}},
            ],
        },
    },
    "Buccaneer": {
        "cost": 500, "range": 160, "damage": 1, "fire_rate": 1.0,
        "projectile": "dart", "color": (100, 60, 30), "barrel_color": (70, 40, 20),
        "damage_type": "sharp", "multishot": 2,
        "upgrades": {
            "path1": [
                {"name": "Faster Shot", "cost": 150, "effects": {"fire_rate": 0.4}},
                {"name": "Double Shot", "cost": 300, "effects": {"multishot": 2}},
                {"name": "Destroyer", "cost": 2500, "effects": {"fire_rate": 1.0, "damage": 2}},
                {"name": "Carrier", "cost": 7000, "effects": {"damage": 3, "multishot": 4}},
            ],
            "path2": [
                {"name": "Grape Shot", "cost": 200, "effects": {"grape": True}},
                {"name": "Hot Shot", "cost": 350, "effects": {"damage_type": "fire"}},
                {"name": "Cannon Ship", "cost": 1500, "effects": {"damage": 3}},
                {"name": "Pirates", "cost": 5000, "effects": {"damage": 5, "moab_hook": True}},
            ],
        },
    },
    "Super Monkey": {
        "cost": 2500, "range": 200, "damage": 1, "fire_rate": 10.0,
        "projectile": "laser", "color": (100, 50, 150), "barrel_color": (140, 60, 200),
        "damage_type": "energy",
        "upgrades": {
            "path1": [
                {"name": "Laser Blasts", "cost": 500, "effects": {"damage_type": "energy"}},
                {"name": "Plasma", "cost": 1500, "effects": {"damage": 2}},
                {"name": "Sun Avatar", "cost": 5000, "effects": {"damage": 3, "multishot": 3}},
                {"name": "Sun Temple", "cost": 20000, "effects": {"damage": 10, "range": 50}},
            ],
            "path2": [
                {"name": "Super Range", "cost": 500, "effects": {"range": 40}},
                {"name": "Epic Range", "cost": 800, "effects": {"range": 40}},
                {"name": "Robo Monkey", "cost": 5000, "effects": {"multishot": 2, "damage": 2}},
                {"name": "Tech Terror", "cost": 15000, "effects": {"damage": 5, "ability": "terror"}},
            ],
        },
    },
}

# Targeting modes
TARGETING_MODES = ["First", "Last", "Strong", "Close"]
