import math
from typing import List, Tuple

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.Camera import Camera
from Py4GWCoreLib.DXOverlay import DXOverlay
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


Waypoint2D = Tuple[float, float]
Waypoint3D = Tuple[float, float, float]
draw_throttle = ThrottledTimer(2000)
path_throttle = ThrottledTimer(250)
paths: dict[int, List[Waypoint3D]] = {}
closest_waypoint = 0
path_requested = False

current_path_generator = None
current_partial_path: List[Waypoint3D] = []
path_finished = False


flag_color = Color(0, 204, 156, 100)
path_color = Color(255, 255, 255, 150)
    

waypoint_dict: dict[int, List[Waypoint2D]] = {
    444: [
        (16081.63, -11048.55),
        (16205.75, -11561.24),
        (16573.59, -12127.98),
        (16796.12, -12380.12),
        (17619.33, -13093.12),
        (17361.46, -13667.42),
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
    437: [
        (4465.54, -16118.44),
        (5902.26, -14744.68),
        (6435.12, -13821.38),
        (7723.12, -13543.52),
        (8420.34, -12646.81),
        (9466.96, -11992.94),
        (10401.58, -11021.58),
        (10968.76, -8763.79),
        (11302.09, -7145.48),
    ],
}


def configure():
    pass


def draw_flag(overlay: Overlay, x: float, y: float, z: float):
    global flag_color
    
    size = 25
    z_min = z
    z_max = z - 75
    
    overlay.DrawLine3D(
        x, y, z_min,
        x, y, z_max,
        flag_color.color_int,
        3
    )

    overlay.DrawTriangleFilled3D(
        x, y, z_max,
        x, y, z_max + size,
        x - size, y, z_max + (size / 2),
        flag_color.color_int
    )


def IsPointInFOV(target_x: float, target_y: float) -> bool:
    cam_x, cam_y, _ = Camera.GetPosition()
    yaw = Camera.GetYaw()
    fov = Camera.GetFieldOfView()

    dx = target_x - cam_x
    dy = target_y - cam_y

    dist = math.hypot(dx, dy)
    if dist == 0:
        return True

    angle_to_target = math.atan2(dy, dx)
    angle_diff = angle_to_target - yaw

    while angle_diff > math.pi:
        angle_diff -= 2 * math.pi
    while angle_diff < -math.pi:
        angle_diff += 2 * math.pi

    half_fov = (fov / 2) + 0.2
    return abs(angle_diff) < half_fov


def draw_paths():
    global paths, path_color, closest_waypoint
    if paths:
        # Draw paths
        for idx, path in paths.items():
            if idx < closest_waypoint:
                continue
            
            for i in range(1, len(path)):
                x1, y1, z1 = path[i - 1]
                x2, y2, z2 = path[i]

            for i in range(len(path) - 1):
                x1, y1, _ = path[i]
                x2, y2, _ = path[i + 1]
                z1 = DXOverlay.FindZ(x1, y1)
                z2 = DXOverlay.FindZ(x2, y2)
                DXOverlay().DrawLine3D(x1, y1, z1 - 50, x2, y2, z2 - 50, path_color.color_int, False)
            
def draw_waypoints_ui():
    global paths, closest_waypoint, path_color
    
    overlay = Overlay()
    mapid = GLOBAL_CACHE.Map.GetMapID()

    waypoints = waypoint_dict.get(mapid, [])
    if not waypoints:
        return

    player_x, player_y = GLOBAL_CACHE.Player.GetXY()

    closest_distance = float("inf")

    for idx, (x, y) in enumerate(waypoints):
        dist = Utils.Distance((player_x, player_y), (x, y))
        if dist < closest_distance:
            closest_distance = dist
            closest_waypoint = idx
        
    # if path_throttle.IsExpired():
    #     path_throttle.Reset()
    #     paths = get_paths(waypoints, closest_waypoint)

    overlay.BeginDraw()

    draw_paths()
            
    # Draw waypoint flags
    for idx, (x, y) in enumerate(waypoints):
        if idx < closest_waypoint:
            continue

        if not IsPointInFOV(x, y):
            continue

        z = overlay.FindZ(x, y)
        draw_flag(overlay, x, y, z)

    overlay.EndDraw()

def search_path_generator():                
    global paths, waypoint_dict, closest_waypoint, path_requested, current_path_generator
    path_requested = True
    
    waypoints = waypoint_dict.get(GLOBAL_CACHE.Map.GetMapID(), [])
    if not waypoints:
        return
    
    z1 = GLOBAL_CACHE.Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())
    
    new_paths : dict[int, List[Waypoint3D]] = {}
        
    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
    for idx in range(closest_waypoint, len(waypoints)):                
        if idx in paths and idx != closest_waypoint:
            continue
        
        if idx == 0 or idx == closest_waypoint:
            start_x, start_y = player_x, player_y
            
        else:
            start_x, start_y = waypoints[idx - 1]

        goal_x, goal_y = waypoints[idx]

        start: Waypoint3D = (
            start_x,
            start_y,
            z1,
        )

        goal: Waypoint3D = (
            goal_x,
            goal_y,
            z1,
        )

        path = yield from AutoPathing().get_path(start, goal)
        if path:                
            paths[idx] = path
                            
    current_path_generator = None
    
def main():
    global path_requested, current_path_generator
    
    if Routines.Checks.Map.IsLoading():
        draw_throttle.Reset()
        return
        
    if not Routines.Checks.Map.IsMapReady():
        draw_throttle.Reset()
        return
    
    if not Routines.Checks.Map.IsExplorable():
        draw_throttle.Reset()
        return
    
    if UIManager.IsWorldMapShowing():
        draw_throttle.Reset()
        return

    if not draw_throttle.IsExpired():
        return
    
    if current_path_generator is not None:
        try:
            next(current_path_generator, None)
            
        except StopIteration:
            ConsoleLog("SulfourRunner", "Path calculation finished.")
            current_path_generator = None
    else:
        current_path_generator = search_path_generator()
        
    draw_waypoints_ui()
    
    if path_throttle.IsExpired():
        path_throttle.Reset()


__all__ = ["main", "configure"]
