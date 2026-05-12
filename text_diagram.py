"""Text-to-diagram generator for AutoFlow AI with a Graphviz-free SVG fallback."""

from __future__ import annotations

import html
import math
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

try:
    from graphviz import Digraph
except ImportError:  # pragma: no cover
    Digraph = None


@dataclass
class DiagramTheme:
    bgcolor: str
    node_fill: str
    node_color: str
    node_fontcolor: str
    edge_color: str
    edge_fontcolor: str


@dataclass
class LayoutNode:
    key: str
    label: str
    shape: str
    branch: str = "main"


@dataclass
class LayoutEdge:
    source: str
    target: str
    label: str = ""


THEMES = {
    "Dark Developer": DiagramTheme(
        bgcolor="#0f172a",
        node_fill="#1e293b",
        node_color="#334155",
        node_fontcolor="#e2e8f0",
        edge_color="#94a3b8",
        edge_fontcolor="#cbd5e1",
    ),
    "Blue Theme": DiagramTheme(
        bgcolor="#0a192f",
        node_fill="#112240",
        node_color="#233554",
        node_fontcolor="#64ffda",
        edge_color="#8892b0",
        edge_fontcolor="#a8b2d1",
    ),
    "Green Theme": DiagramTheme(
        bgcolor="#064e3b",
        node_fill="#065f46",
        node_color="#047857",
        node_fontcolor="#ecfdf5",
        edge_color="#a7f3d0",
        edge_fontcolor="#d1fae5",
    ),
    "Purple Theme": DiagramTheme(
        bgcolor="#2e1065",
        node_fill="#3b0764",
        node_color="#4c1d95",
        node_fontcolor="#f3e8ff",
        edge_color="#d8b4fe",
        edge_fontcolor="#e9d5ff",
    ),
    "PPT Light Theme": DiagramTheme(
        bgcolor="#ffffff",
        node_fill="#f8fafc",
        node_color="#cbd5e1",
        node_fontcolor="#0f172a",
        edge_color="#475569",
        edge_fontcolor="#1e293b",
    ),
    "PPT": DiagramTheme(
        bgcolor="#ffffff",
        node_fill="#f8fafc",
        node_color="#cbd5e1",
        node_fontcolor="#0f172a",
        edge_color="#475569",
        edge_fontcolor="#1e293b",
    ),
}


def extract_natural_language(text: str) -> str:
    """Intelligently parse a raw paragraph into a structured graphic format."""
    text = text.strip()
    if not text:
        return ""

    if "->" in text or "â†’" in text or "\n" in text and len(text.split("\n")) > 2:
        return text

    raw_clauses = re.split(r"(?i)\.|\n|, and |\s+and\s+|, then |\s+then\s+", text)

    steps = []
    for clause in raw_clauses:
        clause = clause.strip()
        if not clause:
            continue

        clause = re.sub(r"(?i)^(the system )?(is designed to )?(allows? )?(users? to )?", "", clause)
        clause = clause.replace("their ", "")
        clause = clause.replace("provide access to", "show")
        clause = clause.replace("display an", "show")
        clause = clause.replace("display a", "show")
        clause = clause.strip()

        if " if " in clause and not clause.lower().startswith("if "):
            parts = re.split(r"\s+if\s+", clause, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) == 2:
                clause = f"if {parts[1].strip()} {parts[0].strip()}"

        clause = re.sub(r"(?i)\botherwise\b", "else", clause)

        if clause:
            clause = clause[0].upper() + clause[1:]
            for segment in [sub.strip() for sub in clause.split(",") if sub.strip()]:
                steps.append(segment)

    return "\n-> ".join(steps)


