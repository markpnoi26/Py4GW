# Reload imports
from datetime import datetime
from enum import Enum
import importlib
import os
from typing import Optional

import Py4GW
import PyImGui
from PyOverlay import Overlay

from Py4GWCoreLib import IconsFontAwesome5, ImGui, Routines
from Py4GWCoreLib.ImGui import Style
from Py4GWCoreLib.ImGui_src.Textures import MapTexture, GameTexture, TextureState, ThemeTexture, ThemeTextures
from Py4GWCoreLib.ImGui_src.types import MINIMALUS_FOLDER, TEXTURE_FOLDER, ControlAppearance, StyleColorType, StyleTheme
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler
from Py4GWCoreLib import Timer
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer

import sys

from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GW_widget_manager import WidgetHandler

MODULE_NAME = "Style Manager"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(
    root_directory, "Widgets/Config/Style Manager.ini")
ini_handler = IniHandler(ini_file_location)


save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

window_x = ini_handler.read_int(MODULE_NAME + str(" Config"), "x", 100)
window_y = ini_handler.read_int(MODULE_NAME + str(" Config"), "y", 100)

window_width = ini_handler.read_int(MODULE_NAME + str(" Config"), "width", 600)
window_height = ini_handler.read_int(
    MODULE_NAME + str(" Config"), "height", 500)

window_collapsed = ini_handler.read_bool(
    MODULE_NAME + str(" Config"), "collapsed", False)

#imgui_ini_reader = ImGuiIniReader()
window = None #imgui_ini_reader.get(name)
screen_width, screen_height = ImGui.overlay_instance.GetDisplaySize().x, ImGui.overlay_instance.GetDisplaySize().y

window_size = window.size if window else (800.0, 600.0)
window_pos = (screen_width / 2 - window_size[0] / 2, screen_height / 2 - window_size[1] / 2)
window_pos = window.pos if window else window_pos
collapse = window.collapsed if window else False

