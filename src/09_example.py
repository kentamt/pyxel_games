import copy
import random
from enum import Enum
from collections import deque

import numpy as np
import pyxel

from maze import Maze
from tile import *

class State(Enum):
  START = 1 # 開始演出
  MAIN = 2 # メイン
  GOAL = 3 # ゴール
  QUESTION = 4
  CHANGE = 5 # マップ切り替え
  END = 6 # 終了

class Turn(Enum):
    EGO = 1
    ENEMY = 2
    WAIT = 3

class Direction(Enum):
    UP = 1,
    UPRIGHT =2,
    RIGHT=3,
    DOWNRIHGHT=4,
    DOWN=5,
    DOWNLEFT=6,
    LEFT=7,
    UPLEFT=8

def draw_tile(x, y, tile_type):
    txy = get_tile_loc(tile_type)
    pyxel.blt(x, y, 0, txy[0], txy[1], 16, 16)

    
class Man:
    def __init__(self, _x, _y, _c, _d=Direction.UP, _hp=10):
        super().__init__()
        self.x = _x
        self.y = _y
        self.c = _c # 色
        self.d = _d # 描画用の方向
        self.moved = False
        self.attacked = False

        self.hitpoints = _hp


    def update(self, _x, _y):
        self.x = _x
        self.y = _y

