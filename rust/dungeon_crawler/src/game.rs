use crate::level::{generate_level, Level};
use rand::Rng;
use std::collections::HashMap;

pub const MAP_WIDTH: usize = 40;
pub const MAP_HEIGHT: usize = 22;
pub const MAX_ROOMS: usize = 10;
pub const MIN_ROOM_SIZE: usize = 4;
pub const MAX_ROOM_SIZE: usize = 9;
pub const FOV_RADIUS: i32 = 8;
pub const MAX_DEPTH: usize = 5;

#[derive(Clone, Copy, PartialEq)]
pub enum Tile {
    Wall,
    Floor,
    StairsDown,
    StairsUp,
}

#[derive(Clone, Debug, PartialEq)]
pub enum ItemKind {
    HealthPotion,
    StrengthScroll,
    ShieldScroll,
    FireScroll,
    Bomb,
}

impl ItemKind {
    pub fn name(&self) -> &str {
        match self {
            ItemKind::HealthPotion => "Health Potion",
            ItemKind::StrengthScroll => "Scroll of Strength",
            ItemKind::ShieldScroll => "Scroll of Shield",
            ItemKind::FireScroll => "Scroll of Fireball",
            ItemKind::Bomb => "Bomb",
        }
    }
}

#[derive(Clone, Debug)]
pub struct Item {
    pub x: usize,
    pub y: usize,
    pub kind: ItemKind,
}

#[derive(Clone, PartialEq)]
pub enum EnemyKind {
    Rat,
    Goblin,
    Skeleton,
    Ogre,
    Dragon,
}

#[derive(Clone)]
pub struct Enemy {
    pub x: usize,
    pub y: usize,
    pub hp: i32,
    pub max_hp: i32,
    pub attack: i32,
    pub defense: i32,
    pub name: String,
    pub xp_value: i32,
    pub kind: EnemyKind,
}

pub fn make_enemy(kind: &str, x: usize, y: usize, depth: usize) -> Enemy {
    let scale = 1.0 + depth as f32 * 0.3;
    match kind {
        "rat" => Enemy {
            x, y,
            hp: (5.0 * scale) as i32,
            max_hp: (5.0 * scale) as i32,
            attack: (2.0 * scale) as i32,
            defense: 0,
            name: "Rat".into(),
            xp_value: (5.0 * scale) as i32,
            kind: EnemyKind::Rat,
        },
        "goblin" => Enemy {
            x, y,
            hp: (10.0 * scale) as i32,
            max_hp: (10.0 * scale) as i32,
            attack: (4.0 * scale) as i32,
            defense: (1.0 * scale) as i32,
            name: "Goblin".into(),
            xp_value: (10.0 * scale) as i32,
            kind: EnemyKind::Goblin,
        },
        "skeleton" => Enemy {
            x, y,
            hp: (15.0 * scale) as i32,
            max_hp: (15.0 * scale) as i32,
            attack: (6.0 * scale) as i32,
            defense: (2.0 * scale) as i32,
            name: "Skeleton".into(),
            xp_value: (15.0 * scale) as i32,
            kind: EnemyKind::Skeleton,
        },
        "ogre" => Enemy {
            x, y,
            hp: (25.0 * scale) as i32,
            max_hp: (25.0 * scale) as i32,
            attack: (8.0 * scale) as i32,
            defense: (3.0 * scale) as i32,
            name: "Ogre".into(),
            xp_value: (25.0 * scale) as i32,
            kind: EnemyKind::Ogre,
        },
        "dragon" => Enemy {
            x, y,
            hp: (50.0 * scale) as i32,
            max_hp: (50.0 * scale) as i32,
            attack: (12.0 * scale) as i32,
            defense: (5.0 * scale) as i32,
            name: "Dragon".into(),
            xp_value: (50.0 * scale) as i32,
            kind: EnemyKind::Dragon,
        },
        _ => make_enemy("rat", x, y, depth),
    }
}

pub struct Player {
    pub x: usize,
    pub y: usize,
    pub hp: i32,
    pub max_hp: i32,
    pub attack: i32,
    pub defense: i32,
    pub xp: i32,
    pub level: i32,
    pub xp_to_next: i32,
    pub inventory: Vec<ItemKind>,
    pub gold: i32,
    pub kills: i32,
}

impl Player {
    pub fn new(x: usize, y: usize) -> Self {
        Player {
            x, y,
            hp: 30, max_hp: 30,
            attack: 5, defense: 2,
            xp: 0, level: 1, xp_to_next: 20,
            inventory: Vec::new(),
            gold: 0, kills: 0,
        }
    }