class WindowModule:
        _windows : dict[str, 'WindowModule'] = {}
        
        def __init__(self, module_name="", window_name="", window_size=(100,100), window_pos=(0,0), window_flags=PyImGui.WindowFlags.NoFlag, collapse= False, can_close=False, forced_theme: Optional[StyleTheme] = None, resize_on_collapse: bool = False):
            self.module_name = module_name
            
            self.window_name = window_name if window_name else module_name
            self.window_size = window_size
            self.collapse = collapse
            self.resize_on_collapse = resize_on_collapse

            if window_pos == (0,0):
                overlay = Overlay()
                screen_width, screen_height = overlay.GetDisplaySize().x, overlay.GetDisplaySize().y
                #set position to the middle of the screen
                self.window_pos = (screen_width / 2 - window_size[0] / 2, screen_height / 2 - window_size[1] / 2)
            else:
                self.window_pos = window_pos
            self.window_flags = window_flags
            
            self.can_close = can_close
            self.can_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.NoResize)) == 0 and (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) == 0

            self.end_pos = window_pos  # Initialize end_pos to window_pos
            self.first_run = True
            
            #internal variables
            self.window_display_name = self.window_name.split("##")[0]
            self.window_name_size : tuple[float, float] = PyImGui.calc_text_size(self.window_display_name)
            
            self.open = True
            self.theme : StyleTheme | None = forced_theme
            
            self.__geometry_ready : bool = False
            
            self.__decorated_window_min_size = (self.window_name_size[0] + 40, 32.0) # Internal use only
            self.__decorators_left = window_pos[0] - 15 # Internal use only
            self.__decorators_top = window_pos[1] - (26) # Internal use only
            
            self.__decorators_right = self.__decorators_left + window_size[0] + 30 # Internal use only
            self.__decorators_bottom = self.__decorators_top + window_size[1] + 14 + (26) # Internal use only
            
            self.__decorators_width = self.__decorators_right - self.__decorators_left # Internal use only
            self.__decorators_height = self.__decorators_bottom - self.__decorators_top # Internal use only
            
            self.__close_button_rect = (self.__decorators_right - 29, self.__decorators_top + 9, 11, 11) # Internal use only
            self.__title_bar_rect = (self.__decorators_left + 5, self.__decorators_top + 2, self.__decorators_width - 10, 26) # Internal use only
            
            self.__resize = False # Internal use only
            self.__set_focus = False # Internal use only

            self.__dragging = False # Internal use only
            self.__drag_started = False # Internal use only
            #endregion

            #debug variables
            self.collapsed_status = True
            self.tracking_position = self.window_pos
            
            WindowModule._windows[self.window_name] = self
            
        def get_theme(self) -> StyleTheme:
            """
            Returns the current theme of the ImGui module.
            """

            theme = self.theme if self.theme else ImGui.get_style().Theme

            return theme
             

        def initialize(self):
            if not self.module_name:
                return
            
            if self.first_run:
                PyImGui.set_next_window_size(self.window_size[0], self.window_size[1])     
                PyImGui.set_next_window_pos(self.window_pos[0], self.window_pos[1])
                PyImGui.set_next_window_collapsed(self.collapse, PyImGui.ImGuiCond.Always)
                self.first_run = False                

        def begin(self, p_open: Optional[bool] = None, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> bool:   
            self.__current_theme = self.get_theme()
                                  
            if p_open is not None:
                self.open = p_open
                
            if flags != PyImGui.WindowFlags.NoFlag:
                self.window_flags = flags
        
            is_expanded = not self.collapse
            is_first_run = self.first_run
            
            self.can_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.NoResize)) == 0 and (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) == 0
            
            if self.first_run:
                self.initialize()
                            
            match (self.__current_theme):
                case StyleTheme.Guild_Wars:
                    has_always_auto_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) != 0
                    
                    internal_flags = int(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoBackground) | int(self.window_flags)
                    self.__dragging = PyImGui.is_mouse_dragging(0, -1) and self.__dragging and self.__drag_started
                    if not PyImGui.is_mouse_dragging(0, -1) and not PyImGui.is_mouse_down(0):
                        self.__drag_started = False
                                
                    if self.open and is_expanded: 
                        if not is_first_run:
                            if self.__resize or self.window_size[0] < self.__decorated_window_min_size[0] or self.window_size[1] < self.__decorated_window_min_size[1]:
                                if not has_always_auto_resize:
                                    self.window_size = (max(self.__decorated_window_min_size[0], self.window_size[0]), max(self.__decorated_window_min_size[1], self.window_size[1]))
                                    PyImGui.set_next_window_size((self.window_size[0], self.window_size[1]), PyImGui.ImGuiCond.Always)    
                                            
                                self.__resize = False
                                                
                    if not is_expanded:
                        # Remove PyImGui.WindowFlags.MenuBar and PyImGui.WindowFlags.AlwaysAutoResize from internal_flags when not expanded
                        internal_flags &= ~int(PyImGui.WindowFlags.MenuBar)
                        internal_flags &= ~int(PyImGui.WindowFlags.AlwaysAutoResize)
                        internal_flags |= int(PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse| PyImGui.WindowFlags.NoResize| PyImGui.WindowFlags.NoMouseInputs)
                        
                    if self.__set_focus:
                        internal_flags &= ~int(PyImGui.WindowFlags.AlwaysAutoResize)
                                                                 
                        
                    PyImGui.set_next_window_collapsed(self.collapse, PyImGui.ImGuiCond.Always)
                    _, open = PyImGui.begin_with_close(name = self.window_name, p_open=self.open, flags=internal_flags)
                                            
                    self.open = open         
                                    
                    if self.__set_focus and not self.__dragging and not self.__drag_started:
                        PyImGui.set_window_focus(self.window_name)
                        self.__set_focus = False
                    
                    if self.__dragging:
                        PyImGui.set_window_focus(self.window_name)
                        PyImGui.set_window_focus(f"{self.window_name}##titlebar_fake")

                    if self.open and self.__geometry_ready:
                        self.__draw_decorations()

                    # PyImGui.pop_style_var(1)
                    
                    if has_always_auto_resize:                    
                        cursor = PyImGui.get_cursor_pos()
                        PyImGui.dummy(int(self.window_name_size[0] + 20), 0)
                        PyImGui.set_cursor_pos(cursor[0], cursor[1])
                                    
                case _:  
                    if self.can_close:
                        expanded, self.open = PyImGui.begin_with_close(name = self.window_name, p_open=self.open, flags=self.window_flags)
                        self.collapse = not expanded
                    else:
                        self.collapse = not PyImGui.begin(self.window_name, self.window_flags)
                        self.open = True                   
                        
            if is_expanded and not self.collapse and self.open and not self.__dragging:
                self.window_size = PyImGui.get_window_size()
                          

            self.window_pos = PyImGui.get_window_pos()
            self.__get_geometry()

            return self.open and not self.collapse
        

        def process_window(self):
            self.collapsed_status = PyImGui.is_window_collapsed()
            self.end_pos = PyImGui.get_window_pos()

        def end(self):
            # PyImGui.pop_clip_rect()
            PyImGui.end()
        
        def __get_geometry(self):
            self.__geometry_ready = True
            has_title_bar = (int(self.window_flags) & int(PyImGui.WindowFlags.NoTitleBar)) == 0
        
            window_pos = self.window_pos
            window_size = self.window_size      
            title_bar_height = 32 if has_title_bar else 0                              
            
            self.__window_decorator_rect = (
                window_pos[0] - 10,
                window_pos[1],
                window_size[0] + 20,
                window_size[1] + 10
                )
            
            self.__title_bar_rect = (
                self.__window_decorator_rect[0],
                self.__window_decorator_rect[1] - title_bar_height,
                self.__window_decorator_rect[2],
                title_bar_height
            )
            
            self.__faketitle_bar_rect = (
                self.__window_decorator_rect[0],
                self.__window_decorator_rect[1] - title_bar_height + 5,
                self.__window_decorator_rect[2],
                title_bar_height - 2
            )
            
            self.__title_text_rect = (
                self.__faketitle_bar_rect[0] + 15,
                self.__faketitle_bar_rect[1] + ((self.__faketitle_bar_rect[3] - self.window_name_size[1])/2),
                self.window_name_size[0],
                    self.window_name_size[1]
            )
            
            self.__close_button_rect = (
                self.__faketitle_bar_rect[0] + self.__faketitle_bar_rect[2] - 25,
                self.__faketitle_bar_rect[1] + 9,
                13,
                13
            )
            
            self.__window_clip_rect = (
                self.__title_bar_rect[0],
                self.__title_bar_rect[1],
                self.__title_bar_rect[0] + self.__title_bar_rect[2],                
                self.__title_bar_rect[1] + self.__title_bar_rect[3] + self.__window_decorator_rect[2],
            )
        
        def __draw_decorations(self): 
            has_title_bar = (int(self.window_flags) & int(PyImGui.WindowFlags.NoTitleBar)) == 0
            
            close_button_state = TextureState.Normal     
            if ImGui.is_mouse_in_rect(self.__close_button_rect) and ((int(self.window_flags) & int(PyImGui.WindowFlags.NoMouseInputs)) == 0):
                if PyImGui.is_mouse_down(0):
                    close_button_state = TextureState.Active
                else:
                    close_button_state = TextureState.Hovered
            
            PyImGui.push_clip_rect(*self.__window_clip_rect, False)  
            if not self.collapse and self.open: 
                window_texture = ThemeTextures.Window
                if not self.can_resize and not has_title_bar:
                    window_texture = ThemeTextures.Window_NoResize_NoTitleBar  
                elif not self.can_resize:
                    window_texture = ThemeTextures.Window_NoResize
                elif not has_title_bar:
                    window_texture = ThemeTextures.Window_NoTitleBar
                    
                if has_title_bar:                    
                    ThemeTextures.Title_Bar.value.get_texture().draw_in_drawlist(
                        x=self.__title_bar_rect[0],
                        y=self.__title_bar_rect[1],
                        size=self.__title_bar_rect[2:]
                    )
                    
                    if self.can_close:
                        ThemeTextures.Close_Button.value.get_texture().draw_in_drawlist(
                            x=self.__close_button_rect[0],
                            y=self.__close_button_rect[1],
                            size=self.__close_button_rect[2:],
                            state=close_button_state
                        )
                                                              
                    self.__draw_title_bar_fake(self.__faketitle_bar_rect)
                        
                    # Draw the title text
                    PyImGui.push_clip_rect(
                        *self.__title_text_rect,
                        False
                    )
                    
                    PyImGui.draw_list_add_text(
                        *self.__title_text_rect[:2],    
                        style.Text.color_int,
                        self.window_display_name
                    )                    
                    PyImGui.pop_clip_rect()
                    
                window_texture.value.get_texture().draw_in_drawlist(
                    x=self.__window_decorator_rect[0],                         
                    y=self.__window_decorator_rect[1],
                    size=self.__window_decorator_rect[2:]
                )
                    

            else:      
                if self.resize_on_collapse:
                    pass #TODO: Resize title bar when collapsed
                                  
                if has_title_bar:         
                    ThemeTextures.Title_Bar_Collapsed.value.get_texture().draw_in_drawlist(
                        x=self.__title_bar_rect[0],
                        y=self.__title_bar_rect[1],
                        size=(self.__title_bar_rect[2], self.__title_bar_rect[3])
                    )
                    
                    if self.can_close:
                        ThemeTextures.Close_Button.value.get_texture().draw_in_drawlist(
                            x=self.__close_button_rect[0],
                            y=self.__close_button_rect[1],
                            size=self.__close_button_rect[2:],
                            state=close_button_state
                        )
                                                              
                    self.__draw_title_bar_fake(self.__faketitle_bar_rect)
                        
                    # Draw the title text
                    PyImGui.push_clip_rect(
                        *self.__title_text_rect,
                        False
                    )
                    
                    PyImGui.draw_list_add_text(
                        *self.__title_text_rect[:2],    
                        style.Text.color_int,
                        self.window_display_name
                    )                    
                    PyImGui.pop_clip_rect()                

            PyImGui.pop_clip_rect()
            
        def __draw_title_bar_fake(self, title_bar_rect):  
            can_interact = (int(self.window_flags) & int(PyImGui.WindowFlags.NoMouseInputs)) == 0
            
            PyImGui.set_next_window_pos(title_bar_rect[0], title_bar_rect[1])
            PyImGui.set_next_window_size(title_bar_rect[2], title_bar_rect[3])

            flags = (
                    PyImGui.WindowFlags.NoCollapse |
                    PyImGui.WindowFlags.NoTitleBar |
                    PyImGui.WindowFlags.NoScrollbar |
                    PyImGui.WindowFlags.NoScrollWithMouse |
                    PyImGui.WindowFlags.AlwaysAutoResize 
                    | PyImGui.WindowFlags.NoBackground
                )
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, -1, -0)
            ImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 1, 0, 0.0))  # Fully transparent
            PyImGui.begin(f"{self.window_name}##titlebar_fake", flags)
            PyImGui.invisible_button("##titlebar_dragging_area_1", title_bar_rect[2] - (30 if self.can_close else 0), title_bar_rect[3])
            self.__dragging = (PyImGui.is_item_active() or self.__dragging) and can_interact
                        
            if PyImGui.is_item_focused():
                self.__set_focus = True
                
            PyImGui.set_cursor_screen_pos(self.__close_button_rect[0] + self.__close_button_rect[2], self.__close_button_rect[1] + self.__close_button_rect[3])
            PyImGui.invisible_button("##titlebar_dragging_area_2", 15, title_bar_rect[3])
            self.__dragging = (PyImGui.is_item_active() or self.__dragging) and can_interact
                    
            if PyImGui.is_item_focused():
                self.__set_focus = True
                
            # Handle Double Click to Expand/Collapse
            if PyImGui.is_mouse_double_clicked(0) and self.__set_focus:
                can_collapse = (int(self.window_flags) & int(PyImGui.WindowFlags.NoCollapse)) == 0                
                if can_collapse and can_interact:
                    self.collapse = not self.collapse

                    if not self.collapse:
                        self.__resize = True

            if self.can_close:
                PyImGui.set_cursor_screen_pos(self.__close_button_rect[0], self.__close_button_rect[1])
                if PyImGui.invisible_button(f"##Close", self.__close_button_rect[2] + 1, self.__close_button_rect[3] + 1) and can_interact:
                    self.open = False
                    self.__set_focus = False
                    
                    
            PyImGui.end()
            ImGui.pop_style_color(1)
            PyImGui.pop_style_var(1)
                                
            # Handle dragging
            if self.__dragging:   
                can_drag = (int(self.window_flags) & int(PyImGui.WindowFlags.NoMove)) == 0
        
                if can_drag:
                    if self.__drag_started:                    
                        delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                        new_window_pos = (title_bar_rect[0] + 10 + delta[0], title_bar_rect[1] + title_bar_rect[3] - 3 + delta[1])
                        PyImGui.reset_mouse_drag_delta(0)
                        PyImGui.set_window_pos(new_window_pos[0], new_window_pos[1], PyImGui.ImGuiCond.Always)
                    else:
                        self.__drag_started = True
                else:
                    self.__dragging = False
                    self.__drag_started = False
         
         
