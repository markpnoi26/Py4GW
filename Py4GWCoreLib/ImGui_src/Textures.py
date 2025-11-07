from dataclasses import dataclass
from enum import IntEnum, Enum
from .types import TEXTURE_FOLDER, MINIMALUS_FOLDER, StyleTheme
from ..Overlay import Overlay
import os


class TextureState(IntEnum):
    Normal = 0
    Hovered = 1
    Active = 2
    Disabled = 3

@dataclass(slots=True)
class UVRegion:
    """Simple UV coordinate pair (u0, v0, u1, v1)."""
    u0: float
    v0: float
    u1: float
    v1: float

@dataclass(slots=True)
class SplitUVMap:
    """Holds 9-slice UV regions for one texture."""
    top_left: UVRegion
    top: UVRegion
    top_right: UVRegion
    left: UVRegion
    center: UVRegion
    right: UVRegion
    bottom_left: UVRegion
    bottom: UVRegion
    bottom_right: UVRegion


class GameTexture:
    """Optimized 9-slice texture renderer with struct-based UV access."""

    def __init__(self, texture: str, texture_size: tuple[float, float], margin: int | None = None):
        self.texture = texture
        self.width, self.height = texture_size

        if self.height <= 32:
            self.margin = 10 if not margin else margin
            
        elif self.height >= 64:
            self.margin = 40 if not margin else margin
            
        else:
            self.margin = int(10 + (self.height - 32) * (30 / (64 - 32))) if not margin else margin

        self.uvs = self._generate_uvs()

    def _calc_uv(self, region: tuple[float, float, float, float]) -> UVRegion:
        x0, y0, x1, y1 = region
        return UVRegion(x0 / self.width, y0 / self.height, x1 / self.width, y1 / self.height)

    def _generate_uvs(self) -> SplitUVMap:
        m = self.margin
        w, h = self.width, self.height

        return SplitUVMap(
            top_left=self._calc_uv((0, 0, m, m)),
            top=self._calc_uv((m, 0, w - m, m)),
            top_right=self._calc_uv((w - m, 0, w, m)),

            left=self._calc_uv((0, m, m, h - m)),
            center=self._calc_uv((m, m, w - m, h - m)),
            right=self._calc_uv((w - m, m, w, h - m)),

            bottom_left=self._calc_uv((0, h - m, m, h)),
            bottom=self._calc_uv((m, h - m, w - m, h)),
            bottom_right=self._calc_uv((w - m, h - m, w, h))
        )

    def draw_in_drawlist(
        self,
        x: float,
        y: float,
        size: tuple[float, float],
        tint=(255, 255, 255, 255),
        state: TextureState = TextureState.Normal
    ):
        from .ImGuisrc import ImGui

        total_w, total_h = size
        m = self.margin

        left = x
        top = y
        right = x + total_w
        bottom = y + total_h

        left_w = m
        right_w = m
        top_h = m
        bottom_h = m
        mid_w = max(total_w - left_w - right_w, 0)
        mid_h = max(total_h - top_h - bottom_h, 0)

        uv = self.uvs  # local ref → faster

        # --- Row 1 (top) ---
        ImGui.DrawTextureInDrawList((left, top), (left_w, top_h), self.texture, uv0=(uv.top_left.u0, uv.top_left.v0), uv1=(uv.top_left.u1, uv.top_left.v1), tint=tint)
        ImGui.DrawTextureInDrawList((left + left_w, top), (mid_w, top_h), self.texture, uv0=(uv.top.u0, uv.top.v0), uv1=(uv.top.u1, uv.top.v1), tint=tint)
        ImGui.DrawTextureInDrawList((right - right_w, top), (right_w, top_h), self.texture, uv0=(uv.top_right.u0, uv.top_right.v0), uv1=(uv.top_right.u1, uv.top_right.v1), tint=tint)

        # --- Row 2 (middle) ---
        ImGui.DrawTextureInDrawList((left, top + top_h), (left_w, mid_h), self.texture, uv0=(uv.left.u0, uv.left.v0), uv1=(uv.left.u1, uv.left.v1), tint=tint)
        ImGui.DrawTextureInDrawList((left + left_w, top + top_h), (mid_w, mid_h), self.texture, uv0=(uv.center.u0, uv.center.v0), uv1=(uv.center.u1, uv.center.v1), tint=tint)
        ImGui.DrawTextureInDrawList((right - right_w, top + top_h), (right_w, mid_h), self.texture, uv0=(uv.right.u0, uv.right.v0), uv1=(uv.right.u1, uv.right.v1), tint=tint)

        # --- Row 3 (bottom) ---
        ImGui.DrawTextureInDrawList((left, bottom - bottom_h), (left_w, bottom_h), self.texture, uv0=(uv.bottom_left.u0, uv.bottom_left.v0), uv1=(uv.bottom_left.u1, uv.bottom_left.v1), tint=tint)
        ImGui.DrawTextureInDrawList((left + left_w, bottom - bottom_h), (mid_w, bottom_h), self.texture, uv0=(uv.bottom.u0, uv.bottom.v0), uv1=(uv.bottom.u1, uv.bottom.v1), tint=tint)
        ImGui.DrawTextureInDrawList((right - right_w, bottom - bottom_h), (right_w, bottom_h), self.texture, uv0=(uv.bottom_right.u0, uv.bottom_right.v0), uv1=(uv.bottom_right.u1, uv.bottom_right.v1), tint=tint)

    def __repr__(self):
        return f"<GameTexture9 '{self.texture}' size=({self.width}x{self.height}) margin={self.margin}>"

