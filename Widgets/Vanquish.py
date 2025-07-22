import os

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Color
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import Overlay
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Timer

module_name = "Vanquish Monitor"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(root_directory, "Widgets/Config/Vanquish.ini")

ini_handler = IniHandler(ini_file_location)
sync_interval = 1000

class Config:
    global ini_handler, module_name, sync_interval
    def __init__(self):
        self.x = ini_handler.read_int(module_name, "x", 100)
        self.y = ini_handler.read_int(module_name, "y", 200)
        self.font_size = ini_handler.read_int(module_name, "font_size", 20)
        self.color = Color(
                    ini_handler.read_int(module_name, "color_r", 255),
                    ini_handler.read_int(module_name, "color_g", 255),
                    ini_handler.read_int(module_name, "color_b", 255),
                    ini_handler.read_int(module_name, "color_a", 255))
        self.string = "000/000"
        self.sync_interval = sync_interval
        
    def save(self):
        """Save the current configuration to the INI file."""
        ini_handler.write_key(module_name, "x", str(self.x))
        ini_handler.write_key(module_name, "y", str(self.y))
        ini_handler.write_key(module_name, "font_size", str(self.font_size))
        ini_handler.write_key(module_name, "color_r", str(self.color.get_r()))
        ini_handler.write_key(module_name, "color_g", str(self.color.get_g()))
        ini_handler.write_key(module_name, "color_b", str(self.color.get_b()))
        ini_handler.write_key(module_name, "color_a", str(self.color.get_a()))
        
widget_config = Config()
window_module = ImGui.WindowModule(
    module_name, 
    window_name="Vanquish Monitor##Vanquish Monitor",
    window_size=(100, 100), 
    window_flags=PyImGui.WindowFlags(
        PyImGui.WindowFlags.AlwaysAutoResize | 
        PyImGui.WindowFlags.NoBackground | 
        PyImGui.WindowFlags.NoTitleBar | 
        PyImGui.WindowFlags.NoCollapse
    )
)

config_module = ImGui.WindowModule(f"Config {module_name}", window_name="Vanquish Monitor##Vanquish Monitor config", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
window_x = ini_handler.read_int(module_name +str(" Config"), "config_x", 100)
window_y = ini_handler.read_int(module_name +str(" Config"), "config_y", 100)

config_module.window_pos = (window_x, window_y)

is_map_ready = False
is_party_loaded = False
is_explorable = False
is_vanquishable = False
is_hard_mode = False
killed = 0
total =0

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()
  


def configure():
    global widget_config, config_module, ini_handler

    if config_module.first_run:
        PyImGui.set_next_window_size(config_module.window_size[0], config_module.window_size[1])     
        PyImGui.set_next_window_pos(config_module.window_pos[0], config_module.window_pos[1])
        config_module.first_run = False

    new_collapsed = True
    end_pos = config_module.window_pos
    if PyImGui.begin(config_module.window_name, config_module.window_flags):
        new_collapsed = PyImGui.is_window_collapsed()
        overlay = Overlay()
        screen_width, screen_height = overlay.GetDisplaySize().x, overlay.GetDisplaySize().y
        widget_config.x = PyImGui.slider_int("X", widget_config.x, 0, screen_width)
        widget_config.y = PyImGui.slider_int("Y", widget_config.y, 0, screen_height)

        widget_config.font_size = PyImGui.slider_int("Font Size", widget_config.font_size, 1, 250)
        color = PyImGui.color_edit4("Color", widget_config.color.to_tuple_normalized())
        widget_config.color = Color(
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255),
            int(color[3] * 255)
        )

        widget_config.save()
        end_pos = PyImGui.get_window_pos()

    PyImGui.end()

    if end_pos[0] != config_module.window_pos[0] or end_pos[1] != config_module.window_pos[1]:
        config_module.window_pos = (int(end_pos[0]), int(end_pos[1]))
        ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
        ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))


def DrawWindow():
    global widget_config, window_module
    global killed, total
    
    widget_config.string = f"{total:03}/{killed:03}"

    PyImGui.set_next_window_pos(widget_config.x, widget_config.y)

    if PyImGui.begin(window_module.window_name, window_module.window_flags):
        ImGui.push_font("Regular", widget_config.font_size)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text,widget_config.color.to_tuple_normalized())
        PyImGui.text(widget_config.string)
        PyImGui.pop_style_color(1)
        ImGui.pop_font()
    PyImGui.end()
  
  
def main():
    global is_map_ready, is_party_loaded, is_explorable, is_vanquishable, is_hard_mode, game_throttle_timer
    global game_throttle_time, widget_config, killed, total
    
    if game_throttle_timer.HasElapsed(game_throttle_time):
        is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
        is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        is_explorable = GLOBAL_CACHE.Map.IsExplorable()
        is_vanquishable = GLOBAL_CACHE.Map.IsVanquishable()
        is_hard_mode = GLOBAL_CACHE.Party.IsHardMode()
        if (
            is_map_ready and
            is_party_loaded and
            is_explorable and
            is_vanquishable and
            is_hard_mode
        ):
            killed = GLOBAL_CACHE.Map.GetFoesKilled()
            total = GLOBAL_CACHE.Map.GetFoesToKill()
            
        game_throttle_timer.Start()
         
    if (
        is_map_ready and
        is_party_loaded and
        is_explorable and
        is_vanquishable and
        is_hard_mode
    ):
        DrawWindow()

if __name__ == "__main__":
    main()

