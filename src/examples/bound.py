from pyxel import circ, cls, flip, init, line
import numpy as np

def min_max(x, axis=None):
    min = x.min(axis=axis, keepdims=True)
    max = x.max(axis=axis, keepdims=True)
    result = (x-min)/(max-min)
    return result

def rot(p):
    px = p[0]
    py = p[1]
    pz = p[2]
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(px), np.sin(px)],
                   [0, -np.sin(px), np.cos(px)]])
    Ry = np.array([[np.cos(py), 0, -np.sin(py)],
                   [0, 1, 0],
                   [np.sin(py), 0, np.cos(py)]])
    Rz = np.array([[np.cos(pz), np.sin(pz), 0],
                   [-np.sin(pz), np.cos(pz), 0],
                   [0, 0, 1]])
    R = Rz.dot(Ry).dot(Rx)
    return R


init(256,256)
xmax = ymax = 256
zmax = 30

x = np.mgrid[-2:2:0.05] 
y = np.mgrid[-2:2:0.05] 
X, Y = np.meshgrid(x, y)
R = rot(np.array([1, 0.2, 0]))
t = 0
while 1:
    cls(0)
    # Z = min_max(np.sin(X*2*np.pi + t) * np.cos(Y*2*np.pi + t))
    Z = min_max(np.sin( np.sqrt((X**2 + Y**2)) *4*np.pi + t))
    P = np.vstack([X.ravel(), Y.ravel(), Z.ravel()])
    P[0, :] = (P[0, :]) * xmax + xmax/2
    P[1, :] = (P[1, :]) * ymax + ymax/2
    P[2, :] = (P[2, :]) * zmax
    P = R.dot(P)

    for i in range(P.shape[1] - 1):
        x1 = int(P[0, i])
        y1 = int(P[1, i])
        x2 = int(P[0, i+1])
        y2 = int(P[1, i+1])
        if np.fabs(x1 - x2) > 30:
            continue
        line(x1, y1, x2, y2, 11)
        circ(x1, y1, 1, 11)
    flip()
    t += 0.01