import copy
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

        # ゲームの設定
        self.name = "05_example"
        pyxel.init(256, 256, caption=self.name, scale=2, fps=15)
        pyxel.load("my_resource.pyxres")

        scale = int(256/16)

        self.map = City(16, 16) # int(pyxel.width), int(pyxel.height/8))
        self.map.data = np.ones((self.map.h, self.map.w), dtype=np.int)
        self.map.data[2:-2, 2:-2] = 0
        self.map.data[6:-6, 6:-6] = 1
        self.map.data[:, 4] = 0
        self.map.data[5, :] = 0
        
        


        self.real_size_map = copy.deepcopy(self.map.data )
        
        # 自キャラの初期化
        x = int(np.random.rand() * self.map.w)
        y = int(np.random.rand() * self.map.h)
        while self.map.data[y, x] != 0:
            x = int(np.random.rand() * self.map.w)
            y = int(np.random.rand() * self.map.h)
        c = 11
        self.ego = Vehicle(x, y, c)
        


        # 実行        
        pyxel.run(self.update, self.draw)

    def update(self):
        """
        状態を変更する関数。毎フレーム呼ばれる。
        """
        # 自キャラの操作            
        self.move_target(self.ego)
 
    
    def draw(self):
        """
        描画に関することのみここでは書く。状態は変更しないこと。
        """
        pyxel.cls(0)
        pyxel.text(5, 5, self.name,  7)            
        
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
            

        tile_info_map = np.zeros((self.map.h, self.map.w), dtype=np.int)

        # y方向に微分して境目を見つける
        for iy in range(self.map.h-1):
            line = self.map.data[iy+1, :] - self.map.data[iy, :]
            # 壁から通路なら-1, 通路から壁なら1
            for ix, e in enumerate(line):
                if e == -1:                    
                    tile_info_map[iy, ix] = 1
                if e == 1:                    
                    tile_info_map[iy+1, ix] = 2

        # x方向に微分して境目を見つける
        for ix in range(self.map.w-1):
            line = self.map.data[:, ix+1] - self.map.data[:, ix]
            # 壁から通路なら-1, 通路から壁なら1
            for iy, e in enumerate(line):
                if e == -1:                    
                    tile_info_map[iy, ix] = 3
                if e == 1:                    
                    tile_info_map[iy, ix+1] = 4
        # 0, 1     5, 1
        # 3, 0 ==> 3, 0
        srcs = [
            np.array([[0,1],[3, 0]]),
            np.array([[3,0],[0, 2]]),
            np.array([[1,0],[0, 4]]),
            np.array([[0,4],[2, 0]]),
            np.array([[4,2],[4, 0]]),            
            np.array([[4,0],[4, 1]]),            
            np.array([[2,3],[0, 3]]),
            np.array([[0,3],[1, 3]]),

        ]
        
        dsts = [
            np.array([[5,1],[3, 0]]),
            np.array([[3,0],[6, 2]]),
            np.array([[1,7],[0, 4]]),
            np.array([[0,4],[2, 8]]),
            np.array([[13,2],[4, 0]]),
            np.array([[4,0],[14, 1]]),            
            np.array([[2,15],[0, 3]]),
            np.array([[0,3],[1, 16]]),                        
        ]

        import copy 
        for src, dst in zip(srcs, dsts):
            tile_info_map_copy = copy.deepcopy(tile_info_map)
            for iy in range(self.map.h-1):
                for ix in range(self.map.w-1):
                    diff = tile_info_map[iy:iy+2, ix:ix+2] - src                
                    if np.all(diff == 0):
                        tile_info_map_copy[iy:iy+2, ix:ix+2] = dst
            tile_info_map = copy.deepcopy(tile_info_map_copy)
        
        src = np.array([1,0,1,0,2])
        dst = np.array([1,0,17,0,2])
        
        tile_info_map_copy = copy.deepcopy(tile_info_map)
        for iy in range(self.map.h-4):
            for ix in range(self.map.w):
                diff = tile_info_map[iy:iy+5, ix] - src                
                if np.all(diff == 0):
                    tile_info_map_copy[iy:iy+5, ix] = dst
        tile_info_map = copy.deepcopy(tile_info_map_copy)
