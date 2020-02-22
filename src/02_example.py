from enum import Enum
import random
import numpy as np
import pyxel

class State(Enum):
  START = 1 # 開始演出
  MAIN = 2 # メイン
  CHANGE = 3 # マップ切り替え

class Vehicle:
    def __init__(self, _x, _y, _c):
        super().__init__()
        self.x = _x
        self.y = _y
        self.c = _c

    def update(self, _x, _y):
        self.x = _x
        self.y = _y

class Map:
    def __init__(self, w, h):
        super().__init__()
        self.w = w
        self.h = h
        self.data = np.zeros((h, w), np.int)
        self.goal_x = 0 
        self.goal_y = 0 
        
    def create_map_stick_down(self):
        
        # 柱の設置
        for i in range(1, self.w)[::2]:
            for j in range(1, self.h)[::2]:
                self.data[j, i] = 1 # occupied
                
        # 柱を倒す
        for i in range(1, self.w)[::2]:
            for j in range(1, self.h)[::2]:
                num = np.random.randint(3) # [r,u,l,d] = [0, 1, 2, 3]
                if num == 0:
                    self.data[j, i+1] = 1
                elif num == 1:
                    self.data[j-1, i] = 1
                elif num ==2:
                    self.data[j, i-1] = 1
                elif num==3:
                    self.data[j+1, i] = 1
                    
    def create_map_dungeon(self, num_row_rooms=2, num_col_rooms=3):
        """
        TODO: 部屋を作らなば場合も実する。その場合、全部がつながっているかをチェックする関数をつくる
        """

        self.data = np.ones(self.data.shape, np.int)
        
        # 適当に配列を分割する
        # NOTE: 各値は偶数でないと道がつながらない。
        rand_col_idx = [ int(e)&~1 for e in np.linspace(0, self.w-1, num=int(num_col_rooms)+1)]
        rand_row_idx = [ int(e)&~1 for e in np.linspace(0, self.h-1, num=int(num_row_rooms)+1).astype(np.int)]

        # 各部屋の中心, 大きさ
        num_col_rooms = len(rand_col_idx) - 1
        num_row_rooms = len(rand_row_idx) - 1
        room_max_size_x = np.zeros((num_row_rooms, num_col_rooms),np.int)
        room_max_size_y = np.zeros((num_row_rooms, num_col_rooms),np.int)
        room_center_x = np.zeros((num_row_rooms, num_col_rooms), np.int)
        room_center_y = np.zeros((num_row_rooms, num_col_rooms),np.int)

        for ic in range(len(rand_col_idx)-1):
            for ir in range(len(rand_row_idx)-1):
                x = int(0.5 * (rand_col_idx[ic] + rand_col_idx[ic+1]))
                size_x = rand_col_idx[ic+1] - rand_col_idx[ic]
                y = int(0.5 * (rand_row_idx[ir] + rand_row_idx[ir+1]))
                size_y = rand_row_idx[ir+1] - rand_row_idx[ir]

                room_center_y[ir, ic] = int(y)
                room_max_size_y[ir, ic] = int(size_y)
                room_center_x[ir, ic] = int(x)
                room_max_size_x[ir, ic] = int(size_x)
        
        # 各部屋の大きさを決める
        room_size_x = np.zeros((num_row_rooms, num_col_rooms))
        room_size_y = np.zeros((num_row_rooms, num_col_rooms))
        for iy in range(num_row_rooms):
            for ix in range(num_col_rooms):            
                rmsx = room_max_size_x[iy,ix]
                rmsy = room_max_size_y[iy,ix]
                
                rsx = np.random.randint(int(rmsx*0.3), int(rmsx*0.9))
                rsy = np.random.randint(int(rmsy*0.3), int(rmsy*0.9))

                room_size_x[iy, ix] = rsx
                room_size_y[iy, ix] = rsy
    
        # 各部屋を塗りつぶす + 通路をつくる
        for iy in range(num_row_rooms):
            for ix in range(num_col_rooms):            
                w = room_size_x[iy, ix]
                h = room_size_y[iy, ix]
                cx = room_center_x[iy, ix]
                cy = room_center_y[iy, ix]                
                rmsx = room_max_size_x[iy,ix]
                rmsy = room_max_size_y[iy,ix]
                self.data[cy-int(h/2.0):cy+int(h/2.0), cx-int(w/2.0):cx+int(w/2.0)] = 0
        
                # 各部かから通路への垂線を上下左右４本分生成
                exit_x_up = np.random.randint(cx-int(w/2.0)+1, cx+int(w/2.0)-1)
                exit_x_down = np.random.randint(cx-int(w/2.0)+1, cx+int(w/2.0)-1)
                exit_left = np.random.randint(cy-int(h/2.0)+1, cy+int(h/2.0)-1)
                exit_right = np.random.randint(cy-int(h/2.0)+1, cy+int(h/2.0)-1)
                
                # cxからcx+rmsx/2.0, cx-rmsx/2.0だけ線を引く
                # ただし, 端に触れていへ部屋は通路をつくらない
                
                rx = int(rmsx/2.0)
                ry = int(rmsy/2.0)
                
                if iy == 0 and ix == 0:
                    # self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    # self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == num_row_rooms-1 and ix == num_col_rooms-1:
                    self.data[exit_left, cx-rx:cx] = 0
                    # self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    # self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == 0 and ix == num_col_rooms-1:
                    self.data[exit_left, cx-rx:cx] = 0
                    # self.data[exit_right, cx:cx+rx] = 0
                    # self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == num_row_rooms-1 and ix == 0:
                    # self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    # self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == num_row_rooms-1 and ix == 0:
                    # self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    # self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == 0:
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    # self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == num_row_rooms-1:
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    # self.data[cy:cy+ry, exit_x_down] = 0

                elif ix == 0:
                    # self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

                elif ix == num_col_rooms-1:
                    self.data[exit_left, cx-rx:cx] = 0
                    # self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0
                            
                else:                
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

        # 線をつなげる
        rand_col_idx = np.array(rand_col_idx)
        # print(rand_col_idx)
        for col_idx in rand_col_idx[1:-1]:
            print(col_idx)
            end_y_l = np.where(self.data[:, col_idx - 1]== 0 )
            end_y_r = np.where(self.data[:, col_idx + 1]== 0 )
            for idx in range(num_row_rooms):
                end_y = sorted([end_y_l[0][idx], end_y_r[0][idx]])
                self.data[end_y[0]:end_y[1]+1, col_idx] = 0                

        rand_row_idx = np.array(rand_row_idx)
        # print(rand_row_idx)
        for row_idx in rand_row_idx[1:-1]:
            end_x_u = np.where(self.data[row_idx - 1, :]== 0 )
            end_x_d = np.where(self.data[row_idx + 1, :]== 0 )
            for idx in range(num_col_rooms):
                end_x = sorted([end_x_u[0][idx], end_x_d[0][idx]])
                self.data[row_idx, end_x[0]:end_x[1]+1] = 0                

        # ゴールの初期をきめておく
        x = np.random.randint(self.w)
        y = np.random.randint(self.h)        
        while self.data[y, x] != 0:
            x = np.random.randint(self.w)
            y = np.random.randint(self.h)        
        self.goal_x = x
        self.goal_y = y

    def set_goal(self):
        # ゴールの設置 # TODO: 壁からは選ばないようにする
        self.data[self.goal_y, self.goal_x] = 0 # Reset Goal

        x = np.random.randint(self.w)
        y = np.random.randint(self.h)        
        while self.data[y, x] != 0:
            x = np.random.randint(self.w)
            y = np.random.randint(self.h)        

        self.data[y, x] = -1 # Goal
        self.goal_x = x
        self.goal_y = y
 

