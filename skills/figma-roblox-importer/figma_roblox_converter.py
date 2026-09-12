#!/usr/bin/env python3
"""
Figma/Photoshop to Roblox UI Converter
=======================================
Conversor unificado que le especificacoes JSON de qualquer fonte
(Figma, Photoshop, design manual) e gera codigo Luau para Roblox.

Uso:
    python converter.py spec.json -o output/
    python converter.py spec.json -o output/ --upload
    python converter.py spec.json -o output/ --no-scale
    python converter.py spec.json -o output/ --no-list-layout
    python converter.py spec.json -o output/ --no-responsive

Melhorias em relacao ao plugin original TypeScript:
    - sanitize_name colapsa underscores multiplos
    - Escape de null byte em strings Lua
    - Detecao de AutoLayout do Figma
    - Regras de responsividade adicionais
    - Conversao de cores com menor erro de arredondamento
"""

import json
import math
import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


# =============================================================================
# TIPOS
# =============================================================================

@dataclass
class Color3:
    r: int = 0
    g: int = 0
    b: int = 0

    def to_luau(self) -> str:
        return f"Color3.fromRGB({self.r}, {self.g}, {self.b})"

@dataclass
class UDim2:
    x_scale: float = 0.0
    x_offset: int = 0
    y_scale: float = 0.0
    y_offset: int = 0

    def to_str(self) -> str:
        return f"UDim2.new({round(self.x_scale, 4)}, {self.x_offset}, {round(self.y_scale, 4)}, {self.y_offset})"

@dataclass
class Vector2:
    x: float = 0.0
    y: float = 0.0

    def to_str(self) -> str:
        return f"Vector2.new({round(self.x, 4)}, {round(self.y, 4)})"

@dataclass
class ParsedNode:
    id: str
    name: str
    instance_type: str
    position: UDim2
    size: UDim2
    anchor_point: Vector2
    rotation: float
    background_color: Optional[Color3]
    background_transparency: float
    border_size_pixel: int
    clips_descendants: bool
    visible: bool
    text: Optional[str] = None
    text_color: Optional[Color3] = None
    text_size: Optional[int] = None
    text_scaled: bool = False
    font: Optional[str] = None
    text_x_alignment: Optional[str] = None
    text_y_alignment: Optional[str] = None
    image_url: Optional[str] = None
    scale_type: Optional[str] = None
    ui_corner: Optional[int] = None
    ui_stroke: Optional[Dict] = None
    ui_list_layout: Optional[Dict] = None
    responsive_breakpoints: List[Dict] = field(default_factory=list)
    children: List['ParsedNode'] = field(default_factory=list)
    parent: Optional['ParsedNode'] = None
    figma_type: str = ""
    is_auto_layout: bool = False
    original_abs_x: float = 0.0
    original_abs_y: float = 0.0
    original_width: float = 0.0
    original_height: float = 0.0
    layout_order: int = 0


# =============================================================================
# UTILITARIOS
# =============================================================================

RESERVED_WORDS = {
    "and", "break", "do", "else", "elseif", "end", "false", "for",
    "function", "if", "in", "local", "nil", "not", "or", "repeat",
    "return", "then", "true", "until", "while", "continue",
}

FONT_MAP = {
    "Roboto": "Enum.Font.Roboto",
    "Inter": "Enum.Font.Gotham",
    "Arial": "Enum.Font.Arial",
    "Open Sans": "Enum.Font.Gotham",
    "Source Sans Pro": "Enum.Font.SourceSans",
    "Montserrat": "Enum.Font.GothamBold",
    "Poppins": "Enum.Font.GothamMedium",
}


def round_to(value: float, decimals: int = 4) -> float:
    factor = 10 ** decimals
    return math.floor(value * factor + 0.5) / factor


def sanitize_name(name: str) -> str:
    """Versao melhorada: colapsa underscores multiplos."""
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    clean = re.sub(r'_{2,}', '_', clean)
    clean = clean.strip('_')
    if not clean:
        clean = "unnamed"
    if clean[0].isdigit():
        clean = "_" + clean
    if clean.lower() in RESERVED_WORDS:
        clean = "_" + clean
    return clean