∑    
        src = np.array([3,0,3,0,4])
        dst = np.array([3,0,18,0,4])
        
        tile_info_map_copy = copy.deepcopy(tile_info_map)
        for iy in range(self.map.h):
            for ix in range(self.map.w-4):
                diff = tile_info_map[iy, ix:ix+5] - src                
                if np.all(diff == 0):
                    tile_info_map_copy[iy, ix:ix+5] = dst
        tile_info_map = copy.deepcopy(tile_info_map_copy)
    
        src = np.array([4, 17])
        dst = np.array([19, 17])
        tile_info_map_copy = copy.deepcopy(tile_info_map)
        for iy in range(self.map.h):
            for ix in range(self.map.w-1):
                diff = tile_info_map[iy, ix:ix+2] - src                
                if np.all(diff == 0):
                    tile_info_map_copy[iy, ix:ix+2] = dst
        tile_info_map = copy.deepcopy(tile_info_map_copy)
        

        src = np.array([17, 3])
        dst = np.array([17, 20])
        tile_info_map_copy = copy.deepcopy(tile_info_map)
        for iy in range(self.map.h):
            for ix in range(self.map.w-1):
                diff = tile_info_map[iy, ix:ix+2] - src                
                if np.all(diff == 0):
                    tile_info_map_copy[iy, ix:ix+2] = dst
        tile_info_map = copy.deepcopy(tile_info_map_copy)
        

        src = np.array([18, 3])
        dst = np.array([18, 22])
        tile_info_map_copy = copy.deepcopy(tile_info_map)
        for iy in range(self.map.h-1):
            for ix in range(self.map.w):
                diff = tile_info_map[iy:iy+2, ix] - src                
                if np.all(diff == 0):
                    tile_info_map_copy[iy:iy+2, ix] = dst
        tile_info_map = copy.deepcopy(tile_info_map_copy)
        
        src = np.array([3, 18])
        dst = np.array([21, 18])
        tile_info_map_copy = copy.deepcopy(tile_info_map)
        for iy in range(self.map.h-1):
            for ix in range(self.map.w):
                diff = tile_info_map[iy:iy+2, ix] - src                
                if np.all(diff == 0):
                    tile_info_map_copy[iy:iy+2, ix] = dst
        tile_info_map = copy.deepcopy(tile_info_map_copy)
        
    
        def get_tile_loc(tile_type):
            if tile_type == TyleType.WALL_IN_UP:
                ret = (16, 32)
            elif tile_type == TyleType.WALL_IN_DOWN:
                ret = (16, 64)
            elif tile_type == TyleType.WALL_IN_LEFT:
                ret = (0, 48)
            elif tile_type == TyleType.WALL_IN_RIGHT:
                ret = (32, 48)
            elif tile_type == TyleType.WALL_IN_UL_CORNER:
                ret = (0, 32)
            elif tile_type == TyleType.WALL_IN_DL_CORNER:
                ret = (0, 64)
            elif tile_type == TyleType.WALL_IN_UR_CORNER:
                ret = (32, 32)
            elif tile_type == TyleType.WALL_IN_DR_CORNER:
                ret = (32, 64)
            elif tile_type == TyleType.WALL_OUT_UP:
                ret = (16, 80)
            elif tile_type == TyleType.WALL_OUT_DOWN:
                ret = (16, 112)
            elif tile_type == TyleType.WALL_OUT_LEFT:
                ret = (8, 96)
            elif tile_type == TyleType.WALL_OUT_RIGHT:
                ret = (24, 96)
            elif tile_type == TyleType.WALL_OUT_UL_CORNER:
                ret = (8, 80)
            elif tile_type == TyleType.WALL_OUT_DL_CORNER:
                ret = (8, 112)
            elif tile_type == TyleType.WALL_OUT_UR_CORNER:
                ret = (24, 80)
            elif tile_type == TyleType.WALL_OUT_DR_CORNER:
                ret = (24, 112)
            elif tile_type == TyleType.WALL_CORRIDER_H_CENTER:
                ret = (56, 32)
            elif tile_type == TyleType.WALL_CORRIDER_V_CENTER:
                ret = (40, 96)
            elif tile_type == TyleType.WALL_CORRIDER_LEFT:
                ret = (56, 48)
            elif tile_type == TyleType.WALL_CORRIDER_RIGHT:
                ret = (72, 32)
            elif tile_type == TyleType.WALL_CORRIDER_UP:
                ret = (40, 80)
            elif tile_type == TyleType.WALL_CORRIDER_DOWN:
                ret = (40, 112)
                pass
            else:
                ret = None    
                
            return ret

        def draw_tile(x, y, tile_type):
            txy = get_tile_loc(tile_type)
            pyxel.blt(x, y, 0, txy[0], txy[1], 16, 16)


        # いま地図データは64x64、描画範囲は16x16
        # 画面の描画位置(iy, ix) = (tiy + cy, tix + cx)
        cx = self.ego.x
        cy = self.ego.y
        
        for ix in range(pyxel.width)[::16]:
            for iy in range(pyxel.height)[::16]:                    
               
                tix = int(ix/16 + cx)
                tiy = int(iy/16 + cy)
                if 0 > tix:
                    tix = 0
                elif tix >= self.map.w:
                    tix = self.map.w-1

                if 0 > tiy:
                    tiy = 0
                elif tiy >= self.map.h:
                    tiy = self.map.h-1
                
                print(tiy, tix)
                
                tile_type = tile_info_map[tiy, tix]
                if tile_type == 1:
                    draw_tile(ix, iy, TyleType.WALL_IN_UP)

                elif tile_type == 2:
                    draw_tile(ix, iy, TyleType.WALL_IN_DOWN)

                elif tile_type == 3:
                    draw_tile(ix, iy, TyleType.WALL_IN_LEFT)

                elif tile_type == 4:
                    draw_tile(ix, iy, TyleType.WALL_IN_RIGHT)
                
                elif tile_type == 5:
                    draw_tile(ix, iy, TyleType.WALL_IN_UL_CORNER)

                elif tile_type == 6:
                    draw_tile(ix, iy, TyleType.WALL_IN_DL_CORNER)

                elif tile_type == 7:
                    draw_tile(ix, iy, TyleType.WALL_IN_UR_CORNER)

                elif tile_type == 8:
                    draw_tile(ix, iy, TyleType.WALL_IN_DR_CORNER)
                # -----
                elif tile_type == 9:
                    draw_tile(ix, iy, TyleType.WALL_OUT_UP)

                elif tile_type == 10:
                    draw_tile(ix, iy, TyleType.WALL_OUT_DOWN)

                elif tile_type == 11:
                    draw_tile(ix, iy, TyleType.WALL_OUT_LEFT)

                elif tile_type == 12:
                    draw_tile(ix, iy, TyleType.WALL_OUT_RIGHT)

                elif tile_type == 13:
                    draw_tile(ix, iy, TyleType.WALL_OUT_UL_CORNER)

                elif tile_type == 14:
                    draw_tile(ix, iy, TyleType.WALL_OUT_DL_CORNER)

                elif tile_type == 15:
                    draw_tile(ix, iy, TyleType.WALL_OUT_UR_CORNER)

                elif tile_type == 16:
                    draw_tile(ix, iy, TyleType.WALL_OUT_DR_CORNER)
                    
                elif tile_type == 17:
                    draw_tile(ix, iy, TyleType.WALL_CORRIDER_H_CENTER)

                elif tile_type == 18:
                    draw_tile(ix, iy, TyleType.WALL_CORRIDER_V_CENTER)

                elif tile_type == 19:
                    draw_tile(ix, iy, TyleType.WALL_CORRIDER_LEFT)
                    
                elif tile_type == 20:
                    draw_tile(ix, iy, TyleType.WALL_CORRIDER_RIGHT)
                    
                elif tile_type == 21:
                    draw_tile(ix, iy, TyleType.WALL_CORRIDER_UP)
                elif tile_type == 22:
                    draw_tile(ix, iy, TyleType.WALL_CORRIDER_DOWN)
                    

                else:
                    pass


        # スモールマップの描画
        for i in range(self.map.w):
            for j in range(self.map.h):
                x = i
                y = j + 15
                if self.map.data[j, i] == 0:
                    pyxel.rect(x, y, 1, 1, 5)
                if self.map.data[j, i] == -1:
                    pyxel.rect(x, y, 1, 1, 8)

        pyxel.rect(self.ego.x, self.ego.y + 15, 1, 1, 11)
        pyxel.rectb(self.ego.x-8, self.ego.y-8 + 15, 16, 16, 8)
        
        cx = self.ego.x
        cy = self.ego.y
        print(self.map.data[cy-8:cy+9, cx-8:cx+9])
        
                
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

App()