class App:
    def __init__(self):

        self.name = "02_example"
        
        self.state = State.START

        pyxel.init(48, 36, caption=self.name, scale=6, fps=15)
        pyxel.image(0).load(0, 0, "pyxel_logo_38x16.png") # opening
        
        # 地図の初期化
        self.map = Map(pyxel.width, pyxel.height)
        # self.map.create_map_stick_down()
        self.map.create_map_dungeon()
        self.map.set_goal()
        
        # キャラの初期化
        x = int(np.random.rand() * pyxel.width)
        y = int(np.random.rand() * pyxel.height)
        while self.map.data[y, x] != 0:
            x = int(np.random.rand() * pyxel.width)
            y = int(np.random.rand() * pyxel.height)            
        c = 11
        self.v = Vehicle(x, y, c)

        # 獲得アイテす数
        self.num_got_items = 0
        self.max_items = 3 # これだけ獲得したら次の画面へ

        
        # 実行        
        pyxel.run(self.update, self.draw)

    def update(self):
        
        if self.state == State.START: # 開始演出
            
            if (pyxel.btn(pyxel.KEY_S)):
                self.state = State.MAIN
                
        elif self.state == State.MAIN: # メイン
            
            self.move_target(self.v)
            
            # ゴールに到達したかどうかを判定
            if self.map.data[self.v.y, self.v.x] == -1:
                self.num_got_items += 1
                
                # 獲得アイテムが閾い異常のとき次のstageへ
                if self.num_got_items >= self.max_items:
                    self.state = State.CHANGE
                
                self.map.set_goal()
                
        elif self.state == State.CHANGE:
            if (pyxel.btn(pyxel.KEY_S)):
                self.state = State.MAIN
                
                self.num_got_items = 0
                self.max_items = 3 # これだけ獲得したら次の画面へ

                print("Init Map")
                self.map.create_map_dungeon()
                self.map.set_goal()



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
            pyxel.text(0, 0, "Start(s)", pyxel.frame_count % 16)
            pyxel.blt(30, 40, 0, 0, 0, 38, 16)
            
        elif self.state == State.MAIN:
            pyxel.cls(0)
            
            # 迷路を描画
            self.draw_map()    
            pyxel.rect(self.v.x, self.v.y, 1, 1, self.v.c)
            
        elif self.state == State.CHANGE:
            pyxel.cls(0)
            pyxel.text(0, 0, "Next map(s)", pyxel.frame_count % 16)
            pyxel.blt(30, 40, 0, 0, 0, 38, 16)
            
            

            
            
    def draw_map(self):
        # 迷路を描画
        for i in range(self.map.w):
            for j in range(self.map.h):
                if self.map.data[j, i] == 0:
                    pyxel.rect(i, j, 1, 1, 5)
                if self.map.data[j, i] == -1:
                    pyxel.rect(i, j, 1, 1, 8)
        
    
App()