def simplify_steps(steps: list[str]) -> list[str]:
    """Smart simplification engine for clean, readable diagrams."""
    simplified = ["Start"]

    for step in steps:
        lower_step = step.lower().strip()
        if not lower_step:
            continue

        if "input(" in lower_step or "take input" in lower_step or lower_step.startswith("input"):
            new_step = "Take Input"
        elif "if " in lower_step or "check" in lower_step or "valid" in lower_step or "==" in lower_step:
            new_step = "If Check Condition"
        elif "print(" in lower_step or "display " in lower_step or "show " in lower_step:
            new_step = "Display Output"
        elif "loop" in lower_step or "while " in lower_step or "for " in lower_step or "repeat" in lower_step:
            new_step = "Repeat Process"
        elif "else" in lower_step or "except" in lower_step or "otherwise" in lower_step:
            new_step = "Else"
        elif "def " in lower_step or "class " in lower_step or "import " in lower_step or "return " in lower_step:
            continue
        else:
            new_step = "Process Data"

        if simplified[-1] != new_step:
            simplified.append(new_step)

    final_steps = []
    for step in simplified:
        if final_steps and final_steps[-1] == "Process Data" and step == "Process Data":
            continue
        final_steps.append(step)

    if len(final_steps) > 7:
        final_steps = final_steps[:3] + ["Process Data"] + final_steps[-3:]

    if not final_steps or final_steps[-1] != "End":
        final_steps.append("End")

    ultra_final = []
    for step in final_steps:
        if ultra_final and ultra_final[-1] == step:
            continue
        ultra_final.append(step)

    return ultra_final


def _normalize_diagram_type(diagram_type: str) -> str:
    normalized = str(diagram_type or "Flowchart").strip()
    if normalized in {"Circular", "Circular Diagram"}:
        return "Circular"
    if normalized in {"Block Diagram", "Process Flow UI"}:
        return "Block Diagram"
    return "Flowchart"


def _engine_for_diagram(diagram_type: str) -> str:
    return "circo" if diagram_type == "Circular" else "dot"


def _graphviz_engine_available(engine: str) -> bool:
    return Digraph is not None and shutil.which(engine) is not None


def _style_to_diagram_type(style_name: str) -> str:
    if style_name == "Circular Diagram":
        return "Circular"
    if style_name == "Process Flow UI":
        return "Block Diagram"
    return "Flowchart"


def _split_chunks(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"(?i)\s*->\s*|\s*â†’\s*|\n+", text) if chunk.strip()]


def _shape_for_step(label: str, diagram_type: str) -> tuple[str, str]:
    lower_label = label.lower().strip()

    if diagram_type == "Circular":
        return "circle", label

    if diagram_type == "Flowchart":
        if lower_label.startswith("if ") or " if " in lower_label:
            display_label = re.sub(r"(?i)^if\s+", "", label).strip() or "Condition"
            return "diamond", display_label
        if lower_label in {"start", "end"}:
            return "oval", label

    return "box", label


def _build_layout_graph(steps: list[str], diagram_type: str) -> tuple[list[LayoutNode], list[LayoutEdge]]:
    nodes: list[LayoutNode] = []
    edges: list[LayoutEdge] = []

    last_decision_key: str | None = None
    prev_key: str | None = None
    pending_no = False

    for raw_step in steps:
        step = str(raw_step).strip()
        if not step:
            continue

        lower_step = step.lower()
        if diagram_type == "Flowchart" and lower_step in {"else", "otherwise", "else:", "except"}:
            pending_no = True
            continue

        node_shape, display_label = _shape_for_step(step, diagram_type)
        node_key = f"n{len(nodes)}"
        branch = "no" if pending_no and diagram_type == "Flowchart" else "main"
        nodes.append(LayoutNode(key=node_key, label=display_label, shape=node_shape, branch=branch))

        if pending_no:
            if last_decision_key:
                edges.append(LayoutEdge(source=last_decision_key, target=node_key, label="No"))
            elif prev_key:
                edges.append(LayoutEdge(source=prev_key, target=node_key))
            pending_no = False
        elif prev_key:
            edge_label = "Yes" if diagram_type == "Flowchart" and last_decision_key == prev_key else ""
            edges.append(LayoutEdge(source=prev_key, target=node_key, label=edge_label))

        if diagram_type == "Flowchart" and node_shape == "diamond":
            last_decision_key = node_key

        prev_key = node_key

    return nodes, edges


def _wrap_svg_text(label: str, max_chars: int) -> list[str]:
    words = label.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _measure_node(label: str, shape: str) -> tuple[list[str], float, float]:
    max_chars = 16 if shape == "diamond" else 20
    lines = _wrap_svg_text(label, max_chars=max_chars)
    max_line_length = max((len(line) for line in lines), default=1)
    width = max(132.0, min(320.0, 42.0 + max_line_length * 8.2))
    height = max(56.0, 28.0 + len(lines) * 18.0)

    if shape == "diamond":
        width = max(width, 156.0)
        height = max(height, 92.0)
    elif shape == "oval":
        width = max(width, 138.0)
        height = max(height, 58.0)
    elif shape == "circle":
        diameter = max(width, height, 108.0)
        width = diameter
        height = diameter

    return lines, width, height


