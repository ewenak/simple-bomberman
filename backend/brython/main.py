from browser import document, html

import constants
import classes
import display

window = display.Window()

canvas = window.canvas

document <= canvas

window.fill(constants.background_color)

document.select('title')[0].clear()
document.select('title')[0] <= constants.title

grid = classes.Grid(window)

level = classes.Level(window, grid, '../' + constants.level_file)
level.render()
players = level.players

def start(e):
    level.start()
document['start'].bind('click', start)

def keypress(event):
    print(event, dir(event), event.key, event.keyCode)

document.bind('keypress', keypress)
    #             players[0].move(1, 0)
    #         elif event.key == l.K_d:
    #             if len(players) > 1:
    #                 players[1].move(1, 0)
    #         elif event.key == l.K_LEFT:
    #             players[0].move(-1, 0)
    #         elif event.key == l.K_a:
    #             if len(players) > 1:
    #                 players[1].move(-1, 0)
    #         elif event.key == l.K_UP:
    #             players[0].move(0, -1)
    #         elif event.key == l.K_w:
    #             if len(players) > 1:
    #                 players[1].move(0, -1)
    #         elif event.key == l.K_DOWN:
    #             players[0].move(0, 1)
    #         elif event.key == l.K_s:
    #             if len(players) > 1:
    #                 players[1].move(0, 1)
    #         elif event.key == l.K_SPACE:
    #             players[0].put_bomb()
    #         elif event.key == l.K_x:
    #             if len(players) > 1:
    #                 players[1].put_bomb()
    #         elif event.key == l.K_p:
    #             import pdb; pdb.set_trace()
    # if continue_ and all([ p.continue_ for p in players]):
    #     grid.reload()
    # elif continue_ and not all([ p.continue_ for p in players]):
    #     window.pygame_window.fill(constants.background_color)
    #     window.pygame_window.blit(pygame.image.load(constants.game_over_image), [0, 181])