window_module = WindowModule(
    MODULE_NAME,
    window_name="Style Manager",
    window_size=window_size,
    window_pos=window_pos,
    collapse=collapse,
    window_flags=PyImGui.WindowFlags.NoFlag,
    can_close=True,
)

py4_gw_ini_handler = IniHandler("Py4GW.ini")
selected_theme = Style.StyleTheme[py4_gw_ini_handler.read_key(
    "settings", "style_theme", Style.StyleTheme.ImGui.name)]

force_theme_override = py4_gw_ini_handler.read_bool(
    "settings", "force_theme_override", False)

if force_theme_override:
    for theme in Style.StyleTheme:
        file_path = os.path.join("Styles", f"{theme.name}.json")
        if os.path.exists(file_path):
            time_stamp = datetime.now().strftime("%Y-%m-%d")
            new_file_path = file_path[:-5] + "-" + time_stamp + ".backup.json"
            os.rename(file_path, new_file_path)
    
    py4_gw_ini_handler.write_key("settings", "force_theme_override", "False")

themes = [theme.name.replace("_", " ") + ( f" (Textured)" if theme in ImGui.Textured_Themes else "") for theme in Style.StyleTheme]

org_style: Style.Style = ImGui.Selected_Style.copy()
mouse_down_timer = ThrottledTimer(125)
input_int_value = 150
input_float_value = 150.0
input_text_value = "Text"
search_value = ""
control_compare = False
theme_compare = False
match_style_vars = False
is_first_run = True

