import copy
import random
from enum import Enum
from collections import deque

import numpy as np
import pyxel

from maze import Maze

class State(Enum):
  START = 1 # 開始演出
  MAIN = 2 # メイン
  GOAL = 3 # ゴール
  CHANGE = 4 # マップ切り替え
  END = 5 # 終了

class Direction(Enum):
    UP = 1,
    UPRIGHT =2,
    RIGHT=3,
    DOWNRIHGHT=4,
    DOWN=5,
    DOWNLEFT=6,
    LEFT=7,
    UPLEFT=8
    
class Vehicle:
    def __init__(self, _x, _y, _c, _d=Direction.UP):
        super().__init__()
        self.x = _x
        self.y = _y
        self.c = _c # 色
        self.d = _d # 描画用の方向

    def update(self, _x, _y):
        self.x = _x
        self.y = _y


class App:
    def __init__(self):

        # ゲームの名前
        self.name = "06_example"

        # ゲームの設定
        pyxel.init(256, 256, caption=self.name, scale=2, fps=10)
        pyxel.load("my_resource.pyxres")
        

        # タイミング
        self.tick = 0 

        # 地図
        self.map = Maze(128, 64)
        self.num_col_rooms = 4
        self.num_row_rooms = 3
        self.corrider_width = 3
        self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, 
                                    num_row_rooms=self.num_row_rooms,
                                    corrider_width=self.corrider_width,
                                    max_room_size_ratio=0.8,
                                    min_room_size_ratio=0.2
        )

        # 見たことある場所
        self.is_seen = np.zeros((self.map.h, self.map.w), dtype=bool)
        
        # 自キャラの初期化, map.dataの16倍の位置
        yx = self.map.get_free_space(num=1)
        self.ego = Vehicle(yx[1]*16, yx[0]*16, 11, Direction.UP) 

        # 自車両中心で描画可能な範囲だけを取り出しち地図と、その左右上下のマージン
        self.local_data, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)

        # 実行        
        pyxel.run(self.update, self.draw)

    def update(self):
        """
        状態を変更する関数。毎フレーム呼ばれる。
        """


        # 画面内に表示される分だけのローカル地図
        self.local_data, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)
        
        # 自キャラの操作うけつけ
        self.move_target(self.ego)

        # 画面上での自キャラの位置
        # 基本は画面中央で、画面端のときだけ視覚中央からはずれる
        self.ego_vx = self.margins[0] * 16 
        self.ego_vy = self.margins[2] * 16

        # 探索済みのフラグ更新
        cx = int(self.ego.x/16.)
        cy = int(self.ego.y/16.)
        lsmx, rsmx, usmy, dsmy = self.margins
        for i in range(self.map.w):
            for j in range(self.map.h):                
                if cx - lsmx < i < cx + rsmx and cy - usmy < j < cy + dsmy:
                    self.is_seen[j, i] = True

        # トラック静止中の上下振動描画用時計        
        if pyxel.frame_count%5 == 0:
            self.tick += 1

        
    def draw(self):
        """
        描画に関することのみここでは書く。状態は変更しないこと。
        """
        
        # キャンバスのクリア
        pyxel.cls(0)        
        
        # 地図の描画
        for i in range(16):
            for j in range(16):
                x = i * 16
                y = j * 16
                pyxel.rect(x, y, 16, 16, self.local_data[j, i])
        
        # 自キャラの描画
        pyxel.rect(self.ego_vx, self.ego_vy, 16, 16, 11)   
        # self.draw_vehicle(self.ego_vx, self.ego_vy)        
                 
        # スモールマップの描画みたことあるところだけ描画
        smap_margin = 15 # [pix]
        for i in range(self.map.w):
            for j in range(self.map.h):                                                
                x = i + smap_margin
                y = j + smap_margin   
                if self.map.data[j, i] == 0:
                    if self.is_seen[j, i] == True:
                        pyxel.rect(x, y, 1, 1, 5)
                    else:
                        pass
                        # pyxel.rect(x, y, 1, 1, 12)

        # スモールマップの自キャラと視野範囲の描画
        _, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)
        lsmx, rsmx, usmy, dsmy = self.margins
        cx = int(self.ego.x/16)
        cy = int(self.ego.y/16)
        pyxel.rect (cx + smap_margin, cy + smap_margin, 1,  1, 11)
        pyxel.rectb(cx - lsmx + smap_margin, cy - usmy + 15, 16, 16, 8)

        # ゲームタイトルの描画            
        pyxel.text(5, 5, self.name,  7)            

    def draw_vehicle(self, x, y):
        bltx = 0
        blty = 0
        bltw = 16
        blth = 16
        if self.ego.d == Direction.DOWN:
            if self.tick % 2 == 0:
                bltx = 16*0
            else:
                bltx = 16*8
            blty = 0
        elif self.ego.d == Direction.UP:
            bltx = 16*1
            blty = 0
        elif self.ego.d == Direction.RIGHT:
            bltx = 16*2
            blty = 0
        elif self.ego.d == Direction.LEFT:
            bltx = 16*3
            blty = 0
        elif self.ego.d == Direction.DOWNRIHGHT:
            bltx = 16*4
            blty = 0
        elif self.ego.d == Direction.DOWNLEFT:
            bltx = 16*5 
            blty = 0
        elif self.ego.d == Direction.UPLEFT:
            bltx = 16*6 
            blty = 0
        elif self.ego.d == Direction.UPRIGHT:
            bltx = 16*7 
            blty = 0
            
        pyxel.blt(x, y, 0, bltx, blty, bltw, blth)


    def move_target(self, target):
        x = target.x
        y = target.y            
        s = 16.
        mx = x / 16.
        my = y / 16.
        ms = s / 16.

        if pyxel.btn(pyxel.KEY_LEFT):            
            if self.map.data[int(my), int(mx-ms)] != 1:
                self.ego.d = Direction.LEFT
                x = x - s
                mx = x / 16.

        if pyxel.btn(pyxel.KEY_RIGHT):            
            if self.map.data[int(my), int(mx+ms)] != 1:
                self.ego.d = Direction.RIGHT
                x = x + s
                mx = x / 16.

        if pyxel.btn(pyxel.KEY_UP):
            if self.map.data[int(my-ms), int(mx)] != 1:
                self.ego.d = Direction.UP
                y = y - s
                my = y / 16.

        if pyxel.btn(pyxel.KEY_DOWN):            
            if self.map.data[int(my+ms), int(mx)] != 1:
                self.ego.d = Direction.DOWN
                y = y + s
                my = y / 16.

        if pyxel.btn(pyxel.KEY_LEFT) and pyxel.btn(pyxel.KEY_UP):
            
            if self.map.data[int(my-ms), int(mx-ms)] != 1:
                self.ego.d = Direction.UPLEFT

        if pyxel.btn(pyxel.KEY_LEFT) and pyxel.btn(pyxel.KEY_DOWN):

            if self.map.data[int(my+ms), int(mx-ms)] != 1:
                self.ego.d = Direction.DOWNLEFT

        if pyxel.btn(pyxel.KEY_RIGHT) and pyxel.btn(pyxel.KEY_UP):
            
            if self.map.data[int(my-ms), int(mx+ms)] != 1:
                self.ego.d = Direction.UPRIGHT

        if pyxel.btn(pyxel.KEY_RIGHT) and pyxel.btn(pyxel.KEY_DOWN):
            if self.map.data[int(my+ms), int(mx+ms)] != 1:
                self.ego.d = Direction.DOWNRIHGHT
                
        target.update(x, y)

App()