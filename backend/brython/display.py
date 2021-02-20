from browser import html

import constants

unremoveable_objects = []


class Window:
    def __init__(self):
        self.canvas = html.CANVAS('Upgrade your browser to play to this bomberman',
                                  width=constants.dimensions[0], height=constants.dimensions[1])
        if not hasattr(self.canvas, 'getContext'):
            raise RuntimeError('Canvas not supported')
            return
        self.ctx = self.canvas.getContext('2d')

    def fill(self, color):
        self.ctx.fillStyle = f'rgb({ ", ".join(str(n) for n in color) })'
        self.ctx.fillRect(0, 0, *constants.dimensions)


class GridObject:
    """GridObject class
    It is the class of any object in the grid"""
    def __init__(self, window, grid, pos):
        el = grid.get_element(pos)
        # Create a GridObject where there is already a Wall is impossible
        if el is not None and el.__class__ not in unremoveable_objects and not el.deletable:
            self.accepted = False
            return
        else:
            self.accepted = True
        if el and not el.__class__ not in unremoveable_objects:
            el.delete()

        self.image = html.IMG(src=self.get_image())
        grid.add_element(pos, self)
        self.grid = grid
        self.gridpos = pos
        pos = [ p * constants.sprite_size for p in pos ]
        self.pos = pos
        self.window = window
        self.deletable = True
        self.display()

    def move_obj(self, x, y):
        self.pos = [self.pos[0] + x, self.pos[0] + y]

    def goto(self, x, y):
        self.pos = [x, y]

    def display(self):
        """Display self"""
        self.window.ctx.drawImage(self.image, *self.pos)

    def delete(self):
        pass

def game_over(window, grid, player):
    """When called, show the constants.game_over_image image"""
    grid.cancel_timers()
    grid.data = {}
    grid.reload()
    player.continue_ = False
    window.fill(constants.background_color)
    window.ctx.drawImage(html.IMG(src=constants.game_over_image), 0, 181)
