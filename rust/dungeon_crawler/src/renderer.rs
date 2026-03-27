use macroquad::prelude::*;
use crate::game::*;

const TILE_SIZE: f32 = 32.0;
const HUD_HEIGHT: f32 = 36.0;
const MAP_OFFSET_Y: f32 = HUD_HEIGHT;

fn draw_filled_ellipse(cx: f32, cy: f32, rx: f32, ry: f32, color: Color) {
    let segments = 24;
    for i in 0..segments {
        let a1 = (i as f32 / segments as f32) * std::f32::consts::TAU;
        let a2 = ((i + 1) as f32 / segments as f32) * std::f32::consts::TAU;
        draw_triangle(
            Vec2::new(cx, cy),
            Vec2::new(cx + rx * a1.cos(), cy + ry * a1.sin()),
            Vec2::new(cx + rx * a2.cos(), cy + ry * a2.sin()),
            color,
        );
    }
}

pub fn render(game: &Game) {
    clear_background(Color::new(0.02, 0.02, 0.04, 1.0));

    let level = game.level();

    for y in 0..MAP_HEIGHT {
        for x in 0..MAP_WIDTH {
            let sx = x as f32 * TILE_SIZE;
            let sy = y as f32 * TILE_SIZE + MAP_OFFSET_Y;

            if level.visible[y][x] {
                draw_tile(level.tiles[y][x], sx, sy, 1.0);
            } else if level.revealed[y][x] {
                draw_tile(level.tiles[y][x], sx, sy, 0.25);
            }
        }
    }

    for item in &level.items {
        if level.visible[item.y][item.x] {
            let sx = item.x as f32 * TILE_SIZE;
            let sy = item.y as f32 * TILE_SIZE + MAP_OFFSET_Y;
            draw_item(&item.kind, sx, sy);
        }
    }

    for enemy in &level.enemies {
        if level.visible[enemy.y][enemy.x] {
            let sx = enemy.x as f32 * TILE_SIZE;
            let sy = enemy.y as f32 * TILE_SIZE + MAP_OFFSET_Y;
            draw_enemy_sprite(enemy, sx, sy);
        }
    }

    let px = game.player.x as f32 * TILE_SIZE;
    let py = game.player.y as f32 * TILE_SIZE + MAP_OFFSET_Y;
    draw_player(px, py);

    draw_hud(game);

    let inv_y = MAP_HEIGHT as f32 * TILE_SIZE + MAP_OFFSET_Y + 4.0;
    draw_inventory(game, inv_y);

    let msg_y = inv_y + 24.0;
    draw_messages(game, msg_y);

    if game.game_over {
        draw_game_over(game);
    }
}

fn draw_tile(tile: Tile, x: f32, y: f32, brightness: f32) {
    let b = brightness;
    match tile {
        Tile::Wall => {
            draw_rectangle(x, y, TILE_SIZE, TILE_SIZE, Color::new(0.3 * b, 0.25 * b, 0.2 * b, 1.0));
            draw_rectangle(x + 1.0, y + 1.0, TILE_SIZE * 0.45, TILE_SIZE * 0.45,
                Color::new(0.35 * b, 0.28 * b, 0.22 * b, 1.0));
            draw_rectangle(x + TILE_SIZE * 0.5 + 1.0, y + 1.0, TILE_SIZE * 0.45, TILE_SIZE * 0.45,
                Color::new(0.38 * b, 0.3 * b, 0.24 * b, 1.0));
            draw_rectangle(x + TILE_SIZE * 0.25, y + TILE_SIZE * 0.5 + 1.0, TILE_SIZE * 0.45, TILE_SIZE * 0.45,
                Color::new(0.32 * b, 0.26 * b, 0.2 * b, 1.0));
        }
        Tile::Floor => {
            draw_rectangle(x, y, TILE_SIZE, TILE_SIZE, Color::new(0.15 * b, 0.12 * b, 0.1 * b, 1.0));
            draw_rectangle(x + 2.0, y + 2.0, 3.0, 3.0, Color::new(0.18 * b, 0.14 * b, 0.12 * b, 1.0));
            draw_rectangle(x + 14.0, y + 18.0, 2.0, 2.0, Color::new(0.12 * b, 0.1 * b, 0.08 * b, 1.0));
        }
        Tile::StairsDown => {
            draw_rectangle(x, y, TILE_SIZE, TILE_SIZE, Color::new(0.15 * b, 0.12 * b, 0.1 * b, 1.0));
            let c = Color::new(0.2 * b, 0.6 * b, 0.8 * b, 1.0);
            for i in 0..4 {
                let step_y = y + 4.0 + i as f32 * 7.0;
                let step_x = x + 6.0 + i as f32 * 2.0;
                let step_w = TILE_SIZE - 12.0 - i as f32 * 4.0;
                draw_rectangle(step_x, step_y, step_w, 5.0, c);
            }
        }
        Tile::StairsUp => {
            draw_rectangle(x, y, TILE_SIZE, TILE_SIZE, Color::new(0.15 * b, 0.12 * b, 0.1 * b, 1.0));
            let c = Color::new(0.2 * b, 0.8 * b, 0.6 * b, 1.0);
            for i in 0..4 {
                let step_y = y + TILE_SIZE - 8.0 - i as f32 * 7.0;
                let step_x = x + 6.0 + i as f32 * 2.0;
                let step_w = TILE_SIZE - 12.0 - i as f32 * 4.0;
                draw_rectangle(step_x, step_y, step_w, 5.0, c);
            }
        }
    }
}