widget_handler = WidgetHandler()
module_info = None

class preview_states:
    def __init__(self):
        self.input_int_value = 150
        self.input_float_value = 150.0
        self.input_text_value = "Text"
        self.search_value = ""
        self.combo = 0
        self.toggle_button_1 = True
        self.toggle_button_2 = False
        self.toggle_button_3 = False
        self.toggle_button_4 = False
        self.image_toggle_button_1 = True
        self.image_toggle_button_2 = False
        self.image_toggle_button_3 = False
        self.image_toggle_button_4 = False
        self.icon_toggle_button_1 = True
        self.icon_toggle_button_2 = False
        self.icon_toggle_button_3 = False
        self.icon_toggle_button_4 = False
        self.objective_1 = True
        self.objective_2 = False
        self.checkbox = True
        self.checkbox_2 = False
        self.radio_button = 0
        self.slider_int = 25
        self.slider_float = 33.0
        
        self.theme_1 = Style.StyleTheme.ImGui
        self.theme_2 = Style.StyleTheme.Guild_Wars
        self.theme_3 = Style.StyleTheme.Minimalus

class ThemeTexturesDev(Enum):
    pass
    
class ImGuiDev:
    pass


preview = preview_states()

textures = [
    ("Textures/Item Models/17081-Battle_Commendation.png",
     ControlAppearance.Default, True),
    ("Textures/Item Models/00514-Molten_Heart.png",
     ControlAppearance.Primary, True),
    ("Textures/Item Models/00035-Bag.png", ControlAppearance.Danger, True),
    ("Textures/Item Models/30855-Bottle_of_Grog.png",
     ControlAppearance.Default, False),
]


def draw_button(theme: Style.StyleTheme):

    ImGui.button("Default" + "##" + theme.name)
    PyImGui.same_line(0, 5)
    ImGui.button("Primary" + "##" + theme.name,
                 appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGui.button("Danger" + "##" + theme.name,
                 appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGui.button("Disabled" + "##" + theme.name, disabled=True)


def draw_small_button(theme: Style.StyleTheme):
    ImGui.small_button("Default" + "##" + theme.name)
    PyImGui.same_line(0, 5)
    ImGui.small_button("Primary" + "##" + theme.name,
                       appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGui.small_button("Danger" + "##" + theme.name,
                       appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGui.small_button("Disabled" + "##" + theme.name, disabled=True)

def draw_icon_button(theme: Style.StyleTheme):
    ImGui.icon_button(IconsFontAwesome5.ICON_SYNC + " With Text" + "##" + theme.name)
    PyImGui.same_line(0, 5)
    ImGui.icon_button(IconsFontAwesome5.ICON_SYNC + "##" + theme.name)
    PyImGui.same_line(0, 5)
    ImGui.icon_button(IconsFontAwesome5.ICON_SYNC + "##" +
                      theme.name, appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGui.icon_button(IconsFontAwesome5.ICON_SYNC + "##" +
                      theme.name, appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGui.icon_button(
        IconsFontAwesome5.ICON_SYNC, disabled=True)


def draw_icon_toggle_button(theme: Style.StyleTheme):
    preview.icon_toggle_button_1 = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_SYNC) + " With Text" + "##toggle_icon_button" + theme.name, preview.icon_toggle_button_1)
    PyImGui.same_line(0, 5)
    preview.icon_toggle_button_2 = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_TOGGLE_ON if preview.icon_toggle_button_2 else IconsFontAwesome5.ICON_TOGGLE_OFF) + "##toggle_icon_button" + theme.name, preview.icon_toggle_button_2)
    PyImGui.same_line(0, 5)
    preview.icon_toggle_button_3 = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_EYE if preview.icon_toggle_button_3 else IconsFontAwesome5.ICON_EYE_SLASH) + "##toggle_icon_button" +
                      theme.name, preview.icon_toggle_button_3)


