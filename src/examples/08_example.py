import random
from enum import Enum
from collections import deque

import numpy as np
import pyxel

# from maze import Maze
from pydungeon import Dungeon

class State(Enum):
  START = 1 # 開始演出
  MAIN = 2 # メイン
  GOAL = 3 # ゴール
  CHANGE = 4 # マップ切り替え
  END = 5 # 終了

class Vehicle:
    def __init__(self, _x, _y, _c, _cidx):
        super().__init__()
        # 位置情報
        self.x = _x
        self.y = _y
        self.c = _c # 色
        self.cidx = _cidx # 番号
        
        self.dest = None # 目的地
        self.route = deque() # 走行経路
        self.route_permission = deque() # 走行経路の予約
        
        self.is_working = False # locationで作業待ちかどうか

        self.waiting_time = 50 # [frames] ゴールに到着したらこれが0になるまで出発できない
        # self.stop_time = 0 # [frames] 何かしらの理由で止まったらこのカウントだけ待って再計算する
        self.loaded = False # 積荷かどうか
        self.load_capacity = 100 # [ton] 

        

    def reset(self):
        self.load_capacity = 100
        self.route = deque()

    def update(self, _x, _y):
        self.x = _x
        self.y = _y

class Location:
    def __init__(self, _x, _y, _type):
        super().__init__()
        self.x = _x
        self.y = _y
        self.type = _type
        self.is_working = False
        self.assined_cidx = None
        self.is_service_done = False 
        
    def start_working(self):
        self.is_working = True
    
    def end_working(self):
        self.is_working = False