fn draw_player(x: f32, y: f32) {
    let s = TILE_SIZE;
    draw_filled_ellipse(x + s * 0.5, y + s * 0.9, s * 0.3, s * 0.08, Color::new(0.0, 0.0, 0.0, 0.3));
    draw_rectangle(x + s * 0.2, y + s * 0.75, s * 0.2, s * 0.15, Color::new(0.4, 0.25, 0.1, 1.0));
    draw_rectangle(x + s * 0.6, y + s * 0.75, s * 0.2, s * 0.15, Color::new(0.4, 0.25, 0.1, 1.0));
    draw_rectangle(x + s * 0.25, y + s * 0.6, s * 0.15, s * 0.2, Color::new(0.3, 0.3, 0.6, 1.0));
    draw_rectangle(x + s * 0.6, y + s * 0.6, s * 0.15, s * 0.2, Color::new(0.3, 0.3, 0.6, 1.0));
    draw_rectangle(x + s * 0.2, y + s * 0.3, s * 0.6, s * 0.35, Color::new(0.8, 0.7, 0.2, 1.0));
    draw_rectangle(x + s * 0.2, y + s * 0.55, s * 0.6, s * 0.06, Color::new(0.5, 0.3, 0.1, 1.0));
    draw_circle(x + s * 0.5, y + s * 0.22, s * 0.14, Color::new(0.9, 0.75, 0.55, 1.0));
    draw_rectangle(x + s * 0.3, y + s * 0.08, s * 0.4, s * 0.12, Color::new(0.7, 0.6, 0.15, 1.0));
    draw_triangle(
        Vec2::new(x + s * 0.5, y + s * 0.02),
        Vec2::new(x + s * 0.4, y + s * 0.1),
        Vec2::new(x + s * 0.6, y + s * 0.1),
        Color::new(0.7, 0.6, 0.15, 1.0),
    );
    draw_circle(x + s * 0.43, y + s * 0.2, s * 0.025, WHITE);
    draw_circle(x + s * 0.57, y + s * 0.2, s * 0.025, WHITE);
    draw_rectangle(x + s * 0.82, y + s * 0.15, s * 0.06, s * 0.45, Color::new(0.8, 0.8, 0.85, 1.0));
    draw_rectangle(x + s * 0.75, y + s * 0.35, s * 0.2, s * 0.06, Color::new(0.6, 0.5, 0.1, 1.0));
    draw_circle(x + s * 0.12, y + s * 0.45, s * 0.12, Color::new(0.5, 0.5, 0.6, 1.0));
    draw_circle(x + s * 0.12, y + s * 0.45, s * 0.06, Color::new(0.7, 0.6, 0.15, 1.0));
}

fn draw_enemy_sprite(enemy: &Enemy, x: f32, y: f32) {
    match enemy.kind {
        EnemyKind::Rat => draw_rat(x, y),
        EnemyKind::Goblin => draw_goblin(x, y),
        EnemyKind::Skeleton => draw_skeleton(x, y),
        EnemyKind::Ogre => draw_ogre(x, y),
        EnemyKind::Dragon => draw_dragon(x, y),
    }
    let hp_frac = enemy.hp as f32 / enemy.max_hp as f32;
    draw_rectangle(x + 2.0, y, TILE_SIZE - 4.0, 3.0, Color::new(0.3, 0.0, 0.0, 0.8));
    draw_rectangle(x + 2.0, y, (TILE_SIZE - 4.0) * hp_frac, 3.0, Color::new(0.0, 0.8, 0.0, 0.8));
}