    pub fn gain_xp(&mut self, amount: i32) -> Option<String> {
        self.xp += amount;
        if self.xp >= self.xp_to_next {
            self.xp -= self.xp_to_next;
            self.level += 1;
            self.xp_to_next = (self.xp_to_next as f32 * 1.5) as i32;
            self.max_hp += 5;
            self.hp = self.max_hp;
            self.attack += 2;
            self.defense += 1;
            Some(format!("LEVEL UP! Now level {}!", self.level))
        } else {
            None
        }
    }
}

pub struct MsgEntry {
    pub text: String,
    pub color: [f32; 4],
}

pub struct Game {
    pub player: Player,
    pub levels: HashMap<usize, Level>,
    pub current_depth: usize,
    pub messages: Vec<MsgEntry>,
    pub game_over: bool,
    pub victory: bool,
    pub turns: u32,
}

impl Game {
    pub fn new() -> Self {
        let first_level = generate_level(1);
        let (px, py) = first_level.rooms[0].center();
        let player = Player::new(px, py);
        let mut levels = HashMap::new();
        levels.insert(1, first_level);

        let mut game = Game {
            player, levels,
            current_depth: 1,
            messages: Vec::new(),
            game_over: false,
            victory: false,
            turns: 0,
        };
        game.log("Welcome to the Dungeon! Clear floor 5 to win!", [1.0, 1.0, 0.0, 1.0]);
        game.log("WASD/Arrows=move  G=grab  1-9=use item  ./,=stairs  ESC=quit", [0.5, 0.5, 0.5, 1.0]);
        game.compute_fov();
        game
    }

    pub fn log(&mut self, msg: &str, color: [f32; 4]) {
        self.messages.push(MsgEntry { text: msg.to_string(), color });
        if self.messages.len() > 5 {
            self.messages.remove(0);
        }
    }

    pub fn level(&self) -> &Level {
        self.levels.get(&self.current_depth).unwrap()
    }

    pub fn level_mut(&mut self) -> &mut Level {
        self.levels.get_mut(&self.current_depth).unwrap()
    }

    pub fn compute_fov(&mut self) {
        let level = self.levels.get_mut(&self.current_depth).unwrap();
        for row in level.visible.iter_mut() {
            for v in row.iter_mut() {
                *v = false;
            }
        }

        let px = self.player.x as i32;
        let py = self.player.y as i32;

        for angle in 0..360 {
            let rad = (angle as f64) * std::f64::consts::PI / 180.0;
            let dx = rad.cos();
            let dy = rad.sin();
            let mut x = px as f64 + 0.5;
            let mut y = py as f64 + 0.5;

            for _ in 0..FOV_RADIUS {
                let ix = x as i32;
                let iy = y as i32;
                if ix < 0 || iy < 0 || ix >= MAP_WIDTH as i32 || iy >= MAP_HEIGHT as i32 {
                    break;
                }
                let ux = ix as usize;
                let uy = iy as usize;
                level.visible[uy][ux] = true;
                level.revealed[uy][ux] = true;
                if level.tiles[uy][ux] == Tile::Wall {
                    break;
                }
                x += dx;
                y += dy;
            }
        }
    }

    pub fn try_move(&mut self, dx: i32, dy: i32) {
        let nx = (self.player.x as i32 + dx) as usize;
        let ny = (self.player.y as i32 + dy) as usize;

        if nx >= MAP_WIDTH || ny >= MAP_HEIGHT {
            return;
        }

        let enemy_idx = self.level().enemies.iter().position(|e| e.x == nx && e.y == ny);
        if let Some(idx) = enemy_idx {
            self.attack_enemy(idx);
            self.turns += 1;
            self.enemy_turns();
            self.compute_fov();
            return;
        }

        if self.level().tiles[ny][nx] == Tile::Wall {
            return;
        }

        self.player.x = nx;
        self.player.y = ny;
        self.turns += 1;

        let mut rng = rand::thread_rng();
        if rng.gen_range(0..20) == 0 {
            let gold = rng.gen_range(1..=5 + self.current_depth as i32);
            self.player.gold += gold;
            self.log(&format!("Found {} gold!", gold), [1.0, 1.0, 0.0, 1.0]);
        }

        if self.current_depth == MAX_DEPTH && self.levels.get(&self.current_depth).unwrap().enemies.is_empty() {
            self.victory = true;
            self.game_over = true;
            self.log("You cleared the final floor! VICTORY!", [1.0, 1.0, 0.0, 1.0]);
        }

        self.enemy_turns();
        self.compute_fov();
    }