class App:
    def __init__(self):

        # ゲームの設定
        self.name = "08_example"
        self.state = State.START
        self.header = 0 #[pix]
        pyxel.init(128, 128, caption=self.name, scale=4, fps=15)
        self.use_random_map = True    

        # 
        self.waiting_count = 1 # [frames]
        self.count = 0 # 画面遷移用カウンタ
        self.num_got_items = 0
        self.max_items = 1e10 # これだけ獲得したら次の画面へ
        self.total_score = 0 # 運んだ量
        
        # 地図の初期化
        self.map = Dungeon(pyxel.width, pyxel.height-self.header)
        self.load_map_from_png()
        # self.num_col_rooms = 3
        # self.num_row_rooms = 2
        # self.corridor_width = 3
        # self.map.create_map_dungeon(num_col_rooms=self.num_col_rooms, 
        #                             num_row_rooms=self.num_row_rooms,
        #                             corridor_width=self.corridor_width,
        #                             max_room_size_ratio=0.6,
        #                             min_room_size_ratio=0.5
        #                             )
        self.map.set_start_random()

        self.occupancy = np.zeros((self.map.h, self.map.w), np.int) 

        # 自キャラの初期化
        self.num_vehicles = 6
        self.cars = []
        # start_points = self.map.get_free_space(num=self.num_vehicles)
        start_points = self.map.get_pos_from_rooms(num=self.num_vehicles)
        for idx, xy in enumerate(start_points):
            # print(xy)
            x = xy[1]
            y = xy[0]
            v = Vehicle(x, y, 11, idx)
            self.cars.append(v)
            self.occupancy[y, x] = True
        
        # loading, dumpingの状態を管理するインスタンス初期化
        self.locations = {}
        for location in self.map.room_idx.items():
            loc_idx = location[0] # int
            yx = location[1] # (y, x)
            if loc_idx %2 == 0:
                loc_type = "dumping"
            else:
                loc_type = "loading"
            self.locations[loc_idx] = Location(yx[1], yx[0], loc_type)
        
        for car in self.cars:        
            if car.loaded:
                # 奇数のものをひとつ選ぶ
                # TODO: self.locationsを使って書き直す
                dumping_locations = [(k, self.map.room_idx[k]) for k in self.map.room_idx.keys() if k%2 == 0]
                car.dest = random.choice(dumping_locations) # (idx, (y, x)) # キャラの目的地
            else:
                # 偶数のものを一つ選ぶ
                loading_locations = [(k, self.map.room_idx[k])  for k in self.map.room_idx.keys() if k%2 == 1]
                car.dest = random.choice(loading_locations) # list(self.map.loadings.items())) # (idx, (y, x)) # キャラの目的地


        # 実行        
        pyxel.run(self.update, self.draw)

    def load_map_from_png(self):
        """
        (r,g,b) = (255,0,0) ==> entrance
        (r,g,b) = (0,255,0) ==> corridor
        (r,g,b) = (0,0,255) ==> location
        (r,g,b) = (0,0,0)   ==> wall
        (r,g,b) = (X,X,X)   ==> rooms        
        """
        from PIL import Image
        from matplotlib import pyplot as plt
        img = np.array(Image.open("../data/map.png"))
        
        plt.imshow(img)
        plt.show()
        
        def get_yx_rgb(rgb):
            return list(zip(*np.where((img[:,:,0]==rgb[0]) & 
                                      (img[:,:,1]==rgb[1]) & 
                                      (img[:,:,2]==rgb[2])
                                      )
                            )
                        )
        locations_yx = get_yx_rgb((0,0,255))
        entrances_yx = get_yx_rgb((255,0,0))
        corridors_yx = get_yx_rgb((0,255,0))
        walls_yx = get_yx_rgb((0,0,0))
        rooms_yx = []
        for gray in range(1, 254):
            room_yx = get_yx_rgb((gray, gray, gray))
            if len(room_yx) != 0:
                rooms_yx.append(room_yx)

        data = np.zeros((128, 128), dtype=np.int)
        for (y, x) in walls_yx:
            data[y, x] = 1

        corridors = np.ones((128, 128), dtype=np.int)
        for (y, x) in corridors_yx:
            corridors[y, x] = 0

        # entrances = np.ones((128, 128), dtype=np.int)
        # for (y, x) in entrances_yx:
        #     entrances[y, x] = 0
            
        rooms_named = np.ones((128, 128), dtype=np.int)
        rooms = np.ones((128, 128), dtype=np.bool)
        
        room_idx = {}
        for idx, (y, x) in enumerate(locations_yx):            
            idx = idx + 1
            room_idx[idx] = (y, x)
        
        for idx, room_yx in enumerate(rooms_yx):
            for (y, x) in room_yx:
                rooms_named[y, x] = idx+1
                rooms[y, x] = False

                
                
                
        # plt.imshow(rooms)
        # plt.show()

        # plt.imshow(corridors)
        # plt.show()

        # plt.imshow(entrances)
        # plt.show()

        # plt.imshow(data)        
        # plt.show()
        self.map.data = data
        self.map.corridors = corridors
        self.map.entrances = entrances_yx
        self.map.rooms_named = rooms_named
        self.map.rooms = rooms
        print(self.map.rooms)


        self.map.room_idx = room_idx
        
    def update(self):
        """
        状態を変更する関数。毎フレーム呼ばれる。
        """
        

        if self.state == State.START: # 開始演出            
            if (pyxel.btn(pyxel.KEY_S)):
                self.state = State.MAIN

            if (pyxel.btn(pyxel.KEY_DOWN)):
                self.use_random_map = False

            if (pyxel.btn(pyxel.KEY_UP)):
                self.use_random_map = True
                

        elif self.state == State.MAIN: # メイン画面
            # return 
        
            # 自キャラの自動操縦
            for car in self.cars:
                
                # パーミッションの取得と移動
                self.act_target(car)        
                
                # 各locationの予約状況の更新
                self.update_locations()    

                # 目的地に到達したか
                if (car.y, car.x) == car.dest[1]:

                    if not self.locations[car.dest[0]].is_working:
                        self.locations[car.dest[0]].start_working() # 動作開始

                    car.is_working = True # 目的地にいるので仕事中
                    car.waiting_time -= 1 # 0になるまで出発できない

                    if car.waiting_time == 0:
                    
                        # locationでの作業終了
                        self.locations[car.dest[0]].end_working()
                        # self.locations[car.dest[0]].assined_cidx = None
                        self.locations[car.dest[0]].is_service_done = True # 車が部屋から出た時に初期化(False)される
                        
                        # 目的地についたので積荷空荷を反転                
                        if car.loaded:
                            car.loaded = False
                            self.total_score += car.load_capacity
                        else:
                            car.loaded = True

                        #  現在の状態に合わせて目的地を変更
                        if car.loaded:
                            # 奇数のものをひとつ選ぶ
                            dumping_locations = [(k, self.map.room_idx[k]) for k in self.map.room_idx.keys() if k%2 == 0]
                            car.dest = random.choice(dumping_locations) # (idx, (y, x)) # キャラの目的地
                        else:   
                            # 偶数のものを一つ選ぶ
                            loading_locations = [(k, self.map.room_idx[k])  for k in self.map.room_idx.keys() if k%2 == 1]
                            car.dest = random.choice(loading_locations) # list(self.map.loadings.items())) # (idx, (y, x)) # キャラの目的地

                        # 待ち時間を初期化
                        car.waiting_time = 50 # TODO: reset関数
                        # 走り出したので仕事状態を変更
                        car.is_working = False
                        
                        
                        
                    else:
                        pass



    def draw(self):
        """
        描画に関することのみここでは書く。状態は変更しないこと。
        """
        if self.state == State.START:
            pyxel.cls(0)
            pyxel.text(0, 0, self.name, 7)
            pyxel.text(40, 64, "RANDOM MAP",  7)            
            pyxel.text(40, 74, "PRESET MAP",  7)            

            if self.use_random_map:
                pyxel.tri(32, 63, 38, 66, 32, 69, 7)
            else:
                pyxel.tri(32, 73, 38, 76, 32, 79, 7)

            
        elif self.state == State.MAIN:
            pyxel.cls(0)
            pyxel.text(0, 0, self.name, 7)
            pyxel.text(0, 7, f"SCORE: {self.total_score:08d} TON",  7)            
            pyxel.text(0, 14, f"TIME: {int(pyxel.frame_count/15.)}",  7)            
            

            # 迷路
            self.draw_map()    

            # 経路
            self.draw_route_permission()

            # 自キャラ
            for car in self.cars:
                pyxel.rect(car.x, car.y + self.header, 1, 1, car.c)



        elif self.state == State.END:
            pyxel.cls(0)
            pyxel.text(0, 0, self.name, 7)
            pyxel.text(5, int(pyxel.height/2.0), "GAME OVER",  7 )            

    # ----------------------------------------------------------------------



    # 描画関数
    def draw_route(self):
        for car in self.cars:
            for idx, cell in enumerate(car.route):
                if idx != 0 and idx != len(car.route)-1:
                    x = cell[1]
                    y = cell[0] + self.header
                    pyxel.rect(x, y, 1, 1, 6)

    def draw_route_permission(self):
        for car in self.cars:
            for idx, cell in enumerate(car.route_permission):
                #if idx != len(car.route_permission)-1:
                x = cell[1]
                y = cell[0] + self.header
                pyxel.rect(x, y, 1, 1, 6)

    def draw_map(self):
        """地図を描画"""
        for i in range(self.map.w):
            for j in range(self.map.h):
                ix = i
                iy = j + self.header
                if self.map.data[j, i] == 0 or self.map.data[j, i] == -2: # FREE and START
                    pyxel.rect(ix, iy, 1, 1, 5)
                elif self.map.data[j, i] == -1: # GOAL
                    pyxel.rect(ix, iy, 1, 1, 8)
                elif self.occupancy[j, i] == True: # Occupied
                    pyxel.rect(ix, iy, 1, 1, 1)
                        

            for ridx in self.map.room_idx:
                pyxel.rect(self.map.room_idx[ridx][1], 
                           self.map.room_idx[ridx][0]+self.header, 1, 1, 9)

    def is_car_in_room(self, room_idx, car):
        if self.map.rooms_named[car.y, car.x] == room_idx:
            return True
        else:
            return False
        

    def update_locations(self):
        for loc in self.locations.items():

            acidx = loc[1].assined_cidx
            loc_idx = loc[0]
            print(f"LOC ID {loc_idx}, ASSINED: {acidx}")
            if acidx is None:
                continue
            
            if not self.is_car_in_room(loc_idx, self.cars[acidx]) and loc[1].is_service_done:
                loc[1].assined_cidx = None # 部屋から出ているようなので予約を終了する
                loc[1].is_service_done = False

    # 状態を更新する関数
    def act_target(self, car):
    
        # print(self.map.corridor[car.x, car.y])
        
        # 最短経路の更新
        if len(car.route) == 0 and len(car.route_permission) == 0 and not car.is_working:        
            car.route = self.map.search_shortest_path_dws((car.y, car.x), car.dest[1])
            car.route = deque(car.route)
            car.route.popleft() # 一つ目はstartなので捨てる
            print("search path!")

        if len(car.route) > 0:

            # コースの予約
            p_length = 20
            for _ in range(p_length):
                if len(car.route_permission) >= p_length:
                    break
                
                next_cell = car.route.popleft()                
                ny = next_cell[0]
                nx = next_cell[1]
                dest_idx = car.dest[0]
                
                # すでに取られていたら戻す
                if self.occupancy[ny, nx] != 0:
                    car.route.appendleft(next_cell) # 戻す
                    break
                
                # まだ取られていない
                else:
                
                    # 次のセルが目的地のある部屋で、かつ誰かの予約があれば戻す
                    if self.map.rooms_named[ny, nx] == dest_idx and self.locations[dest_idx].assined_cidx != car.cidx and self.locations[dest_idx].assined_cidx is not None:
                        car.route.appendleft(next_cell) # 戻す
                        break
                    
                    # 次のセルが目的地のある部屋で、かつ誰の予約もなければlocationを予約する
                    # なお、作業終了後も部屋をでるまでは予約を離さないこと
                    if self.map.rooms_named[ny, nx] == dest_idx and self.locations[dest_idx].assined_cidx is None:
                        self.locations[dest_idx].assined_cidx = car.cidx
                    
                    # 取られていないのでoccupyにする                
                    self.occupancy[ny, nx] = car.cidx

                    # パーミッションとして保持
                    car.route_permission.append(next_cell)
                
                    # 目的地ならパーミッションはそこまでとする
                    if car.dest[1] == (ny, nx):
                        break
                
                    # Routeがなくなればそこまでとする
                    if len(car.route) == 0 :
                        break        
        
        if len(car.route_permission) > 0:
            
            next_cell = car.route_permission.popleft()
            

            x = next_cell[1]
            y = next_cell[0]
            dest_idx = car.dest[0]
            
            # 次のセルが別の車にすでに予約されていたら移動しない
            if self.occupancy[y, x] != car.cidx:                
                car.route_permission.appendleft(next_cell) # 戻す
            
            # 次のセルが目的地で、かつそこが稼働なら移しない
            elif self.map.rooms_named[y, x] == dest_idx and self.locations[dest_idx].is_working:
                car.route_permission.appendleft(next_cell) # 戻す
            else:
                px = car.x
                py = car.y
                car.update(x, y)

                # 移動し終わったので開放する
                self.occupancy[py, px] = 0
            
        else:
            pass


    
App()