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
    def __init__(self, _x, _y, _c, _d=Direction.UP, hitpoints=10, max_hitpoints=10):
        super().__init__()
        self.x = _x
        self.y = _y
        self.px = None
        self.py = None # 一回前の座標
        self.c = _c # 色
        self.d = _d # 描画用の方向
        self.moved = False
        self.attacked = False
        self.hitpoints = hitpoints
        self.max_hp = max_hitpoints
        self.alive = True
        self.vx = None 
        self.vy = None
        self.hunger = 100
        self.step_count = 0
        self.attack_motion_timer = 3  # [frames]
        self.lv = 1
        self.exp = 0

    def update(self, _x, _y):
        
        self.px = self.x
        self.py = self.y        
        self.x = _x
        self.y = _y
        
        
        if self.step_count % 10 == 0:
            self.step_count += 1
            self.hunger -= 1

    def kill(self):
        self.x = -255
        self.x = -255
        self.alive = False

class Enemy(Man):
    def __init__(self, _x, _y, _c, _d=Direction.UP, hitpoints=10, max_hitpoints=10, exp=1):
        super().__init__(_x, _y, _c, _d=_d, hitpoints=hitpoints, max_hitpoints=max_hitpoints)
        self.route = None
        self.exp = exp

    def set_route(self, _route):
        self.route = _route
    