    fn attack_enemy(&mut self, idx: usize) {
        let mut rng = rand::thread_rng();
        let damage = (self.player.attack - self.level().enemies[idx].defense + rng.gen_range(-1..=2)).max(1);
        let enemy = &mut self.level_mut().enemies[idx];
        enemy.hp -= damage;
        let name = enemy.name.clone();
        let dead = enemy.hp <= 0;
        let xp = enemy.xp_value;

        if dead {
            self.log(&format!("{} killed! ({} dmg)", name, damage), [1.0, 0.8, 0.0, 1.0]);
            self.level_mut().enemies.remove(idx);
            self.player.kills += 1;
            if let Some(msg) = self.player.gain_xp(xp) {
                self.log(&msg, [1.0, 0.0, 1.0, 1.0]);
            } else {
                self.log(&format!("+{} XP", xp), [0.0, 1.0, 1.0, 1.0]);
            }
        } else {
            let hp = self.level().enemies[idx].hp;
            let max_hp = self.level().enemies[idx].max_hp;
            self.log(
                &format!("Hit {} for {} ({}/{})", name, damage, hp, max_hp),
                [1.0, 1.0, 1.0, 1.0],
            );
        }
    }

    fn enemy_turns(&mut self) {
        let px = self.player.x;
        let py = self.player.y;
        let level = self.levels.get_mut(&self.current_depth).unwrap();

        let mut damage_total = 0i32;
        let mut attackers: Vec<String> = Vec::new();
        let enemy_positions: Vec<(usize, usize)> = level.enemies.iter().map(|e| (e.x, e.y)).collect();

        for enemy in level.enemies.iter_mut() {
            let dist = ((enemy.x as i32 - px as i32).pow(2) + (enemy.y as i32 - py as i32).pow(2)) as f64;
            let dist = dist.sqrt();

            if !level.visible[enemy.y][enemy.x] && dist > 5.0 {
                continue;
            }

            let dx = if px > enemy.x { 1i32 } else if px < enemy.x { -1 } else { 0 };
            let dy = if py > enemy.y { 1i32 } else if py < enemy.y { -1 } else { 0 };

            let nx = (enemy.x as i32 + dx) as usize;
            let ny = (enemy.y as i32 + dy) as usize;

            if nx == px && ny == py {
                let mut rng = rand::thread_rng();
                let dmg = (enemy.attack - self.player.defense + rng.gen_range(-1..=1)).max(0);
                damage_total += dmg;
                attackers.push(enemy.name.clone());
            } else if nx < MAP_WIDTH && ny < MAP_HEIGHT && level.tiles[ny][nx] == Tile::Floor {
                let blocked = enemy_positions.iter().any(|&(ex, ey)| ex == nx && ey == ny);
                if !blocked {
                    enemy.x = nx;
                    enemy.y = ny;
                }
            }
        }

        if damage_total > 0 {
            self.player.hp -= damage_total;
            let names = attackers.join(", ");
            self.log(&format!("{} hit you for {}!", names, damage_total), [1.0, 0.2, 0.2, 1.0]);
            if self.player.hp <= 0 {
                self.game_over = true;
                self.log("You have been slain...", [0.5, 0.0, 0.0, 1.0]);
            }
        }
    }

    pub fn grab_item(&mut self) {
        let px = self.player.x;
        let py = self.player.y;
        let level = self.levels.get_mut(&self.current_depth).unwrap();

        if let Some(idx) = level.items.iter().position(|i| i.x == px && i.y == py) {
            let item = level.items.remove(idx);
            let name = item.kind.name().to_string();
            if self.player.inventory.len() < 9 {
                self.player.inventory.push(item.kind);
                self.log(&format!("Picked up {}!", name), [0.0, 1.0, 0.0, 1.0]);
            } else {
                level.items.push(item);
                self.log("Inventory full!", [1.0, 0.0, 0.0, 1.0]);
            }
        } else {
            self.log("Nothing here.", [0.5, 0.5, 0.5, 1.0]);
        }
    }

