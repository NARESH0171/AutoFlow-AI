"""Text-to-Diagram Infographic generator for AutoFlow AI."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

try:
    from graphviz import Digraph
except ImportError:  # pragma: no cover
    Digraph = None

def extract_natural_language(text: str) -> str:
    """Intelligently parse a raw paragraph into a structured graphic format."""
    text = text.strip()
    if not text:
        return ""
        
    if "->" in text or "→" in text or "\n" in text and len(text.split("\n")) > 2:
        return text # Already structured
        
    raw_clauses = re.split(r'(?i)\.|\n|, and |\s+and\s+|, then |\s+then\s+', text)
    
    steps = []
    for clause in raw_clauses:
        clause = clause.strip()
        if not clause:
            continue
            
        lower_clause = clause.lower()
        clause = re.sub(r'(?i)^(the system )?(is designed to )?(allows? )?(users? to )?', '', clause)
        
        clause = clause.replace("their ", "")
        clause = clause.replace("provide access to", "show")
        clause = clause.replace("display an", "show")
        clause = clause.replace("display a", "show")
        clause = clause.strip()
        
        if " if " in clause and not clause.lower().startswith("if "):
            parts = re.split(r'\s+if\s+', clause, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) == 2:
                clause = f"if {parts[1].strip()} {parts[0].strip()}"
                
        clause = re.sub(r'(?i)\botherwise\b', 'else', clause)
        
        if clause:
            clause = clause[0].upper() + clause[1:]
            for c in [sub.strip() for sub in clause.split(",") if sub.strip()]:
                steps.append(c)

    return "\n-> ".join(steps)


def simplify_steps(steps: list[str]) -> list[str]:
    """Smart Simplification Engine for Clean & Readable Flowcharts."""
    simplified = ["Start"]
    
    for step in steps:
        lower_step = step.lower().strip()
        if not lower_step: continue
        
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

    # Clean duplicates & limit size 6-10
    final_steps = []
    for s in simplified:
        if final_steps and final_steps[-1] == "Process Data" and s == "Process Data":
            continue # Merge contiguous processes
        final_steps.append(s)

    if len(final_steps) > 7:
        # compress the middle nodes into a single process
        final_steps = final_steps[:3] + ["Process Data"] + final_steps[-3:]

    # Ensure "End" is at the end implicitly via generation, but explicit makes logic clean
    if not final_steps or final_steps[-1] != "End":
        final_steps.append("End")
        
    # Final deduplicate check
    ultra_final = []
    for s in final_steps:
        if ultra_final and ultra_final[-1] == s: continue
        ultra_final.append(s)
        
    return ultra_final


@dataclass
class DiagramTheme:
    bgcolor: str
    node_fill: str
    node_color: str
    node_fontcolor: str
    edge_color: str
    edge_fontcolor: str


THEMES = {
    "Dark Developer": DiagramTheme(
        bgcolor="#0f172a", node_fill="#1e293b", node_color="#334155", 
        node_fontcolor="#e2e8f0", edge_color="#94a3b8", edge_fontcolor="#cbd5e1"
    ),
    "Blue Theme": DiagramTheme(
        bgcolor="#0a192f", node_fill="#112240", node_color="#233554", 
        node_fontcolor="#64ffda", edge_color="#8892b0", edge_fontcolor="#a8b2d1"
    ),
    "Green Theme": DiagramTheme(
        bgcolor="#064e3b", node_fill="#065f46", node_color="#047857", 
        node_fontcolor="#ecfdf5", edge_color="#a7f3d0", edge_fontcolor="#d1fae5"
    ),
    "Purple Theme": DiagramTheme(
        bgcolor="#2e1065", node_fill="#3b0764", node_color="#4c1d95", 
        node_fontcolor="#f3e8ff", edge_color="#d8b4fe", edge_fontcolor="#e9d5ff"
    ),
    "PPT Light Theme": DiagramTheme(
        bgcolor="#ffffff", node_fill="#f8fafc", node_color="#cbd5e1", 
        node_fontcolor="#0f172a", edge_color="#475569", edge_fontcolor="#1e293b"
    ),
}


class TextDiagramBuilder:
    def __init__(self, theme_name: str = "Dark Developer", style_name: str = "Classic Flowchart") -> None:
        if Digraph is None:
            raise RuntimeError("The graphviz Python package is not installed.")

        self.theme = THEMES.get(theme_name, THEMES["Dark Developer"])
        self.style_name = style_name
        
        # Configure layout engine based on diagram style
        engine = "dot"
        if style_name == "Circular Diagram":
            engine = "circo"
            
        self.graph = Digraph("text_diagram", format="png", engine=engine)
        self.graph.attr(dpi="300")
        
        # Base graph attributes
        rankdir = "LR" if style_name == "Process Flow UI" else "TB"
        nodesep = "0.8" if style_name == "Circular Diagram" else "0.5"
        
        self.graph.attr(
            rankdir=rankdir,
            bgcolor=self.theme.bgcolor,
            pad="0.5",
            nodesep=nodesep,
            ranksep="0.8",
        )
        
        # Adjust Node configuration based on styles
        shape = "rect"
        style = "filled,rounded"
        penwidth = "1.5"
        fontsize = "12"
        fontname = "Segoe UI, sans-serif"
        
        if style_name == "Step Cards":
            shape = "rect"
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
            margin="0.2,0.1"
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
            
            # Apply dynamic styles if needed
            shape = None
            if self.style_name == "Step Cards":
                # Cycle colors for cards
                colors = ["#0284c7", "#16a34a", "#9333ea", "#ea580c", "#ca8a04"]
                fillcolor = colors[self.counter % len(colors)]
                self.graph.node(node_id, label, fillcolor=fillcolor, fontcolor="#ffffff")
            else:
                self.graph.node(node_id, label, shape=shape)
                
        return self.node_registry[label]

    def _update_shape(self, label: str, shape: str):
        """Force a shape update for decision nodes."""
        if self.style_name in ("Classic Flowchart", "Process Flow UI"):
            node_id = self._get_node_id(label)
            self.graph.node(node_id, shape=shape)

    def build(self, text: str, output_path: str) -> str:
        """Parse raw text, apply smart keyword groupings, and output PNG."""
        # 1. Split by arrows or pure newlines safely
        chunks = [c.strip() for c in re.split(r'(?i)\s*->\s*|\s*→\s*|\n+', text) if c.strip()]
        if not chunks:
            return ""

        previous_node_label = None
        last_decision_label = None

        for chunk in chunks:
            lower_chunk = chunk.lower()
            
            # Smart Branching Detection
            is_if = lower_chunk.startswith("if ") or " if " in lower_chunk
            is_else = lower_chunk.startswith("else ") or " else " in lower_chunk or lower_chunk.startswith("otherwise")

            if is_if and previous_node_label:
                # Retrospectively mark the previous node as a decision diamond
                self._update_shape(previous_node_label, "diamond")
                last_decision_label = previous_node_label
                
                # Clean the text
                clean_text = re.sub(r'(?i)^if\s+([a-z0-9]+\s+)?', '', chunk).strip()
                if not clean_text: clean_text = "Action"
                
                # Connect branch
                src = self._get_node_id(previous_node_label)
                dst = self._get_node_id(clean_text)
                self.graph.edge(src, dst, label="Yes")
                
                previous_node_label = clean_text

            elif is_else and last_decision_label:
                # Clean the text
                clean_text = re.sub(r'(?i)^(else|otherwise)\s*', '', chunk).strip()
                if not clean_text: clean_text = "Fallback Action"
                
                # Connect branch back to the LAST decision node
                src = self._get_node_id(last_decision_label)
                dst = self._get_node_id(clean_text)
                self.graph.edge(src, dst, label="No")
                
                previous_node_label = clean_text

            else:
                # Standard linear link
                if previous_node_label:
                    src = self._get_node_id(previous_node_label)
                    dst = self._get_node_id(chunk)
                    self.graph.edge(src, dst)
                
                # For step 1, or sequential moves
                previous_node_label = chunk

        try:
            return self.graph.render(filename=output_path, cleanup=True)
        except Exception as exc:
            raise RuntimeError("Graphviz diagram execution failed.") from exc


def generate_text_diagram(text: str, output_dir: str = "static", theme: str = "Dark Developer", style: str = "Classic Flowchart") -> str:
    """Entry point for the text diagram feature."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_stem = f"autoflow_text_{uuid.uuid4().hex}"
    output_path = target_dir / file_stem

    builder = TextDiagramBuilder(theme_name=theme, style_name=style)
    return builder.build(text, str(output_path))


