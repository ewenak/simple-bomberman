#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame

import constants

from threading import Timer


class Grid:
    def __init__(self, window):
        self.data = {}
        self.window = window
        self.all_timers = []

    def add_element(self, position, element):
        if not isinstance(element, GridObject):
            raise TypeError('Element must be a GridObject')
        self.data[tuple(position)] = element

    def move_element(self, position, element, new_pos):
        position = tuple(position)
        if position not in self.data or self.data[position] != element:
            raise TypeError(f'{ position } is empty or is not { element }')
        self.data[tuple(new_pos)] = self.data[position]
        del self.data[position]
        self.reload()

    def clear_position(self, position):
        position = tuple(position)
        if position in self.data:
            del self.data[position]
            self.reload()

    def clear_positions(self, *positions):
        for pos in positions:
            self.clear_position(pos)

    def get_element(self, position):
        position = tuple(position)
        if position in self.data:
            return self.data[position]
        else:
            return None

    def cancel_timers(self):
        for t in self.all_timers:
            t.cancel()

    def reload(self):
        self.window.fill(constants.background_color)
        for i in self.data.values():
            i.display()


class GridObject:
    def __init__(self, window, grid, pos):
        el = grid.get_element(pos)
        if isinstance(el, Wall) and not el.destroyable:
            self.accepted = False
            return
        else:
            self.accepted = True
        if el and not isinstance(el, Wall):
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
        window.blit(self.image, self.rect)

    def display(self):
        self.window.blit(self.image, self.rect)

    def delete(self):
        pass


class Player(GridObject):
    def __init__(self, window, grid, pos=[0, 0]):
        super().__init__(window, grid, pos)
        self.continue_ = True
        self.bombpos = None

    def move(self, move_x, move_y):
        if (self.gridpos[0] + move_x < 0 or
            self.gridpos[1] + move_y < 0 or
            (self.gridpos[0] + move_x) * constants.sprite_size >= constants.dimensions[0] or
            (self.gridpos[1] + move_y) * constants.sprite_size >= constants.dimensions[1]):
            return
        new_pos = [self.gridpos[0] + move_x, self.gridpos[1] + move_y]
        if self.grid.get_element(new_pos) \
            is not None:
            return

        self.rect.move_ip(move_x * constants.sprite_size, move_y * constants.sprite_size)
        self.grid.move_element(self.gridpos, self, new_pos)
        self.gridpos = new_pos
        if self.bombpos:
            b = Bomb(self.window, self.grid, self.bombpos)
            b.start_timer()
            self.bombpos = None

    def set_bomb(self):
        self.bombpos = tuple(self.gridpos)

    def get_image(self):
        return constants.player_image

    def delete(self):
        self.grid.cancel_timers()
        self.grid.data = {}
        self.grid.reload()
        self.continue_ = False
        self.window.fill(constants.background_color)
        self.window.blit(pygame.image.load(constants.game_over_image), [0, 181])


class Bomb(GridObject):
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)

    def get_image(self):
        return constants.bomb_image

    def start_timer(self):
        timer = Timer(constants.bomb_explosion_delay, self.explode)
        self.grid.all_timers.append(timer)
        timer.start()

    def explode(self):
        directions = [
            lambda i: [self.gridpos[0] + i, self.gridpos[1]],
            lambda i: [self.gridpos[0] - i, self.gridpos[1]],
            lambda i: [self.gridpos[0], self.gridpos[1] + i],
            lambda i: [self.gridpos[0], self.gridpos[1] - i]
        ]
        not_to_fire_directions = []
        for i in range(1, constants.bomb_explosion_scope):
            for d in enumerate(directions):
                p = d[1](i)
                el = self.grid.get_element(p)
                if isinstance(el, Wall) and not el.destroyable:
                    not_to_fire_directions.append(d[0])
                elif not d[0] in not_to_fire_directions:
                    Fire(self.window, self.grid, p)
        timer = Timer(constants.bomb_explosion_duration, self.delete)
        self.grid.all_timers.append(timer)
        timer.start()

    def delete(self):
        self.grid.clear_position(self.gridpos)


class Fire(GridObject):
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        if self.accepted:
            timer = Timer(constants.bomb_explosion_duration, self.delete)
            grid.all_timers.append(timer)
            timer.start()

    def get_image(self):
        return constants.fire_image

    def delete(self):
        self.grid.clear_position(self.gridpos)


class Wall(GridObject):
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        self.destroyable = False

    def get_image(self):
        return constants.wall_image

class DestroyableWall(Wall):
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        self.destroyable = True
    
    def get_image(self):
        return constants.destroyable_wall_image
