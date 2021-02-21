import pygame

from ... import constants


class Window:
    def __init__(self):
        self.pygame_window = pygame.display.set_mode(constants.dimensions)

    def fill(self, color):
       self.pygame_window.fill(color) 


class GridObject:
    """GridObject class
    It is the class of any object in the grid"""
    def __init__(self, window, grid, pos):
        el = grid.get_element(pos)
        # Create a GridObject where there is already a Wall is impossible
        if el is not None and not el.deletable:
            self.accepted = False
            return
        else:
            self.accepted = True
        if el and not el.deletable:
            el.delete()

        self.image = pygame.image.load(self.get_image())
        grid.add_element(pos, self)
        self.grid = grid
        self.gridpos = pos
        pos = [ p * constants.sprite_size for p in pos ]
        self.pos = pos
        self.rect = self.image.get_rect()
        self.rect.move_ip(*pos)
        self.window = window
        window.pygame_window.blit(self.image, self.rect)
        self.deletable = True

    def move_obj(self, x, y):
        self.rect.move_ip(x, y)

    def goto(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 50)

    def display(self):
        """Display self"""
        self.window.pygame_window.blit(self.image, self.rect)

    def delete(self):
        pass

def game_over(window, grid, player):
    """When called, show the constants.game_over_image image"""
    grid.cancel_timers()
    grid.data = {}
    grid.reload()
    player.continue_ = False
    window.pygame_window.fill(constants.background_color)
    window.pygame_window.blit(pygame.image.load(constants.game_over_image), [0, 181])