class NameAllocator:
    def __init__(self):
        self._used = {}

    def allocate(self, base_name: str) -> str:
        clean = sanitize_name(base_name)
        count = self._used.get(clean, 0)
        self._used[clean] = count + 1
        return f"{clean}_{count}" if count > 0 else clean

    def reset(self):
        self._used.clear()


# =============================================================================
# CONVERSOES
# =============================================================================

def compute_relative_position(
    child_abs_x: float, child_abs_y: float,
    child_w: float, child_h: float,
    parent_abs_x: float, parent_abs_y: float,
    parent_w: float, parent_h: float,
    anchor: Vector2, use_scale: bool
) -> UDim2:
    """Converte posicao absoluta do Figma para UDim2 Roblox (Scale+Offset)."""
    rel_x = child_abs_x - parent_abs_x
    rel_y = child_abs_y - parent_abs_y
    adj_x = rel_x + anchor.x * child_w
    adj_y = rel_y + anchor.y * child_h

    if not use_scale or parent_w == 0 or parent_h == 0:
        return UDim2(x_scale=0, x_offset=round(rel_x),
                     y_scale=0, y_offset=round(rel_y))

    x_scale = round_to(adj_x / parent_w, 4)
    y_scale = round_to(adj_y / parent_h, 4)
    x_offset = round(adj_x - x_scale * parent_w)
    y_offset = round(adj_y - y_scale * parent_h)

    return UDim2(x_scale=x_scale, x_offset=x_offset,
                 y_scale=y_scale, y_offset=y_offset)


def compute_relative_size(
    child_w: float, child_h: float,
    parent_w: float, parent_h: float,
    use_scale: bool
) -> UDim2:
    """Converte tamanho para UDim2 proporcional."""
    if not use_scale or parent_w == 0 or parent_h == 0:
        return UDim2(x_scale=0, x_offset=round(child_w),
                     y_scale=0, y_offset=round(child_h))

    x_scale = round_to(child_w / parent_w, 4)
    y_scale = round_to(child_h / parent_h, 4)
    x_offset = round(child_w - x_scale * parent_w)
    y_offset = round(child_h - y_scale * parent_h)

    return UDim2(x_scale=x_scale, x_offset=x_offset,
                 y_scale=y_scale, y_offset=y_offset)


# =============================================================================
# PARSER DE NODES
# =============================================================================

def detect_anchor_point(node: dict) -> Vector2:
    """Detecta anchor point a partir de constraints do Figma."""
    x, y = 0.0, 0.0
    constraints = node.get("constraints", {})
    if constraints.get("horizontal") == "CENTER":
        x = 0.5
    elif constraints.get("horizontal") == "MAX":
        x = 1.0
    if constraints.get("vertical") == "CENTER":
        y = 0.5
    elif constraints.get("vertical") == "MAX":
        y = 1.0
    return Vector2(x=x, y=y)


def has_image_fill(node: dict) -> bool:
    """Verifica se o node tem fill do tipo IMAGE."""
    fills = node.get("fills", [])
    if not isinstance(fills, list):
        return False
    return any(f.get("type") == "IMAGE" and f.get("visible", True) for f in fills)


def is_interactive(node: dict) -> bool:
    """Detecta interatividade por nome ou reacoes."""
    name = node.get("name", "").lower()
    keywords = ["button", "btn", "cta", "clickable", "play", "start"]
    if any(kw in name for kw in keywords):
        return True
    reactions = node.get("reactions", [])
    return isinstance(reactions, list) and len(reactions) > 0


