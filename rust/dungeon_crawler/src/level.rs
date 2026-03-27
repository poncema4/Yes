use crate::game::*;
use rand::Rng;

#[derive(Clone)]
pub struct Room {
    pub x: usize,
    pub y: usize,
    pub w: usize,
    pub h: usize,
}

impl Room {
    pub fn center(&self) -> (usize, usize) {
        (self.x + self.w / 2, self.y + self.h / 2)
    }

    pub fn intersects(&self, other: &Room) -> bool {
        self.x <= other.x + other.w
            && self.x + self.w >= other.x
            && self.y <= other.y + other.h
            && self.y + self.h >= other.y
    }
}

pub struct Level {
    pub tiles: Vec<Vec<Tile>>,
    pub revealed: Vec<Vec<bool>>,
    pub visible: Vec<Vec<bool>>,
    pub rooms: Vec<Room>,
    pub items: Vec<Item>,
    pub enemies: Vec<Enemy>,
}

pub fn generate_level(depth: usize) -> Level {
    let mut rng = rand::thread_rng();
    let mut tiles = vec![vec![Tile::Wall; MAP_WIDTH]; MAP_HEIGHT];
    let mut rooms: Vec<Room> = Vec::new();

    for _ in 0..200 {
        if rooms.len() >= MAX_ROOMS {
            break;
        }
        let w = rng.gen_range(MIN_ROOM_SIZE..=MAX_ROOM_SIZE);
        let h = rng.gen_range(MIN_ROOM_SIZE..=MAX_ROOM_SIZE);
        let x = rng.gen_range(1..MAP_WIDTH - w - 1);
        let y = rng.gen_range(1..MAP_HEIGHT - h - 1);
        let room = Room { x, y, w, h };

        if rooms.iter().any(|r| room.intersects(r)) {
            continue;
        }

        for ry in room.y..room.y + room.h {
            for rx in room.x..room.x + room.w {
                tiles[ry][rx] = Tile::Floor;
            }
        }

        if let Some(prev) = rooms.last() {
            let (cx, cy) = room.center();
            let (px, py) = prev.center();
            if rng.gen_bool(0.5) {
                carve_h_tunnel(&mut tiles, cx, px, cy);
                carve_v_tunnel(&mut tiles, py, cy, px);
            } else {
                carve_v_tunnel(&mut tiles, cy, py, cx);
                carve_h_tunnel(&mut tiles, cx, px, py);
            }
        }

        rooms.push(room);
    }

    if depth < MAX_DEPTH {
        let (sx, sy) = rooms.last().unwrap().center();
        tiles[sy][sx] = Tile::StairsDown;
    }

    if depth > 1 {
        let (sx, sy) = rooms.first().unwrap().center();
        if sx + 1 < MAP_WIDTH && tiles[sy][sx + 1] == Tile::Floor {
            tiles[sy][sx + 1] = Tile::StairsUp;
        }
    }

    let mut items = Vec::new();
    let num_items = rng.gen_range(3..=6 + depth);
    for _ in 0..num_items {
        let room = &rooms[rng.gen_range(0..rooms.len())];
        if room.w <= 2 || room.h <= 2 {
            continue;
        }
        let ix = rng.gen_range(room.x + 1..room.x + room.w - 1);
        let iy = rng.gen_range(room.y + 1..room.y + room.h - 1);
        if tiles[iy][ix] == Tile::Floor {
            let kind = match rng.gen_range(0..10) {
                0..=3 => ItemKind::HealthPotion,
                4..=5 => ItemKind::StrengthScroll,
                6..=7 => ItemKind::ShieldScroll,
                8 => ItemKind::FireScroll,
                _ => ItemKind::Bomb,
            };
            items.push(Item { x: ix, y: iy, kind });
        }
    }

    let mut enemies = Vec::new();
    let enemy_types: Vec<&str> = match depth {
        1 => vec!["rat", "rat", "goblin"],
        2 => vec!["rat", "goblin", "goblin", "skeleton"],
        3 => vec!["goblin", "skeleton", "skeleton", "ogre"],
        4 => vec!["skeleton", "ogre", "ogre", "dragon"],
        _ => vec!["ogre", "dragon", "dragon"],
    };

    let num_enemies = rng.gen_range(4..=6 + depth * 2);
    for _ in 0..num_enemies {
        if rooms.len() < 2 {
            break;
        }
        let room_idx = rng.gen_range(1..rooms.len());
        let room = &rooms[room_idx];
        if room.w <= 2 || room.h <= 2 {
            continue;
        }
        let ex = rng.gen_range(room.x + 1..room.x + room.w - 1);
        let ey = rng.gen_range(room.y + 1..room.y + room.h - 1);
        if tiles[ey][ex] == Tile::Floor {
            let kind = enemy_types[rng.gen_range(0..enemy_types.len())];
            enemies.push(make_enemy(kind, ex, ey, depth));
        }
    }

    Level {
        tiles,
        revealed: vec![vec![false; MAP_WIDTH]; MAP_HEIGHT],
        visible: vec![vec![false; MAP_WIDTH]; MAP_HEIGHT],
        rooms,
        items,
        enemies,
    }
}

fn carve_h_tunnel(tiles: &mut [Vec<Tile>], x1: usize, x2: usize, y: usize) {
    let (start, end) = if x1 < x2 { (x1, x2) } else { (x2, x1) };
    for x in start..=end {
        if y < MAP_HEIGHT && x < MAP_WIDTH {
            tiles[y][x] = Tile::Floor;
        }
    }
}

fn carve_v_tunnel(tiles: &mut [Vec<Tile>], y1: usize, y2: usize, x: usize) {
    let (start, end) = if y1 < y2 { (y1, y2) } else { (y2, y1) };
    for y in start..=end {
        if y < MAP_HEIGHT && x < MAP_WIDTH {
            tiles[y][x] = Tile::Floor;
        }
    }
}