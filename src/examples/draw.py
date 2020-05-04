from math import sin, sqrt
from pyxel import circ, circb, cls, flip, init
import numpy as np
import random
from collections import deque

init(256,256)
rs = np.random.rand(np.random.randint(1, 3))*5
colors = [5, 12]
center = [np.random.randint(128), np.random.randint(128)]
max_size = 256
class Drop:
    def __init__(self, c, rs, colors):
        self.c = c
        self.rs = rs
        self.is_alive = True
        self.colors = colors

drop = Drop(center, rs, colors)
drops = list()
drops.append(drop)

while 1:
    cls(1)
    for e in drops:
        for idx in range(len(e.rs)):
            e.rs[idx] += 1
        if e.rs[0] > 60:
            e.colors = [5]
        if e.rs[0] > 90:
            e.colors = [1]
        if e.rs[0] > 200:
            e.is_alive = False
        for idx in range(len(e.rs)):
            circb(e.c[0], e.c[1], e.rs[idx], random.choice(e.colors) )
        for i, e in enumerate(drops):
            if not e.is_alive:
                drops.pop(i)
    if np.random.rand() > 0.9:
        center = [np.random.randint(max_size), np.random.randint(max_size)]
        rs = np.random.rand(np.random.randint(1, 5))*10
        colors = [5, 12]
        drop = Drop(center, rs, colors)
        drops.append(drop)
    flip()