fn draw_rat(x: f32, y: f32) {
    let s = TILE_SIZE;
    draw_filled_ellipse(x + s * 0.5, y + s * 0.9, s * 0.2, s * 0.05, Color::new(0.0, 0.0, 0.0, 0.3));
    draw_line(x + s * 0.15, y + s * 0.6, x + s * 0.05, y + s * 0.3, 2.0, Color::new(0.6, 0.4, 0.35, 1.0));
    draw_filled_ellipse(x + s * 0.5, y + s * 0.6, s * 0.25, s * 0.18, Color::new(0.45, 0.3, 0.2, 1.0));
    draw_filled_ellipse(x + s * 0.75, y + s * 0.55, s * 0.15, s * 0.12, Color::new(0.5, 0.35, 0.25, 1.0));
    draw_circle(x + s * 0.78, y + s * 0.42, s * 0.06, Color::new(0.6, 0.4, 0.3, 1.0));
    draw_circle(x + s * 0.88, y + s * 0.45, s * 0.05, Color::new(0.6, 0.4, 0.3, 1.0));
    draw_circle(x + s * 0.8, y + s * 0.52, s * 0.025, Color::new(1.0, 0.2, 0.2, 1.0));
    draw_rectangle(x + s * 0.35, y + s * 0.72, s * 0.08, s * 0.12, Color::new(0.4, 0.25, 0.18, 1.0));
    draw_rectangle(x + s * 0.55, y + s * 0.72, s * 0.08, s * 0.12, Color::new(0.4, 0.25, 0.18, 1.0));
}

fn draw_goblin(x: f32, y: f32) {
    let s = TILE_SIZE;
    draw_filled_ellipse(x + s * 0.5, y + s * 0.9, s * 0.25, s * 0.06, Color::new(0.0, 0.0, 0.0, 0.3));
    draw_rectangle(x + s * 0.3, y + s * 0.7, s * 0.12, s * 0.18, Color::new(0.2, 0.5, 0.15, 1.0));
    draw_rectangle(x + s * 0.58, y + s * 0.7, s * 0.12, s * 0.18, Color::new(0.2, 0.5, 0.15, 1.0));
    draw_rectangle(x + s * 0.25, y + s * 0.4, s * 0.5, s * 0.35, Color::new(0.25, 0.55, 0.2, 1.0));
    draw_circle(x + s * 0.5, y + s * 0.3, s * 0.16, Color::new(0.3, 0.6, 0.25, 1.0));
    draw_triangle(
        Vec2::new(x + s * 0.2, y + s * 0.2),
        Vec2::new(x + s * 0.32, y + s * 0.25),
        Vec2::new(x + s * 0.28, y + s * 0.35),
        Color::new(0.3, 0.6, 0.25, 1.0),
    );
    draw_triangle(
        Vec2::new(x + s * 0.8, y + s * 0.2),
        Vec2::new(x + s * 0.68, y + s * 0.25),
        Vec2::new(x + s * 0.72, y + s * 0.35),
        Color::new(0.3, 0.6, 0.25, 1.0),
    );
    draw_circle(x + s * 0.42, y + s * 0.28, s * 0.04, YELLOW);
    draw_circle(x + s * 0.58, y + s * 0.28, s * 0.04, YELLOW);
    draw_circle(x + s * 0.42, y + s * 0.28, s * 0.02, BLACK);
    draw_circle(x + s * 0.58, y + s * 0.28, s * 0.02, BLACK);
    draw_rectangle(x + s * 0.78, y + s * 0.3, s * 0.06, s * 0.35, Color::new(0.4, 0.25, 0.1, 1.0));
    draw_circle(x + s * 0.81, y + s * 0.28, s * 0.06, Color::new(0.35, 0.2, 0.08, 1.0));
}

