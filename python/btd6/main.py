"""Entry point - opens a 1280x720 Pygame window."""

import pygame
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE
from game.engine import Game


def main():
    pygame.init()
    try:
        pygame.mixer.init(22050, -16, 1, 512)
    except pygame.error:
        pass  # No audio device (e.g. WSL2) — runs fine without sound

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)

    game = Game(screen)
    game.run()


if __name__ == "__main__":
    main()
