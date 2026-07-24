import pygame
import sys
from typing import Any


class Renderer:
    def __init__(self, width: int = 800, height: int = 600) -> None:
        """Window and graph render."""
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Fly-in Simulation")
        self.clock = pygame.time.Clock()

    def events_handle(self) -> bool:
        """Handle SO events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def draw_state(self, graph: Any) -> None:
        """Clean and update the display."""
        self.screen.fill("blue")
        pygame.display.flip()
        self.clock.tick(60)

    def cleanup(self) -> None:
        """Safe way to close Pygame."""
        pygame.quit()
        sys.exit(0)