    pub fn use_item(&mut self, slot: usize) {
        if slot >= self.player.inventory.len() {
            return;
        }

        let item = self.player.inventory.remove(slot);
        match item {
            ItemKind::HealthPotion => {
                let heal = 15;
                self.player.hp = (self.player.hp + heal).min(self.player.max_hp);
                self.log(
                    &format!("Healed {}HP ({}/{})", heal, self.player.hp, self.player.max_hp),
                    [1.0, 0.3, 0.3, 1.0],
                );
            }
            ItemKind::StrengthScroll => {
                self.player.attack += 3;
                self.log(&format!("ATK -> {}!", self.player.attack), [1.0, 1.0, 0.0, 1.0]);
            }
            ItemKind::ShieldScroll => {
                self.player.defense += 2;
                self.log(&format!("DEF -> {}!", self.player.defense), [0.0, 1.0, 1.0, 1.0]);
            }
            ItemKind::FireScroll => {
                let mut killed = 0;
                let mut xp_gained = 0;
                let level = self.levels.get_mut(&self.current_depth).unwrap();
                level.enemies.retain(|e| {
                    if level.visible[e.y][e.x] {
                        if e.hp <= 12 {
                            killed += 1;
                            xp_gained += e.xp_value;
                            false
                        } else {
                            true
                        }
                    } else {
                        true
                    }
                });
                for enemy in level.enemies.iter_mut() {
                    if level.visible[enemy.y][enemy.x] {
                        enemy.hp -= 12;
                    }
                }
                self.player.kills += killed;
                self.log(&format!("FIREBALL! {} killed!", killed), [1.0, 0.4, 0.0, 1.0]);
                if xp_gained > 0 {
                    if let Some(msg) = self.player.gain_xp(xp_gained) {
                        self.log(&msg, [1.0, 0.0, 1.0, 1.0]);
                    }
                }
            }
            ItemKind::Bomb => {
                let px = self.player.x as i32;
                let py = self.player.y as i32;
                let mut killed = 0;
                let mut xp_gained = 0;
                let level = self.levels.get_mut(&self.current_depth).unwrap();
                level.enemies.retain(|e| {
                    let dist = ((e.x as i32 - px).pow(2) + (e.y as i32 - py).pow(2)) as f64;
                    if dist.sqrt() <= 3.0 && e.hp <= 20 {
                        killed += 1;
                        xp_gained += e.xp_value;
                        false
                    } else {
                        true
                    }
                });
                for enemy in level.enemies.iter_mut() {
                    let dist = ((enemy.x as i32 - px).pow(2) + (enemy.y as i32 - py).pow(2)) as f64;
                    if dist.sqrt() <= 3.0 {
                        enemy.hp -= 20;
                    }
                }
                self.player.hp -= 5;
                self.player.kills += killed;
                self.log(&format!("BOOM! {} killed! (-5 HP)", killed), [1.0, 0.2, 0.2, 1.0]);
                if xp_gained > 0 {
                    if let Some(msg) = self.player.gain_xp(xp_gained) {
                        self.log(&msg, [1.0, 0.0, 1.0, 1.0]);
                    }
                }
                if self.player.hp <= 0 {
                    self.game_over = true;
                    self.log("You blew yourself up...", [0.5, 0.0, 0.0, 1.0]);
                }
            }
        }
    }

    pub fn go_downstairs(&mut self) {
        if self.level().tiles[self.player.y][self.player.x] != Tile::StairsDown {
            self.log("No stairs down here.", [0.5, 0.5, 0.5, 1.0]);
            return;
        }

        self.current_depth += 1;
        if !self.levels.contains_key(&self.current_depth) {
            self.levels.insert(self.current_depth, generate_level(self.current_depth));
        }
        let (px, py) = self.levels[&self.current_depth].rooms[0].center();
        self.player.x = px;
        self.player.y = py;
        self.log(&format!("Descending to floor {}...", self.current_depth), [0.0, 1.0, 1.0, 1.0]);
        self.compute_fov();
    }

    pub fn go_upstairs(&mut self) {
        if self.level().tiles[self.player.y][self.player.x] != Tile::StairsUp {
            self.log("No stairs up here.", [0.5, 0.5, 0.5, 1.0]);
            return;
        }
        if self.current_depth <= 1 {
            return;
        }

        self.current_depth -= 1;
        let level = self.levels.get(&self.current_depth).unwrap();
        let mut stair_pos = (self.player.x, self.player.y);
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                if level.tiles[y][x] == Tile::StairsDown {
                    stair_pos = (x, y);
                }
            }
        }
        self.player.x = stair_pos.0;
        self.player.y = stair_pos.1;
        self.log(&format!("Ascending to floor {}...", self.current_depth), [0.0, 1.0, 1.0, 1.0]);
        self.compute_fov();
    }
}