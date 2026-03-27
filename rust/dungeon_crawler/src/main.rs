mod game;
mod level;
mod renderer;

use macroquad::prelude::*;
use game::Game;

fn window_conf() -> Conf {
    Conf {
        window_title: String::from("Dungeon Crawler"),
        window_width: 1280,
        window_height: 880,
        window_resizable: false,
        ..Default::default()
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    let mut game = Game::new();

    loop {
        if is_key_pressed(KeyCode::Escape) {
            break;
        }

        if !game.game_over {
            if is_key_pressed(KeyCode::W) || is_key_pressed(KeyCode::Up) {
                game.try_move(0, -1);
            } else if is_key_pressed(KeyCode::S) || is_key_pressed(KeyCode::Down) {
                game.try_move(0, 1);
            } else if is_key_pressed(KeyCode::A) || is_key_pressed(KeyCode::Left) {
                game.try_move(-1, 0);
            } else if is_key_pressed(KeyCode::D) || is_key_pressed(KeyCode::Right) {
                game.try_move(1, 0);
            } else if is_key_pressed(KeyCode::G) {
                game.grab_item();
            } else if is_key_pressed(KeyCode::Period) {
                game.go_downstairs();
            } else if is_key_pressed(KeyCode::Comma) {
                game.go_upstairs();
            }

            let keys = [
                KeyCode::Key1, KeyCode::Key2, KeyCode::Key3,
                KeyCode::Key4, KeyCode::Key5, KeyCode::Key6,
                KeyCode::Key7, KeyCode::Key8, KeyCode::Key9,
            ];
            for (i, &key) in keys.iter().enumerate() {
                if is_key_pressed(key) {
                    game.use_item(i);
                }
            }
        } else if is_key_pressed(KeyCode::Enter) || is_key_pressed(KeyCode::Space) {
            break;
        }

        renderer::render(&game);
        next_frame().await;
    }
}