#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame

import constants

import random
from threading import Timer


class Grid:
    """Grid class
    It stores the map of the game. They are all GridObject instances"""

    def __init__(self, window):
        self.data = {}
        self.window = window
        self.to_remove_before_reload = []
        self.to_add_before_reload = []
        self.all_timers = []

    def add_element(self, position, element):
        """Add an element to the grid"""
        if not isinstance(element, GridObject):
            raise TypeError('Element must be a GridObject')
        self.to_add_before_reload.append((tuple(position), element))

    def move_element(self, position, element, new_pos):
        """Move an element"""
        position = tuple(position)
        if position not in self.data or self.data[position] != element:
            raise TypeError(f'{ position } is empty or is not { element }')
        self.to_add_before_reload.append((tuple(new_pos), element))
        self.to_remove_before_reload.append(position)
        self.reload()

    def clear_position(self, position):
        """Clear a position
        If there is nothing, do nothing"""
        position = tuple(position)
        if position in self.data:
            self.to_remove_before_reload.append(position)

    def clear_positions(self, *positions):
        """Clear a list of positions"""
        for pos in positions:
           self.clear_position(pos)

    def get_element(self, position):
        """Get a GridObject
        Return None if there is nothing"""
        position = tuple(position)
        if position in self.data:
            return self.data[position]
        else:
            return None

    def cancel_timers(self):
        """Cancel all timers
        Used to prevent errors when the game is exited"""
        for t in self.all_timers:
            t.cancel()

    def reload(self):
        """Reload the grid
        Really change self.data only here"""

        # Remove and add elements to self.data
        for pos in self.to_remove_before_reload:
            del self.data[pos]
        self.to_remove_before_reload = []
        for el in self.to_add_before_reload:
            self.data[el[0]] = el[1]
        self.to_add_before_reload = []

        # Fill the window and call display for each element
        self.window.fill(constants.background_color)
        for i in list(self.data.values()):
            i.display()


class Level:
    """Level class
    It creates the grid objects"""
    def __init__(self, window, grid, file):
        self.window = window
        self.grid = grid

        self.players = []
        self.walls = []
        self.destroyable_walls = []
        self.goals = []
        self.random_robots = []
        self.orientation_robots = []
        self.timid_robots = []

        with open(file) as f:
            self.level_grid = [ list(l) for l in f.read().split('\n') ]

    def render(self):
        """Render level
        Level are text files
        A p represents a player
        # a wall
        : a wall which can be destroyed with a bomb
        g is the goal
        r is a random robot
        o is an orientation robot
        t is a timid robot"""

        matching_dict = {
            'p': ('players', Player),
            '#': ('walls', Wall),
            ':': ('destroyable_walls', DestructibleWall),
            'g': ('goals', Goal),
            'r': ('random_robots', RandomRobot),
            'o': ('orientation_robots', OrientationRobot),
            't': ('timid_robots', TimidRobot)
        }
        for l in range(0, 15):
            for c in range(0, 15):
                cell = self.level_grid[l][c]
                class_classname = matching_dict.get(cell)
                if class_classname is not None:
                    getattr(self, class_classname[0]).append(class_classname[1](self.window, self.grid, [c, l]))

        if len(self.players) > 1:
            for r in self.orientation_robots + self.timid_robots:
                r.player = random.choice(self.players)
        else:
            for r in self.orientation_robots + self.timid_robots:
                r.player = self.players[0]


class GridObject:
    """GridObject class
    It is the class of any object in the grid"""
    def __init__(self, window, grid, pos):
        el = grid.get_element(pos)
        # Create a GridObject where there is already a Wall is impossible
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
        """Display self"""
        self.window.blit(self.image, self.rect)

    def delete(self):
        pass


class Goal(GridObject):
    """Goal class
    It is the goal of the game, where player must go"""
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        self.deletable = False

    def get_image(self):
        return constants.goal_image


class Player(GridObject):
    """Player class
    Controlled with the keys, space to put a bomb"""
    def __init__(self, window, grid, pos=[0, 0]):
        super().__init__(window, grid, pos)
        self.hp = constants.default_hp
        self.continue_ = True
        self.bombpos = None
        self.deletable = False

    def move(self, move_x, move_y):
        """Move player
        Called when arrows keys are pressed"""
        # Verify player can go there
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

        # Put a bomb if needed
        if self.bombpos:
            b = Bomb(self.window, self.grid, self.bombpos)
            b.start_timer()
            self.bombpos = None

    def put_bomb(self):
        """Put a bomb
        Called when pressing space. The bomb will really be created when player
        will move"""
        self.bombpos = tuple(self.gridpos)

    def get_image(self):
        return constants.player_image

    def attack(self, force=1):
        """Remove force hp
        By default, force is one"""
        self.hp -= force
        if self.hp < 1:
            self.game_over()

    def game_over(self):
        """When called show the constants.game_over_image"""
        self.grid.cancel_timers()
        self.grid.data = {}
        self.grid.reload()
        self.continue_ = False
        self.window.fill(constants.background_color)
        self.window.blit(pygame.image.load(constants.game_over_image), [0, 181])

    def on_explode(self):
        """Called when player explodes"""
        self.game_over()


class Bomb(GridObject):
    """Bomb class
    Created by player"""
    def get_image(self):
        return constants.bomb_image

    def start_timer(self):
        """Start bomb timer"""
        timer = Timer(constants.bomb_explosion_delay, self.explode)
        self.grid.all_timers.append(timer)
        timer.start()

    def explode(self):
        """Explode"""
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
    """Fire class"""
    def __init__(self, window, grid, pos):
        el = grid.get_element(pos)
        if el and el.deletable == False:
            if hasattr(el, 'on_explode'):
                # Call el.on_explode
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
    """Wall class
    These ones are indestructible"""
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        self.deletable = False

    def get_image(self):
        return constants.wall_image


class DestructibleWall(Wall):
    """DestrucibleWall class
    These walls are destructible"""
    def __init__(self, window, grid, pos):
        super().__init__(window, grid, pos)
        self.deletable = True
    
    def get_image(self):
        return constants.destroyable_wall_image


class Robot(GridObject):
    """Robot class"""
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
        """Move robot"""
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
    """RandomRobot class
    It moves randomly"""
    def choose_position(self, possible_places):
        return random.choice(possible_places)


class OrientationRobot(Robot):
    """OrientationRobot class
    It moves in the player direction"""
    def __init__(self, window, grid, pos, player=None):
        super().__init__(window, grid, pos)
        self.player = player

    def choose_position(self, positions):
        player_pos = self.player.gridpos
        def distance(pos):
            return (pos[0] - player_pos[0]) ** 2 + (pos[1] - player_pos[1]) ** 2

        return sorted(positions, key=distance)[0]


class TimidRobot(Robot):
    """TimidRobot class
    It fears player"""
    def __init__(self, window, grid, pos, player=None):
        super().__init__(window, grid, pos)
        self.player = player
    
    def choose_position(self, positions):
        player_pos = self.player.gridpos
        def distance(pos):
            return (pos[0] - player_pos[0]) ** 2 + (pos[1] - player_pos[1]) ** 2

        return sorted(positions, key=distance)[-1]