fn draw_skeleton(x: f32, y: f32) {
    let s = TILE_SIZE;
    draw_circle(x + s * 0.5, y + s * 0.2, s * 0.15, Color::new(0.9, 0.88, 0.82, 1.0));
    draw_circle(x + s * 0.43, y + s * 0.18, s * 0.04, BLACK);
    draw_circle(x + s * 0.57, y + s * 0.18, s * 0.04, BLACK);
    draw_rectangle(x + s * 0.4, y + s * 0.28, s * 0.2, s * 0.04, Color::new(0.85, 0.83, 0.77, 1.0));
    draw_rectangle(x + s * 0.47, y + s * 0.32, s * 0.06, s * 0.3, Color::new(0.85, 0.83, 0.77, 1.0));
    for i in 0..3 {
        let ry = y + s * 0.36 + i as f32 * s * 0.08;
        draw_rectangle(x + s * 0.3, ry, s * 0.4, s * 0.03, Color::new(0.8, 0.78, 0.72, 1.0));
    }
    draw_line(x + s * 0.3, y + s * 0.38, x + s * 0.15, y + s * 0.55, 2.0, Color::new(0.85, 0.83, 0.77, 1.0));
    draw_line(x + s * 0.7, y + s * 0.38, x + s * 0.85, y + s * 0.55, 2.0, Color::new(0.85, 0.83, 0.77, 1.0));
    draw_line(x + s * 0.47, y + s * 0.62, x + s * 0.35, y + s * 0.88, 2.0, Color::new(0.85, 0.83, 0.77, 1.0));
    draw_line(x + s * 0.53, y + s * 0.62, x + s * 0.65, y + s * 0.88, 2.0, Color::new(0.85, 0.83, 0.77, 1.0));
    draw_rectangle(x + s * 0.85, y + s * 0.2, s * 0.04, s * 0.4, Color::new(0.7, 0.7, 0.75, 1.0));
}

fn draw_ogre(x: f32, y: f32) {
    let s = TILE_SIZE;
    draw_filled_ellipse(x + s * 0.5, y + s * 0.92, s * 0.35, s * 0.06, Color::new(0.0, 0.0, 0.0, 0.3));
    draw_rectangle(x + s * 0.2, y + s * 0.65, s * 0.2, s * 0.25, Color::new(0.55, 0.35, 0.2, 1.0));
    draw_rectangle(x + s * 0.6, y + s * 0.65, s * 0.2, s * 0.25, Color::new(0.55, 0.35, 0.2, 1.0));
    draw_rectangle(x + s * 0.12, y + s * 0.25, s * 0.76, s * 0.45, Color::new(0.6, 0.4, 0.25, 1.0));
    draw_circle(x + s * 0.5, y + s * 0.18, s * 0.18, Color::new(0.6, 0.4, 0.25, 1.0));
    draw_circle(x + s * 0.42, y + s * 0.16, s * 0.04, YELLOW);
    draw_circle(x + s * 0.58, y + s * 0.16, s * 0.04, YELLOW);
    draw_rectangle(x + s * 0.4, y + s * 0.25, s * 0.06, s * 0.05, WHITE);
    draw_rectangle(x + s * 0.54, y + s * 0.25, s * 0.06, s * 0.05, WHITE);
    draw_rectangle(x + s * 0.0, y + s * 0.3, s * 0.15, s * 0.3, Color::new(0.55, 0.35, 0.2, 1.0));
    draw_rectangle(x + s * 0.85, y + s * 0.3, s * 0.15, s * 0.3, Color::new(0.55, 0.35, 0.2, 1.0));
}

fn draw_dragon(x: f32, y: f32) {
    let s = TILE_SIZE;
    draw_triangle(
        Vec2::new(x + s * 0.1, y + s * 0.1),
        Vec2::new(x + s * 0.3, y + s * 0.3),
        Vec2::new(x + s * 0.05, y + s * 0.5),
        Color::new(0.7, 0.15, 0.0, 1.0),
    );
    draw_triangle(
        Vec2::new(x + s * 0.9, y + s * 0.1),
        Vec2::new(x + s * 0.7, y + s * 0.3),
        Vec2::new(x + s * 0.95, y + s * 0.5),
        Color::new(0.7, 0.15, 0.0, 1.0),
    );
    draw_filled_ellipse(x + s * 0.5, y + s * 0.55, s * 0.25, s * 0.2, Color::new(0.85, 0.2, 0.0, 1.0));
    draw_circle(x + s * 0.5, y + s * 0.3, s * 0.15, Color::new(0.9, 0.25, 0.05, 1.0));
    draw_triangle(
        Vec2::new(x + s * 0.35, y + s * 0.1),
        Vec2::new(x + s * 0.38, y + s * 0.25),
        Vec2::new(x + s * 0.42, y + s * 0.2),
        Color::new(0.3, 0.1, 0.0, 1.0),
    );
    draw_triangle(
        Vec2::new(x + s * 0.65, y + s * 0.1),
        Vec2::new(x + s * 0.62, y + s * 0.25),
        Vec2::new(x + s * 0.58, y + s * 0.2),
        Color::new(0.3, 0.1, 0.0, 1.0),
    );
    draw_circle(x + s * 0.43, y + s * 0.27, s * 0.035, YELLOW);
    draw_circle(x + s * 0.57, y + s * 0.27, s * 0.035, YELLOW);
    draw_circle(x + s * 0.46, y + s * 0.35, s * 0.02, Color::new(0.3, 0.1, 0.0, 1.0));
    draw_circle(x + s * 0.54, y + s * 0.35, s * 0.02, Color::new(0.3, 0.1, 0.0, 1.0));
    draw_line(x + s * 0.5, y + s * 0.7, x + s * 0.2, y + s * 0.9, 3.0, Color::new(0.8, 0.18, 0.0, 1.0));
    draw_line(x + s * 0.2, y + s * 0.9, x + s * 0.1, y + s * 0.85, 2.0, Color::new(0.8, 0.18, 0.0, 1.0));
    draw_rectangle(x + s * 0.3, y + s * 0.68, s * 0.12, s * 0.15, Color::new(0.8, 0.18, 0.0, 1.0));
    draw_rectangle(x + s * 0.58, y + s * 0.68, s * 0.12, s * 0.15, Color::new(0.8, 0.18, 0.0, 1.0));
}