class App:
    def __init__(self):

        # ゲームの名前
        self.name = "09_example"
        
        # ゲームの状態
        self.state = State.START
        self.turn = Turn.EGO

        # ゲームの設定
        palette=[0x000000, 0x1D2B53, 0x7E2553, 0x008751, 0xAB5236, 
                 0x4F473F, 0xC2C3C7, 0xFFF1E8, 0xFF004D, 0xFFA300, 
                 0xFFEC27, 0x00E436, 0x29ADFF, 0x63567C, 0xFF77A8, 0xDDAA88]
        pyxel.init(256, 256, caption=self.name, scale=2, fps=15, palette=palette)
        pyxel.load("my_resource.pyxres")
        pyxel.playm(0, loop=True)        
        
        # SE
        pyxel.sound(10).set("A3", "N", "3", "F", 20) # 剣を振る
        pyxel.sound(11).set("F2RRF2RRF2RRF2RR", "N", "6", "F", 10) # 階段
        pyxel.sound(12).set("C1", "N", "6", "F", 15) # 攻撃があたる
        pyxel.sound(13).set("A3", "T", "3", "F", 20) # 敵の攻撃
        
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
        self.occupancy = np.zeros((self.map.h, self.map.w), dtype=bool) # キャラとかアイテムがある場所
        
        # 自キャラの初期化, map.dataの16倍の位置
        yx = self.map.get_free_space(num=1)
        self.ego = Man(yx[1], yx[0], 11, Direction.UP, hitpoints=50, max_hitpoints=50) 

        # 敵キャラの配置
        self.enemies = []
        for _ in range(4):
            yx = self.map.get_free_space(num=1)
            enemy = Enemy(yx[1], yx[0], 14, Direction.UP, hitpoints=9, max_hitpoints=9) 
            enemy.set_route(deque())
            self.enemies.append(enemy)

        # 自分中心で描画可能な範囲だけを取り出しち地図と、その左右上下のマージン
        self.local_data, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)
                
        # 画面上での自キャラの位置
        # 基本は画面中央で、画面端のときだけ視覚中央からはずれる
        # TODO: 直接メンバを触っているので変すること
        self.ego.vx = self.margins[0] * 16 
        self.ego.vy = self.margins[2] * 16
        for ene in self.enemies:
            ene.vx = self.ego.vx + (ene.x - self.ego.x) * 16
            ene.vy = self.ego.vy + (ene.y - self.ego.y) * 16

        
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
                    
                    for idx, enemy in enumerate(self.enemies):                        
                        if enemy.x == attacked_cell[0] and enemy.y == attacked_cell[1]:
                            # 敵の体力を減らす
                            enemy.hitpoints -= 8    
                            pyxel.play(3, [12]) # 攻撃があたる音
                            
                            # 敵の体力が0以下なら、殺す
                            if enemy.hitpoints <= 0:
                                self.occupancy[enemy.y, enemy.x] = False # 殺す前に解放
                                enemy.kill()# TODO: リストからの削除をすること
                                self.ego.exp += enemy.exp
                                del self.enemies[idx] # TODO: デストラクでOCCを解放したい
                                
                        
                        
                if self.ego.moved and self.ego.attacked:
                    self.turn = Turn.WAIT           
                elif self.ego.moved:
                    self.turn = Turn.ENEMY

            if self.turn == Turn.ENEMY:

                # 敵キャラの行動
                # TODO 順番にうごいてほしい                
                for enemy in self.enemies:
                    if enemy.hitpoints > 0:
                        self.act_enemy(enemy)                        
                        
                        if enemy.attacked:
                            pyxel.play(3, [12]) # 攻撃があたる音
                            self.ego.hitpoints -= 1
                            # enemy.attacked = False
                                                            
                self.turn = Turn.EGO

            if self.turn == Turn.WAIT:
                self.change_turn_timer -= 1
                if self.change_turn_timer == 0:
                    self.turn = Turn.ENEMY
                    self.change_turn_timer = 6

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
            if self.map.data[cy, cx] == -1 and self.map.data[self.ego.py, self.ego.px] != -1:
                self.state = State.QUESTION

            # 死亡判定
            if self.ego.hitpoints <= 0:
                self.state = State.END

            # updateの最後に自キャラの行動フラグをクリア
            self.ego.moved = False
            

        elif self.state == State.QUESTION:
            if (pyxel.btn(pyxel.KEY_Y)):                    
                self.state = State.CHANGE
                pyxel.play(3, [11]) # 階段をおりる音
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
            self.ego.update(yx[1], yx[0])
        
            # 敵キャラの配置
            self.enemies = []
            for _ in range(4):
                yx = self.map.get_free_space(num=1)
                enemy = Enemy(yx[1], yx[0], 14, Direction.UP) 
                enemy.set_route(deque())
                self.enemies.append(enemy)

            # 自分両中心で描画可能な範囲だけを取り出しち地図と、その左右上下のマージン
            self.local_data, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)

            self.ego.vx = self.margins[0] * 16 
            self.ego.vy = self.margins[2] * 16
            for ene in self.enemies:
                ene.vx = self.ego.vx + (ene.x - self.ego.x) * 16
                ene.vy = self.ego.vy + (ene.y - self.ego.y) * 16


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
            
            pyxel.bltm(30, 30, 0, 0, 0, 22, 25)
            
            pyxel.text(0, 0, self.name, 7)
            # pyxel.text(20, 20, "LOW RISK WARRIOR TAKACHI'S MISTERY DUNGEON",  7)      
            pyxel.text(80, 230, "PRESS S TO START",  7)      

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
            for enemy in self.enemies:
                if enemy.hitpoints > 0:
                    self.draw_enemy(enemy)


            # スモールマップの描画
            self.draw_small_map()            

            # ゲームタイトルの描画            
            pyxel.text(5, 5, self.name,  7) 
            
            # フロア
            pyxel.text(50, 5, f"{self.floor}F",  7) 
            
            # 体力
            pyxel.text(70, 5, f"HP: {self.ego.hitpoints}/{self.ego.max_hp}",  7) 
            
            # 経験値
            pyxel.text(120, 5, f"Exp: {self.ego.exp}",  7) 
            
            # 満腹度
            # pyxel.text(90, 5, f"Hunger: {self.ego.hitpoints}/{self.ego.max_hp}",  7) 

        elif self.state == State.QUESTION:

            pyxel.cls(0)
            
            _, self.margins = self.map.get_local_data(self.ego.y, self.ego.x)
            self.create_tile_map()

            # 地図の描画
            self.draw_map()
            
            # 自キャラの描画
            self.draw_ego()

            # 敵キャラの描画
            for enemy in self.enemies:
                self.draw_enemy(enemy)

            # スモールマップの描画
            self.draw_small_map()            

            pyxel.rect(self.ego.vx-12, self.ego.vy-17, 50, 13, 13)
            pyxel.text(self.ego.vx-10, self.ego.vy-15, "ORIRU?[Y/N]", 7)

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


    def draw_enemy(self, enemy):
        
        # localでの自キャラとの相対位置計算
        enemy.vx = self.ego.vx + (enemy.x - self.ego.x) * 16
        enemy.vy = self.ego.vy + (enemy.y - self.ego.y) * 16
        
        if enemy.attacked:
            
                    
            enemy.vy = self.ego.vy + (enemy.y - self.ego.y) * 16 - (enemy.y - self.ego.y) * 8
            enemy.vx = self.ego.vx + (enemy.x - self.ego.x) * 16 - (enemy.x - self.ego.x) * 8
            enemy.attack_motion_timer -= 1
            
            if enemy.attack_motion_timer == 0:
                enemy.attacked = False
                enemy.attack_motion_timer = 3 # [frames]
         
        x = enemy.vx
        y = enemy.vy   
        if enemy.d == Direction.UP:
            if self.tick %2 == 0:
                pyxel.blt(x, y, 0, 112, 96, 16, 16, 0)
            else:
                pyxel.blt(x, y, 0, 112, 112, 16, 16, 0)

        elif enemy.d == Direction.RIGHT:
            if self.tick %2 == 0:
                pyxel.blt(x, y, 0, 128, 96, -16, 16, 0)
            else:
                pyxel.blt(x, y, 0, 128, 112, -16, 16, 0)
            
        elif enemy.d == Direction.DOWN:
            if self.tick %2 == 0:
                pyxel.blt(x, y, 0, 96, 96, 16, 16, 0)
            else:
                pyxel.blt(x, y, 0, 96, 112, 16, 16, 0)

        elif enemy.d == Direction.LEFT:
            if self.tick %2 == 0:
                pyxel.blt(x, y, 0, 128, 96, 16, 16, 0)
            else:
                pyxel.blt(x, y, 0, 128, 112, 16, 16, 0)

        

        # HPの表示
        # pyxel.text(enemy.vx, enemy.vy-5, f"{enemy.hitpoints}/{enemy.max_hp}", 7)
        # バーでぼ描画
        pyxel.rect(enemy.vx, enemy.vy-5, int((enemy.hitpoints/enemy.max_hp)*16), 1, 8)

    def draw_ego(self):

        # 基本は画面中央で、画面端のときだけ視覚中央からはずれる            
        self.ego.vx = self.margins[0] * 16 
        self.ego.vy = self.margins[2] * 16

        ex = self.ego.vx
        ey = self.ego.vy
        
        # 攻撃の描画
        x = y = None
        if self.ego.attacked:
            if self.ego.d == Direction.UP:
                x = self.ego.vx 
                y = self.ego.vy-16
                ex = ex
                ey = ey - 4
                s = 112
                w = 16
                h = -16
                
            elif self.ego.d == Direction.RIGHT:
                x = self.ego.vx+16
                y = self.ego.vy
                ex = ex + 4
                ey = ey
                s = 128
                w = 16
                h = 16

            elif self.ego.d == Direction.DOWN:
                x = self.ego.vx 
                y = self.ego.vy+16
                ex = ex
                ey = ey + 4
                s = 112
                w = 16
                h = 16

            elif self.ego.d == Direction.LEFT:
                x = self.ego.vx-16
                y = self.ego.vy
                ex = ex - 4
                ey = ey
                s = 128
                w = -16
                h = 16

            if x is not None and y is not None:
                pyxel.blt(x, y, 0, s, 48, w, h, 0)
                self.ego.attack_motion_timer -= 1
                if self.ego.attack_motion_timer == 0:
                    pyxel.play(3, [10])                         
                    self.ego.attacked = False
                    self.ego.attack_motion_timer = 3 # [frames]

        self.draw_warrior(ex, ey)        


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


    def draw_warrior(self, x, y):
        bltx = 0
        blty = 0
        bltw = 16
        blth = 16

        if self.ego.d == Direction.UP:
            if self.tick %2 == 0:
                pyxel.blt(x, y, 0, 112, 64, 16, 16,0)
            else:
                pyxel.blt(x, y, 0, 112, 80, 16, 16,0)

        elif self.ego.d == Direction.RIGHT:
            if self.tick %2 == 0:
                pyxel.blt(x, y, 0, 128, 64, -16, 16,0)
            else:
                pyxel.blt(x, y, 0, 128, 80, -16, 16,0)
            
        elif self.ego.d == Direction.DOWN:
            if self.tick %2 == 0:
                pyxel.blt(x, y, 0, 96, 64, 16, 16,0)
            else:
                pyxel.blt(x, y, 0, 96, 80, 16, 16,0)

        elif self.ego.d == Direction.LEFT:
            if self.tick %2 == 0:
                pyxel.blt(x, y, 0, 128, 64, 16, 16,0)
            else:
                pyxel.blt(x, y, 0, 128, 80, 16, 16,0)


    def act_enemy(self, enemy):
        
        ex = enemy.x
        ey = enemy.y
        cy = self.ego.y
        cx = self.ego.x
        
        # 最短経路の更新
        if not pyxel.frame_count % 1:
                
            enemy.route = self.map.search_shortest_path_dws((ey, ex), (cy, cx))
            enemy.route = deque(enemy.route)
            enemy.route.popleft() # 一つ目はstartなので捨てる
            # enemy.route.pop() # 最後は自分キャラ
            

        if len(enemy.route) > 0:
            next_cell = enemy.route.popleft()
            x = next_cell[1]
            y = next_cell[0]
            
            # 敵味方アイテムと重なることはしない TODO: 現時点では敵同士はかさなる。判定はOCCUPIED_MAPをつくって管理すること
            # もし隣接していれば敵の攻撃
            if x == self.ego.x and y == self.ego.y:
                enemy.attacked = True
                
            # 占有されていなければ動く
            elif self.occupancy[y, x] == False:
                
                d = Direction.DOWN
                dx = x - enemy.x
                dy = y - enemy.y
                if dx == 0 and dy == -1:
                    d = Direction.UP
                elif dx == 1 and dy == 0:
                    d = Direction.RIGHT
                elif dx == 0 and dy == 1:
                    d = Direction.DOWN
                elif dx == -1 and dy == 0:
                    d = Direction.LEFT
                    
                enemy.d = d
                self.occupancy[enemy.y, enemy.x] = False # 占有
                enemy.update(x, y)
                self.occupancy[enemy.y, enemy.x] = True # 占有
                
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
        
        # if pyxel.btn(pyxel.KEY_LEFT) and pyxel.btn(pyxel.KEY_UP):
        #     if self.map.data[int(my-ms), int(mx-ms)] != 1:
        #         self.ego.d = Direction.UPLEFT
            
        # if pyxel.btn(pyxel.KEY_LEFT) and pyxel.btn(pyxel.KEY_DOWN):
        #     if self.map.data[int(my+ms), int(mx-ms)] != 1:
        #         self.ego.d = Direction.DOWNLEFT

        # if pyxel.btn(pyxel.KEY_RIGHT) and pyxel.btn(pyxel.KEY_UP):
        #     if self.map.data[int(my-ms), int(mx+ms)] != 1:
        #         self.ego.d = Direction.UPRIGHT

        # if pyxel.btn(pyxel.KEY_RIGHT) and pyxel.btn(pyxel.KEY_DOWN):
        #     if self.map.data[int(my+ms), int(mx+ms)] != 1:
        #         self.ego.d = Direction.DOWNRIHGHT
                
        # 敵とかさなるなら動かない
        # ひとつでもかさなて敵がみつかればそこで関数をぬける
        for enemy in self.enemies:
            if mx == enemy.x and my == enemy.y:        
                target.moved = False # クリア
                return
        
        self.occupancy[target.y, target.x] = False # 解放               
        target.update(mx, my)
        self.occupancy[target.y, target.x] = True # 占有

App()