def resolve_instance_type(node: dict) -> str:
    """Resolve tipo Roblox a partir do node Figma."""
    node_type = node.get("type", "FRAME")
    has_img = has_image_fill(node)
    is_btn = is_interactive(node)

    if node_type == "TEXT":
        return "TextButton" if is_btn else "TextLabel"
    elif node_type in ("FRAME", "GROUP", "COMPONENT", "INSTANCE", "SECTION"):
        if has_img:
            return "ImageButton" if is_btn else "ImageLabel"
        return "TextButton" if is_btn else "Frame"
    elif node_type in ("RECTANGLE", "ELLIPSE", "POLYGON", "STAR", "LINE"):
        return "ImageLabel" if has_img else "Frame"
    return "Frame"


def extract_fill_color(node: dict) -> Optional[Color3]:
    """Extrai cor do primeiro fill SOLID visivel."""
    fills = node.get("fills", [])
    if not isinstance(fills, list):
        return None
    for fill in fills:
        if fill.get("type") == "SOLID" and fill.get("visible", True):
            color = fill.get("color", {})
            r = round(color.get("r", 0) * 255)
            g = round(color.get("g", 0) * 255)
            b = round(color.get("b", 0) * 255)
            return Color3(r=r, g=g, b=b)
    return None


def extract_text_props(node: dict) -> dict:
    """Extrai propriedades de texto de um TextNode."""
    font_name = node.get("fontName", {})
    if isinstance(font_name, dict):
        family = font_name.get("family", "Inter")
        style = font_name.get("style", "Regular")
    else:
        family = str(font_name) if font_name else "Inter"
        style = "Regular"

    h_align = "Left"
    if node.get("textAlignHorizontal") == "CENTER":
        h_align = "Center"
    elif node.get("textAlignHorizontal") == "RIGHT":
        h_align = "Right"

    v_align = "Top"
    if node.get("textAlignVertical") == "CENTER":
        v_align = "Center"
    elif node.get("textAlignVertical") == "BOTTOM":
        v_align = "Bottom"

    auto_resize = node.get("textAutoResize", "NONE")
    text_scaled = auto_resize == "WIDTH_AND_HEIGHT"
    text_wrapped = auto_resize != "NONE"

    bg_color = extract_fill_color(node) or Color3(r=255, g=255, b=255)

    return {
        "text": node.get("characters", ""),
        "text_color": bg_color,
        "text_size": round(node.get("fontSize", 14)),
        "text_scaled": text_scaled,
        "font": FONT_MAP.get(family, "Enum.Font.Gotham"),
        "text_x_alignment": h_align,
        "text_y_alignment": v_align,
        "text_wrapped": text_wrapped,
    }