def draw_toggle_button(theme: Style.StyleTheme):
    preview.toggle_button_1 = ImGui.toggle_button(
        ("On" if preview.toggle_button_1 else "Off") + "##Toggle" + theme.name, preview.toggle_button_1)
    PyImGui.same_line(0, 5)
    preview.toggle_button_2 = ImGui.toggle_button(
        ("On" if preview.toggle_button_2 else "Off") + "##Toggle2" + theme.name, preview.toggle_button_2)
    PyImGui.same_line(0, 5)
    preview.toggle_button_3 = ImGui.toggle_button(
        "Disabled" + "##Toggle3" + theme.name, preview.toggle_button_3, disabled=True)


def draw_image_toggle(theme: Style.StyleTheme):
    preview.image_toggle_button_1 = ImGui.image_toggle_button(
        ("On" if preview.image_toggle_button_1 else "Off") + "##ImageToggle_1" + theme.name, texture_path=textures[0][0], v=preview.image_toggle_button_1)
    PyImGui.same_line(0, 5)
    preview.image_toggle_button_2 = ImGui.image_toggle_button(
        ("On" if preview.image_toggle_button_2 else "Off") + "##ImageToggle_2" + theme.name, texture_path=textures[1][0], v=preview.image_toggle_button_2)
    PyImGui.same_line(0, 5)
    preview.image_toggle_button_3 = ImGui.image_toggle_button(
        ("On" if preview.image_toggle_button_3 else "Off") + "##ImageToggle_3" + theme.name, texture_path=textures[2][0], v=preview.image_toggle_button_3, disabled=True)


def draw_image_button(theme: Style.StyleTheme):
    for (texture, appearance, enabled) in textures:
        ImGui.image_button("Image Button" + "##" + theme.name +
                           texture, texture, appearance=appearance, disabled=not enabled)
        PyImGui.same_line(0, 5)


def draw_combo(theme: Style.StyleTheme):
    preview.combo = ImGui.combo("Combo##" + theme.name, preview.combo, [
                                "Option 1", "Option 2", "Option 3"])


def draw_checkbox(theme: Style.StyleTheme):
    preview.checkbox_2 = ImGui.checkbox(
        "##Checkbox 2" + "##" + theme.name, preview.checkbox_2)
    PyImGui.same_line(0, 5)
    preview.checkbox = ImGui.checkbox(
        "Checkbox" + "##" + theme.name, preview.checkbox)


def draw_radio_button(theme: Style.StyleTheme):
    preview.radio_button = ImGui.radio_button(
        "Option 1##Radio Button 1" + "##" + theme.name, preview.radio_button, 0)
    preview.radio_button = ImGui.radio_button(
        "Option 2##Radio Button 2" + "##" + theme.name, preview.radio_button, 1)
    preview.radio_button = ImGui.radio_button(
        "Option 3##Radio Button 3" + "##" + theme.name, preview.radio_button, 2)


def draw_slider(theme: Style.StyleTheme):
    preview.slider_int = ImGui.slider_int(
        "Slider Int##" + theme.name, preview.slider_int, 0, 100)
    preview.slider_float = ImGui.slider_float(
        "Slider Float##" + theme.name, preview.slider_float, 0.0, 100.0)


def draw_input(theme: Style.StyleTheme):
    changed, preview.search_value = ImGui.search_field(
        "Search##" + theme.name, preview.search_value)
    preview.input_text_value = ImGui.input_text(
        "Text##" + theme.name, preview.input_text_value)
    preview.input_float_value = ImGui.input_float(
        "Float##" + theme.name, preview.input_float_value)
    preview.input_int_value = ImGui.input_int(
        "Int##3" + theme.name, preview.input_int_value, 0, 10000, 0)
    preview.input_int_value = ImGui.input_int(
        "Int Buttons##2" + theme.name, preview.input_int_value)


def draw_separator(theme: Style.StyleTheme):
    ImGui.separator()


def draw_progress_bar(theme: Style.StyleTheme):
    ImGui.progress_bar(0.25, 0, 20, "25 points")


def draw_text(theme: Style.StyleTheme):
    ImGui.text("This is some text.")


def draw_hyperlink(theme: Style.StyleTheme):
    ImGui.hyperlink("Click Me")


def draw_bullet_text(theme: Style.StyleTheme):
    ImGui.bullet_text("Bullet Text 1")
    ImGui.bullet_text("Bullet Text 2")


def draw_objective_text(theme: Style.StyleTheme):
    preview.objective_1 = ImGui.objective_text(
        "Objective 1", preview.objective_1)
    preview.objective_2 = ImGui.objective_text(
        "Objective 2", preview.objective_2)