class MapTexture:
    """
    Represents a UI element with multiple states (Normal, Hovered, etc.)
    mapped to different regions of a texture atlas.
    """

    def __init__(
        self,
        texture: str,
        texture_size: tuple[float, float],
        size: tuple[float, float],
        normal: tuple[float, float] = (0, 0),
        hovered: tuple[float, float] | None = None,
        active: tuple[float, float] | None = None,
        disabled: tuple[float, float] | None = None,
    ):
        self.texture = texture
        self.texture_size = texture_size
        self.size = size
        self.width, self.height = size

        self.normal_offset = self._make_uv(normal)
        self.hovered_offset = self._make_uv(hovered) if hovered else (0, 0, 1, 1)
        self.active_offset = self._make_uv(active) if active else (0, 0, 1, 1)
        self.disabled_offset = self._make_uv(disabled) if disabled else (0, 0, 1, 1)

    def _make_uv(self, pos: tuple[float, float]) -> tuple[float, float, float, float]:
        x, y = pos
        w, h = self.texture_size
        sx, sy = self.size
        return x / w, y / h, (x + sx) / w, (y + sy) / h

    def get_uv(self, state: TextureState) -> tuple[float, float, float, float]:
        match state:
            case TextureState.Normal: return self.normal_offset
            case TextureState.Hovered: return self.hovered_offset
            case TextureState.Active: return self.active_offset
            case TextureState.Disabled: return self.disabled_offset
        return self.normal_offset  # Fallback in case of unexpected state

    def draw_in_drawlist(
        self,
        x: float,
        y: float,
        size: tuple[float, float],
        state: TextureState = TextureState.Normal,
        tint=(255, 255, 255, 255)
    ):
        from .ImGuisrc import ImGui
        uv = self.get_uv(state)
        ImGui.DrawTextureInDrawList(
            pos=(x, y),
            size=size,
            texture_path=self.texture,
            uv0=uv[:2],
            uv1=uv[2:],
            tint=tint,
        )

    def draw_in_background_drawlist(
        self,
        x: float,
        y: float,
        size: tuple[float, float],
        state: TextureState = TextureState.Normal,
        tint=(255, 255, 255, 255),
        overlay_name: str = ""
    ):
        from .ImGuisrc import ImGui
        
        uv = self.get_uv(state)
        ImGui.overlay_instance.BeginDraw(overlay_name)

        ImGui.overlay_instance.DrawTexturedRectExtended((x, y), size, self.texture, uv[:2], uv[2:], tint)

        ImGui.overlay_instance.EndDraw()

