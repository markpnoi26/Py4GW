
# Reload imports
import importlib
import os

from Py4GWCoreLib import Player
from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import Py4GWSharedMemoryManager
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Widgets.frenkey.Polymock import combat
from Widgets.frenkey.Polymock import gui
from Widgets.frenkey.Polymock import state

importlib.reload(gui)
importlib.reload(combat)
importlib.reload(state)

MODULE_NAME = "Polymock"
throttle_timer = ThrottledTimer(250)
script_directory = os.path.dirname(os.path.abspath(__file__))


sharedMemoryManager = Py4GWSharedMemoryManager()

combat_handler = combat.Combat()
widget_state = state.WidgetState()
ui = gui.UI()

def configure():
    pass


def main():    
    if not Routines.Checks.Map.MapValid():
        return    
            
    widget_state.update()
    ui.draw()
    
    if not GLOBAL_CACHE.Map.IsExplorable():
        return                    
                     
    if throttle_timer.IsExpired():
        throttle_timer.Reset()
        
        combat_handler.Fight()
        
        
        

__all__ = ['main', 'configure']