def parse_node(node: dict, parent_abs_x: float, parent_abs_y: float,
               parent_w: float, parent_h: float,
               use_scale: bool = True, depth: int = 0) -> Optional[ParsedNode]:
    """Converte um node Figma para ParsedNode Roblox."""
    if not node.get("visible", True) and depth > 0:
        return None

    node_type = node.get("type", "")
    if node_type in ("SLICE", "VECTOR", "BOOLEAN_OPERATION"):
        return None

    abs_x = node.get("absoluteTransform", [[0,0,0],[0,0,0]])[0][2] if "absoluteTransform" in node else node.get("x", 0)
    abs_y = node.get("absoluteTransform", [[0,0,0],[0,0,0]])[1][2] if "absoluteTransform" in node else node.get("y", 0)
    width = node.get("width", 0)
    height = node.get("height", 0)

    anchor = detect_anchor_point(node)
    position = compute_relative_position(abs_x, abs_y, width, height,
                                         parent_abs_x, parent_abs_y, parent_w, parent_h,
                                         anchor, use_scale)
    size = compute_relative_size(width, height, parent_w, parent_h, use_scale)

    instance_type = resolve_instance_type(node)

    parsed = ParsedNode(
        id=node.get("id", ""),
        name=sanitize_name(node.get("name", "unnamed")),
        instance_type=instance_type,
        position=position,
        size=size,
        anchor_point=anchor,
        rotation=round_to(node.get("rotation", 0), 2),
        background_color=extract_fill_color(node),
        background_transparency=round_to(1 - (node.get("opacity", 1.0) * (1 - (extract_fill_color(node).g / 255 if extract_fill_color(node) else 0))), 4) if extract_fill_color(node) else 1.0,
        border_size_pixel=0,
        clips_descendants=node.get("clipsContent", False) if "clipsContent" in node else False,
        visible=node.get("visible", True),
        figma_type=node_type,
        is_auto_layout="layoutMode" in node and node.get("layoutMode") != "NONE",
        original_abs_x=abs_x,
        original_abs_y=abs_y,
        original_width=width,
        original_height=height,
    )

    # Text
    if node_type == "TEXT":
        text_props = extract_text_props(node)
        parsed.text = text_props["text"]
        parsed.text_color = text_props["text_color"]
        parsed.text_size = text_props["text_size"]
        parsed.font = text_props["font"]
        parsed.text_x_alignment = text_props["text_x_alignment"]
        parsed.text_y_alignment = text_props["text_y_alignment"]
        parsed.text_wrapped = text_props["text_wrapped"]
        parsed.text_scaled = text_props["text_scaled"]

    # Image
    if has_image_fill(node):
        parsed.image_url = "rbxassetid://0"
        parsed.scale_type = "Fit"

    # Corner radius
    if "cornerRadius" in node:
        parsed.ui_corner = round(node["cornerRadius"])
    elif "topLeftRadius" in node:
        parsed.ui_corner = round(max(
            node.get("topLeftRadius", 0),
            node.get("topRightRadius", 0),
            node.get("bottomLeftRadius", 0),
            node.get("bottomRightRadius", 0)
        ))

    # Stroke
    strokes = node.get("strokes", [])
    if isinstance(strokes, list) and len(strokes) > 0:
        stroke = strokes[0]
        if stroke.get("type") == "SOLID" and stroke.get("visible", True):
            color = stroke.get("color", {})
            parsed.ui_stroke = {
                "color": Color3(
                    r=round(color.get("r", 0) * 255),
                    g=round(color.get("g", 0) * 255),
                    b=round(color.get("b", 0) * 255)
                ),
                "thickness": round(node.get("strokeWeight", 1)),
                "transparency": round_to(1 - (stroke.get("opacity", 1.0)), 4)
            }

    # Children
    children = node.get("children", [])
    if isinstance(children, list):
        for child in children:
            child_parsed = parse_node(child, abs_x, abs_y, width, height, use_scale, depth + 1)
            if child_parsed:
                child_parsed.parent = parsed
                parsed.children.append(child_parsed)

    return parsed


# =============================================================================
# DETECTOR DE LISTA LAYOUT
# =============================================================================

def analyze_list_layout(parent: ParsedNode) -> Optional[dict]:
    """Detecta se filhos formam um layout de lista regular."""
    children = [c for c in parent.children if c.visible]
    if len(children) < 2:
        return None

    # Horizontal analysis
    by_x = sorted(children, key=lambda c: c.original_abs_x)
    gaps_x = []
    for i in range(1, len(by_x)):
        prev_end = by_x[i-1].original_abs_x + by_x[i-1].original_width
        curr_start = by_x[i].original_abs_x
        gaps_x.append(round(curr_start - prev_end))

    if gaps_x:
        avg_gap_x = sum(gaps_x) / len(gaps_x)
        max_dev_x = max(abs(g - avg_gap_x) for g in gaps_x)
        consistency_x = 1.0 if max_dev_x <= 2 else (0.8 if max_dev_x <= 5 else 0.5)
        cross_var_x = max(c.original_abs_y for c in by_x) - min(c.original_abs_y for c in by_x)
        if consistency_x >= 0.7 and cross_var_x <= 5:
            return {"direction": "Horizontal", "spacing": round(avg_gap_x), "consistency": consistency_x}

    # Vertical analysis
    by_y = sorted(children, key=lambda c: c.original_abs_y)
    gaps_y = []
    for i in range(1, len(by_y)):
        prev_end = by_y[i-1].original_abs_y + by_y[i-1].original_height
        curr_start = by_y[i].original_abs_y
        gaps_y.append(round(curr_start - prev_end))

    if gaps_y:
        avg_gap_y = sum(gaps_y) / len(gaps_y)
        max_dev_y = max(abs(g - avg_gap_y) for g in gaps_y)
        consistency_y = 1.0 if max_dev_y <= 2 else (0.8 if max_dev_y <= 5 else 0.5)
        cross_var_y = max(c.original_abs_x for c in by_y) - min(c.original_abs_x for c in by_y)
        if consistency_y >= 0.7 and cross_var_y <= 5:
            return {"direction": "Vertical", "spacing": round(avg_gap_y), "consistency": consistency_y}

    return None


