import copy
import random
from enum import Enum
from collections import deque

import numpy as np
import pyxel

from city2 import City

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
        self.c = _c
        self.d = _d

    def update(self, _x, _y):
        self.x = _x
        self.y = _y


class App:
    def __init__(self):

        # ゲームの設定
        self.name = "06_example"
        pyxel.init(256, 256, caption=self.name, scale=2, fps=10)
        pyxel.load("my_resource.pyxres")

        scale = int(256/16)

        self.map = City(128, 64) # int(pyxel.width), int(pyxel.height/8))
        self.num_col_rooms = 4
        self.num_row_rooms = 3
        self.corrider_width = 1
        self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, 
                                    num_row_rooms=self.num_row_rooms,
                                    corrider_width=self.corrider_width,
                                    max_room_size_ratio=0.8,
                                    min_room_size_ratio=0.2
        )
        self.is_seen = np.zeros((self.map.h, self.map.w), dtype=bool)
        
        # self.map.data = np.ones((self.map.h, self.map.w), dtype=np.int)
        # self.map.data[2:-2, 2:-2] = 0
        # self.map.data[6:-6, 6:-6] = 1

        self.real_size_map = self.map.data.repeat(16, axis=0).repeat(16, axis=1)
        print(self.real_size_map.shape)
        
        # 自キャラの初期化
        x = int(np.random.rand() * self.map.w)
        y = int(np.random.rand() * self.map.h)
        while self.map.data[y, x] != 0:
            x = int(np.random.rand() * self.map.w)
            y = int(np.random.rand() * self.map.h)
        c = 11
        self.ego = Vehicle(x*16, y*16, c, Direction.UP)
        
        # いま地図データは64x64、描画範囲は16x16
        # 画面の描画位置(iy, ix) = (tiy + cy, tix + cx)
        cx = self.ego.x
        cy = self.ego.y
        mcx = int(cx/16)
        mcy = int(cy/16)        
        rmdx = 8
        lmdx = 8
        umdy = 8
        dmdy = 8
        mdx2 = 16
        mdy2 = 16
        
        if mcx - lmdx < 0:            
            lmdx = mcx - 0
            rmdx = mdx2 - lmdx
        if mcx + rmdx > self.map.w:
            rmdx = self.map.w - mcx
            lmdx = mdx2 - rmdx
        if mcy - umdy < 0:
            umdy = mcy - 0
            dmdy = mdy2 - umdy
        if mcy + dmdy > self.map.h:
            dmdy = self.map.h - mcy
            umdy = mdy2 - dmdy
            
        self.local_data = self.map.data[mcy-umdy:mcy+dmdy, mcx-lmdx:mcx+rmdx]

        
        # 実行        
        pyxel.run(self.update, self.draw)

    def update(self):
        """
        状態を変更する関数。毎フレーム呼ばれる。
        """

        # いま地図データは64x64、描画範囲は16x16
        # 画面の描画位置(iy, ix) = (tiy + cy, tix + cx)
        cx = self.ego.x
        cy = self.ego.y
        mcx = int(cx/16)
        mcy = int(cy/16)        
        rmdx = 8
        lmdx = 8
        umdy = 8
        dmdy = 8
        mdx2 = 16
        mdy2 = 16
        
        if mcx - lmdx < 0:            
            lmdx = mcx - 0
            rmdx = mdx2 - lmdx
        if mcx + rmdx > self.map.w:
            rmdx = self.map.w - mcx
            lmdx = mdx2 - rmdx
        if mcy - umdy < 0:
            umdy = mcy - 0
            dmdy = mdy2 - umdy
        if mcy + dmdy > self.map.h:
            dmdy = self.map.h - mcy
            umdy = mdy2 - dmdy
            
        self.local_data = self.map.data[mcy-umdy:mcy+dmdy, mcx-lmdx:mcx+rmdx]        
        mx = int(self.ego.x/16)
        my = int(self.ego.y/16)
        # self.map.data[my, mx] = 9
        print(self.local_data)
        print(self.local_data.shape)

        # 自キャラの操作            
        self.move_target(self.ego)
        print(self.ego.d)

        # 画面上での自キャラの位置
        # 基本は画面中央
        # 画面端のときだけ視覚中央からはずれる
        self.ego_vx = int(256/2)
        self.ego_vy = int(256/2)
        lvdx = rvdx = uvdy = dvdy = 128

        if self.ego.x - 128< 0:
            lvdx = self.ego.x
            rvdx = 256 - lvdx
            self.ego_vx = lvdx
        if self.ego.x + rvdx > self.map.w*16:
            rvdx = self.map.w*16 - self.ego.x
            lvdx = 256 - rvdx 
            self.ego_vx = lvdx
        if self.ego.y - 128 < 0:
            uvdy = self.ego.y
            dvdy = 256 - uvdy
            self.ego_vy = uvdy
        if self.ego.y + dvdy > self.map.h*16:
            dvdy = self.map.h*16 - self.ego.y
            uvdy = 256 - dvdy 
            self.ego_vy = uvdy
        print(lvdx, rvdx, uvdy, dvdy)    
        print(self.ego.x, self.ego.y)
        print(self.ego_vx, self.ego_vy)

    
    def draw(self):
        """
        描画に関することのみここでは書く。状態は変更しないこと。
        """
        pyxel.cls(0)
        pyxel.text(5, 5, "04-EXAMPLE",  7)            
        
        class TyleType(Enum):
            WALL_IN_UP = 1,
            WALL_IN_DOWN = 2,
            WALL_IN_LEFT = 3,
            WALL_IN_RIGHT = 4,
            WALL_IN_UL_CORNER = 5,
            WALL_IN_DL_CORNER = 6,
            WALL_IN_UR_CORNER = 7,
            WALL_IN_DR_CORNER = 8,

            WALL_OUT_UP = 9,
            WALL_OUT_DOWN = 10,
            WALL_OUT_LEFT = 11,
            WALL_OUT_RIGHT = 12,
            WALL_OUT_UL_CORNER = 13,
            WALL_OUT_DL_CORNER = 14,
            WALL_OUT_UR_CORNER = 15,
            WALL_OUT_DR_CORNER = 16,
                        
            WALL_CORRIDER_H_CENTER = 17,
            WALL_CORRIDER_V_CENTER = 18,
            
            WALL_CORRIDER_LEFT = 19,
            WALL_CORRIDER_RIGHT = 20,
            WALL_CORRIDER_UP = 21,
            WALL_CORRIDER_DOWN = 22,
            
        def draw_tile(x, y, tile_type):
            # txy = get_tile_loc(tile_type)
            # pyxel.blt(x, y, 0, txy[0], txy[1], 16, 16)
            pass

        # リアルでの描画
        for i in range(16):
            for j in range(16):
                x = i * 16
                y = j * 16
                # if self.local_data[j, i] == 0:
                pyxel.rect(x, y, 16, 16, self.local_data[j, i])
                # elif self.local_data[j, i] == 1:
                    # pyxel.rect(x, y, 16, 16, 0)

        
        
        
        pyxel.rect(self.ego_vx, self.ego_vy, 16, 16, 11)   
        bltx = 0
        blty = 0
        bltw = 16
        blth = 16
        if self.ego.d == Direction.DOWN:
            bltx = 16*0
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
            
            
        pyxel.blt(self.ego_vx, self.ego_vy, 0, bltx, 16, bltw, blth)
        
        # print(self.ego.x, self.ego.y)

                    
        lsmx = rsmx = usmy = dsmy = 8        
        if int(self.ego.x/16)-8 < 0:
            lsmx = int(self.ego.x/16)
            rsmx = 16 - lsmx
        if int(self.ego.x/16)+8 > self.map.w:
            rsmx = self.map.w - int(self.ego.x/16)
            lsmx = 16 - rsmx
        
        if int(self.ego.y/16)-8 < 0:
            usmy = int(self.ego.y/16)
            dsmy = 16 - usmy
        if int(self.ego.y/16)+8 > self.map.h:
            dsmy = self.map.h - int(self.ego.y/16)
            usmy = 16 - dsmy

        # スモールマップの描画
        # みたことあるところだけ描画
        for i in range(self.map.w):
            for j in range(self.map.h):
                                                
                x = i + 15
                y = j + 15
            
                if self.map.data[j, i] == 0:
                    if self.is_seen[j, i] == True:
                        pyxel.rect(x, y, 1, 1, 5)
                    else:
                        pass
                        # pyxel.rect(x, y, 1, 1, 12)
                        

        pyxel.rect(int(self.ego.x/16) + 15, int(self.ego.y/16) + 15, 1, 1, 11)
        pyxel.rectb(int(self.ego.x/16)- lsmx + 15, int(self.ego.y/16) - usmy + 15, 16, 16, 8)

        for i in range(self.map.w):
            for j in range(self.map.h):
                
                if int(self.ego.x/16)- lsmx < i < int(self.ego.x/16) + rsmx and \
                    int(self.ego.y/16) - usmy < j < int(self.ego.y/16) + dsmy:
                    x = i + 15
                    y = j + 15
                
                    self.is_seen[j, i] = True
                
        
    def move_target(self, target):
        x = target.x
        y = target.y            
        s = 16.
        mx = x / 16.
        my = y / 16.
        ms = s / 16.

        if pyxel.btn(pyxel.KEY_LEFT):            
            self.ego.d = Direction.LEFT
            if self.map.data[int(my), int(mx-ms)] != 1:
                x = x - s
                mx = x / 16.

        if pyxel.btn(pyxel.KEY_RIGHT):
            self.ego.d = Direction.RIGHT
            if self.map.data[int(my), int(mx+ms)] != 1:
                x = x + s
                mx = x / 16.

        if pyxel.btn(pyxel.KEY_UP):
            self.ego.d = Direction.UP
            if self.map.data[int(my-ms), int(mx)] != 1:
                y = y - s
                my = y / 16.

        if pyxel.btn(pyxel.KEY_DOWN):
            self.ego.d = Direction.DOWN
            if self.map.data[int(my+ms), int(mx)] != 1:
                y = y + s
                my = y / 16.

        if pyxel.btn(pyxel.KEY_LEFT) and pyxel.btn(pyxel.KEY_UP):
            self.ego.d = Direction.UPLEFT
            # if self.map.data[int(my-ms), int(mx-ms)] != 1:
            #     x = x - s
            #     y = y - s
            #     mx = x / 16.
            #     my = y / 16.

        if pyxel.btn(pyxel.KEY_LEFT) and pyxel.btn(pyxel.KEY_DOWN):
            self.ego.d = Direction.DOWNLEFT
            # if self.map.data[int(my+ms), int(mx-ms)] != 1:
            #     x = x - s
            #     y = y + s
            #     mx = x / 16.
            #     my = y / 16.

        if pyxel.btn(pyxel.KEY_RIGHT) and pyxel.btn(pyxel.KEY_UP):
            self.ego.d = Direction.UPRIGHT
            # if self.map.data[int(my-ms), int(mx+ms)] != 1:
            #     x = x + s
            #     y = y - s
            #     mx = x / 16.
            #     my = y / 16.

        if pyxel.btn(pyxel.KEY_RIGHT) and pyxel.btn(pyxel.KEY_DOWN):
            self.ego.d = Direction.DOWNRIHGHT
            # if self.map.data[int(my+ms), int(mx+ms)] != 1:
            #     x = x + s
            #     y = y + s
            #     mx = x / 16.
            #     my = y / 16.
                
        target.update(x, y)

App()