def draw_tree_node(theme: Style.StyleTheme):
    if ImGui.tree_node("Tree Node 1##" + theme.name):
        if ImGui.tree_node("Tree Node 1.1##" + theme.name):
            ImGui.text("This is a tree node content.")
            ImGui.tree_pop()

        ImGui.tree_pop()


def draw_collapsing_header(theme: Style.StyleTheme):
    if ImGui.collapsing_header("Collapsing Header##" + theme.name, 0):
        ImGui.text("This is a collapsible header content.")


def draw_child(theme: Style.StyleTheme):
    if ImGui.begin_child("Child##" + theme.name, (0, 68), True, PyImGui.WindowFlags.AlwaysHorizontalScrollbar):
        ImGui.text("This is a child content.")
        ImGui.text("This is a child content.")
        ImGui.text("This is a child content.")
        ImGui.text("This is a child content.")
        ImGui.text("This is a child content.")
    ImGui.end_child()


def draw_tab_bar(theme: Style.StyleTheme):
    if ImGui.begin_tab_bar("Tab Bar PyImGui##" + theme.name):
        if ImGui.begin_tab_item("Tab 1##" + theme.name):
            ImGui.text("Content for Tab 1")
            PyImGui.end_tab_item()

        if ImGui.begin_tab_item("Tab 2##" + theme.name):
            ImGui.text("Content for Tab 2")
            PyImGui.end_tab_item()

        ImGui.end_tab_bar()


controls = {
    "Button": draw_button,
    "Small Button": draw_small_button,
    "Icon Button": draw_icon_button,
    "Icon Toggle Button": draw_icon_toggle_button,
    "Toggle Button": draw_toggle_button,
    "Image Toggle Button": draw_image_toggle,
    "Image Button": draw_image_button,
    "Combo": draw_combo,
    "Checkbox": draw_checkbox,
    "Radio Button": draw_radio_button,
    "Slider": draw_slider,
    "Input": draw_input,
    "Separator": draw_separator,
    "Progress Bar": draw_progress_bar,
    "Text": draw_text,
    "Hyperlink": draw_hyperlink,
    "Bullet Text": draw_bullet_text,
    "Objective Text": draw_objective_text,
    "Tree Node": draw_tree_node,
    "Collapsing Header": draw_collapsing_header,
    "Child & Scrollbars": draw_child,
    "Tab Bar": draw_tab_bar,
}


