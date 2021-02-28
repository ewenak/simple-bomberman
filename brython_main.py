from browser import document, html
from browser.timer import set_timeout, request_animation_frame

import time

from bomberman import constants, common, display

window = display.Window()

canvas = window.canvas

document <= canvas

window.fill(constants.background_color)

document.select('title')[0].clear()
document.select('title')[0] <= constants.title

grid = common.Grid(window)

level = common.Level(window, grid, constants.level_file)
level.render()
players = level.players

def keydown(event):
    print(event.key, repr(event.code), players)
    print(players[0], players[0].gridpos)

    if event.code == 'ArrowRight':
        players[0].move(1, 0)
    elif event.code == 'KeyD':
        if len(players) > 1:
            players[1].move(1, 0)
    elif event.code == 'ArrowLeft':
        players[0].move(-1, 0)
    elif event.code == 'KeyA':
        if len(players) > 1:
           players[1].move(-1, 0)
    elif event.code == 'ArrowUp':
        players[0].move(0, -1)
    elif event.code == 'KeyW':
        if len(players) > 1:
            players[1].move(0, -1)
    elif event.code == 'ArrowDown':
        players[0].move(0, 1)
    elif event.code == 'KeyS':
        if len(players) > 1:
            players[1].move(0, 1)
    elif event.code == 'Space':
        players[0].put_bomb()
    elif event.code == 'KeyX':
        if len(players) > 1:
            players[1].put_bomb()
    elif event.code == 'KeyP':
        from interpreter import Inspector
        print(Inspector())

document.bind('keydown', keydown)
