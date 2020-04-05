import copy
import random
from enum import Enum, auto
from collections import deque

import numpy as np
import pyxel

class Direction(Enum):
    UP = 1,
    UPRIGHT =2,
    RIGHT=3,
    DOWNRIHGHT=4,
    DOWN=5,
    DOWNLEFT=6,
    LEFT=7,
    UPLEFT=8

class Man:
    def __init__(self, _x, _y, _c, _d=Direction.UP, hitpoints=10, max_hitpoints=10):
        super().__init__()
        self.x = _x
        self.y = _y
        self.px = None
        self.py = None # 一回前の座標
        self.vx = None 
        self.vy = None
        self.c = _c # 色
        self.d = _d # 描画用の方向
        
        # Flags
        self.moved = False
        self.attacked = False
        self.alive = True
        self.step_count = 0
        
        # Draw
        self.attack_motion_timer = 3  # [frames]
        
        # Ability
        self.lv = 1
        self.exp = 0
        self.strength = 5
        self.defense = 5        
        self.hitpoints = hitpoints
        self.max_hp = max_hitpoints
        self.hunger = 100        
        

    def update(self, _x, _y):
        
        self.px = self.x
        self.py = self.y        
        self.x = _x
        self.y = _y

        # TODO: 本来、　移動がなければupdate呼ばないほうがいい
        if not (self.px == _x and self.py == _y):            
            
            # 満腹だと体力が回復する
            if self.hunger > 0: 
                if self.step_count % 13 == 1:
                    self.hitpoints = self.hitpoints + 1 if self.hitpoints + 1 <= self.max_hp else self.hitpoints         

            # 空腹だと体力が減る
            else: 
                if self.step_count % 13 == 1:
                    self.hitpoints -= 1
                self.step_count += 1

            # 空腹度の減算            
            self.step_count += 1            
            if self.step_count % 11 == 1:        
                self.hunger = self.hunger - 1 if self.hunger - 1 >= 0 else self.hunger

                                        
    def level_up(self):
        self.lv += 1
        self.strength += np.random.randint(1,5)
        self.defense += np.random.randint(1,5)
        max_hp_up = np.random.randint(7,15)
        self.max_hp += max_hp_up
        self.hitpoints += max_hp_up        

    def kill(self):
        # self.x = -255
        # self.x = -255
        self.alive = False

class Enemy(Man):
    def __init__(self, _x, _y, _c, _d=Direction.UP, hitpoints=10, max_hitpoints=10, exp=5):
        super().__init__(_x, _y, _c, _d=_d, hitpoints=hitpoints, max_hitpoints=max_hitpoints)
        self.route = None
        self.exp = exp
        self.id = np.random.randint(0,3)
        
    def set_route(self, _route):
        self.route = _route

class Object(object):
    def __init__(self, _x, _y):
        self.x = _x
        self.y = _y

class FoodType(Enum):
    SUPTER_NIKU = auto()
    NIKU = auto()
    YASAI = auto()
    KOME = auto()
        

class Food(Object):
    def __init__(self, _x, _y):
        super().__init__(_x, _y)
    