fn draw_item(kind: &ItemKind, x: f32, y: f32) {
    match kind {
        ItemKind::HealthPotion => draw_potion(x, y, Color::new(0.9, 0.15, 0.15, 1.0)),
        ItemKind::StrengthScroll => draw_scroll(x, y, Color::new(0.9, 0.8, 0.1, 1.0)),
        ItemKind::ShieldScroll => draw_scroll(x, y, Color::new(0.1, 0.8, 0.9, 1.0)),
        ItemKind::FireScroll => draw_scroll(x, y, Color::new(1.0, 0.45, 0.0, 1.0)),
        ItemKind::Bomb => draw_bomb(x, y),
    }
}

fn draw_potion(x: f32, y: f32, color: Color) {
    let s = TILE_SIZE;
    draw_rectangle(x + s * 0.3, y + s * 0.4, s * 0.4, s * 0.45, color);
    draw_rectangle(x + s * 0.25, y + s * 0.5, s * 0.5, s * 0.3, color);
    draw_rectangle(x + s * 0.4, y + s * 0.2, s * 0.2, s * 0.25, Color::new(0.6, 0.6, 0.7, 0.8));
    draw_rectangle(x + s * 0.38, y + s * 0.15, s * 0.24, s * 0.1, Color::new(0.5, 0.3, 0.1, 1.0));
    draw_rectangle(x + s * 0.35, y + s * 0.5, s * 0.08, s * 0.15, Color::new(1.0, 1.0, 1.0, 0.3));
    draw_circle(x + s * 0.55, y + s * 0.65, s * 0.03, Color::new(1.0, 1.0, 1.0, 0.4));
    draw_circle(x + s * 0.45, y + s * 0.7, s * 0.02, Color::new(1.0, 1.0, 1.0, 0.3));
}

fn draw_scroll(x: f32, y: f32, color: Color) {
    let s = TILE_SIZE;
    draw_rectangle(x + s * 0.2, y + s * 0.25, s * 0.6, s * 0.5, Color::new(0.9, 0.85, 0.7, 1.0));
    draw_filled_ellipse(x + s * 0.5, y + s * 0.25, s * 0.35, s * 0.08, color);
    draw_filled_ellipse(x + s * 0.5, y + s * 0.75, s * 0.35, s * 0.08, color);
    draw_circle(x + s * 0.5, y + s * 0.5, s * 0.1, color);
    draw_circle(x + s * 0.5, y + s * 0.5, s * 0.06, Color::new(0.9, 0.85, 0.7, 1.0));
}

fn draw_bomb(x: f32, y: f32) {
    let s = TILE_SIZE;
    draw_circle(x + s * 0.5, y + s * 0.58, s * 0.22, Color::new(0.2, 0.2, 0.22, 1.0));
    draw_circle(x + s * 0.42, y + s * 0.5, s * 0.06, Color::new(0.35, 0.35, 0.4, 1.0));
    draw_line(x + s * 0.58, y + s * 0.38, x + s * 0.7, y + s * 0.2, 2.0, Color::new(0.5, 0.35, 0.1, 1.0));
    draw_circle(x + s * 0.7, y + s * 0.18, s * 0.04, Color::new(1.0, 0.7, 0.0, 1.0));
    draw_circle(x + s * 0.7, y + s * 0.18, s * 0.02, Color::new(1.0, 1.0, 0.5, 1.0));
}

