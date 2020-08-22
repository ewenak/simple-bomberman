#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame

import constants

import random
from threading import Timer


class Grid:
    def __init__(self, window):
        self.data = {}
        self.window = window
        self.to_remove_before_reload = []
        self.to_add_before_reload = []
        self.all_timers = []

    def add_element(self, position, element):
        if not isinstance(element, GridObject):
            raise TypeError('Element must be a GridObject')
        self.to_add_before_reload.append((tuple(position), element))

    def move_element(self, position, element, new_pos):
        position = tuple(position)
        if position not in self.data or self.data[position] != element:
            raise TypeError(f'{ position } is empty or is not { element }')
        self.to_add_before_reload.append((tuple(new_pos), element))
        self.to_remove_before_reload.append(position)
        self.reload()

    def clear_position(self, position):
        position = tuple(position)
        if position in self.data:
            self.to_remove_before_reload.append(position)

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

        for pos in self.to_remove_before_reload:
            del self.data[pos]
        self.to_remove_before_reload = []
        for el in self.to_add_before_reload:
            self.data[el[0]] = el[1]
        self.to_add_before_reload = []

        for i in self.data.values():
            i.display()


class Level:
    def __init__(self, window, grid, file):
        self.window = window
        self.grid = grid

        self.players = []
        self.walls = []
        self.destroyable_walls = []
        self.goals = []
        self.random_robots = []

        with open(file) as f:
            self.level_grid = [ list(l) for l in f.read().split('\n') ]

    def render(self):
        matching_dict = {
            'p': ('players', Player),
            '#': ('walls', Wall),
            ':': ('destroyable_walls', DestroyableWall),
            'g': ('goals', Goal),
            'r': ('random_robots', RandomRobot)
        }
        for l in range(0, 15):
            for c in range(0, 15):
                cell = self.level_grid[l][c]
                class_classname = matching_dict.get(cell)
                if class_classname is not None:
                    getattr(self, class_classname[0]).append(class_classname[1](self.window, self.grid, [c, l]))


class GridObject:
    def __init__(self, window, grid, pos):
        el = grid.get_element(pos)
        if isinstance(el, Wall) and not el.deletable:
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
        self.deletable = True

    def display(self):
        self.window.blit(self.image, self.rect)

    def delete(self):
        pass


class Goal(GridObject):
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        self.deletable = False

    def get_image(self):
        return constants.goal_image


class Player(GridObject):
    def __init__(self, window, grid, pos=[0, 0]):
        super().__init__(window, grid, pos)
        self.hp = constants.default_hp
        self.continue_ = True
        self.bombpos = None

    def move(self, move_x, move_y):
        if (self.gridpos[0] + move_x < 0 or
            self.gridpos[1] + move_y < 0 or
            (self.gridpos[0] + move_x) * constants.sprite_size >= constants.dimensions[0] or
            (self.gridpos[1] + move_y) * constants.sprite_size >= constants.dimensions[1]):
            return
        new_pos = [self.gridpos[0] + move_x, self.gridpos[1] + move_y]
        el = self.grid.get_element(new_pos)
        if isinstance(el, Goal):
            self.rect.move_ip(move_x * constants.sprite_size, move_y * constants.sprite_size)
            self.display()
            return
        elif isinstance(el, Fire):
            self.on_explode()
            return
        elif el is not None:
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

    def attack(self, force=1):
        self.hp -= force
        if self.hp < 1:
            self.game_over()

    def game_over(self):
        self.grid.cancel_timers()
        self.grid.data = {}
        self.grid.reload()
        self.continue_ = False
        self.window.fill(constants.background_color)
        self.window.blit(pygame.image.load(constants.game_over_image), [0, 181])

    def on_explode(self):
        self.game_over()


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
        for d in directions:
            for i in range(1, constants.bomb_explosion_scope):
                p = d(i)
                el = self.grid.get_element(p)
                if isinstance(el, Wall):
                    if el.deletable:
                        Fire(self.window, self.grid, p)
                    break
                else:
                    Fire(self.window, self.grid, p)
        timer = Timer(constants.bomb_explosion_duration, self.delete)
        self.grid.all_timers.append(timer)
        timer.start()

    def delete(self):
        self.grid.clear_position(self.gridpos)


class Fire(GridObject):
    def __init__(self, window, grid, pos):
        el = grid.get_element(pos)
        if el and el.deletable == False:
            if hasattr(el, 'on_explode'):
                el.on_explode()
        else:
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
        self.deletable = False

    def get_image(self):
        return constants.wall_image


class DestroyableWall(Wall):
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        self.deletable = True
    
    def get_image(self):
        return constants.destroyable_wall_image


class Robot(GridObject):
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        self.attacks = True
        self.move_delay = self.get_move_delay()
        self.timer = Timer(self.move_delay, self.move)
        self.grid.all_timers.append(self.timer)
        self.timer.start()

    def get_image(self):
        return constants.robot_image
    
    def move(self):
        possible_places = []
        for p in [[self.gridpos[0] + 1, self.gridpos[1]],
            [self.gridpos[0] - 1, self.gridpos[1]],
            [self.gridpos[0], self.gridpos[1] + 1],
            [self.gridpos[0], self.gridpos[1] - 1]]:
            el = self.grid.get_element(p)
            if isinstance(el, Player) and self.attacks:
                el.attack()
            elif (el is None and p[0] >= 0 and p[1] >= 0 and
                p[0] * constants.sprite_size < constants.dimensions[0] and 
                p[1] * constants.sprite_size < constants.dimensions[1]):
                possible_places.append(p)

        if len(possible_places) > 0:
            new_gridpos = self.choose_position(possible_places)
            self.rect = pygame.Rect(new_gridpos[0] * constants.sprite_size, new_gridpos[1] * constants.sprite_size, 50, 50)
            self.grid.move_element(self.gridpos, self, new_gridpos)
            self.gridpos = new_gridpos

        self.timer = Timer(self.move_delay, self.move)
        self.grid.all_timers.append(self.timer)
        self.timer.start()

    def get_move_delay(self):
        return constants.robot_move_delay

    def delete(self):
        self.timer.cancel()


class RandomRobot(Robot):
    def choose_position(self, possible_places):
        return random.choice(possible_places)
