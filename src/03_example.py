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
        # 位置情報
        self.x = _x
        self.y = _y
        self.c = _c # 色
        
        self.waiting_time = 15 # [frames] ゴールに到着したらこれが0になるまで出発できない
        self.loaded = False # 積荷かどうか
        self.load_capacity = 100 # [ton] 

    def update(self, _x, _y):
        self.x = _x
        self.y = _y

class App:
    def __init__(self):

        # ゲームの設定
        self.name = "03_example"
        self.state = State.START
        pyxel.init(96, 64, caption=self.name, scale=3, fps=30)

        self.waiting_count = 7 # [frames]
        self.count = 0 # 画面遷移用カウンタ
        self.num_got_items = 0
        self.max_items = 1e10 # これだけ獲得したら次の画面へ
        
        self.total_score = 0 # 運んだ量
        
        # 地図の初期化
        self.map = City(pyxel.width, pyxel.height)
        self.num_col_rooms = 3
        self.num_row_rooms = 3
        self.corrider_width = 2
        self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, 
                                    num_row_rooms=self.num_row_rooms,
                                    corrider_width=self.corrider_width,
                                    max_room_size_ratio=0.7,
                                    min_room_size_ratio=0.2
                                    )
        self.map.set_start()
        
        # 自キャラの初期化
        self.ego = Vehicle(self.map.start_x, self.map.start_y, 11)
        self.route = deque()
        if self.ego.loaded:
            self.destination = random.choice(list(self.map.dumpings.items())) # (idx, (y, x)) # キャラの目的地
        else:
            self.destination = random.choice(list(self.map.loadings.items())) # (idx, (y, x)) # キャラの目的地

        # 実行        
        pyxel.run(self.update, self.draw)

    def update(self):
        """
        状態を変更する関数。毎フレーム呼ばれる。
        """
        if self.state == State.START: # 開始演出            
            if (pyxel.btn(pyxel.KEY_S)):
                self.state = State.MAIN

        elif self.state == State.MAIN: # メイン画面

            # 自キャラの自動操縦
            # self.move_target(self.ego)
            self.act_target(self.ego)            

            # 目的地に到達したかどうかを判定
            if self.map.data[self.ego.y, self.ego.x] == self.destination[0]:# -1:

                self.ego.waiting_time -= 1 # 0になるまで出発できない

                if self.ego.waiting_time == 0:
                    
                    # 目的地についたので積荷空荷を反転                
                    if self.ego.loaded:
                        self.ego.loaded = False
                        self.total_score += self.ego.load_capacity
                    else:
                        self.ego.loaded = True

                    #  現在の状態に合わせて目的地を変更
                    if self.ego.loaded:
                        self.destination = random.choice(list(self.map.dumpings.items())) # (idx, (y, x)) # キャラの目的地
                    else:   
                        self.destination = random.choice(list(self.map.loadings.items())) # (idx, (y, x)) # キャラの目的地

                    # 待ち時間を初期化
                    self.ego.waiting_time = 15 # TODO: reset関数
                else:
                    pass



    def draw(self):
        """
        描画に関することのみここでは書く。状態は変更しないこと。
        """
        if self.state == State.START:
            pyxel.cls(0)
            pyxel.text(5, int(pyxel.height/2.0), "PLAY GAME",  7)            
            
        elif self.state == State.MAIN:
            pyxel.cls(0)
            pyxel.text(0, 0, f"Score: {self.total_score} ton",  7)            
            
            # 迷路
            self.draw_map()    

            # 経路
            self.draw_route()

            # 自キャラ
            pyxel.rect(self.ego.x, self.ego.y, 1, 1, self.ego.c)

        elif self.state == State.END:
            pyxel.cls(0)
            pyxel.text(5, int(pyxel.height/2.0), "GAME OVER",  7 )            

    # ----------------------------------------------------------------------



    # 描画関数
    def draw_route(self):
        for idx, cell in enumerate(self.route):
            if idx != 0 and idx != len(self.route)-1:
                x = cell[1]
                y = cell[0]
                pyxel.rect(x, y, 1, 1, 6)

    def draw_map(self):
        """地図を描画"""
        for i in range(self.map.w):
            for j in range(self.map.h):
                if self.map.data[j, i] == 0 or self.map.data[j, i] == -2: # FREE and START
                    pyxel.rect(i, j, 1, 1, 5)
                if self.map.data[j, i] == -1: # GOAL
                    pyxel.rect(i, j, 1, 1, 8)
                if self.map.data[j, i] >= 2: # LOCATION
                    if self.map.data[j, i] %2 == 0: # DUMP
                        pyxel.rect(i, j, 1, 1, 2)
                    elif self.map.data[j, i] %2 != 0: # LOAD                        
                        pyxel.rect(i, j, 1, 1, 12)
    
    # 状態を更新する関数
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
        
    
App()