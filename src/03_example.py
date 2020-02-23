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
        self.dest = 0 # 目的の部屋番号

    def update(self, _x, _y):
        self.x = _x
        self.y = _y

class App:
    def __init__(self):

        self.name = "02_example"
        
        self.state = State.START
        
        pyxel.init(42, 42, caption=self.name, scale=6, fps=15)
        # pyxel.image(0).load(0, 0, "pyxel_logo_38x16.png") # opening
        
        # 地図の初期化
        self.map = Map(pyxel.width, pyxel.height)
        self.num_col_rooms = 2
        self.num_row_rooms = 2
        self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, 
                                    num_row_rooms=self.num_row_rooms,
                                    corrider_width=2,
                                    max_room_size_ratio=0.5,
                                    min_room_size_ratio=0.2
                                    )
        self.map.set_goal()
        
        # 自キャラの初期化
        x = int(np.random.rand() * pyxel.width)
        y = int(np.random.rand() * pyxel.height)
        while self.map.data[y, x] != 0:
            x = int(np.random.rand() * pyxel.width)
            y = int(np.random.rand() * pyxel.height)            
        c = 11
        self.ego = Vehicle(x, y, c)


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


        elif self.state == State.MAIN: # メイン

            # 自キャラの操作            
            self.move_target(self.ego)

            # ゴールに到達したかどうかを判定
            if self.map.data[self.ego.y, self.ego.x] == -1:
                self.num_got_items += 1
                
                # 獲得アイテムが閾い異常のとき次のstageへ
                if self.num_got_items >= self.max_items:
                    self.state = State.CHANGE
                
                self.map.set_goal()

    def draw(self):
        if self.state == State.START:
            pyxel.cls(0)
            pyxel.text(int(pyxel.width/4.0), int(pyxel.height/2.0), "1 PLAYER GAME",  7)            
            
        elif self.state == State.MAIN:
            pyxel.cls(0)
            
            # 迷路
            self.draw_map()    
            
            # 自キャラ
            pyxel.rect(self.ego.x, self.ego.y, 1, 1, self.ego.c)

        elif self.state == State.CHANGE:
            pyxel.cls(0)
            pyxel.text(int(pyxel.width/4.0), int(pyxel.height/2.0), "NEXT MAP",  7 )            

        elif self.state == State.END:
            pyxel.cls(0)
            pyxel.text(int(pyxel.width/4.0), int(pyxel.height/2.0), "GAME OVER",  7 )            

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
        
            
    def draw_map(self):
        # 迷路を描画
        for i in range(self.map.w):
            for j in range(self.map.h):
                if self.map.data[j, i] == 0:
                    pyxel.rect(i, j, 1, 1, 5)
                if self.map.data[j, i] == -1:
                    pyxel.rect(i, j, 1, 1, 8)
        
    
App()