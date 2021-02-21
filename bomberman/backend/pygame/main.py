#! /usr/bin/env python3

import pygame
from pygame import locals as l

from ... import common, constants, display

def main():
    # Init
    pygame.init()
    window = display.Window()
    window.pygame_window.fill(constants.background_color)

    # Title
    pygame.display.set_caption(constants.title)
    
    pygame.key.set_repeat(400, 30)
    pygame.time.Clock().tick(30)
    
    grid = common.Grid(window)
    
    level = common.Level(window, grid, constants.level_file)
    level.render()
    players = level.players
    
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
            elif event.type == l.KEYDOWN and all([ p.continue_ for p in players]):
                if event.key == l.K_RIGHT:
                    players[0].move(1, 0)
                elif event.key == l.K_d:
                    if len(players) > 1:
                        players[1].move(1, 0)
                elif event.key == l.K_LEFT:
                    players[0].move(-1, 0)
                elif event.key == l.K_a:
                    if len(players) > 1:
                        players[1].move(-1, 0)
                elif event.key == l.K_UP:
                    players[0].move(0, -1)
                elif event.key == l.K_w:
                    if len(players) > 1:
                        players[1].move(0, -1)
                elif event.key == l.K_DOWN:
                    players[0].move(0, 1)
                elif event.key == l.K_s:
                    if len(players) > 1:
                        players[1].move(0, 1)
                elif event.key == l.K_SPACE:
                    players[0].put_bomb()
                elif event.key == l.K_x:
                    if len(players) > 1:
                        players[1].put_bomb()
                elif event.key == l.K_p:
                    import pdb; pdb.set_trace()

        if continue_ and all([ p.continue_ for p in players]):
            grid.reload()
        elif continue_ and not all([ p.continue_ for p in players]):
            window.pygame_window.fill(constants.background_color)
            window.pygame_window.blit(pygame.image.load(constants.game_over_image), [0, 181])