class ThemeTexture:
    PlaceHolderTexture = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "missing_texture.png"),
        texture_size = (1, 1),
        size = (1, 1),
        normal=(0, 0)
    )

    def __init__(
        self,
        *args: tuple[StyleTheme, GameTexture | MapTexture],
    ):
        self.textures: dict[StyleTheme, GameTexture | MapTexture] = {}

        for theme, texture in args:
            self.textures[theme] = texture

    def get_texture(self, theme: StyleTheme | None = None) -> GameTexture | MapTexture:
        from .ImGuisrc import ImGui
        theme = theme or ImGui.get_style().Theme
        return self.textures.get(theme, ThemeTexture.PlaceHolderTexture)

class ThemeTextures(Enum):  
    Empty_Pixel = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "empty_pixel.png"),
        texture_size = (1, 1),
        size = (1, 1),
        normal=(0, 0)
    )

    TravelCursor = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "Cursor", "travel_cursor.png"),
        texture_size=(32, 32),
        size=(32, 32),
        normal=(0, 0)
    )

    ScrollGrab_Top = GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
        texture_size=(16, 16),
    )

    ScrollGrab_Middle = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
        texture_size=(16, 16),
        size=(16, 2),
        normal=(0, 7)
    )

    Scroll_Bg = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_scroll_background.png"),
        texture_size=(16, 16),
        size=(16, 16),
        normal=(0, 0)
    )

    ScrollGrab_Bottom = GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
        texture_size=(16, 16), 
    )            

    RightButton = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_left_right.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal=(1, 0)
    )

    LeftButton = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_left_right.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal = (17, 0),
        active = (49, 0),
    )

    Horizontal_ScrollGrab_Top = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(7, 16),
        normal=(0, 0),
    )

    Horizontal_ScrollGrab_Middle = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(2, 16),
        normal=(7, 0)
    )

    Horizontal_ScrollGrab_Bottom = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(7, 16),
        normal=(9, 0),   
    )   

    Horizontal_Scroll_Bg = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_horizontal_scroll_background.png"),
        texture_size=(16, 16),
        size=(16, 16),
        normal=(0, 0)
    )                         

    CircleButtons = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_profession_circle_buttons.png"),
        texture_size=(256, 128),
        size=(32, 32),
        active=(192, 96),
        normal=(224, 96)
    )

    UpButton = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_up_down.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal=(1, 0)
    )

    DownButton = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_up_down.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal = (17, 0),
        active = (49, 0),
    )

    Combo_Arrow = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_arrow.png"),
            texture_size=(128, 32),
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_combo_arrow.png"),
            texture_size=(128, 32),
        ))
    )

    Combo_Background = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_background.png"),
            texture_size=(128, 32),
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(
                TEXTURE_FOLDER, "ui_combo_background.png"),
            texture_size=(128, 32),
        ))
    )

    Combo_Frame = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_frame.png"),
            texture_size=(128, 32),
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_combo_frame.png"),
            texture_size=(128, 32),
        ))
    )
    ArrowCollapsed = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        size = (16, 16),
        normal = (16, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        size = (16, 16),
        normal = (16, 0),
    )),
    )  

    ArrowExpanded = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    )    
    
    CollapsingHeader_Background = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_collapsing_header_background.png"),
            texture_size=(128, 32),
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(
                TEXTURE_FOLDER, "ui_collapsing_header_background.png"),
            texture_size=(128, 32),
        ))
    )

    CollapsingHeader_Frame = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_collapsing_header_frame.png"),
            texture_size=(128, 32),
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_collapsing_header_frame.png"),
            texture_size=(128, 32),
        ))
    )

    Button_Frame = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_button_frame.png"),
            texture_size=(32, 32),
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_button_frame.png"),
            texture_size=(32, 32),
        ))
    )

    Button_Background = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_button_background.png"),
            texture_size=(32, 32),
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_button_background.png"),
            texture_size=(32, 32),
        ))
    )

    CheckBox_Unchecked = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 17),
        normal=(2, 2),
        active=(23, 2),
        disabled=(107, 2),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 17),
        normal=(2, 2),
        active=(23, 2),
        disabled=(107, 2),
    )),
    )

    CheckBox_Checked = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 18),
        normal=(44, 1),
        active=(65, 1),
        disabled=(86, 1),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 18),
        normal=(44, 1),
        active=(65, 1),
        disabled=(86, 1),
    )),
    )

    SliderBar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_slider_bar.png"),
        texture_size=(32, 16),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_slider_bar.png"),
        texture_size=(32, 16),
    )),
    )

    SliderGrab = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_slider_grab.png"),
        texture_size=(32, 32),
        size=(18, 18),
        normal=(7, 7)
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_slider_grab.png"),
        texture_size=(32, 32),
        size=(18, 18),
        normal=(7, 7)
    )),
    )

    Input_Inactive = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
    )),
    )

    Input_Active = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
    )),
    )

    Expand = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (13, 12),
        normal = (0, 3),
        hovered = (16, 3),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (12, 12),
        normal = (1, 3),
        hovered = (17, 3),
    )),
    )

    Collapse = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (13, 12),
        normal = (0, 19),
        hovered = (16, 19),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (12, 12),
        normal = (1, 19),
        hovered = (17, 19),
    )),
    )        

    Tab_Frame_Top = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
    )),
    )

    Tab_Frame_Body = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
    )),
    )

    Tab_Active = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_active.png"),
        texture_size=(32, 32),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_active.png"),
        texture_size=(32, 32),
    )),
    )

    Tab_Inactive = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_inactive.png"),
        texture_size=(32, 32),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_inactive.png"),
        texture_size=(32, 32),
    )),
    )

    Quest_Objective_Bullet_Point = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_quest_objective_bullet_point.png"),
        texture_size = (32, 16),
        size = (13, 13),
        normal=(0, 0),
        active=(13, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_quest_objective_bullet_point.png"),
        texture_size = (32, 16),
        size = (13, 13),
        normal=(0, 0),
        active=(13, 0),
    )),
    )

    Pip_Regen = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_pips.png"),
        texture_size = (32, 16),
        size = (10, 16),
        normal=(10, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_pips.png"),
        texture_size = (32, 16),
        size = (10, 16),
        normal=(10, 0),
    )),
    )

    Pip_Degen = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_pips.png"),
        texture_size = (32, 16),
        size = (10, 16),
        normal=(0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_pips.png"),
        texture_size = (32, 16),
        size = (10, 16),
        normal=(0, 0),
    )),
    )

    Close_Button = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        size = (12, 12),
        normal=(1, 1),
        hovered=(17, 1),
        active=(33, 1),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        size = (12, 12),
        normal=(1, 1),
        hovered=(17, 1),
        active=(33, 1),
    )),
    )

    Title_Bar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_titlebar.png"),
        texture_size=(128, 32),
        margin=18,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_titlebar.png"),
        texture_size=(128, 32),
        margin=18,
    )),
    )
    
    Title_Bar_Collapsed = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_titlebar_collapsed.png"),
        texture_size=(128, 32),
        margin=18,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_titlebar_collapsed.png"),
        texture_size=(128, 32),
        margin=18,
    )),
    )

    Window = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    )
    
    Window_NoResize_NoTitleBar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_notitlebar_noresize.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_notitlebar_noresize.png"),
        texture_size=(128, 128),
    )),
    )

    Window_NoResize = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_noresize.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_noresize.png"),
        texture_size=(128, 128),
    )),
    )

    Window_NoTitleBar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_notitlebar.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_notitlebar.png"),
        texture_size=(128, 128),
    )),
    )

    Window_NoResize_NoTitlebar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    )





    Window_Frame_Top = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    )

    Window_Frame_Center = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    )

    Window_Frame_Bottom = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
    )),
    )

    Window_Frame_Top_NoTitleBar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_no_titlebar.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_no_titlebar.png"),
        texture_size=(128, 128),
    )),
    )

    Window_Frame_Bottom_No_Resize = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_noresize.png"),
        texture_size=(128, 128),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_noresize.png"),
        texture_size=(128, 128),
    )),
    )


    Separator = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_separator.png"),
        texture_size = (32, 4),
        size = (32, 4),
        normal = (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_separator.png"),
        texture_size = (32, 4),
        size = (32, 4),
        normal = (0, 0),
    )),
    )

    ProgressBarFrame = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progressbar_frame.png"),
        texture_size=(16, 16),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progressbar_frame.png"),
        texture_size=(16, 16),
    )),
    )
    
    HealthBarFill = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        size=(3, 16),
        normal= (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        size=(3, 16),
        normal= (0, 0),
    )),
    )
    
    HealthBarCursor = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        size=(4, 16),
        normal= (3, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        size=(4, 16),
        normal= (3, 0),
    )),
    )
    
    HealthBarEmpty = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        size=(9, 16),
        normal= (7, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        size=(9, 16),
        normal= (7, 0),
    )),
    )
    
    EnergyBarFill = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        size=(3, 16),
        normal= (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        size=(3, 16),
        normal= (0, 0),
    )),
    )
    
    EnergyBarCursor = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        size=(4, 16),
        normal= (3, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        size=(4, 16),
        normal= (3, 0),
    )),
    )
    
    EnergyBarEmpty = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        size=(9, 16),
        normal= (7, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        size=(9, 16),
        normal= (7, 0),
    )),
    )
    
    ProgressBarProgressCursor = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        size= (16, 16),
        normal = (0, 0)
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        size= (16, 16),
        normal = (0, 0)
    )),
    )

    ProgressBarProgress = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (0, 0),
    )),
    )

    ProgressBarBackground = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (6, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (6, 0),
    )),
    )   

    BulletPoint = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_bullet_point.png"),
        texture_size = (16, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_bullet_point.png"),
        texture_size = (16, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    )   

    #Skill
    Skill_Slot_Empty = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_empty_skill_slot.png"),
        texture_size = (64, 64),
        size = (56, 56),
        normal = (4, 4),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_empty_skill_slot.png"),
        texture_size = (64, 64),
        size = (56, 56),
        normal = (4, 4),
    )),
    )
    
    Skill_Frame = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (0, 0),
        active = (56, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (0, 0),
        active = (56, 0),
    )),
    )
    
    Effect_Frame_Skill = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (112, 0),
        active= (168, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (112, 0),
        active= (168, 0),
    )),
    )
    
    Effect_Frame_Condition = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (0, 56),
        active = (56, 56),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (0, 56),
        active = (56, 56),
    )),
    )
    
    Effect_Frame_Enchantment = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (112, 56),
        active = (168, 56),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (112, 56),
        active = (168, 56),
    )),
    )

    Effect_Frame_Hex = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (0, 112),
        active = (56, 112),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (0, 112),
        active = (56, 112),
    )),
    )
    
    Effect_Frame_Blue = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (112, 112),
        active= (168, 112),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        size = (56, 56),
        normal = (112, 112),
        active= (168, 112),
    )),
    )

    Dropdown_Button_Base = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_dropdown_button.png"),
        texture_size = (64, 32),
        size = (21, 21),
        normal = (1, 1),
        active= (25, 1),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_dropdown_button.png"),
        texture_size = (64, 32),
        size = (21, 21),
        normal = (1, 1),
        active= (25, 1),
    )),
    )
    
    Hero_Panel_Toggle_Base = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_hero_panel_toggle.png"),
        texture_size = (64, 32),
        size = (17, 17),
        normal = (1, 2),
        active= (22, 2),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_hero_panel_toggle.png"),
        texture_size = (64, 32),
        size = (17, 17),
        normal = (1, 2),
        active= (22, 2),
    )),
    )
    
    Check = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_check_cancel.png"),
        texture_size = (64, 64),
        size = (32, 32),
        normal = (0, 0),
        hovered= (32, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_check_cancel.png"),
        texture_size = (64, 64),
        size = (32, 32),
        normal = (0, 0),
        hovered= (32, 0),
    )),
    )
    
    Cancel = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_check_cancel.png"),
        texture_size = (64, 64),
        size = (32, 32),
        normal = (0, 32),
        hovered= (32, 32),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_check_cancel.png"),
        texture_size = (64, 64),
        size = (32, 32),
        normal = (0, 32),
        hovered= (32, 32),
    )),
    )
    
    TemplateAction = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (21, 21),
        hovered = (1, 1),
        normal= (25, 1),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (21, 21),
        hovered = (1, 1),
        normal= (25, 1),
    )),
    )
    
    TemplateLoad = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (21, 21),
        hovered = (49, 1),
        normal= (74, 1),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (21, 21),
        hovered = (49, 1),
        normal= (74, 1),
    )),
    )
    
    TemplateSave = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (21, 21),
        hovered = (97, 1),
        normal= (2, 25),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (21, 21),
        hovered = (97, 1),
        normal= (2, 25),
    )),
    )
    
    TemplateManage = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (21, 21),
        hovered = (25, 25),
        normal= (50, 25),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (21, 21),
        hovered = (25, 25),
        normal= (50, 25),
    )),
    )
    
    TemplateCode = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (22, 22),
        hovered = (72, 23),
        normal= (97, 23),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        size = (22, 22),
        hovered = (72, 23),
        normal= (97, 23),
    )),
    )
    
    HeroPanelButtonBase = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_aggression.png"),
        texture_size = (128, 64),
        size = (27, 29),
        normal= (67, 34),
        active= (99, 34),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_aggression.png"),
        texture_size = (128, 64),
        size = (27, 29),
        normal= (67, 34),
        active= (99, 34),
    )),
    )

    HeaderLabelBackground = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "header_label.png"),
        texture_size = (128, 32),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture = os.path.join(TEXTURE_FOLDER, "header_label.png"),
        texture_size = (128, 32),
    )),
    )
    
    AdrenalineBarFill = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_adrenaline_effect.png"),
        texture_size = (64, 64),
        size = (64, 64),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_adrenaline_effect.png"),
        texture_size = (64, 64),
        size = (64, 64),
    )),
    )
    
    Inventory_Slots = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        size = (52, 64),
        normal= (0, 0),
        active = (0, 64),      
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        size = (52, 64),
        normal= (0, 0),
        active = (0, 64),      
    )),
    )
    
    Inventory_Slot_Blue = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        size = (52, 64),  
        normal= (52, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        size = (52, 64),     
        normal= (52, 0),
    )),
    )
    
    Inventory_Slot_Red = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        size = (52, 64),
        normal= (52, 64),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        size = (52, 64),        
        normal= (52, 64),
    )),
    )
    
    MoraleBoost = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "morale_boost_effect.png"),
        texture_size = (64, 64),
        size = (64, 64),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "morale_boost_effect.png"),
        texture_size = (64, 64),
        size = (64, 64),
    )),
    )
    
    DeathPenalty = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "death_penalty_effect.png"),
        texture_size = (64, 64),
        size = (64, 64),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "death_penalty_effect.png"),
        texture_size = (64, 64),
        size = (64, 64),
    )),
    )
