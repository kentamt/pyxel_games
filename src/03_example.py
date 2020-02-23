import random
from enum import Enum
from collections import deque

import numpy as np
import pyxel

from city import City

class State(Enum):
  START = 1 # 開始演出
  MAIN = 2 # メイン
  GOAL = 3 # ゴール
  CHANGE = 4 # マップ切り替え
  END = 5 # 終了

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

        self.name = "03_example"
        self.state = State.START
        pyxel.init(48, 64, caption=self.name, scale=3, fps=30)
        self.waiting_count = 7 # [frames]
        self.count = 0 # 画面遷移用カウンタ
        
        # 地図の初期化
        self.map = City(pyxel.width, pyxel.height)
        self.num_col_rooms = 2
        self.num_row_rooms = 3
        self.corrider_width = 1
        self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, 
                                    num_row_rooms=self.num_row_rooms,
                                    corrider_width=self.corrider_width,
                                    max_room_size_ratio=0.7,
                                    min_room_size_ratio=0.2
                                    )
        self.map.set_start()
        # self.map.set_goal()

        
        # 自キャラの初期化
        c = 11
        self.ego = Vehicle(self.map.start_x, self.map.start_y, c)
        self.route = deque()
        print(self.map.locations)
        self.destination = random.choice(list(self.map.locations.items())) # (idx, (y, x))
        print(self.destination)

        # 獲得item数
        self.num_got_items = 0
        self.max_items = 1e10 # これだけ獲得したら次の画面へ
        
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
                self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms,
                                            num_row_rooms=self.num_row_rooms, 
                                            corrider_width=self.corrider_width)
                # self.map.set_goal()
                
                # キャラの初期化
                self.ego.x = self.map.start_x
                self.ego.y = self.map.start_y
                self.route = deque()

        elif self.state == State.MAIN:

            # 自キャラの自動操縦
            # self.move_target(self.ego)
            self.act_target(self.ego)            
            # print(self.map.data[self.ego.y, self.ego.x])

            # ゴールに到達したかどうかを判定
            if self.map.data[self.ego.y, self.ego.x] == self.destination[0]:# -1:
                self.num_got_items += 1                
                
                # 獲得アイテムが閾い以上のとき次のstageへ
                if self.num_got_items >= self.max_items:
                    self.state = State.GOAL
                    self.count = 0         
                
                else: # そうでなければ次の目的地へ
                    # self.map.set_goal()                
                    self.destination = random.choice(list(self.map.locations.items()))# 座標
                    
        elif self.state == State.GOAL: # ゴール後
        
            if self.state == State.GOAL:
                self.count += 1
                if self.count > self.waiting_count:
                    self.state = State.CHANGE
            
                

    def draw(self):
        if self.state == State.START:
            pyxel.cls(0)
            pyxel.text(5, int(pyxel.height/2.0), "PLAY GAME",  7)            
            
        elif self.state == State.MAIN or self.state == State.GOAL:
            pyxel.cls(0)

            # 迷路
            self.draw_map()    

            # 経路
            self.draw_route()

            # 自キャラ
            pyxel.rect(self.ego.x, self.ego.y, 1, 1, self.ego.c)

        elif self.state == State.CHANGE:
            pyxel.cls(0)
            pyxel.text(5, int(pyxel.height/2.0), "NEXT MAP",  7 )            

        elif self.state == State.END:
            pyxel.cls(0)
            pyxel.text(5, int(pyxel.height/2.0), "GAME OVER",  7 )            

    def act_target(self, target):
        # 最短経路の更新
        if len(self.route) == 0:        
            self.route = self.map.search_shortest_path_dws((self.ego.y, self.ego.x), self.destination[1])
            self.route = deque(self.route)
            self.route.popleft() # 一つ目はstartなので捨てる

        if len(self.route) > 0:
            next_cell = self.route.popleft()
            target.update(next_cell[1], next_cell[0])

        else:
            pass


    def move_target(self, target):
        x = target.x
        y = target.y            
        if pyxel.btn(pyxel.KEY_LEFT):
            if 0 <= x - 1 < pyxel.width and self.map.data[y, x -1] != 1:
                x = x - 1
        if pyxel.btn(pyxel.KEY_RIGHT):
            if 0 <= x + 1 < pyxel.width and self.map.data[y, x +1] != 1:
                x = x + 1
        if pyxel.btn(pyxel.KEY_UP):
            if 0 <= y - 1 < pyxel.height and self.map.data[y-1, x] != 1:
                y = y - 1
        if pyxel.btn(pyxel.KEY_DOWN):
            if 0 <= y + 1 < pyxel.height and self.map.data[y+1, x] != 1:
                y = y + 1
        target.update(x, y)
        
    def draw_route(self):
        for idx, cell in enumerate(self.route):
            if idx != 0 and idx != len(self.route)-1:
                x = cell[1]
                y = cell[0]
                pyxel.rect(x, y, 1, 1, 6)

    def draw_map(self):
        # 迷路を描画
        for i in range(self.map.w):
            for j in range(self.map.h):
                if self.map.data[j, i] == 0 or self.map.data[j, i] == -2: # FREE and START
                    pyxel.rect(i, j, 1, 1, 5)
                if self.map.data[j, i] == -1: # GOAL
                    pyxel.rect(i, j, 1, 1, 8)
                if self.map.data[j, i] >= 2: # LOCATION CENTER
                    pyxel.rect(i, j, 1, 1, 12)
        
    
App()