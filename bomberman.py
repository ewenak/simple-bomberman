#! /usr/bin/env python3

import pygame
from pygame import locals as l

import classes
import constants

# Init
pygame.init()
window = pygame.display.set_mode(constants.dimensions)
window.fill(constants.background_color)

# Title
pygame.display.set_caption(constants.title)

pygame.time.Clock().tick(30)

grid = classes.Grid(window)

player = classes.Player(window, grid)

pygame.key.set_repeat(400, 30)

# Main loop
continue_ = True
while continue_:
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == l.QUIT or (event.type == l.KEYDOWN and event.key == l.K_ESCAPE):
            continue_ = False
            grid.cancel_timers()
            pygame.quit()
            break
        elif event.type == l.KEYDOWN:
            if event.key == l.K_RIGHT:
                player.move(1, 0)
            elif event.key == l.K_LEFT:
                player.move(-1, 0)
            elif event.key == l.K_UP:
                player.move(0, -1)
            elif event.key == l.K_DOWN:
                player.move(0, 1)
            elif event.key == l.K_SPACE:
                player.set_bomb()
            elif event.key == l.K_p:
                import pdb; pdb.set_trace()
    if continue_ and player.continue_:
        grid.reload()
    elif continue_ and not player.continue_:
        window.fill(constants.background_color)
        window.blit(pygame.image.load(constants.game_over_image), [0, 181])
