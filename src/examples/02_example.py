import random
from enum import Enum
from collections import deque

import numpy as np
import pyxel

from map import Map

class State(Enum):
  START = 1 # 開始演出
  MAIN = 2 # メイン
  CHANGE = 3 # マップ切り替え
  END = 4 # 終了

class Vehicle:
    def __init__(self, _x, _y, _c):
        super().__init__()
        self.x = _x
        self.y = _y
        self.c = _c

    def update(self, _x, _y):
        self.x = _x
        self.y = _y

class App:
    def __init__(self):

        self.name = "RANDOM MAP"
        
        self.state = State.START
        self.fps = 15
        
        pyxel.init(64, 64, caption=self.name, scale=6, fps=self.fps)
        # pyxel.image(0).load(0, 0, "pyxel_logo_38x16.png") # opening
        
        # 地図の初期化
        self.map = Map(pyxel.width, pyxel.height)
        
        self.timer = 30
        
        # self.map.create_map_stick_down()
        self.num_col_rooms = 4
        self.num_row_rooms = 3
        self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, num_row_rooms=self.num_row_rooms)
        self.map.set_goal()
        self.floor = 0
        self.is_open = np.zeros(self.map.data.shape, np.bool)
        
        # 自キャラの初期化
        x = int(np.random.rand() * pyxel.width)
        y = int(np.random.rand() * pyxel.height)
        while self.map.data[y, x] != 0:
            x = int(np.random.rand() * pyxel.width)
            y = int(np.random.rand() * pyxel.height)            
        c = 11
        self.ego = Vehicle(x, y, c)

        # 敵キャラの初期化
        # self.num_enemy = 3
        # self.enemy_list = []        
        # for idx in range(self.num_enemy)
        x = int(np.random.rand() * pyxel.width)
        y = int(np.random.rand() * pyxel.height)
        while self.map.data[y, x] != 0:
            x = int(np.random.rand() * pyxel.width)
            y = int(np.random.rand() * pyxel.height)            
        c = 14
        self.enemy = Vehicle(x, y, c)

        self.route = deque()


        # 獲得アイテす数
        self.num_got_items = 0
        self.max_items = 3 # これだけ獲得したら次の画面へ

        
        # 実行        
        pyxel.run(self.update, self.draw)

    def update(self):
        
        if self.state == State.START: # 開始演出
            
            if (pyxel.btn(pyxel.KEY_S)):
                self.state = State.MAIN

        elif self.state == State.CHANGE:
            if (pyxel.btn(pyxel.KEY_S)):
                self.state = State.MAIN
                
                self.num_got_items = 0
                self.max_items = 3 # これだけ獲得したら次の画面へ
                self.floor += 1
                print("Init Map")
                self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, num_row_rooms=self.num_row_rooms)
                self.map.set_goal()
                
                # キャラの初期化
                x = int(np.random.rand() * pyxel.width)
                y = int(np.random.rand() * pyxel.height)
                while self.map.data[y, x] != 0:
                    x = int(np.random.rand() * pyxel.width)
                    y = int(np.random.rand() * pyxel.height)            
                self.ego.x = x
                self.ego.y = y

                x = int(np.random.rand() * pyxel.width)
                y = int(np.random.rand() * pyxel.height)
                while self.map.data[y, x] != 0:
                    x = int(np.random.rand() * pyxel.width)
                    y = int(np.random.rand() * pyxel.height)            
                self.enemy.x = x
                self.enemy.y = y
                self.route = deque()
                self.is_open = np.zeros(self.map.data.shape, np.bool)
                self.timer = 30.0

        elif self.state == State.MAIN: # メイン
            self.timer -= 1./self.fps

            # 自キャラの操作            
            self.move_target(self.ego)

            # 敵キャラの行動
            self.act_enemy()

            # 到達した地図のフラグをたてる
            self.is_open[self.ego.y-4:self.ego.y+4, self.ego.x-4:self.ego.x+4] = True


            # ゴールに到達したかどうかを判定
            if self.map.data[self.ego.y, self.ego.x] == -1:
                self.num_got_items += 1
                
                # 獲得アイテムが閾い異常のとき次のstageへ
                if self.num_got_items >= self.max_items:
                    self.state = State.CHANGE
                
                self.map.set_goal()

            if self.ego.x == self.enemy.x and self.ego.y == self.enemy.y:
                self.state = State.END
                
            if int(self.timer) <= 0:
                self.state = State.END

    def act_enemy(self):
        
        # 最短経路の更新
        if not pyxel.frame_count % 20:
        
            self.route = self.map.search_shortest_path_dws((self.enemy.y, self.enemy.x), (self.ego.y, self.ego.x))
            self.route = deque(self.route)
            self.route.popleft() # 一つ目はstartなので捨てる

        if len(self.route) > 0:
            next_cell = self.route.popleft()
            self.enemy.update(next_cell[1], next_cell[0])

        else:
            pass
        
    def move_target(self, target):
        x = target.x
        y = target.y            
        if pyxel.btn(pyxel.KEY_LEFT):
            if 0 <= x - 1 < pyxel.width and self.map.data[y, x -1] <= 0:
                x = x - 1
        if pyxel.btn(pyxel.KEY_RIGHT):
            if 0 <= x + 1 < pyxel.width and self.map.data[y, x +1] <= 0:
                x = x + 1
        if pyxel.btn(pyxel.KEY_UP):
            if 0 <= y - 1 < pyxel.height and self.map.data[y-1, x] <= 0:
                y = y - 1
        if pyxel.btn(pyxel.KEY_DOWN):
            if 0 <= y + 1 < pyxel.height and self.map.data[y+1, x] <= 0:
                y = y + 1
        target.update(x, y)
        
    def draw(self):
        if self.state == State.START:
            pyxel.cls(0)
            pyxel.text(0, 0, "PRESS S", 7)
            # pyxel.text(int(pyxel.width/4.0), int(pyxel.height/2.0), "1 PLAYER GAME",  7)            
            
        elif self.state == State.MAIN:
            pyxel.cls(0)
            pyxel.text(0, 0, f"{int(self.timer)}sec", 7)
            pyxel.text(30,0, f"{self.num_got_items}/{self.max_items}", 7)

            # 迷路
            self.draw_map()    
            
            # 敵キャラのパス
            self.draw_enemy_route()
            
            # 自キャラ
            pyxel.rect(self.ego.x, self.ego.y, 1, 1, self.ego.c)
            
            # 敵キャラ
            pyxel.rect(self.enemy.x, self.enemy.y, 1, 1, self.enemy.c)
            
        elif self.state == State.CHANGE:
            pyxel.cls(0)
            pyxel.text(int(pyxel.width/4.0), int(pyxel.height/2.0), "NEXT FLOOR",  7 )            

        elif self.state == State.END:
            pyxel.cls(0)            
            pyxel.text(int(pyxel.width/4.0), int(pyxel.height/2.0), "GAME OVER",  7 )            
        
        

    def draw_enemy_route(self):
        for cell in self.route:
            x = cell[1]
            y = cell[0]
            pyxel.rect(x, y, 1, 1, 6)

            
    def draw_map(self):
        # 迷路を描画
        for i in range(self.map.w):
            for j in range(self.map.h):
                if self.is_open[j, i]:
                    if self.map.data[j, i] == 0:
                        pyxel.rect(i, j, 1, 1, 5)
                if self.map.data[j, i] == -1:
                    pyxel.rect(i, j, 1, 1, 8)
        
    
App()