#! /usr/bin/env python3

DEBUG = True

title = 'Bomberman'
dimensions = [750, 750]
background_color = [128, 128, 128]

level_file = 'level.json'

sprite_size = 50

player_image = 'images/player.png'
bomb_image = 'images/bomb.png'
fire_image = 'images/fire.png'
wall_image = 'images/wall.png'
destroyable_wall_image = 'images/destroyable_wall.png'
robot_image = 'images/robot.png'
goal_image = 'images/goal.png'
game_over_image = 'images/game_over.png'

robot_move_delay = 1.0

default_hp = 3

bomb_explosion_delay = 2.0
bomb_explosion_scope = 4
bomb_explosion_duration = 0.6
