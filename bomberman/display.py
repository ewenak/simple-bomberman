#! /usr/bin/env python3

try:
    import browser
    backend = 'brython'
except ImportError:
    backend = 'pygame'

if backend == 'pygame':
    from .backend.pygame.display import game_over, GridObject, Window
    from threading import Timer
else:
    import bomberman.backend.brython.display as display
    game_over = display.game_over
    GridObject = display.GridObject
    Window = display.Window

    from browser.timer import clear_timeout, set_timeout

    class Timer:
        def __init__(self, interval, function):
            self.interval = interval
            self.function = function
            self._tid = None

        def start(self):
            self._tid = set_timeout(self.function, self.interval * 1000)

        def cancel(self):
            clear_timeout(self._tid)
