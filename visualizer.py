"""Graphviz-based flowchart rendering with domain-aware visual themes."""

from __future__ import annotations

import ast
import uuid
from dataclasses import dataclass
from pathlib import Path

from analyzer import Theme, apply_color_overrides

try:
    from graphviz import Digraph
    try:
        from graphviz.backend import ExecutableNotFound
    except ImportError:  # pragma: no cover - compatibility fallback
        from graphviz.backend.execute import ExecutableNotFound
except ImportError:  # pragma: no cover - handled at runtime
    Digraph = None

    class ExecutableNotFound(Exception):
        """Fallback exception when Graphviz is unavailable."""


@dataclass
class FlowExit:
    node_id: str
    edge_label: str | None = None


class ThemedFlowchartBuilder:
    """Create a themed flowchart from Python AST nodes."""

    def __init__(self, theme: Theme) -> None:
        if Digraph is None:
            raise RuntimeError("The graphviz package is not installed.")

        self.theme = theme
        self.graph = Digraph("autoflow_theme", format="png")
        self.graph.attr(rankdir="TB", bgcolor="#0f172a", pad="0.35", nodesep="0.55", ranksep="0.75")
        self.graph.attr(
            "node",
            fontname="Consolas",
            fontsize="12",
            style="filled,rounded",
            color=theme.secondary_color,
            fontcolor=theme.text_color,
            penwidth="1.3",
        )
        self.graph.attr(
            "edge",
            color=theme.edge_color,
            fontcolor=theme.edge_color,
            fontname="Consolas",
            fontsize="10",
        )
        self.counter = 0

    def build(self, code: str, output_path: Path) -> Path:
        tree = ast.parse(code)
        start_node = self._add_node("Start", self.theme.start_end_shape, self.theme.primary_color)
        exits = self._build_block(tree.body, [FlowExit(start_node)])
        end_node = self._add_node("End", self.theme.start_end_shape, self.theme.secondary_color)

        for flow_exit in exits:
            self._connect(flow_exit, end_node)

        try:
            rendered = self.graph.render(filename=str(output_path), cleanup=True)
        except ExecutableNotFound as exc:
            raise RuntimeError("Graphviz executable not found. Install Graphviz and add 'dot' to PATH.") from exc

        return Path(rendered)

    def _build_block(self, statements: list[ast.stmt], incoming: list[FlowExit]) -> list[FlowExit]:
        exits = incoming
        for statement in statements:
            exits = self._build_statement(statement, exits)
        return exits

    def _build_statement(self, statement: ast.stmt, incoming: list[FlowExit]) -> list[FlowExit]:
        if isinstance(statement, ast.If):
            return self._build_if(statement, incoming)
        if isinstance(statement, ast.While):
            return self._build_while(statement, incoming)

        label = self._statement_label(statement)
        node_id = self._add_node(label, self.theme.process_shape, self.theme.primary_color)
        for flow_exit in incoming:
            self._connect(flow_exit, node_id)
        return [FlowExit(node_id)]

    def _build_if(self, statement: ast.If, incoming: list[FlowExit]) -> list[FlowExit]:
        node_id = self._add_node(
            f"If {self._to_source(statement.test)}?",
            self.theme.decision_shape,
            self.theme.secondary_color,
        )
        for flow_exit in incoming:
            self._connect(flow_exit, node_id)

        true_exits = (
            self._build_block(statement.body, [FlowExit(node_id, "True")])
            if statement.body
            else [FlowExit(node_id, "True")]
        )
        false_exits = (
            self._build_block(statement.orelse, [FlowExit(node_id, "False")])
            if statement.orelse
            else [FlowExit(node_id, "False")]
        )
        return true_exits + false_exits

    def _build_while(self, statement: ast.While, incoming: list[FlowExit]) -> list[FlowExit]:
        node_id = self._add_node(
            f"While {self._to_source(statement.test)}?",
            self.theme.decision_shape,
            self.theme.secondary_color,
        )
        for flow_exit in incoming:
            self._connect(flow_exit, node_id)

        body_exits = (
            self._build_block(statement.body, [FlowExit(node_id, "Loop")])
            if statement.body
            else [FlowExit(node_id, "Loop")]
        )
        for flow_exit in body_exits:
            self._connect(FlowExit(flow_exit.node_id), node_id)

        return [FlowExit(node_id, "Done")]

    def _statement_label(self, statement: ast.stmt) -> str:
        if isinstance(statement, ast.Assign):
            targets = ", ".join(self._to_source(target) for target in statement.targets)
            return f"{targets} = {self._to_source(statement.value)}"
        if isinstance(statement, ast.AnnAssign):
            value = self._to_source(statement.value) if statement.value else "None"
            return f"{self._to_source(statement.target)} = {value}"
        if isinstance(statement, ast.AugAssign):
            return (
                f"{self._to_source(statement.target)} "
                f"{self._operator_symbol(statement.op)}= {self._to_source(statement.value)}"
            )
        if isinstance(statement, ast.Expr):
            return self._to_source(statement.value)
        return self._to_source(statement)

    def _add_node(self, label: str, shape: str, fillcolor: str) -> str:
        node_id = f"node_{self.counter}"
        self.counter += 1
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

    @staticmethod
    def _operator_symbol(operator: ast.operator) -> str:
        mapping = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.Pow: "**",
            ast.FloorDiv: "//",
        }
        return mapping.get(type(operator), "?")


def generate_flowchart(
    code: str,
    theme: Theme,
    output_dir: Path,
    primary_override: str | None = None,
    secondary_override: str | None = None,
) -> Path:
    """Generate a themed flowchart image and return the created PNG path."""
    resolved_theme = apply_color_overrides(theme, primary_override, secondary_override)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"autoflow_theme_{uuid.uuid4().hex}"
    builder = ThemedFlowchartBuilder(resolved_theme)
    return builder.build(code, file_path)
