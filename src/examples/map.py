from enum import Enum
import numpy as np
from scipy.signal import convolve2d
from scipy.ndimage.filters import minimum_filter, maximum_filter

def dilation(arr, ksize=3):                

    ret_arr = np.copy(arr)
    dilation_kernel = np.ones((ksize, ksize))
    if ksize % 2 == 0: 
        l = int(ksize / 2.0)
        r = int(ksize / 2.0)
    else:
        l = int(np.floor(ksize / 2.0))
        r = int(np.floor(ksize / 2.0))+1    
            
    for iy in range(l, arr.shape[0]-r):
        for ix in range(l, arr.shape[1]-r):
            if np.any(arr[iy, ix]==0):
                ret_arr[iy-l:iy+r, ix-l:ix+r] = 0                            
    return ret_arr

class Map:
    def __init__(self, w, h, debug=False):
        super().__init__()
        """
        self.dataが地図
        0: 走行可能
        1: 走行不可
        -1: ゴール
        -2: スタート
        """
        self.w = w
        self.h = h

        self.data = np.zeros((h, w), np.int)
    
        self.goal_x = None
        self.goal_y = None
        self.start_x = None 
        self.start_y = None
        
        self.debug = debug         
        
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
                    
    def create_map_dungeon(self, num_col_rooms=3, 
                           num_row_rooms=2, 
                           corrider_width=1, 
                           min_room_size_ratio=0.3, 
                           max_room_size_ratio=0.9
                           ):
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
                
                rsx = np.random.randint(int(rmsx * min_room_size_ratio), int(rmsx * max_room_size_ratio))
                rsy = np.random.randint(int(rmsy * min_room_size_ratio), int(rmsy * max_room_size_ratio))
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
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == num_row_rooms-1 and ix == num_col_rooms-1:
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0

                elif iy == 0 and ix == num_col_rooms-1:
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == num_row_rooms-1 and ix == 0:
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0

                elif iy == num_row_rooms-1 and ix == 0:
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0

                elif iy == 0:
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

                elif iy == num_row_rooms-1:
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0

                elif ix == 0:
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

                elif ix == num_col_rooms-1:
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0
                            
                else:                
                    self.data[exit_left, cx-rx:cx] = 0
                    self.data[exit_right, cx:cx+rx] = 0
                    self.data[cy-ry:cy, exit_x_up] = 0
                    self.data[cy:cy+ry, exit_x_down] = 0

        # 線をつなげる
        rand_col_idx = np.array(rand_col_idx)
        for col_idx in rand_col_idx[1:-1]:
            end_y_l = np.where(self.data[:, col_idx - 1]== 0 )
            end_y_r = np.where(self.data[:, col_idx + 1]== 0 )
            for idx in range(num_row_rooms):
                end_y = sorted([end_y_l[0][idx], end_y_r[0][idx]])
                self.data[end_y[0]:end_y[1]+1, col_idx] = 0                

        rand_row_idx = np.array(rand_row_idx)
        for row_idx in rand_row_idx[1:-1]:
            end_x_u = np.where(self.data[row_idx - 1, :]== 0 )
            end_x_d = np.where(self.data[row_idx + 1, :]== 0 )
            for idx in range(num_col_rooms):
                end_x = sorted([end_x_u[0][idx], end_x_d[0][idx]])
                self.data[row_idx, end_x[0]:end_x[1]+1] = 0                

        if corrider_width > 1:            
            self.data = dilation(self.data, ksize=corrider_width)

    def set_start(self):

        # 地図中にスタートがあれば通路0に置き換え
        self.data = np.where(self.data == -2, 0, self.data)
        
        # 通路0を引くまでランダムに選択する
        x = np.random.randint(self.w)
        y = np.random.randint(self.h)        
        while self.data[y, x] != 0 and self.data[y, x] != -1:
            x = np.random.randint(self.w)
            y = np.random.randint(self.h)        

        self.data[y, x] = -2 # Start
        self.start_x = x
        self.start_y = y
        
    def set_goal(self):
        # 地図中にゴールがあれば通路0に置き換え
        self.data = np.where(self.data == -1, 0, self.data)

        x = np.random.randint(self.w)
        y = np.random.randint(self.h)        
        while self.data[y, x] != 0 and self.data[y, x] != -2:
            x = np.random.randint(self.w)
            y = np.random.randint(self.h)        

        self.data[y, x] = -1 # Goal
        self.goal_x = x
        self.goal_y = y
 
    def search_shortest_path_dws(self, start, goal):
        """
        start = (y, x)
        goal = (y, x)
        """
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        import matplotlib.colors as colors
        import numpy as np
        
        
        start_goal = np.zeros((self.h, self.w), dtype=int)
        cost = np.zeros((self.h, self.w), dtype=int) + 999
        done = np.zeros((self.h, self.w), dtype=bool)
        barrier = np.zeros((self.h, self.w), dtype=bool)
        path = np.zeros((self.h, self.w), dtype=int)
        
        #プーリング用のフィルタ
        g = np.array([[0, 1, 0],
                      [1, 1, 1],
                      [0, 1, 0]])
        
        for iy in range(self.h):
            for ix in range(self.w):
                if iy == start[0] and ix == start[1]:
                    cost[iy, ix] = 0
                    done[iy, ix] = True
                    start_goal[iy, ix] = -255
                if iy == goal[0] and ix == goal[1]:                
                    start_goal[iy, ix] = 255
                if self.data[iy, ix] == 1: # barrier
                    barrier[iy, ix] = True 

        # print('start\n{}'.format(start))
        # print('goal\n{}'.format(goal))
        # print('cost\n{}'.format(cost))
        # print('done\n{}'.format(done))
        # print('barrier\n{}'.format(barrier))
 
        for i in range(1, 999):

            #次に進出するマスのbool
            done_next = maximum_filter(done, footprint=g) * ~done
            #print('done_next\n{}'.format(done_next))
            
            #次に進出するマスのcost
            cost_next = minimum_filter(cost, footprint=g) * done_next
            cost_next[done_next] += 1
            #print('cost_next\n{}'.format(cost_next))
            
            #costを更新
            cost[done_next] = cost_next[done_next]
            
            #ただし障害物のコストは999とする
            cost[barrier] = 999
            #print('cost\n{}'.format(cost))
            
            #探索終了マスを更新
            done[done_next] = done_next[done_next]
            #ただし障害物は探索終了としない
            done[barrier] = False
            #print('done\n{}'.format(done))
            
            # x, y = np.where(cost != 999)
            # c = cost[x, y]
            # for i in range(len(x)):
                # plt.text(y[i]-0.1, x[i]+0.1, c[i], size = 20, color = 'gray')

            
            #終了判定
            if done[goal[0], goal[1]] == True:
                break
                    #表示

    
        point_now = goal
        cost_now = cost[goal[0], goal[1]]
        route = [goal]
        # print('route\n{}'.format(route))
        while cost_now > 0:
            #上から来た場合
            try:
                if cost[point_now[0] - 1, point_now[1]] == cost_now - 1:
                    #更新
                    point_now = (point_now[0] - 1, point_now[1])
                    cost_now = cost_now - 1
                    #記録
                    route.append(point_now)
            except: pass
            #下から来た場合
            try:
                if cost[point_now[0] + 1, point_now[1]] == cost_now - 1:
                    #更新
                    point_now = (point_now[0] + 1, point_now[1])
                    cost_now = cost_now - 1
                    #記録
                    route.append(point_now)
            except: pass
            #左から来た場合    
            try:
                if cost[point_now[0], point_now[1] - 1] == cost_now - 1:
                    #更新
                    point_now = (point_now[0], point_now[1] - 1)
                    cost_now = cost_now - 1
                    #記録
                    route.append(point_now)
            except: pass
            #右から来た場合
            try:
                if cost[point_now[0], point_now[1] + 1] == cost_now - 1:
                    #更新
                    point_now = (point_now[0], point_now[1] + 1)
                    cost_now = cost_now - 1
                    #記録
                    route.append(point_now)
            except: pass

        #ルートを逆順にする
        route = route[::-1]
                
        for cell in route:
            ix = cell[1]
            iy = cell[0]
            path[iy, ix] = 1

        if self.debug:        
            cmap = cm.jet
            cmap_data = cmap(np.arange(cmap.N))
            cmap_data[0, 3] = 0 # 0 のときのα値を0(透明)にする
            customized_jet = colors.ListedColormap(cmap_data)

            cmap = cm.cool
            cmap_data = cmap(np.arange(cmap.N))
            cmap_data[0, 3] = 0 # 0 のときのα値を0(透明)にする
            customized_cool = colors.ListedColormap(cmap_data)

            cmap = cm.gist_yarg
            cmap_data = cmap(np.arange(cmap.N))
            cmap_data[0, 3] = 0 # 0 のときのα値を0(透明)にする
            customized_gist_yarg = colors.ListedColormap(cmap_data)

            plt.imshow(path, cmap=customized_cool)        
            plt.imshow(barrier, cmap=customized_gist_yarg)
            plt.show()
        return route
    
if __name__ == "__main__":

    from collections import deque
    
    width = 128
    height = 64
    map = Map(width, height, debug=False)
    # map.create_map_stick_down()
    map.create_map_dungeon(num_col_rooms=5, num_row_rooms=4)
    map.set_goal()
    map.set_start()
    route = map.search_shortest_path_dws((map.start_y, map.start_x), (map.goal_y, map.goal_x))
    route_deque = deque(route)
    print(route_deque)
    s = route_deque.popleft()
    n = route_deque.popleft()
    print(s)
    print(n)
    print(map.start_y, map.start_x)