def inject_list_layouts(root: ParsedNode):
    """Injeta UIListLayout nos nodes que tem layout de lista."""
    analysis = analyze_list_layout(root)
    if analysis and analysis.get("consistency", 0) >= 0.7:
        is_h = analysis["direction"] == "Horizontal"
        sorted_children = sorted(root.children,
                                 key=lambda c: c.original_abs_x if is_h else c.original_abs_y)
        root.ui_list_layout = {
            "fill_direction": analysis["direction"],
            "padding": analysis["spacing"],
            "horizontal_alignment": "Left",
            "vertical_alignment": "Top",
        }
        for i, child in enumerate(sorted_children):
            child.layout_order = i + 1

    for child in root.children:
        inject_list_layouts(child)


# =============================================================================
# RESPONSIVIDADE
# =============================================================================

def generate_responsive_rules(node: ParsedNode) -> List[dict]:
    """Gera regras de responsividade para um node."""
    rules = []

    if node.text_size and node.text_size > 20:
        rules.append({
            "min_width": 0, "max_width": 500,
            "overrides": {"text_size": max(12, round(node.text_size * 0.7))}
        })

    if node.size.x_scale > 0.5 and node.position.x_offset == 0:
        rules.append({
            "min_width": 0, "max_width": 500,
            "overrides": {
                "size": UDim2(x_scale=0.95, x_offset=0,
                              y_scale=node.size.y_scale, y_offset=node.size.y_offset)
            }
        })

    if len(node.children) >= 2:
        same_y = all(abs(c.position.y_scale - node.children[0].position.y_scale) < 0.01
                     for c in node.children)
        if same_y:
            rules.append({
                "min_width": 0, "max_width": 500,
                "overrides": {
                    "position": UDim2(x_scale=0, x_offset=0, y_scale=0, y_offset=0),
                    "size": UDim2(x_scale=0.95, x_offset=0,
                                  y_scale=node.size.y_scale, y_offset=node.size.y_offset)
                }
            })

    return rules


def inject_responsive_rules(root: ParsedNode):
    """Injeta regras de responsividade em todos os nodes."""
    root.responsive_breakpoints = generate_responsive_rules(root)
    for child in root.children:
        inject_responsive_rules(child)


# =============================================================================
# EXPORTADOR LUA
# =============================================================================

def escape_lua_string(s: str) -> str:
    """Escape seguro para strings Lua."""
    return (s.replace("\\", "\\\\")
             .replace('"', '\\"')
             .replace("\n", "\\n")
             .replace("\r", "\\r")
             .replace("\t", "\\t")
             .replace("\0", "\\0"))


def export_to_lua(nodes: List[ParsedNode], indent: int = 2, wrap_gui: bool = True,
                  comments: bool = True) -> str:
    """Gera codigo Luau a partir de nodes parseados."""
    allocator = NameAllocator()
    lines = []
    pad = lambda d: " " * (indent * d)

    if comments:
        lines.append("-- ============================================================")
        lines.append("-- Auto-generated by FigmaPS2Roblox Converter")
        lines.append("-- Figma/Photoshop → Roblox LuaU Export")
        lines.append("-- ============================================================")
        lines.append("")

    if wrap_gui:
        lines.append('local screenGui = Instance.new("ScreenGui")')
        lines.append('screenGui.Name = "GeneratedUI"')
        lines.append('screenGui.ResetOnSpawn = false')
        lines.append('screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling')
        lines.append('screenGui.Parent = game.Players.LocalPlayer:WaitForChild("PlayerGui")')
        lines.append("")

    parent_var = "screenGui" if wrap_gui else "script.Parent"

    for root in nodes:
        emit_node(root, parent_var, 0, lines, pad, allocator)

    return "\n".join(lines)