def _edge_points(
    source_center: tuple[float, float],
    source_size: tuple[float, float],
    target_center: tuple[float, float],
    target_size: tuple[float, float],
) -> tuple[float, float, float, float]:
    source_x, source_y = source_center
    source_width, source_height = source_size
    target_x, target_y = target_center
    target_width, target_height = target_size

    delta_x = target_x - source_x
    delta_y = target_y - source_y

    if abs(delta_x) > abs(delta_y):
        source_anchor_x = source_x + (source_width / 2.0 if delta_x >= 0 else -source_width / 2.0)
        source_anchor_y = source_y
        target_anchor_x = target_x - (target_width / 2.0 if delta_x >= 0 else -target_width / 2.0)
        target_anchor_y = target_y
    else:
        source_anchor_x = source_x
        source_anchor_y = source_y + (source_height / 2.0 if delta_y >= 0 else -source_height / 2.0)
        target_anchor_x = target_x
        target_anchor_y = target_y - (target_height / 2.0 if delta_y >= 0 else -target_height / 2.0)

    return source_anchor_x, source_anchor_y, target_anchor_x, target_anchor_y


def _render_svg_diagram(steps: list[str], diagram_type: str, output_path: str, theme: DiagramTheme) -> str:
    nodes, edges = _build_layout_graph(steps, diagram_type)
    if not nodes:
        return ""

    node_map = {node.key: node for node in nodes}
    node_lines: dict[str, list[str]] = {}
    node_sizes: dict[str, tuple[float, float]] = {}
    max_width = 0.0
    max_height = 0.0

    for node in nodes:
        lines, width, height = _measure_node(node.label, node.shape)
        node_lines[node.key] = lines
        node_sizes[node.key] = (width, height)
        max_width = max(max_width, width)
        max_height = max(max_height, height)

    positions: dict[str, tuple[float, float]] = {}
    key_by_branch_target = {edge.target: edge.source for edge in edges if edge.label == "No"}

    padding = 56.0
    main_gap = 82.0
    branch_gap = 108.0

    if diagram_type == "Circular":
        max_diameter = max(max(size) for size in node_sizes.values())
        radius = max(170.0, (len(nodes) * max_diameter) / (2.0 * math.pi) + 36.0)
        center_x = padding + radius + max_diameter
        center_y = padding + radius + max_diameter

        for index, node in enumerate(nodes):
            angle = (-math.pi / 2.0) + (2.0 * math.pi * index / len(nodes))
            positions[node.key] = (
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
            )

        svg_width = center_x + radius + max_diameter + padding
        svg_height = center_y + radius + max_diameter + padding
    elif diagram_type == "Block Diagram":
        cursor_x = padding
        center_y = padding + max_height / 2.0
        branch_offsets: dict[str, int] = {}

        for node in nodes:
            width, height = node_sizes[node.key]
            if node.branch == "main":
                positions[node.key] = (cursor_x + width / 2.0, center_y)
                cursor_x += width + main_gap

        for node in nodes:
            if node.branch != "no":
                continue

            width, height = node_sizes[node.key]
            source_key = key_by_branch_target.get(node.key)
            if source_key and source_key in positions:
                source_x, source_y = positions[source_key]
                branch_index = branch_offsets.get(source_key, 0)
                branch_offsets[source_key] = branch_index + 1
                positions[node.key] = (
                    source_x,
                    source_y + (height + branch_gap) * (branch_index + 1),
                )
            else:
                positions[node.key] = (cursor_x + width / 2.0, center_y + height + branch_gap)
                cursor_x += width + main_gap

        svg_width = max((center[0] + node_sizes[key][0] / 2.0 for key, center in positions.items()), default=0.0) + padding
        svg_height = max((center[1] + node_sizes[key][1] / 2.0 for key, center in positions.items()), default=0.0) + padding
    else:
        center_x = padding + max_width / 2.0
        cursor_y = padding
        branch_offsets: dict[str, int] = {}
        max_right_edge = center_x + max_width / 2.0

        for node in nodes:
            width, height = node_sizes[node.key]
            if node.branch == "main":
                positions[node.key] = (center_x, cursor_y + height / 2.0)
                cursor_y += height + main_gap

        for node in nodes:
            if node.branch != "no":
                continue

            width, height = node_sizes[node.key]
            source_key = key_by_branch_target.get(node.key)
            if source_key and source_key in positions:
                source_x, source_y = positions[source_key]
                branch_index = branch_offsets.get(source_key, 0)
                branch_offsets[source_key] = branch_index + 1
                branch_x = source_x + max_width / 2.0 + width / 2.0 + branch_gap
                branch_y = source_y + branch_index * (height + 34.0)
                positions[node.key] = (branch_x, branch_y)
                max_right_edge = max(max_right_edge, branch_x + width / 2.0)
            else:
                positions[node.key] = (center_x, cursor_y + height / 2.0)
                cursor_y += height + main_gap

        svg_width = max_right_edge + padding
        svg_height = max((center[1] + node_sizes[key][1] / 2.0 for key, center in positions.items()), default=0.0) + padding

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(math.ceil(svg_width))}" '
        f'height="{int(math.ceil(svg_height))}" viewBox="0 0 {int(math.ceil(svg_width))} {int(math.ceil(svg_height))}">',
        "<defs>",
        '<marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">',
        f'<path d="M0,0 L12,6 L0,12 z" fill="{theme.edge_color}" />',
        "</marker>",
        "</defs>",
        f'<rect width="100%" height="100%" fill="{theme.bgcolor}" rx="24" ry="24" />',
    ]

    for edge in edges:
        source_center = positions[edge.source]
        target_center = positions[edge.target]
        source_size = node_sizes[edge.source]
        target_size = node_sizes[edge.target]
        x1, y1, x2, y2 = _edge_points(source_center, source_size, target_center, target_size)

        parts.append(
            f'<path d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}" '
            f'stroke="{theme.edge_color}" stroke-width="2.5" fill="none" marker-end="url(#arrow)" />'
        )

        if edge.label:
            label_x = (x1 + x2) / 2.0
            label_y = (y1 + y2) / 2.0 - 10.0
            parts.append(
                f'<text x="{label_x:.1f}" y="{label_y:.1f}" fill="{theme.edge_fontcolor}" '
                'font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="600" text-anchor="middle">'
                f"{html.escape(edge.label)}</text>"
            )

    for node in nodes:
        center_x, center_y = positions[node.key]
        width, height = node_sizes[node.key]
        x = center_x - width / 2.0
        y = center_y - height / 2.0

        if node.shape == "diamond":
            points = [
                f"{center_x:.1f},{y:.1f}",
                f"{x + width:.1f},{center_y:.1f}",
                f"{center_x:.1f},{y + height:.1f}",
                f"{x:.1f},{center_y:.1f}",
            ]
            parts.append(
                f'<polygon points="{" ".join(points)}" fill="{theme.node_fill}" '
                f'stroke="{theme.node_color}" stroke-width="2.2" />'
            )
        elif node.shape == "oval":
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
                f'rx="{height / 2.0:.1f}" ry="{height / 2.0:.1f}" fill="{theme.node_fill}" '
                f'stroke="{theme.node_color}" stroke-width="2.2" />'
            )
        elif node.shape == "circle":
            radius = width / 2.0
            parts.append(
                f'<circle cx="{center_x:.1f}" cy="{center_y:.1f}" r="{radius:.1f}" '
                f'fill="{theme.node_fill}" stroke="{theme.node_color}" stroke-width="2.2" />'
            )
        else:
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
                f'rx="18" ry="18" fill="{theme.node_fill}" stroke="{theme.node_color}" stroke-width="2.2" />'
            )

        lines = node_lines[node.key]
        baseline = center_y - ((len(lines) - 1) * 11.0)
        for index, line in enumerate(lines):
            parts.append(
                f'<text x="{center_x:.1f}" y="{baseline + index * 22.0:.1f}" fill="{theme.node_fontcolor}" '
                'font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="600" '
                f'text-anchor="middle" dominant-baseline="middle">{html.escape(line)}</text>'
            )

    parts.append("</svg>")

    svg_path = Path(output_path).with_suffix(".svg")
    svg_path.write_text("\n".join(parts), encoding="utf-8")
    return str(svg_path)