def DrawThemeCompare():
    global match_style_vars, preview, themes, theme_compare
    name = "Theme Compare"
    
    if theme_compare and ImGui.WindowModule._windows.get(name, None) and not ImGui.WindowModule._windows[name].open:
        ImGui.WindowModule._windows[name].open = True
    
    if ImGui.begin_with_close(name):
        window_size = PyImGui.get_window_size()
        
        if window_size[1] > 100:
            comparing_themes = [preview.theme_1, preview.theme_2, preview.theme_3]

            PyImGui.push_item_width(150)
            style = ImGui.get_style()

            # region Header
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 4, 8)
            if ImGui.begin_table("Control Preview#Header", 4, PyImGui.TableFlags.BordersOuterH, 0, 30):
                PyImGui.table_setup_column(
                    "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Guild Wars", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Minimalus", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                checked = ImGui.checkbox("Match Style Vars", match_style_vars)
                if checked != match_style_vars:
                    match_style_vars = checked

                    for theme in comparing_themes:
                        ImGui.reload_theme(theme)

                if match_style_vars:
                    for theme in comparing_themes:
                        s = ImGui.Styles[theme]

                        for var_enum, var in s.StyleVars.items():
                            var.value1 = style.StyleVars[var_enum].value1
                            var.value2 = style.StyleVars[var_enum].value2

                PyImGui.table_next_column()

                theme_1 = ImGui.combo(preview.theme_1.name + "##theme_1", preview.theme_1.value, themes)
                if theme_1 != preview.theme_1.value:
                    preview.theme_1 = Style.StyleTheme(theme_1)
                    ImGui.reload_theme(preview.theme_1)
                    
                PyImGui.table_next_column()


                theme_2 = ImGui.combo(preview.theme_2.name + "##theme_2", preview.theme_2.value, themes)
                if theme_2 != preview.theme_2.value:
                    preview.theme_2 = Style.StyleTheme(theme_2)
                    ImGui.reload_theme(preview.theme_2)
                    
                PyImGui.table_next_column()

                theme_3 = ImGui.combo(preview.theme_3.name + "##theme_3", preview.theme_3.value, themes)
                if theme_3 != preview.theme_3.value:
                    preview.theme_3 = Style.StyleTheme(theme_3)
                    ImGui.reload_theme(preview.theme_3)
                    
                ImGui.end_table()
            PyImGui.pop_style_var(1)
            # endregion

            if ImGui.begin_table("Theme Compare Control Preview", len(comparing_themes) + 1, PyImGui.TableFlags.ScrollX | PyImGui.TableFlags.ScrollY):
                PyImGui.table_setup_column(
                    "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Guild Wars", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Minimalus", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                for control_name, control_draw_func in controls.items():
                    ImGui.text(control_name)
                    PyImGui.table_next_column()

                    for style in comparing_themes:
                        ImGui.push_theme(style)
                        control_draw_func(style)
                        ImGui.pop_theme()
                        PyImGui.table_next_column()
                    
                ImGui.end_table()

            PyImGui.pop_item_width()
            
    ImGui.end()

    if not ImGui.WindowModule._windows[name].open:
        theme_compare = False

def DrawControlCompare():
    global theme_compare, control_compare, style, window_width, window_height, save_throttle_timer, save_throttle_time, module_info
    
    name = "Control Compare"
    
    if theme_compare and ImGui.WindowModule._windows.get(name, None) and not ImGui.WindowModule._windows[name].open:
        ImGui.WindowModule._windows[name].open = True
        
    if ImGui.begin_with_close(name):
        window_size = PyImGui.get_window_size()
        
        if window_size[1] > 100:

            PyImGui.push_item_width(150)
            style = ImGui.get_style()

            if ImGui.begin_table("Control Compare Control Preview", 4, PyImGui.TableFlags.ScrollX):
                PyImGui.table_setup_column(
                    "ControlName", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "PyImgui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "ImGui Style Pushed", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                ImGui.text("Control")
                PyImGui.table_next_column()             
                
                ImGui.end_table()
            PyImGui.pop_item_width()
            
    ImGui.end()
    
    if not ImGui.WindowModule._windows[name].open:
        control_compare = False

def on_enable():
    global selected_theme
    selected_theme = Style.StyleTheme[py4_gw_ini_handler.read_key(
        "settings", "style_theme", Style.StyleTheme.ImGui.name)]
    set_theme(selected_theme)
        
def DrawWindow():
    global theme_compare, control_compare, style, window_width, window_height, save_throttle_timer, save_throttle_time, module_info, widget_handler
    
    style = ImGui.get_style()
    
    if window_module.begin():       
        is_textured = style.Theme in ImGui.Textured_Themes
        tool_tip_visible = False
        
        if PyImGui.begin_child("Theme Buttons", (0, 80), True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
            if PyImGui.begin_child("Theme Selector Header", (0, 24), False, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
                cursor_y = PyImGui.get_cursor_pos_y()
                PyImGui.set_cursor_pos_y(cursor_y + 5)
                ImGui.text("Selected Theme")
                disclaimer_text = "This is a textured theme which can cause performance issues on some systems.\nIf you experience any issues please consider switching to a non-textured theme."
                
                if is_textured:
                    ImGui.push_font("Regular", 10)
                    PyImGui.same_line(0, 5)
                    style.Text.push_color((240, 75, 75, 255))                    
                    ImGui.text(IconsFontAwesome5.ICON_EXCLAMATION_CIRCLE if is_textured else "")
                    style.Text.pop_color()      
                    ImGui.pop_font()
                    
                    if is_textured:
                        ImGui.show_tooltip(disclaimer_text)
                    
                    
                PyImGui.set_cursor_pos(125, cursor_y)
                
                # PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
                remaining = PyImGui.get_content_region_avail()
                PyImGui.push_item_width(remaining[0] - 30)
                value = ImGui.combo("##theme_selector",
                                    ImGui.Selected_Style.Theme.value, themes)

                if is_textured:
                    ImGui.show_tooltip(disclaimer_text)
                
                if value != ImGui.Selected_Style.Theme.value:
                    theme = Style.StyleTheme(value)
                    set_theme(theme)
                    py4_gw_ini_handler.write_key(
                        "settings", "style_theme", ImGui.Selected_Style.Theme.name)

                PyImGui.same_line(0, 5)
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + (2 if style.Theme is StyleTheme.Minimalus else 0))
                theme_compare = ImGui.checkbox(
                    "##show_theme_compare", theme_compare)        
                ImGui.show_tooltip(
                    "Show Theme Compare window")
            
            PyImGui.end_child()
            
            ImGui.separator()
            
            remaining = PyImGui.get_content_region_avail()
            button_width = (remaining[0] - 7) / 2
            
            any_changed = is_style_modified()
            if ImGui.button("Save Changes", button_width, disabled=not any_changed):
                ImGui.Selected_Style.save_to_json()    
                set_theme(ImGui.Selected_Style.Theme)

            PyImGui.same_line(0, 5)

            if ImGui.button("Reset to Default", button_width):
                theme = ImGui.Selected_Style.Theme
                ImGui.Selected_Style.delete()
                set_theme(theme)

        PyImGui.end_child()

        column_width = 0
        item_width = 0

        def table_separator_header(title: str, font_size: int = 20, font_family: str = "Regular", color: Optional[tuple] = None, tooltip: Optional[str] = None):
            PyImGui.spacing()
            PyImGui.spacing()
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            color = color or ImGui.Selected_Style.TextTreeNode.color_tuple

            if color:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)

            ImGui.push_font(font_family, font_size)
            PyImGui.text(title)

            if tooltip:
                ImGui.show_tooltip(tooltip)

            ImGui.pop_font()

            if color:
                PyImGui.pop_style_color(1)

            PyImGui.table_next_row()
            for _ in range(4):
                PyImGui.separator()
                PyImGui.table_next_column()

        if ImGui.begin_tab_bar("Style Customization"):
            if ImGui.begin_tab_item("Style Customization"):                    
                if PyImGui.is_rect_visible(0, 10):
                    style.CellPadding.push_style_var(4, 2)
                    style.ItemInnerSpacing.push_style_var(4, 2)
                    
                    if PyImGui.begin_table("Style Variables", 3, PyImGui.TableFlags.ScrollY):
                        PyImGui.table_setup_column(
                            "Variable", PyImGui.TableColumnFlags.WidthFixed, 250)
                        PyImGui.table_setup_column(
                            "Value", PyImGui.TableColumnFlags.WidthStretch)
                        PyImGui.table_setup_column(
                            "Undo", PyImGui.TableColumnFlags.WidthFixed, 35)

                        table_separator_header("Style Vars")

                        for enum, var in ImGui.Selected_Style.StyleVars.items():
                            PyImGui.set_cursor_pos_y(
                                PyImGui.get_cursor_pos_y() + 5)
                            ImGui.text(f"{var.display_name or enum}")
                            PyImGui.table_next_column()

                            column_width = column_width or PyImGui.get_content_region_avail()[
                                0]
                            item_width = item_width or (
                                column_width - 5) / 2
                            PyImGui.push_item_width(item_width)
                            var.value1 = ImGui.input_float(
                                f"##{enum}_value1", var.value1)

                            if var.value2 is not None:
                                PyImGui.same_line(0, 5)

                                PyImGui.push_item_width(item_width)
                                var.value2 = ImGui.input_float(
                                    f"##{enum}_value2", var.value2)

                            PyImGui.table_next_column()

                            changed = org_style.StyleVars[
                                enum].value1 != var.value1 or org_style.StyleVars[enum].value2 != var.value2

                            if changed:
                                if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                    var.value1 = org_style.StyleVars[enum].value1
                                    var.value2 = org_style.StyleVars[enum].value2

                            PyImGui.table_next_column()
                            
                        table_separator_header("Colors")
                        
                        colors = {**ImGui.Selected_Style.Colors, **ImGui.Selected_Style.CustomColors, **ImGui.Selected_Style.TextureColors}
                        colors = dict(sorted(colors.items(), key=lambda item: item[1].display_name or item[0]))

                        for col_name, col in colors.items():
                            ImGui.text(col.display_name or col_name)
                            PyImGui.table_next_column()

                            column_width = column_width or PyImGui.get_content_region_avail()[
                                0]
                            PyImGui.push_item_width(column_width)

                            new_color = PyImGui.color_edit4(
                                col_name, col.color_tuple)
                            if new_color:
                                col.set_tuple_color(new_color)

                            PyImGui.pop_item_width()
                            PyImGui.table_next_column()
                            
                            match(col.color_type):
                                case StyleColorType.Default:
                                    org_color = org_style.Colors.get(col_name, None)
                                    
                                case StyleColorType.Custom:
                                    org_color = org_style.CustomColors.get(col_name, None)
                                    
                                case StyleColorType.Texture:
                                    org_color = org_style.TextureColors.get(col_name, None)

                            if org_color:
                                show_button = col.color_int != org_color.color_int

                                if show_button:
                                    if ImGui.icon_button(IconsFontAwesome5.ICON_UNDO + "##" + col_name, 25, 25):
                                        col.set_rgba(
                                            *org_color.rgb_tuple)

                            PyImGui.table_next_column()

                        PyImGui.end_table()
                    
                    style.CellPadding.pop_style_var()
                    style.ItemInnerSpacing.pop_style_var()
                    
                if not PyImGui.is_any_item_active():
                    ImGui.Selected_Style.apply_to_style_config()    
                    
                ImGui.end_tab_item()

            if ImGui.begin_tab_item("Control Preview"):
                style = ImGui.get_style()

                if PyImGui.is_rect_visible(50, 50):
                    column_width = 0
                    item_width = 0

                    PyImGui.push_item_width(150)
                    if ImGui.begin_table("Control Preview Tab Control Preview", 2, PyImGui.TableFlags.ScrollX):
                        PyImGui.table_setup_column(
                            "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                        PyImGui.table_setup_column(
                            "Preview", PyImGui.TableColumnFlags.WidthStretch)

                        PyImGui.table_next_row()
                        PyImGui.table_next_column()

                        for control_name, control_draw_func in controls.items():
                            ImGui.text(control_name)
                            PyImGui.table_next_column()

                            control_draw_func(style.Theme)
                            PyImGui.table_next_column()

                        ImGui.end_table()
                    PyImGui.pop_item_width()
                ImGui.end_tab_item()

            ImGui.end_tab_bar()

        window_module.process_window()
            
        if control_compare:
            # DrawControlCompare()
            pass

        if theme_compare:
            DrawThemeCompare()
            pass
        
    window_module.end()    
    
    if not window_module.open:
        WidgetHandler().set_widget_configuring(MODULE_NAME, False)

    pass

def is_style_modified():
    for k, col in ImGui.Selected_Style.Colors.items():
        org_color = org_style.Colors.get(k, None)
        if org_color and col.color_int != org_color.color_int:
            return True
        
    for k, col in ImGui.Selected_Style.CustomColors.items():
        org_color = org_style.CustomColors.get(k, None)
        if org_color and col.color_int != org_color.color_int:
            return True

    for k, col in ImGui.Selected_Style.TextureColors.items():
        org_color = org_style.TextureColors.get(k, None)
        if org_color and col.color_int != org_color.color_int:
            return True

    for k, col in ImGui.Selected_Style.StyleVars.items():
        org_var = org_style.StyleVars.get(k, None)
        
        if org_var and col != org_var:
            return True
        
    return False

def set_theme(theme):
    global org_style
    
    ImGui.reload_theme(theme)
    ImGui.set_theme(theme)            
    org_style = ImGui.Selected_Style.copy()

def configure():
    global module_info
    
    if not module_info:
        module_info = widget_handler.get_widget_info(MODULE_NAME)
    
    pass

def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, window_module, module_info

    window_module.open = module_info["configuring"] if module_info else False
    
    try:
        if window_module.open:
            DrawWindow()

    except Exception as e:
        Py4GW.Console.Log(
            MODULE_NAME, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

__all__ = ['main', 'configure', 'on_enable']