class App:
    def __init__(self):

        # ゲームの名前
        self.name = "07_example"
        
        # ゲームの状態
        self.state = State.START
        self.turn = Turn.EGO

        # ゲームの設定
        pyxel.init(256, 256, caption=self.name, scale=2, fps=10)
        pyxel.load("my_resource.pyxres")
        
        # SE
        pyxel.sound(0).set("A3", "N", "3", "F", 20) # 剣を振る
        pyxel.sound(1).set("F2RRF2RRF2RRF2RR", "N", "6", "F", 10) # 階段
        pyxel.sound(2).set("C1", "N", "6", "F", 15) # 攻撃があたる
        # pyxel.sound(3).set("D", "N", "6", "F", 30) # 敵が死ぬ
        pyxel.sound(3).set("A3", "T", "3", "F", 20) # 敵の攻撃
        
        # 画面切り替え時間
        self.change_view_timer = 13# [frames] 1secくらいまつ    
        self.change_turn_timer = 6# [frames]    
        
        # フロア
        self.floor = 0 # [F]

        # タイミング
        self.tick = 0 

        # 地図
        self.map = Maze(48, 48)
        self.num_col_rooms = 2
        self.num_row_rooms = 2
        self.corrider_width = 1
        self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, 
                                    num_row_rooms=self.num_row_rooms,
                                    corrider_width=self.corrider_width,
                                    max_room_size_ratio=0.8,
                                    min_room_size_ratio=0.2
        )
        self.map.set_goal()

        # 見たことある場所
        self.is_seen = np.zeros((self.map.h, self.map.w), dtype=bool)
        
        # 自キャラの初期化, map.dataの16倍の位置
        yx = self.map.get_free_space(num=1)
        self.ego = Man(yx[1], yx[0], 11, Direction.UP) 

        # 敵キャラの配置
        yx = self.map.get_free_space(num=1)
        self.enemy = Man(yx[1], yx[0], 14, Direction.UP) 
        self.route = deque()

        # 自分中心で描画可能な範囲だけを取り出しち地図と、その左右上下のマージン
        self.local_data, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)
                
        # 画面上での自キャラの位置
        # 基本は画面中央で、画面端のときだけ視覚中央からはずれる
        self.ego_vx = self.margins[0] * 16 
        self.ego_vy = self.margins[2] * 16
        self.ene_vx = self.ego_vx + (self.enemy.x - self.ego.x) * 16
        self.ene_vy = self.ego_vy + (self.enemy.y - self.ego.y) * 16

        
        # 実行        
        pyxel.run(self.update, self.draw)

    def create_tile_map(self):        
        """
        local_mapに大してtile_infoを作成する        
        """

        self.tile_info_map = copy.deepcopy(self.local_data)*0
        local_data = copy.deepcopy(self.local_data)
        w = self.tile_info_map.shape[1]
        h = self.tile_info_map.shape[0]
    
        # goalを見つける
        goal_yx = list(zip(*np.where(local_data==-1)))
        if len(goal_yx) == 1:
            yx = goal_yx[0]
            self.tile_info_map[yx[0], yx[1]] = 23 # GOAL

            # Goalを消した地図の用意
            local_data[yx[0], yx[1]] = 0

        # y方向に微分して境目を見つける
        for iy in range(h-1):
            line = local_data[iy+1, :] - local_data[iy, :]
            # 壁から通路なら-1, 通路から壁なら1
            for ix, e in enumerate(line):
                if e == -1:                    
                    self.tile_info_map[iy, ix] = 1
                if e == 1:                    
                    self.tile_info_map[iy+1, ix] = 2

        # x方向に微分して境目を見つける
        for ix in range(w-1):
            line = local_data[:, ix+1] - local_data[:, ix]
            # 壁から通路なら-1, 通路から壁なら1
            for iy, e in enumerate(line):
                if e == -1:                    
                    self.tile_info_map[iy, ix] = 3
                if e == 1:                    
                    self.tile_info_map[iy, ix+1] = 4
        
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

        for src, dst in zip(srcs, dsts):
            tile_info_map_copy = copy.deepcopy(self.tile_info_map)
            for iy in range(h-1):
                for ix in range(w-1):
                    diff = self.tile_info_map[iy:iy+2, ix:ix+2] - src                
                    if np.all(diff == 0):
                        tile_info_map_copy[iy:iy+2, ix:ix+2] = dst
            self.tile_info_map = copy.deepcopy(tile_info_map_copy)



        
    def update(self):
        """
        状態を変更する関数。毎フレーム呼ばれる。
        敵の行動は自分が行動した後に実行される
        """

        if self.state == State.START: # 開始演出            
            if (pyxel.btn(pyxel.KEY_S)):
                self.state = State.MAIN

            if (pyxel.btn(pyxel.KEY_DOWN)):
                self.use_random_map = False

            if (pyxel.btn(pyxel.KEY_UP)):
                self.use_random_map = True
        
        elif self.state == State.MAIN:                

            if self.turn == Turn.EGO:
                # 自キャラの操作うけつけ
                # 攻撃するか移動するか(道具をつかうかなど。)
                if not self.ego.moved:
                    if (pyxel.btn(pyxel.KEY_W)):
                        self.ego.moved = True
                        self.ego.attacked = True
                        attacked_cell = [self.ego.x, self.ego.y]
                        if self.ego.d == Direction.UP:
                            dx = 0
                            dy = -1
                        elif self.ego.d == Direction.RIGHT:
                            dx = 1
                            dy = 0
                        elif self.ego.d == Direction.DOWN:
                            dx = 0
                            dy = 1
                        elif self.ego.d == Direction.LEFT:
                            dx = -1
                            dy = 0
                        attacked_cell[0] += dx
                        attacked_cell[1] += dy
                
                if not self.ego.moved:
                    self.move_target(self.ego)

                # 攻撃の結果を更新
                if self.ego.attacked:
                    if self.enemy.x == attacked_cell[0] and self.enemy.y == attacked_cell[1]:
                        # 敵の体力を減らす
                        self.enemy.hitpoints -= 3    
                        pyxel.play(3, [2]) # 攻撃があたる音
                        
                if self.ego.moved:
                    self.turn = Turn.WAIT                        

            if self.turn == Turn.ENEMY:

                # 敵キャラの行動
                if self.enemy.hitpoints > 0:
                    if self.ego.moved == True:
                        self.act_enemy()                        
                        
                    if self.enemy.attacked:
                        pyxel.play(3, [3]) # 攻撃があたる音
                        self.ego.hitpoints -= 1
                        self.enemy.attacked = False
                        
                self.turn = Turn.EGO

            if self.turn == Turn.WAIT:
                self.change_turn_timer -= 1
                if self.change_turn_timer == 0:
                    self.turn = Turn.ENEMY

            # 画面内に表示される分だけのローカル地図
            self.local_data, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)
                    
            # 探索済みのフラグ更新
            cx = int(self.ego.x)
            cy = int(self.ego.y)
            lsmx, rsmx, usmy, dsmy = self.margins
            for i in range(self.map.w):
                for j in range(self.map.h):                
                    if cx - lsmx < i < cx + rsmx and cy - usmy < j < cy + dsmy:
                        self.is_seen[j, i] = True

            # 描画用時計        
            if pyxel.frame_count%5 == 0:
                self.tick += 1
      
            # ゴール判定
            if self.map.data[cy, cx] == -1:
                self.state = State.QUESTION


            # updateの最後に自キャラの行動フラグをクリア
            self.ego.moved = False

            

        elif self.state == State.QUESTION:
            if (pyxel.btn(pyxel.KEY_Y)):                    
                self.state = State.CHANGE
                pyxel.play(1, [1]) # 階段をおりる音
            elif (pyxel.btn(pyxel.KEY_N)):                    
                self.state = State.MAIN
      
        elif self.state == State.CHANGE:

            # 急に画面が切り替わらないように少しまつ
            if self.change_view_timer > 0:
                self.change_view_timer -= 1
                return
            
            self.change_view_timer = 13 # 初期化

            self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, 
                                    num_row_rooms=self.num_row_rooms,
                                    corrider_width=self.corrider_width,
                                    max_room_size_ratio=0.8,
                                    min_room_size_ratio=0.2
            )
            
            self.map.set_goal()

            # 見たことある場所
            self.is_seen = np.zeros((self.map.h, self.map.w), dtype=bool)
            
            # 自キャラの初期化, map.dataの16倍の位置
            yx = self.map.get_free_space(num=1)
            self.ego = Man(yx[1], yx[0], 11, Direction.UP) 

            # 敵キャラ
            yx = self.map.get_free_space(num=1)
            self.enemy = Man(yx[1], yx[0], 14, Direction.UP) 
            self.route = deque()

            # 自分両中心で描画可能な範囲だけを取り出しち地図と、その左右上下のマージン
            self.local_data, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)

            self.floor += 1

            self.state = State.MAIN
      
        elif self.state == State.END:
            pass
            
      
    def draw(self):
        """
        描画に関することのみここでは書く。状態は変更しないこと。
        """
        
        if self.state == State.START:
            pyxel.cls(0)
            pyxel.text(0, 0, self.name, 7)
            pyxel.text(20, 20, "LOW RISK WARRIOR TAKACHI'S MISTERY DUNGEON",  7)      
            pyxel.text(40, 74, "PRESS S TO START",  7)      

        elif self.state == State.MAIN:
        
            # キャンバスのクリア
            pyxel.cls(0)        
            
            # ローカルマップのタイル情報作成
            _, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)
            self.create_tile_map()

            # 地図の描画
            self.draw_map()
            
            # 自キャラの描画
            self.draw_ego()

            # 敵キャラの描画
            if self.enemy.hitpoints > 0:
                self.draw_enemy()
            
            # スモールマップの描画
            self.draw_small_map()            

            # ゲームタイトルの描画            
            pyxel.text(5, 5, self.name,  7) 
            
            # フロア
            pyxel.text(50, 5, f"{self.floor}F",  7) 
            
            # 体力
            pyxel.text(70, 5, f"HP: {self.ego.hitpoints}/10",  7) 

        elif self.state == State.QUESTION:

            pyxel.cls(0)
            
            _, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)
            self.create_tile_map()

            # 地図の描画
            self.draw_map()
            
            # 自キャラの描画
            self.draw_ego()

            # 敵キャラの描画
            self.draw_enemy()

            # スモールマップの描画
            self.draw_small_map()            

            pyxel.rect(self.ego_vx-12, self.ego_vy-17, 50, 13, 13)
            pyxel.text(self.ego_vx-10, self.ego_vy-15, "ORIRU?[Y/N]", 7)

            # ゲームタイトルの描画            
            pyxel.text(5, 5, self.name,  7) 
            pyxel.text(50, 5, f"{self.floor}F",  7) 

        elif self.state == State.CHANGE:
            pyxel.cls(0)
            pyxel.text(5, 5, self.name,  7) 
            pyxel.text(50, 5, f"{self.floor}F",  7) 

        elif self.state == State.END:
            pyxel.cls(0)
            pyxel.text(0, 0, self.name, 7)
            pyxel.text(5, int(pyxel.height/2.0), "GAME OVER",  7 )            

    def draw_small_map(self):

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
        cx = int(self.ego.x)
        cy = int(self.ego.y)
        pyxel.rect (cx + smap_margin, cy + smap_margin, 1,  1, 11)
        pyxel.rectb(cx - lsmx + smap_margin, cy - usmy + 15, 16, 16, 8)


    def draw_enemy(self):
        self.ene_vx = self.ego_vx + (self.enemy.x - self.ego.x) * 16
        self.ene_vy = self.ego_vy + (self.enemy.y - self.ego.y) * 16

        # localでの自キャラとの相対位置計算
        # pyxel.rect(self.ene_vx, self.ene_vy, 16, 16, 8) 
        if self.tick % 3 == 0:
            pyxel.blt(self.ene_vx, self.ene_vy, 0, 96, 32, 16, 16, 0)
        else:
            pyxel.blt(self.ene_vx, self.ene_vy, 0, 96, 48, 16, 16, 0)

        # HPの表示
        pyxel.text(self.ene_vx, self.ene_vy-5, f"{self.enemy.hitpoints}/10", 7)


    def draw_ego(self):

        # 基本は画面中央で、画面端のときだけ視覚中央からはずれる            
        self.ego_vx = self.margins[0] * 16 
        self.ego_vy = self.margins[2] * 16

        # pyxel.rect(self.ego_vx, self.ego_vy, 16, 16, 11)  
        self.draw_vehicle(self.ego_vx, self.ego_vy)        

        # 攻撃の描画
        x = y = None
        if self.ego.attacked:
            if self.ego.d == Direction.UP:
                x = self.ego_vx 
                y = self.ego_vy-16
                s = 112
                w = 16
                h = -16
                
                # pyxel.circb(self.ego_vx+8, self.ego_vy+8-16, 8, 7)  
            elif self.ego.d == Direction.RIGHT:
                x = self.ego_vx+16
                y = self.ego_vy
                s = 128
                w = 16
                h = 16

                # pyxel.circb(self.ego_vx+8+16, self.ego_vy+8, 8, 7)  
            elif self.ego.d == Direction.DOWN:
                x = self.ego_vx 
                y = self.ego_vy+16
                s = 112
                w = 16
                h = 16

                # pyxel.blt(self.ego_vx, self.ego_vy+16, 0, 112, 48, 16, 16)
                # pyxel.circb(self.ego_vx+8, self.ego_vy+8+16, 8, 7)  
            elif self.ego.d == Direction.LEFT:
                x = self.ego_vx-16
                y = self.ego_vy
                s = 128
                w = -16
                h = 16

                # pyxel.circb(self.ego_vx+8-16, self.ego_vy+8, 8, 7)  
            if x is not None and y is not None:
                pyxel.blt(x, y, 0, s, 48, w, h, 0)
                pyxel.play(0, [0])                
                self.ego.attacked = False


    def draw_map(self):
        # 地図の描画
        for i in range(16):
            for j in range(16):
                x = i * 16
                y = j * 16
                
                tile_type = self.tile_info_map[j, i]
                if tile_type == 1:
                    draw_tile(x, y, TyleType.WALL_IN_UP)

                elif tile_type == 2:
                    draw_tile(x, y, TyleType.WALL_IN_DOWN)
                    
                elif tile_type == 3:
                    draw_tile(x, y, TyleType.WALL_IN_LEFT)

                elif tile_type == 4:
                    draw_tile(x, y, TyleType.WALL_IN_RIGHT)
                
                elif tile_type == 5:
                    draw_tile(x, y, TyleType.WALL_IN_UL_CORNER)

                elif tile_type == 6:
                    draw_tile(x, y, TyleType.WALL_IN_DL_CORNER)

                elif tile_type == 7:
                    draw_tile(x, y, TyleType.WALL_IN_UR_CORNER)

                elif tile_type == 8:
                    draw_tile(x, y, TyleType.WALL_IN_DR_CORNER)
                # -----
                elif tile_type == 9:
                    draw_tile(x, y, TyleType.WALL_OUT_UP)

                elif tile_type == 10:
                    draw_tile(x, y, TyleType.WALL_OUT_DOWN)

                elif tile_type == 11:
                    draw_tile(x, y, TyleType.WALL_OUT_LEFT)

                elif tile_type == 12:
                    draw_tile(x, y, TyleType.WALL_OUT_RIGHT)

                elif tile_type == 13:
                    draw_tile(x, y, TyleType.WALL_OUT_UL_CORNER)

                elif tile_type == 14:
                    draw_tile(x, y, TyleType.WALL_OUT_DL_CORNER)

                elif tile_type == 15:
                    draw_tile(x, y, TyleType.WALL_OUT_UR_CORNER)

                elif tile_type == 16:
                    draw_tile(x, y, TyleType.WALL_OUT_DR_CORNER)
                    
                # elif tile_type == 17:
                #     draw_tile(x, y, TyleType.WALL_CORRIDER_H_CENTER)

                # elif tile_type == 18:
                #     draw_tile(x, y, TyleType.WALL_CORRIDER_V_CENTER)

                # elif tile_type == 19:
                #     draw_tile(x, y, TyleType.WALL_CORRIDER_LEFT)
                    
                # elif tile_type == 20:
                #     draw_tile(x, y, TyleType.WALL_CORRIDER_RIGHT)
                    
                # elif tile_type == 21:
                #     draw_tile(x, y, TyleType.WALL_CORRIDER_UP)
                # elif tile_type == 22:
                #     draw_tile(x, y, TyleType.WALL_CORRIDER_DOWN)
                    
                elif tile_type == 23:
                    draw_tile(x, y, TyleType.GOAL)
                
                else:
                    pass


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

        if self.tick %2 == 0:
            pyxel.blt(x, y, 0, 96, 64, 16, 16)
        else:
            pyxel.blt(x, y, 0, 96, 80, 16, 16)
        # pyxel.blt(x, y, 0, bltx, blty, bltw, blth)

    def act_enemy(self):
        
        ey = self.enemy.y
        ex = self.enemy.x
        cy = self.ego.y
        cx = self.ego.x
        
        # 最短経路の更新
        if not pyxel.frame_count % 1:
                
            self.route = self.map.search_shortest_path_dws((ey, ex), (cy, cx))
            self.route = deque(self.route)
            self.route.popleft() # 一つ目はstartなので捨てる
            # self.route.pop() # 最後は自分キャラ
            

        if len(self.route) > 0:
            next_cell = self.route.popleft()

            # 重なることはしない
            # もし隣接していれば敵の攻撃
            if next_cell[1] == self.ego.x and next_cell[0] == self.ego.y:
                self.enemy.attacked = True
            else: 
                self.enemy.update(int(next_cell[1]), int(next_cell[0]))

        else:
            pass


    def move_target(self, target):
        """
        入力されたキーと異なる方向をむいていた場合、
        まず向きだけをかえる
        """
        
        
        mx = target.x
        my = target.y            
        ms = 1

        if pyxel.btn(pyxel.KEY_LEFT):            
            if self.map.data[int(my), int(mx-ms)] != 1:
                if self.ego.d == Direction.LEFT:
                    mx = mx - ms
                    target.moved = True
                else:
                    self.ego.d = Direction.LEFT
                
        if pyxel.btn(pyxel.KEY_RIGHT):            
            if self.map.data[int(my), int(mx+ms)] != 1:
                if self.ego.d == Direction.RIGHT:
                    mx = mx + ms
                    target.moved = True
                else:
                    self.ego.d = Direction.RIGHT
        if pyxel.btn(pyxel.KEY_UP):
            if self.map.data[int(my-ms), int(mx)] != 1:
                if self.ego.d == Direction.UP:        
                    my = my - ms
                    target.moved = True
                else:
                    self.ego.d = Direction.UP
                            
        if pyxel.btn(pyxel.KEY_DOWN):            
            if self.map.data[int(my+ms), int(mx)] != 1:
                if self.ego.d == Direction.DOWN:
                    my = my + ms
                    target.moved = True
                else:
                    self.ego.d = Direction.DOWN
        
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
                
        target.update(mx, my)

App()