class TextDiagramBuilder:
    def __init__(self, theme_name: str = "Dark Developer", style_name: str = "Classic Flowchart") -> None:
        if Digraph is None:
            raise RuntimeError("The graphviz Python package is not installed.")

        self.theme = THEMES.get(theme_name, THEMES["Dark Developer"])
        self.style_name = style_name

        engine = "circo" if style_name == "Circular Diagram" else "dot"
        self.graph = Digraph("text_diagram", format="png", engine=engine)
        self.graph.attr(dpi="300")

        rankdir = "LR" if style_name == "Process Flow UI" else "TB"
        nodesep = "0.8" if style_name == "Circular Diagram" else "0.5"

        self.graph.attr(
            rankdir=rankdir,
            bgcolor=self.theme.bgcolor,
            pad="0.5",
            nodesep=nodesep,
            ranksep="0.8",
        )

        shape = "rect"
        style = "filled,rounded"
        penwidth = "1.5"
        fontsize = "12"
        fontname = "Segoe UI, sans-serif"

        if style_name == "Step Cards":
            penwidth = "0"
            fontsize = "14"
        elif style_name == "Circular Diagram":
            shape = "circle"
            penwidth = "2.0"

        self.graph.attr(
            "node",
            fontname=fontname,
            fontsize=fontsize,
            color=self.theme.node_color,
            fontcolor=self.theme.node_fontcolor,
            penwidth=penwidth,
            style=style,
            fillcolor=self.theme.node_fill,
            margin="0.2,0.1",
            shape=shape,
        )

        self.graph.attr(
            "edge",
            color=self.theme.edge_color,
            fontcolor=self.theme.edge_fontcolor,
            penwidth="1.2",
            arrowsize="0.9",
            fontname=fontname,
            fontsize="10",
        )

        self.node_registry = {}
        self.counter = 0

    def _get_node_id(self, label: str) -> str:
        """Create a node and retrieve its internal ID."""
        if label not in self.node_registry:
            node_id = f"n_{self.counter}"
            self.counter += 1
            self.node_registry[label] = node_id

            if self.style_name == "Step Cards":
                colors = ["#0284c7", "#16a34a", "#9333ea", "#ea580c", "#ca8a04"]
                fillcolor = colors[self.counter % len(colors)]
                self.graph.node(node_id, label, fillcolor=fillcolor, fontcolor="#ffffff")
            else:
                self.graph.node(node_id, label)

        return self.node_registry[label]

    def _update_shape(self, label: str, shape: str) -> None:
        """Force a shape update for decision nodes."""
        if self.style_name in ("Classic Flowchart", "Process Flow UI"):
            node_id = self._get_node_id(label)
            self.graph.node(node_id, shape=shape)

    def build(self, text: str, output_path: str) -> str:
        """Parse raw text, apply smart keyword groupings, and output PNG."""
        render_target = Path(output_path)
        chunks = _split_chunks(text)
        if not chunks:
            return ""

        previous_node_label = None
        last_decision_label = None

        for chunk in chunks:
            lower_chunk = chunk.lower()
            is_if = lower_chunk.startswith("if ") or " if " in lower_chunk
            is_else = lower_chunk.startswith("else ") or " else " in lower_chunk or lower_chunk.startswith("otherwise")

            if is_if and previous_node_label:
                self._update_shape(previous_node_label, "diamond")
                last_decision_label = previous_node_label

                clean_text = re.sub(r"(?i)^if\s+([a-z0-9]+\s+)?", "", chunk).strip() or "Action"
                source = self._get_node_id(previous_node_label)
                target = self._get_node_id(clean_text)
                self.graph.edge(source, target, label="Yes")
                previous_node_label = clean_text
            elif is_else and last_decision_label:
                clean_text = re.sub(r"(?i)^(else|otherwise)\s*", "", chunk).strip() or "Fallback Action"
                source = self._get_node_id(last_decision_label)
                target = self._get_node_id(clean_text)
                self.graph.edge(source, target, label="No")
                previous_node_label = clean_text
            else:
                if previous_node_label:
                    source = self._get_node_id(previous_node_label)
                    target = self._get_node_id(chunk)
                    self.graph.edge(source, target)

                previous_node_label = chunk

        try:
            return self.graph.render(filename=render_target.name, directory=str(render_target.parent), cleanup=True)
        except Exception as exc:
            raise RuntimeError("Graphviz diagram execution failed.") from exc


