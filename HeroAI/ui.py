
import PyImGui
from Py4GWCoreLib import ImGui
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData


def draw_hero_panel(account_data : AccountData, open : bool = True):
    if ImGui.begin(str(account_data.CharacterName) + "##Hero Panel" + str(account_data.PlayerID), open, PyImGui.WindowFlags.AlwaysAutoResize):
        
        for i in range(8):
            ImGui.button(f"{i+1}", 32, 32)
            PyImGui.same_line(0,4)
            
        pass
    ImGui.end()
    pass  # Implementation of hero panel drawing logic goes here