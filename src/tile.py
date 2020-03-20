from enum import Enum

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
                
    WALL_CORRIDER_H_CENTER = 17,
    WALL_CORRIDER_V_CENTER = 18,
    
    WALL_CORRIDER_LEFT = 19,
    WALL_CORRIDER_RIGHT = 20,
    WALL_CORRIDER_UP = 21,
    WALL_CORRIDER_DOWN = 22,
    
    GOAL = 23
    
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
    elif tile_type == TyleType.WALL_CORRIDER_H_CENTER:
        ret = (56, 32)
    elif tile_type == TyleType.WALL_CORRIDER_V_CENTER:
        ret = (40, 96)
    elif tile_type == TyleType.WALL_CORRIDER_LEFT:
        ret = (56, 48)
    elif tile_type == TyleType.WALL_CORRIDER_RIGHT:
        ret = (72, 32)
    elif tile_type == TyleType.WALL_CORRIDER_UP:
        ret = (40, 80)
    elif tile_type == TyleType.WALL_CORRIDER_DOWN:
        ret = (40, 112)
    elif tile_type == TyleType.GOAL:
        ret = (16, 48)
    else:
        ret = None    
        
    return ret