def generate_text_diagram(
    text: str,
    output_dir: str = "static",
    theme: str = "Dark Developer",
    style: str = "Classic Flowchart",
) -> str:
    """Entry point for the text diagram feature."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_stem = f"autoflow_text_{uuid.uuid4().hex}"
    output_path = target_dir / file_stem

    resolved_theme = THEMES.get(theme, THEMES["Dark Developer"])
    resolved_diagram_type = _style_to_diagram_type(style)
    engine = _engine_for_diagram(resolved_diagram_type)

    if not _graphviz_engine_available(engine):
        return _render_svg_diagram(_split_chunks(text), resolved_diagram_type, str(output_path), resolved_theme)

    builder = TextDiagramBuilder(theme_name=theme, style_name=style)
    try:
        return builder.build(text, str(output_path))
    except RuntimeError:
        return _render_svg_diagram(_split_chunks(text), resolved_diagram_type, str(output_path), resolved_theme)


def generate_multi_diagram(
    steps: list[str],
    diagram_type: str = "Flowchart",
    output_dir: str = "static",
    theme: str = "Dark Developer",
) -> str:
    """Entry point for the multi-diagram generator from steps array."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_stem = f"autoflow_multi_{uuid.uuid4().hex}"
    output_path = target_dir / file_stem

    resolved_diagram_type = _normalize_diagram_type(diagram_type)
    resolved_theme = THEMES.get(theme, THEMES["Dark Developer"])
    engine = _engine_for_diagram(resolved_diagram_type)

    if not steps:
        return ""

    if not _graphviz_engine_available(engine):
        return _render_svg_diagram(steps, resolved_diagram_type, str(output_path), resolved_theme)

    shape = "circle" if resolved_diagram_type == "Circular" else "box"
    rankdir = "LR" if resolved_diagram_type == "Block Diagram" else "TB"
    nodesep = "0.8" if resolved_diagram_type == "Circular" else "0.5"

    graph = Digraph("multi_diagram", format="png", engine=engine)
    graph.attr(
        dpi="300",
        rankdir=rankdir,
        bgcolor=resolved_theme.bgcolor,
        pad="0.5",
        nodesep=nodesep,
        ranksep="0.8",
    )

    graph.attr(
        "node",
        fontname="Segoe UI, sans-serif",
        fontsize="12",
        color=resolved_theme.node_color,
        fontcolor=resolved_theme.node_fontcolor,
        penwidth="1.5",
        style="filled,rounded",
        fillcolor=resolved_theme.node_fill,
        margin="0.2,0.1",
        shape=shape,
    )

    graph.attr(
        "edge",
        color=resolved_theme.edge_color,
        fontcolor=resolved_theme.edge_fontcolor,
        penwidth="1.2",
        arrowsize="0.9",
        fontname="Segoe UI, sans-serif",
        fontsize="10",
    )

    node_registry: dict[str, str] = {}

    def get_node(label: str) -> str:
        if label not in node_registry:
            node_id = f"n_{len(node_registry)}"
            node_registry[label] = node_id

            node_shape, display_label = _shape_for_step(label, resolved_diagram_type)
            graph.node(node_id, display_label, shape=node_shape)
        return node_registry[label]

    last_decision_id = None
    prev_id = None
    pending_no = False

    for step in steps:
        lower_step = step.lower()

        if resolved_diagram_type == "Flowchart" and lower_step in {"else", "otherwise", "else:", "except"}:
            pending_no = True
            continue

        current_id = get_node(step)

        if pending_no:
            if last_decision_id:
                graph.edge(last_decision_id, current_id, label="No")
            elif prev_id:
                graph.edge(prev_id, current_id)
            pending_no = False
        elif prev_id:
            label = "Yes" if last_decision_id == prev_id else ""
            graph.edge(prev_id, current_id, label=label)

        if resolved_diagram_type == "Flowchart" and (
            lower_step.startswith("if ") or " if " in lower_step
        ):
            last_decision_id = current_id

        prev_id = current_id

    try:
        return graph.render(filename=output_path.name, directory=str(output_path.parent), cleanup=True)
    except Exception:
        return _render_svg_diagram(steps, resolved_diagram_type, str(output_path), resolved_theme)
