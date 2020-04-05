import copy
import numpy as np
from scipy.ndimage.filters import minimum_filter, maximum_filter
from matplotlib import pyplot as plt


def max_pooling(img, direction=4):

    h = img.shape[0]
    w = img.shape[1]

    if direction == 4:
        g = np.array([[0, 1, 0],
                      [1, 1, 1],
                      [0, 1, 0]])
    elif direction == 8:
        g = np.array([[1, 1, 1],
                      [1, 1, 1],
                      [1, 1, 1]])        
    else:
        raise ValueError("Invalid number of directions")
        
    src = np.zeros((h+2, w+2), dtype=np.bool) # 0 padding 
    src[1:-1, 1:-1]  = copy.deepcopy(img)
    dst = copy.deepcopy(src)
    
    import time
    
    start = time.time()
    for iy in range(1, h+1):
        for ix in range(1, w+1):
            dst[iy, ix] = np.max(src[iy-1:iy+2, ix-1:ix+2][g==1])
    print(f"for loop\t\t: {time.time() - start} sec")
    
    start = time.time()
    ret = np.array([[ np.max(src[iy-1:iy+2, ix-1:ix+2][g==1]) for iy in range(1, h+1)] for ix in range(1, w+1)])
    print(f"list comprehension\t: {time.time() - start} sec")
    
    start = time.time()
    ret = maximum_filter(img, footprint=g)
    print(f"scikit-image\t\t: {time.time() - start} sec")
    
    return ret
        
    # return dst[1:-1, 1:-1]

def min_pooling(img, direction=4):

    h = img.shape[0]
    w = img.shape[1]

    if direction == 4:
        g = np.array([[0, 1, 0],
                      [1, 1, 1],
                      [0, 1, 0]])
    elif direction == 8:
        g = np.array([[1, 1, 1],
                      [1, 1, 1],
                      [1, 1, 1]])        
    else:
        raise ValueError("Invalid number of directions")
        
    src = np.zeros((h+2, w+2), dtype=np.bool) # 0 padding 
    src[1:-1, 1:-1]  = copy.deepcopy(img)
    dst = copy.deepcopy(src)
    
    # for iy in range(1, h+1):
    #     for ix in range(1, w+1):
    #         dst[iy, ix] = np.min(src[iy-1:iy+2, ix-1:ix+2][g==1])
    return  np.array([[ np.max(src[iy-1:iy+2, ix-1:ix+2][g==1]) for iy in range(1, h+1)] for ix in range(1, w+1)])
    # return dst[1:-1, 1:-1]


if __name__ == "__main__":
    w = 100
    h = 100
    img = np.zeros((h, w), dtype=np.bool)
    sy = 5
    sx = 5
    img[sy, sx] = True
    
    plt.imshow(img, cmap="gist_yarg")
    plt.show()

    g = np.array([[0, 1, 0],
                  [1, 1, 1],
                  [0, 1, 0]])
    
    print("max pool")
    for _ in range(5):    
        img = max_pooling(img, direction=4)
        plt.imshow(img, cmap="gist_yarg")
        plt.show()
    print("min pool")
    for _ in range(5):    
        img = min_pooling(img, direction=4)
        plt.imshow(img, cmap="gist_yarg")
        plt.show()