def generate_multi_diagram(steps: list[str], diagram_type: str = "Flowchart", output_dir: str = "static", theme: str = "Dark Developer") -> str:
    """Entry point for the multi-diagram generator from steps array."""
    if Digraph is None:
        raise RuntimeError("The graphviz Python package is not installed.")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_stem = f"autoflow_multi_{uuid.uuid4().hex}"
    output_path = target_dir / file_stem

    theme_obj = THEMES.get(theme, THEMES["Dark Developer"])
    
    # Configure graph attributes based on diagram_type
    engine = "dot"
    rankdir = "TB"
    nodesep = "0.5"
    shape = "box"
    
    if diagram_type == "Circular":
        engine = "circo"
        shape = "circle"
        nodesep = "0.8"
    elif diagram_type == "Block Diagram":
        rankdir = "LR"
        shape = "box"
    else: # Flowchart
        rankdir = "TB"
        shape = "box"

    graph = Digraph("multi_diagram", format="png", engine=engine)
    graph.attr(dpi="300", rankdir=rankdir, bgcolor=theme_obj.bgcolor, pad="0.5", nodesep=nodesep, ranksep="0.8")
    
    graph.attr(
        "node",
        fontname="Segoe UI, sans-serif",
        fontsize="12",
        color=theme_obj.node_color,
        fontcolor=theme_obj.node_fontcolor,
        penwidth="1.5",
        style="filled,rounded",
        fillcolor=theme_obj.node_fill,
        margin="0.2,0.1",
        shape=shape
    )
    
    graph.attr(
        "edge",
        color=theme_obj.edge_color,
        fontcolor=theme_obj.edge_fontcolor,
        penwidth="1.2",
        arrowsize="0.9",
        fontname="Segoe UI, sans-serif",
        fontsize="10",
    )

    if not steps:
        return ""

    node_registry = {}
    
    def get_node(label: str):
        if label not in node_registry:
            node_id = f"n_{len(node_registry)}"
            node_registry[label] = node_id
            
            # Smart shape for Flowchart
            node_shape = shape
            display_label = label
            if diagram_type == "Flowchart":
                lower_label = label.lower()
                if lower_label.startswith("if ") or " if " in lower_label:
                    node_shape = "diamond"
                    display_label = re.sub(r'(?i)^if\s+', '', label).strip()
                elif lower_label in ("start", "end"):
                    node_shape = "oval"

            graph.node(node_id, display_label, shape=node_shape)
        return node_registry[label]

    last_decision_id = None
    prev_id = None
    pending_no = False

    for i, step in enumerate(steps):
        lower_step = step.lower()
        
        # Determine if it's an else branch indicator 
        if diagram_type == "Flowchart" and (lower_step == "else" or lower_step == "otherwise" or lower_step == "else:" or lower_step == "except"):
            pending_no = True
            continue # skip creating an explicit "Else" node
            
        current_id = get_node(step)
        
        if pending_no:
            if last_decision_id:
                graph.edge(last_decision_id, current_id, label="No")
            elif prev_id:
                graph.edge(prev_id, current_id)
            pending_no = False
        else:
            if prev_id:
                label = ""
                # if previous was if, it connects as Yes
                if last_decision_id == prev_id:
                     label = "Yes"
                graph.edge(prev_id, current_id, label=label)
        
        if diagram_type == "Flowchart" and (lower_step.startswith("if ") or " if " in lower_step):
            last_decision_id = current_id
            
        prev_id = current_id

    try:
        return graph.render(filename=str(output_path), cleanup=True)
    except Exception as exc:
        raise RuntimeError(f"Graphviz diagram generation failed: {exc}") from exc
