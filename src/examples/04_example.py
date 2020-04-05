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


class App:
    def __init__(self):

        # ゲームの設定
        self.name = "04_example"
        pyxel.init(256, 256, caption=self.name, scale=4, fps=15)
        pyxel.load("my_resource.pyxres")

        scale = 256/16

        self.map = City(16, 16) # int(pyxel.width), int(pyxel.height/8))
        self.map.data = np.ones((self.map.h, self.map.w), dtype=np.int)
        self.map.data[2:-2, 2:-2] = 0
        self.map.data[6:-6, 6:-6] = 1
        
        print(self.map.data)
        
        

        # 実行        
        pyxel.run(self.update, self.draw)

    def update(self):
        """
        状態を変更する関数。毎フレーム呼ばれる。
        """
        pass 
    
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
            
            WALL_ALL = 17,
            FREE_ALL = 18

        
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
            elif tile_type == TyleType.WALL_ALL:
                ret = (16, 96)
            elif tile_type == TyleType.FREE_ALL:
                ret = (16, 48)
            else:
                ret = None    
                
            return ret

        def draw_tile(x, y, tile_type):
            txy = get_tile_loc(tile_type)
            pyxel.blt(x, y, 0, txy[0], txy[1], 16, 16)

        # for i in range(3):            
        #     draw_tile(32+i*16, 28, TyleType.WALL_IN_UP)

        """
        11
        00 = IN_UP
        
        00
        11 = IN_DOWN
        
        10
        10 = IN_LEFT
        
        01
        01 = IN_RIGHT
        
        11
        10 = IN_UL_CORNER
        
        11
        01 = IN_UR_CORNER
        
        10
        11 = IN_DL_CORNER
        
        01
        11 = IN_DR_CORNER
        """

        tile_info_data = np.zeros((self.map.h, self.map.w), dtype=np.int)

        def find_tile_type():
            
            patterns = [
                np.array([[1, 1],[0, 0]], dtype=np.int), # WALL_IN_UP = 1,
                np.array([[0, 0],[1, 1]], dtype=np.int), # WALL_IN_DOWN = 2,
                np.array([[1, 0],[1, 0]], dtype=np.int), # WALL_IN_LEFT = 3,
                np.array([[0, 1],[0, 1]], dtype=np.int), # WALL_IN_RIGHT = 4,
                np.array([[1, 1],[1, 0]], dtype=np.int), # WALL_IN_UL_CORNER = 5,
                np.array([[1, 0],[1, 1]], dtype=np.int), # WALL_IN_DL_CORNER = 6,
                np.array([[1, 1],[0, 1]], dtype=np.int), # WALL_IN_UR_CORNER = 7,
                np.array([[0, 1],[1, 1]], dtype=np.int), # WALL_IN_DR_CORNER = 8,                
                
                # np.array([[1, 1],[0, 0]], dtype=np.int), # WALL_OUT_UP = 9,
                # np.array([[0, 0],[1, 1]], dtype=np.int), # WALL_OUT_DOWN = 10,
                # np.array([[1, 0],[1, 0]], dtype=np.int), # WALL_OUT_LEFT = 11,
                # np.array([[0, 1],[0, 1]], dtype=np.int), # WALL_OUT_RIGHT = 12,
                np.array([[0, 0],[0, 1]], dtype=np.int), # WALL_OUT_UL_CORNER = 13,
                np.array([[0, 1],[0, 0]], dtype=np.int), # WALL_OUT_DL_CORNER = 14,
                np.array([[0, 0],[1, 0]], dtype=np.int), # WALL_OUT_UR_CORNER = 15,
                np.array([[1, 0],[0, 0]], dtype=np.int), # WALL_OUT_DR_CORNER = 16,
                # np.array([[1, 1],[1, 1]], dtype=np.int), # WALL_ALL = 17,
                # np.array([[0, 0],[0, 0]], dtype=np.int), # FREE_ALL = 18,
                
            ]
            tile_types = [1,2,3,4,5,6,7,8,13,14,15,16] # 17,18]
                        
            for ttype, pattern in zip(tile_types, patterns):
                for iy in range(self.map.h):
                    for ix in range(self.map.w):
                        diff = self.map.data[iy:iy+2, ix:ix+2] - pattern
                        if np.all(diff==0):
                            
                            if ttype == 2 or ttype == 6 or ttype == 8 or ttype == 14 or ttype == 16:
                                tile_info_data[iy+1, ix] = ttype # TyleType.WALL_IN_UL_CORNER
                            else:
                                tile_info_data[iy, ix] = ttype # TyleType.WALL_IN_UL_CORNER
        find_tile_type()
        
            

        for ix in range(pyxel.width)[::16]:
            for iy in range(pyxel.height)[::16]:                    
                
                if tile_info_data[int(iy/16), int(ix/16)] == 1:
                    draw_tile(ix, iy, TyleType.WALL_IN_UP)

                elif tile_info_data[int(iy/16), int(ix/16)] == 2:
                    draw_tile(ix, iy, TyleType.WALL_IN_DOWN)

                elif tile_info_data[int(iy/16), int(ix/16)] == 3:
                    draw_tile(ix, iy, TyleType.WALL_IN_LEFT)

                elif tile_info_data[int(iy/16), int(ix/16)] == 4:
                    draw_tile(ix, iy, TyleType.WALL_IN_RIGHT)
                
                elif tile_info_data[int(iy/16), int(ix/16)] == 5:
                    draw_tile(ix, iy, TyleType.WALL_IN_UL_CORNER)

                elif tile_info_data [int(iy/16), int(ix/16)] == 6:
                    draw_tile(ix, iy, TyleType.WALL_IN_DL_CORNER)

                elif tile_info_data[int(iy/16), int(ix/16)] == 7:
                    draw_tile(ix, iy, TyleType.WALL_IN_UR_CORNER)

                elif tile_info_data[int(iy/16), int(ix/16)] == 8:
                    draw_tile(ix, iy, TyleType.WALL_IN_DR_CORNER)
                # -----
                elif tile_info_data [int(iy/16), int(ix/16)] == 9:
                    draw_tile(ix, iy, TyleType.WALL_OUT_UP)

                elif tile_info_data[int(iy/16), int(ix/16)] == 10:
                    draw_tile(ix, iy, TyleType.WALL_OUT_DOWN)

                elif tile_info_data[int(iy/16), int(ix/16)] == 11:
                    draw_tile(ix, iy, TyleType.WALL_OUT_LEFT)

                elif tile_info_data [int(iy/16), int(ix/16)] == 12:
                    draw_tile(ix, iy, TyleType.WALL_OUT_RIGHT)

                elif tile_info_data[int(iy/16), int(ix/16)] == 13:
                    draw_tile(ix, iy, TyleType.WALL_OUT_UL_CORNER)

                elif tile_info_data[int(iy/16), int(ix/16)] == 14:
                    draw_tile(ix, iy, TyleType.WALL_OUT_DL_CORNER)

                elif tile_info_data [int(iy/16), int(ix/16)] == 15:
                    draw_tile(ix, iy, TyleType.WALL_OUT_UR_CORNER)

                elif tile_info_data[int(iy/16), int(ix/16)] == 16:
                    draw_tile(ix, iy, TyleType.WALL_OUT_DR_CORNER)
                elif tile_info_data[int(iy/16), int(ix/16)] == 17:
                    pass # draw_tile(ix, iy, TyleType.WALL_ALL)
                elif tile_info_data[int(iy/16), int(ix/16)] == 18:
                    pass # draw_tile(ix, iy, TyleType.FREE_ALL)
                else:
                    pass
                    # pyxel.rect(ix, iy, 4, 4, 11)               
        # print(tile_info_data)
        # pyxel.blt(32, 28, 0, 16, 32, 16, 16)
        # pyxel.blt(32+16, 28, 0, 16, 32, 16, 16)
        # pyxel.blt(32+16+16, 28, 0, 16, 32, 16, 16)
        # pyxel.blt(48, 48, 0, 0, 0, 8, 8)
        
App()