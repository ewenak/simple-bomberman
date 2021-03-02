#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random

from . import constants
from .display import game_over, GridObject, Timer

class LevelError(Exception):
    pass


class Grid:
    """Grid class
    It stores the map of the game. They are all GridObject instances"""

    def __init__(self, window):
        self.data = {}
        self.window = window
        self.all_timers = []

    def add_element(self, position, element, reload=True):
        """Add an element to the grid"""
        if not isinstance(element, GridObject):
            raise TypeError('Element must be a GridObject')
        self.data[tuple(position)] = element
        if reload:
            self.reload()

    def move_element(self, position, element, new_pos, reload=True):
        """Move an element"""
        position = tuple(position)
        if position not in self.data or self.data[position] != element:
            raise TypeError(f'{ position } is empty or is not { element }')
        self.data[tuple(new_pos)] = element
        del self.data[position]
        if reload:
            self.reload()

    def clear_position(self, position, reload=True):
        """Clear a position
        If there is nothing, do nothing"""
        position = tuple(position)
        if position in self.data:
            del self.data[position]

        if reload:
            self.reload()

    def clear_positions(self, *positions):
        """Clear a list of positions"""
        for pos in positions:
            self.clear_position(pos, False)
        self.reload()

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
        """Reload the grid"""

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
        self.robots = []

        with open(file) as f:
            level = json.loads(f.read())
            self.level_map = level['map']
            if 'robots' in level:
                self.robots_data = level['robots']
            else:
                self.robots_data = None

    def render(self):
        """Render level
        Level are text files
        . represents the start point of a player
        # a wall
        : a wall which can be destroyed with a bomb
        + is the goal
        Robots are represented by letters which are keys of the 'robots' """

        matching_dict = {
            '.': ('players', Player),
            '#': ('walls', Wall),
            ':': ('destroyable_walls', DestructibleWall),
            '+': ('goals', Goal),
        }
        robots_positions = []
        for l in range(0, 15):
            for c in range(0, 15):
                cell = self.level_map[l][c]
                if cell in list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'):
                    robots_positions.append([cell, (c, l)])
                else:
                    class_classname = matching_dict.get(cell)
                    if class_classname is not None:
                        getattr(self, class_classname[0]).append(class_classname[1](self.window, self.grid, [c, l], False))

        robot_classes = {
            'orientation': OrientationRobot,
            'random': RandomRobot,
            'timid': TimidRobot,
            'path': PathRobot,
            'randompath': RandomPathRobot,
        }
        random_path_robot = []
        for r in robots_positions:
            robot_data = self.robots_data.get(r[0])
            if robot_data is None:
                raise LevelError(f'Robot { r[0] } (at pos { r[1] }) is not in robots\' data')
            else:
                if 'type' not in robot_data:
                    raise LevelError(f'No type in { r[0] } data')
                else:
                    robot = robot_classes[robot_data['type']](self.window, self.grid, r[1])
                    self.robots.append(robot)
                    if robot_data['type'] in ['orientation', 'timid']:
                        robot.player = random.choice(self.players)
                    elif robot_data['type'] == 'path':
                        robot.path = robot_data['path']
                    elif robot_data['type'] == 'randompath':
                        random_path_robot.append(robot)

        self.grid.reload()
        for r in random_path_robot:
            r.create_path()

        self.robots_move_timer = Timer(constants.robot_move_delay, self.move_robots)
        self.grid.all_timers.append(self.robots_move_timer)
        self.robots_move_timer.start()

    def move_robots(self):
        i = 0
        while i < len(self.robots):
            r = self.robots[i]
            if not r.exploded:
                r.move()
                i += 1
            else:
                del self.robots[i]

        self.robots_move_timer = Timer(constants.robot_move_delay, self.move_robots)
        self.grid.all_timers.append(self.robots_move_timer)
        self.robots_move_timer.start()
        self.grid.reload()


