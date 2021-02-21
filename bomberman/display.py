#! /usr/bin/env python3

try:
    import browser
    backend = 'brython'
except ImportError:
    backend = 'pygame'

if backend == 'pygame':
    from .backend.pygame.display import game_over, GridObject, Window
else:
    from .backend.brython.display import game_over, GridObject, Window