fn draw_hud(game: &Game) {
    let w = MAP_WIDTH as f32 * TILE_SIZE;
    draw_rectangle(0.0, 0.0, w, HUD_HEIGHT, Color::new(0.15, 0.1, 0.05, 0.95));
    draw_line(0.0, HUD_HEIGHT, w, HUD_HEIGHT, 2.0, Color::new(0.6, 0.5, 0.2, 1.0));

    let hp_pct = game.player.hp as f32 / game.player.max_hp as f32;
    let hp_color = if hp_pct > 0.6 {
        Color::new(0.2, 1.0, 0.2, 1.0)
    } else if hp_pct > 0.3 {
        Color::new(1.0, 1.0, 0.0, 1.0)
    } else {
        Color::new(1.0, 0.2, 0.2, 1.0)
    };

    draw_rectangle(8.0, 5.0, 100.0, 10.0, Color::new(0.3, 0.0, 0.0, 1.0));
    draw_rectangle(8.0, 5.0, 100.0 * hp_pct, 10.0, hp_color);
    draw_text(
        &format!("{}/{}", game.player.hp, game.player.max_hp),
        30.0, 14.0, 13.0, WHITE,
    );

    let text = format!(
        "ATK:{}  DEF:{}  Lv.{} XP:{}/{}  Gold:{}  Kills:{}  Turn:{}  Floor:{}/{}",
        game.player.attack, game.player.defense,
        game.player.level, game.player.xp, game.player.xp_to_next,
        game.player.gold, game.player.kills, game.turns,
        game.current_depth, MAX_DEPTH,
    );
    draw_text(&text, 120.0, 28.0, 16.0, Color::new(0.9, 0.85, 0.65, 1.0));
}

fn draw_inventory(game: &Game, y: f32) {
    let w = MAP_WIDTH as f32 * TILE_SIZE;
    draw_rectangle(0.0, y, w, 22.0, Color::new(0.1, 0.08, 0.05, 0.9));

    if game.player.inventory.is_empty() {
        draw_text("Inventory: (empty)  |  G=grab  1-9=use", 8.0, y + 16.0, 15.0, Color::new(0.5, 0.5, 0.5, 1.0));
    } else {
        let mut text = String::from("Inventory: ");
        for (i, item) in game.player.inventory.iter().enumerate() {
            text.push_str(&format!("[{}]{} ", i + 1, item.name()));
        }
        draw_text(&text, 8.0, y + 16.0, 15.0, Color::new(0.8, 0.75, 0.55, 1.0));
    }
}

fn draw_messages(game: &Game, y: f32) {
    for (i, msg) in game.messages.iter().enumerate() {
        let color = Color::new(msg.color[0], msg.color[1], msg.color[2], msg.color[3]);
        draw_text(&msg.text, 8.0, y + 16.0 + i as f32 * 18.0, 15.0, color);
    }
}

fn draw_game_over(game: &Game) {
    let w = MAP_WIDTH as f32 * TILE_SIZE;
    let h = MAP_HEIGHT as f32 * TILE_SIZE + HUD_HEIGHT + 140.0;
    draw_rectangle(0.0, 0.0, w, h, Color::new(0.0, 0.0, 0.0, 0.7));

    let cx = w * 0.5;
    let cy = h * 0.4;

    if game.victory {
        draw_text("V I C T O R Y !", cx - 120.0, cy, 40.0, Color::new(1.0, 0.84, 0.0, 1.0));
        draw_text("You conquered the dungeon!", cx - 130.0, cy + 40.0, 22.0, WHITE);
    } else {
        draw_text("G A M E   O V E R", cx - 140.0, cy, 40.0, Color::new(0.7, 0.0, 0.0, 1.0));
        draw_text("You have perished...", cx - 100.0, cy + 40.0, 22.0, Color::new(0.5, 0.3, 0.3, 1.0));
    }

    let stats_y = cy + 80.0;
    draw_text(
        &format!("Level: {}    Kills: {}    Gold: {}    Floor: {}/{}",
            game.player.level, game.player.kills, game.player.gold, game.current_depth, MAX_DEPTH),
        cx - 180.0, stats_y, 18.0, WHITE,
    );
    draw_text(&format!("Turns: {}", game.turns), cx - 40.0, stats_y + 25.0, 18.0, WHITE);
    draw_text("Press ENTER or SPACE to exit", cx - 130.0, stats_y + 60.0, 18.0, Color::new(0.5, 0.5, 0.5, 1.0));
}