class Goal(GridObject):
    """Goal class
    It is the goal of the game, where player must go"""
    def __init__(self, window, grid, pos, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.deletable = False

    def get_image(self):
        return constants.goal_image


class Player(GridObject):
    """Player class
    Controlled with the keys, space to put a bomb"""
    def __init__(self, window, grid, pos=[0, 0], reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.hp = constants.default_hp
        self.continue_ = True
        self.bombpos = None
        self.deletable = False

    def move(self, move_x, move_y):
        """Move player
        Called when arrows keys are pressed"""
        # Verify player can go there
        if (self.gridpos[0] + move_x < 0 or self.gridpos[1] + move_y < 0 or
            (self.gridpos[0] + move_x) * constants.sprite_size >= constants.dimensions[0] or
            (self.gridpos[1] + move_y) * constants.sprite_size >= constants.dimensions[1]):
            return
        new_pos = [self.gridpos[0] + move_x, self.gridpos[1] + move_y]
        el = self.grid.get_element(new_pos)
        if isinstance(el, Goal):
            self.move_obj(move_x * constants.sprite_size, move_y * constants.sprite_size)
            self.display()
            return
        elif isinstance(el, Fire):
            self.on_explode()
            return
        elif el is not None:
            return

        self.move_obj(move_x * constants.sprite_size, move_y * constants.sprite_size)
        self.grid.move_element(self.gridpos, self, new_pos)
        self.gridpos = new_pos

        # Put a bomb if needed
        if self.bombpos:
            b = Bomb(self.window, self.grid, self.bombpos, False)
            b.start_timer()
            self.bombpos = None

        self.grid.reload()

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
            game_over(self.window, self.grid, self)

    def on_explode(self):
        """Called when player explodes"""
        # In brython version, the timers are not cancelled so the screen is
        # redrawn when the bomb has finished to explode. So we wait before
        # showing the "Game over!" text.
        Timer(constants.bomb_explosion_duration, lambda: game_over(self.window, self.grid, self)).start()


class Bomb(GridObject):
    """Bomb class
    Created by player"""
    def __init__(self, window, grid, pos, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.deletable = False
        self.exploded = False
        self.fires = []

    def get_image(self):
        return constants.bomb_image

    def start_timer(self):
        """Start bomb timer"""
        timer = Timer(constants.bomb_explosion_delay, self.explode)
        self.grid.all_timers.append(timer)
        timer.start()

    def explode(self):
        """Explode"""
        if not self.exploded:
            self.exploded = True
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
                            self.fires.append(Fire(self.window, self.grid, p))
                        break
                    else:
                        self.fires.append(Fire(self.window, self.grid, p, False))
            timer = Timer(constants.bomb_explosion_duration, self.delete)
            self.grid.all_timers.append(timer)
            timer.start()
        self.grid.reload()

    def delete(self):
        self.grid.clear_position(self.gridpos)
        self.grid.reload()

    def on_explode(self):
        self.explode()


class Fire(GridObject):
    """Fire class"""
    def __init__(self, window, grid, pos, reload_grid=True):
        el = grid.get_element(pos)
        if el:
            if hasattr(el, 'on_explode'):
                # Call el.on_explode
                el.on_explode()
            if not el.deletable:
                return
        super().__init__(window, grid, pos, reload_grid)
        if self.accepted:
            self.timer = Timer(constants.bomb_explosion_duration, self.delete)
            grid.all_timers.append(self.timer)
            self.timer.start()

    def get_image(self):
        return constants.fire_image

    def delete(self):
        self.grid.clear_position(self.gridpos)
        self.grid.reload()


class Wall(GridObject):
    """Wall class
    These ones are indestructible"""
    def __init__(self, window, grid, pos, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.deletable = False

    def get_image(self):
        return constants.wall_image


class DestructibleWall(Wall):
    """DestrucibleWall class
    These walls are destructible"""
    def __init__(self, window, grid, pos, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.deletable = True

    def get_image(self):
        return constants.destroyable_wall_image


class Robot(GridObject):
    """Robot class"""
    def __init__(self, window, grid, pos, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.attacks = True
        self.deletable = True
        self.exploded = False

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
            # None means not to move
            if new_gridpos is None:
                return
            if not new_gridpos in possible_places:
                print(f'choose_position returned a value ({ new_gridpos }) that is not in possible_places ({ possible_places })')
                return
            self.goto(new_gridpos[0] * constants.sprite_size,
                      new_gridpos[1] * constants.sprite_size)
            self.grid.move_element(self.gridpos, self, new_gridpos, False)
            self.gridpos = new_gridpos

    def on_explode(self):
        self.exploded = True


class RandomRobot(Robot):
    """RandomRobot class
    It moves randomly"""
    def choose_position(self, possible_places):
        return random.choice(possible_places)


class OrientationRobot(Robot):
    """OrientationRobot class
    It moves in the player direction"""
    def __init__(self, window, grid, pos, player=None, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.player = player

    def choose_position(self, positions):
        player_pos = self.player.gridpos

        def distance(pos):
            return (pos[0] - player_pos[0]) ** 2 + (pos[1] - player_pos[1]) ** 2

        return sorted(positions, key=distance)[0]


class TimidRobot(Robot):
    """TimidRobot class
    It fears player"""
    def __init__(self, window, grid, pos, player=None, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.player = player

    def choose_position(self, positions):
        player_pos = self.player.gridpos

        def distance(pos):
            return (pos[0] - player_pos[0]) ** 2 + (pos[1] - player_pos[1]) ** 2

        return sorted(positions, key=distance)[-1]


class PathRobot(Robot):
    """Path robot
    it follows a path"""
    def __init__(self, window, grid, pos, path: list = None, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.last_pos = None
        self.index_change = 1
        self.path = path

    def choose_position(self, possible_places):
        if list(self.gridpos) in self.path:
            current_pos_index = self.path.index(list(self.gridpos))
            next_pos_index = current_pos_index + self.index_change
            if next_pos_index == len(self.path) or next_pos_index < 0:
                next_pos_index -= self.index_change * 2
                self.index_change = -self.index_change
            next_pos = self.path[next_pos_index]
            if next_pos not in possible_places:
                if self.last_pos in possible_places:
                    next_pos = self.last_pos
                    self.last_pos = self.gridpos
                    return next_pos
                else:
                    # robot can't move
                    return None
            else:
                self.last_pos = self.gridpos
                return next_pos
        else:
            def distance(pos):
                return (pos[0] - self.path[0][0]) ** 2 + (pos[1] - self.path[0][1]) ** 2

            return sorted(possible_places, key=distance)[0]


class RandomPathRobot(PathRobot):
    def __init__(self, window, grid, pos, reload_grid=True):
        super().__init__(window, grid, pos, reload_grid)
        self.create_path()

    def create_path(self):
        creating_path_pos = self.gridpos
        self.path = [list(self.gridpos)]
        for i in range(random.randint(2, 10)):
            possible_places = []
            for p in [[creating_path_pos[0] + 1, creating_path_pos[1]],
                      [creating_path_pos[0] - 1, creating_path_pos[1]],
                      [creating_path_pos[0], creating_path_pos[1] + 1],
                      [creating_path_pos[0], creating_path_pos[1] - 1]]:
                el = self.grid.get_element(p)
                if (el is None and p[0] >= 0 and p[1] >= 0 and
                    p[0] * constants.sprite_size < constants.dimensions[0] and
                    p[1] * constants.sprite_size < constants.dimensions[1]):
                    possible_places.append(p)

            possible_places_not_in_path = [ p for p in possible_places if p not in self.path ]
            if len(possible_places_not_in_path) == 0:
                break
            else:
                creating_path_pos = random.choice(possible_places_not_in_path)
                self.path.append(list(creating_path_pos))