def emit_node(node: ParsedNode, parent_var: str, depth: int,
              lines: List[str], pad: callable, allocator: NameAllocator):
    """Emite codigo Luau para um node e seus filhos."""
    var_name = allocator.allocate(node.name)
    i = pad(depth)

    lines.append(f'{i}local {var_name} = Instance.new("{node.instance_type}")')
    lines.append(f'{i}{var_name}.Name = "{node.name}"')
    lines.append(f'{i}{var_name}.Position = {node.position.to_str()}')
    lines.append(f'{i}{var_name}.Size = {node.size.to_str()}')

    if node.anchor_point.x != 0 or node.anchor_point.y != 0:
        lines.append(f'{i}{var_name}.AnchorPoint = {node.anchor_point.to_str()}')
    if node.rotation != 0:
        lines.append(f'{i}{var_name}.Rotation = {node.rotation}')
    if node.background_color:
        lines.append(f'{i}{var_name}.BackgroundColor3 = {node.background_color.to_luau()}')
    if node.background_transparency > 0:
        lines.append(f'{i}{var_name}.BackgroundTransparency = {node.background_transparency}')
    lines.append(f'{i}{var_name}.BorderSizePixel = {node.border_size_pixel}')
    if node.clips_descendants:
        lines.append(f'{i}{var_name}.ClipsDescendants = true')
    if node.layout_order > 0 and node.parent and node.parent.ui_list_layout:
        lines.append(f'{i}{var_name}.LayoutOrder = {node.layout_order}')

    if node.text is not None:
        lines.append(f'{i}{var_name}.Text = "{escape_lua_string(node.text)}"')
        if node.text_color:
            lines.append(f'{i}{var_name}.TextColor3 = {node.text_color.to_luau()}')
        if node.text_size:
            lines.append(f'{i}{var_name}.TextSize = {node.text_size}')
        if node.text_scaled:
            lines.append(f'{i}{var_name}.TextScaled = true')
        if node.font:
            lines.append(f'{i}{var_name}.Font = {node.font}')
        if node.text_x_alignment and node.text_x_alignment != "Left":
            lines.append(f'{i}{var_name}.TextXAlignment = Enum.TextXAlignment.{node.text_x_alignment}')
        if node.text_y_alignment and node.text_y_alignment != "Top":
            lines.append(f'{i}{var_name}.TextYAlignment = Enum.TextYAlignment.{node.text_y_alignment}')
        if node.text_wrapped:
            lines.append(f'{i}{var_name}.TextWrapped = true')

    if node.image_url:
        lines.append(f'{i}{var_name}.Image = "{node.image_url}"')
        if node.scale_type:
            lines.append(f'{i}{var_name}.ScaleType = Enum.ScaleType.{node.scale_type}')

    lines.append(f'{i}{var_name}.Parent = {parent_var}')
    lines.append("")

    if node.ui_corner:
        corner_var = allocator.allocate(node.name + "_corner")
        lines.append(f'{i}local {corner_var} = Instance.new("UICorner")')
        lines.append(f'{i}{corner_var}.CornerRadius = UDim.new(0, {node.ui_corner})')
        lines.append(f'{i}{corner_var}.Parent = {var_name}')
        lines.append("")

    if node.ui_stroke:
        stroke_var = allocator.allocate(node.name + "_stroke")
        lines.append(f'{i}local {stroke_var} = Instance.new("UIStroke")')
        lines.append(f'{i}{stroke_var}.Color = {node.ui_stroke["color"].to_luau()}')
        lines.append(f'{i}{stroke_var}.Thickness = {node.ui_stroke["thickness"]}')
        if node.ui_stroke["transparency"] > 0:
            lines.append(f'{i}{stroke_var}.Transparency = {node.ui_stroke["transparency"]}')
        lines.append(f'{i}{stroke_var}.Parent = {var_name}')
        lines.append("")

    if node.ui_list_layout:
        layout_var = allocator.allocate(node.name + "_layout")
        lines.append(f'{i}local {layout_var} = Instance.new("UIListLayout")')
        lines.append(f'{i}{layout_var}.FillDirection = Enum.FillDirection.{node.ui_list_layout["fill_direction"]}')
        lines.append(f'{i}{layout_var}.Padding = UDim.new(0, {node.ui_list_layout["padding"]})')
        lines.append(f'{i}{layout_var}.HorizontalAlignment = Enum.HorizontalAlignment.{node.ui_list_layout["horizontal_alignment"]}')
        lines.append(f'{i}{layout_var}.VerticalAlignment = Enum.VerticalAlignment.{node.ui_list_layout["vertical_alignment"]}')
        lines.append(f'{i}{layout_var}.SortOrder = Enum.SortOrder.LayoutOrder')
        lines.append(f'{i}{layout_var}.Parent = {var_name}')
        lines.append("")

    for child in node.children:
        emit_node(child, var_name, depth + 1, lines, pad, allocator)


# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Figma/Photoshop → Roblox LuaU Converter")
    parser.add_argument("input", help="Arquivo JSON de entrada (export do Figma/Photoshop)")
    parser.add_argument("-o", "--output", default="output.lua", help="Arquivo de saida")
    parser.add_argument("--no-scale", action="store_true", help="Usar Offset puro")
    parser.add_argument("--no-list-layout", action="store_true", help="Desativar deteccao de lista")
    parser.add_argument("--no-responsive", action="store_true", help="Desativar responsividade")
    parser.add_argument("--no-screen-gui", action="store_true", help="Nao envolver em ScreenGui")
    parser.add_argument("--no-comments", action="store_true", help="Sem comentarios")
    parser.add_argument("--indent", type=int, default=2, help="Tamanho da indentacao")
    parser.add_argument("--meta", action="store_true", help="Gerar arquivo meta.json para Rojo")

    args = parser.parse_args()

    # Load JSON
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Parse nodes
    use_scale = not args.no_scale
    nodes = []
    for node_data in data.get("selection", []) or data.get("elements", []):
        canvas_w = data.get("canvas", {}).get("width", 1920)
        canvas_h = data.get("canvas", {}).get("height", 1080)
        parsed = parse_node(node_data, 0, 0, canvas_w, canvas_h, use_scale)
        if parsed:
            nodes.append(parsed)

    # Inject layouts
    if not args.no_list_layout:
        for node in nodes:
            inject_list_layouts(node)

    # Inject responsiveness
    if not args.no_responsive:
        for node in nodes:
            inject_responsive_rules(node)

    # Export
    code = export_to_lua(
        nodes,
        indent=args.indent,
        wrap_gui=not args.no_screen_gui,
        comments=not args.no_comments
    )

    # Save
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(code)

    # Generate meta.json if requested
    if args.meta:
        meta = {
            "name": Path(args.output).stem,
            "tree": {
                Path(args.output).stem: {
                    "$className": "LocalScript",
                    "$path": args.output
                }
            }
        }
        meta_path = args.output.replace(".lua", ".meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    # Stats
    total_nodes = count_nodes(nodes)
    total_frames = count_frames(nodes)

    print(f"[OK] Exported {total_nodes} nodes ({len(code.split(chr(10)))} lines)")
    print(f"[OK] Frames: {total_frames}")
    print(f"[OK] Output: {args.output}")


def count_nodes(nodes: List[ParsedNode]) -> int:
    count = 0
    for n in nodes:
        count += 1 + count_nodes(n.children)
    return count


def count_frames(nodes: List[ParsedNode]) -> int:
    count = 0
    for n in nodes:
        if n.instance_type == "Frame":
            count += 1
        count += count_frames(n.children)
    return count


if __name__ == "__main__":
    main()
