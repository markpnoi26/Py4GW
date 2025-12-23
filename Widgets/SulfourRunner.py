
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


waypoint_dict : dict[int, list[tuple[float, float]]] = {
    444 : [
        (16081.63, -11048.55),
        (16205.75, -11561.24),
        (16796.12, -12380.12),
        (17619.33, -13093.12),
        (16346.84, -13510.79),
        (15204.45, -13802.76),
        (13894.67, -14068.41),
        (12257.97, -13667.80),
        (11530.83, -13535.98),
        (10344.16, -13491.97),
        (9160.40, -13136.81),
        (8865.66, -12580.95),
        (8064.00, -12192.00),
        (7345.84, -11481.20),
        (-516.13, -6785.55),
        (-306.18, -6072.92),
        (-509.03, -5390.10),
        (0.62, -4241.59),
        (44.10, -2897.30),
        (175.36, -1626.59),
        (-21.74, -724.51),
        (706.58, -105.54),
        (931.35, 944.19),
        (-4425.78, 7941.06),
        (-4857.11, 8839.57),
        (-4128.81, 9406.73),
        (-4277.01, 10218.22),
        (-3048.67, 11634.17),
        (-1516.45, 11495.00),
        (-940.59, 12183.17),
    ],
    437 : [
        (4465.54, -16118.44),
        (5902.26, -14744.68),
        (6435.12, -13821.38),
        (7723.12, -13543.52),
        (8420.34, -12646.81),
        (9466.96, -11992.94),
        (10401.58, -11021.58),
        (10968.76, -8763.79),
        (11302.09, -7145.48)

    ],
}


def configure():
    pass

def draw_flag(overlay : Overlay, pos_x: float, pos_y: float, pos_z: float):    
    overlay.DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, Utils.RGBToColor(0, 255, 0, 255), 3)    
    overlay.DrawTriangleFilled3D(
        pos_x, pos_y, pos_z - 150,               # Base point
        pos_x, pos_y, pos_z - 120,               # 30 units up
        pos_x - 50, pos_y, pos_z - 135,          # 50 units left, 15 units up
        Utils.RGBToColor(0, 255, 0, 255)
    )
    
def draw_waypoints_ui():
    overlay = Overlay()
    mapid = GLOBAL_CACHE.Map.GetMapID()
    
    waypoints = waypoint_dict.get(mapid, [])
    overlay.BeginDraw()
    
    for idx, (x, y) in enumerate(waypoints):
        pos_z = overlay.FindZ(x, y)
        draw_flag(overlay, x, y, pos_z)
        
    overlay.EndDraw()    
    
    pass

def main():
    draw_waypoints_ui()
    pass


__all__ = ['main', 'configure']