"""AST-powered flowchart generation for AutoFlow AI, featuring HD output, styles, and themes."""

from __future__ import annotations

import ast
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from graphviz import Digraph
except ImportError:  # pragma: no cover
    Digraph = None


@dataclass
class FlowExit:
    node_id: str
    edge_label: Optional[str] = None


@dataclass
class FlowchartTheme:
    bgcolor: str
    node_fill: str
    node_color: str
    node_fontcolor: str
    edge_color: str
    edge_fontcolor: str


THEMES = {
    "Dark Developer": FlowchartTheme(
        bgcolor="#0f172a", node_fill="#1e293b", node_color="#334155", 
        node_fontcolor="#e2e8f0", edge_color="#94a3b8", edge_fontcolor="#cbd5e1"
    ),
    "Blue Theme": FlowchartTheme(
        bgcolor="#0a192f", node_fill="#112240", node_color="#233554", 
        node_fontcolor="#64ffda", edge_color="#8892b0", edge_fontcolor="#a8b2d1"
    ),
    "Green Theme": FlowchartTheme(
        bgcolor="#064e3b", node_fill="#065f46", node_color="#047857", 
        node_fontcolor="#ecfdf5", edge_color="#a7f3d0", edge_fontcolor="#d1fae5"
    ),
    "Purple Theme": FlowchartTheme(
        bgcolor="#2e1065", node_fill="#3b0764", node_color="#4c1d95", 
        node_fontcolor="#f3e8ff", edge_color="#d8b4fe", edge_fontcolor="#e9d5ff"
    ),
    "PPT": FlowchartTheme(
        bgcolor="#ffffff", node_fill="#f8fafc", node_color="#cbd5e1", 
        node_fontcolor="#0f172a", edge_color="#475569", edge_fontcolor="#1e293b"
    ),
}

STYLES = {
    "Simple": {"pad": "0.3", "nodesep": "0.5", "ranksep": "0.6", "fontsize": "12", "penwidth": "1.0"},
    "Detailed": {"pad": "0.5", "nodesep": "0.7", "ranksep": "0.8", "fontsize": "11", "penwidth": "1.2"},
    "Presentation Mode": {"pad": "0.6", "nodesep": "0.8", "ranksep": "1.0", "fontsize": "16", "penwidth": "2.0"},
    "Minimal": {"pad": "0.2", "nodesep": "0.4", "ranksep": "0.5", "fontsize": "10", "penwidth": "0.8"},
    "Colorful": {"pad": "0.4", "nodesep": "0.6", "ranksep": "0.75", "fontsize": "14", "penwidth": "1.5"},
}

