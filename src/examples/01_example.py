from enum import Enum
import numpy as np
import pyxel

class State(Enum):
  START = 1 # 開始演出
  MAIN = 2 # メイン

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

        self.state = State.START

        pyxel.init(80, 60, caption="01_example", scale=4, fps=15)
        pyxel.image(0).load(0, 0, "pyxel_logo_38x16.png") # opening
        
        # キャラの初期化
        num_vehicles = 20
        self.vehicles = []
        for idx in range(num_vehicles):
            x = int(np.random.rand() * pyxel.width)
            y = int(np.random.rand() * pyxel.height)
            c = int(np.random.randint(15)) + 1 # 1...15の整数
            v = Vehicle(x, y, c)
            self.vehicles.append(v)

        pyxel.run(self.update, self.draw)

    def update(self):
        
        if self.state == State.START: # 開始演出
            
            if (pyxel.btn(pyxel.KEY_S)):
                self.state = State.MAIN
                
        elif self.state == State.MAIN: # メイン
            for v in self.vehicles:
                dx = 1 if np.random.rand() > 0.9 else 0 # TODO seed
                dx = dx if np.random.rand() > 0.5 else -dx # TODO seed            
                dy = 1 if np.random.rand() > 0.9 else 0
                dy = dy if np.random.rand() > 0.5 else -dy
                x = (v.x + dx) % pyxel.width
                y = (v.y + dy) % pyxel.height
                v.update(x, y)

    def draw(self):
        if self.state == State.START:
            pyxel.cls(0)
            pyxel.text(0, 0, "01_example.py", 7)
            
        elif self.state == State.MAIN:
            pyxel.cls(0)
            pyxel.text(0, 0, "01_example.py", 7)
            for v in self.vehicles:
                pyxel.rect(v.x, v.y, 2, 2, v.c)
App()