class FlowchartBuilder:
    def __init__(self, theme_name: str = "Dark Developer", style_name: str = "Simple", detail_mode: str = "Simplified") -> None:
        if Digraph is None:
            raise RuntimeError("The graphviz Python package is not installed.")

        self.theme = THEMES.get(theme_name, THEMES["Dark Developer"])
        self.style = STYLES.get(style_name, STYLES["Simple"])
        self.detail_mode = detail_mode
        
        self.graph = Digraph("autoflow", format="png")
        self.graph.attr(dpi="300")  # HD Flowchart Output
        
        self.graph.attr(
            rankdir="TB",
            bgcolor=self.theme.bgcolor,
            pad=self.style["pad"],
            nodesep=self.style["nodesep"],
            ranksep=self.style["ranksep"],
        )
        self.graph.attr(
            "node",
            fontname="Segoe UI, sans-serif",
            fontsize=self.style["fontsize"],
            color=self.theme.node_color,
            fontcolor=self.theme.node_fontcolor,
            penwidth=self.style["penwidth"],
            style="filled,rounded",
            fillcolor=self.theme.node_fill,
        )
        self.graph.attr(
            "edge",
            color=self.theme.edge_color,
            fontcolor=self.theme.edge_fontcolor,
            penwidth=self.style["penwidth"],
            arrowsize="0.9",
            fontname="Segoe UI, sans-serif",
            fontsize=str(int(self.style["fontsize"]) - 2),
        )
        self.counter = 0

    def build(self, code: str, output_path: str) -> str:
        render_target = Path(output_path)
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ""

        start_node = self._add_node("Start", "oval")
        exits = self._build_block(tree.body, [FlowExit(start_node)])
        end_node = self._add_node("End", "oval")

        for flow_exit in exits:
            self._connect(flow_exit, end_node)

        try:
            return self.graph.render(filename=render_target.name, directory=str(render_target.parent), cleanup=True)
        except Exception as exc:
            raise RuntimeError("Graphviz execution failed.") from exc

    def _build_block(self, statements: list[ast.stmt], incoming: list[FlowExit]) -> list[FlowExit]:
        exits = incoming
        
        if self.detail_mode == "Simplified":
            # Collapse multiple basic statements into fewer nodes, but preserve I/O
            simplified_ops = []
            for stmt in statements:
                if isinstance(stmt, (ast.If, ast.While, ast.For)):
                    simplified_ops.append(stmt)
                else:
                    # Check if I/O
                    is_io = False
                    io_type = "Process Data"
                    shape = "rectangle"
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                        if isinstance(stmt.value.func, ast.Name):
                            if stmt.value.func.id == "print":
                                is_io = True; io_type = "Display Output"
                            elif stmt.value.func.id == "input":
                                is_io = True; io_type = "Take Input"
                    if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                        if getattr(stmt.value.func, 'id', None) == 'input':
                            is_io = True; io_type = "Take Input"
                    
                    if is_io:
                        simplified_ops.append((io_type, "parallelogram"))
                    else:
                        simplified_ops.append(("Process Data", "rectangle"))
                        
            # Merge consecutive "Process Data"
            merged_ops = []
            for op in simplified_ops:
                if merged_ops and merged_ops[-1] == ("Process Data", "rectangle") and op == ("Process Data", "rectangle"):
                    continue
                merged_ops.append(op)
                
            # Limit flowchart size inside a block
            if len(merged_ops) > 6:
                merged_ops = merged_ops[:3] + [("Process Flow", "rectangle")] + merged_ops[-2:]
                
            for op in merged_ops:
                if isinstance(op, tuple):
                    label, shape = op
                    node_id = self._add_node(label, shape)
                    for flow_exit in exits:
                        self._connect(flow_exit, node_id)
                    exits = [FlowExit(node_id)]
                else:
                    exits = self._build_statement(op, exits)
            return exits

        for statement in statements:
            exits = self._build_statement(statement, exits)
        return exits

    def _build_statement(self, statement: ast.stmt, incoming: list[FlowExit]) -> list[FlowExit]:
        if isinstance(statement, ast.If):
            return self._build_if(statement, incoming)
        if isinstance(statement, (ast.While, ast.For)):
            return self._build_loop(statement, incoming)

        label = self._statement_label(statement)
        shape = "rectangle"  # Default process

        # Determine I/O Parallelogram
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            if isinstance(statement.value.func, ast.Name) and statement.value.func.id in ("print", "input"):
                shape = "parallelogram"

        node_id = self._add_node(label, shape)
        for flow_exit in incoming:
            self._connect(flow_exit, node_id)
        return [FlowExit(node_id)]

    def _build_if(self, statement: ast.If, incoming: list[FlowExit]) -> list[FlowExit]:
        label = "Check Condition?" if self.detail_mode == "Simplified" else f"If {self._to_source(statement.test)}?"
        decision_node = self._add_node(label, "diamond")
        for flow_exit in incoming:
            self._connect(flow_exit, decision_node)

        true_exits = self._build_block(statement.body, [FlowExit(decision_node, "True")]) if statement.body else [FlowExit(decision_node, "True")]
        false_exits = self._build_block(statement.orelse, [FlowExit(decision_node, "False")]) if statement.orelse else [FlowExit(decision_node, "False")]
        return true_exits + false_exits

    def _build_loop(self, statement: ast.stmt, incoming: list[FlowExit]) -> list[FlowExit]:
        if self.detail_mode == "Simplified":
            label = "Repeat Process?"
        else:
            test_source = self._to_source(statement.test) if isinstance(statement, ast.While) else self._to_source(statement)
            label = f"Loop {test_source}?"
        decision_node = self._add_node(label, "diamond")
        for flow_exit in incoming:
            self._connect(flow_exit, decision_node)

        if hasattr(statement, "body") and statement.body:
            body_exits = self._build_block(statement.body, [FlowExit(decision_node, "True")])
            for flow_exit in body_exits:
                self._connect(flow_exit, decision_node)
        else:
            self.graph.edge(decision_node, decision_node, label="True")

        return [FlowExit(decision_node, "False")]

    def _statement_label(self, statement: ast.stmt) -> str:
        if isinstance(statement, ast.Assign):
            targets = ", ".join(self._to_source(target) for target in statement.targets)
            return f"{targets} = {self._to_source(statement.value)}"
        if isinstance(statement, ast.Expr):
            return self._to_source(statement.value)
        return self._to_source(statement)

    def _add_node(self, label: str, shape: str) -> str:
        node_id = f"node_{self.counter}"
        self.counter += 1
        # If theme is colorful, add varied colors based on shape
        fillcolor = self.theme.node_fill
        if self.style == STYLES["Colorful"]:
            if shape == "diamond": fillcolor = "#d97706"
            elif shape == "parallelogram": fillcolor = "#0284c7"
            elif shape == "oval": fillcolor = "#16a34a"
        
        self.graph.node(node_id, label, shape=shape, fillcolor=fillcolor)
        return node_id

    def _connect(self, flow_exit: FlowExit, target: str) -> None:
        if flow_exit.edge_label:
            self.graph.edge(flow_exit.node_id, target, label=flow_exit.edge_label)
        else:
            self.graph.edge(flow_exit.node_id, target)

    @staticmethod
    def _to_source(node: ast.AST) -> str:
        if hasattr(ast, "unparse"):
            return ast.unparse(node)
        return ast.dump(node, annotate_fields=False)


def generate_flowchart(code: str, output_dir: str = "static", theme: str = "Dark Developer", style: str = "Simple", detail_mode: str = "Simplified") -> str:
    """Generate a high-resolution PNG flowchart."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_stem = f"autoflow_hd_{uuid.uuid4().hex}"
    output_path = target_dir / file_stem

    builder = FlowchartBuilder(theme_name=theme, style_name=style, detail_mode=detail_mode)
    return builder.build(code, str(output_path))

