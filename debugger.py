"""Utilities for checking Python code and applying simple automatic fixes."""

from __future__ import annotations

import ast
import base64
import subprocess
import sys
import traceback
from typing import Dict


def check_code(code: str) -> Dict[str, str | bool]:
    """Run code in an isolated subprocess and return captured output and errors."""
    result: Dict[str, str | bool] = {
        "success": False,
        "stdout": "",
        "error": "",
        "traceback": "",
    }

    try:
        compile(code, "<user_code>", "exec")
    except SyntaxError as exc:
        result["error"] = f"SyntaxError: {exc.msg} (line {exc.lineno})"
        result["traceback"] = traceback.format_exc()
        return result
    except Exception as exc:  # pragma: no cover - defensive guard
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        return result

    payload = base64.b64encode(code.encode("utf-8")).decode("ascii")
    runner = """
import base64
import builtins
import sys
import traceback

source = base64.b64decode(sys.argv[1]).decode("utf-8")
builtins.input = lambda prompt='': '0'
namespace = {"__name__": "__main__"}

try:
    exec(compile(source, "<user_code>", "exec"), namespace, namespace)
except Exception:
    traceback.print_exc()
    sys.exit(1)
"""

    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", runner, payload],
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        result["error"] = "TimeoutError: Code execution exceeded 5 seconds."
        result["traceback"] = "Execution stopped to keep the debugger responsive."
        return result
    except Exception as exc:  # pragma: no cover - defensive guard
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        return result

    result["stdout"] = completed.stdout.strip()
    if completed.returncode == 0:
        result["success"] = True
        return result

    traceback_text = completed.stderr.strip()
    result["traceback"] = traceback_text
    result["error"] = _extract_error_message(traceback_text)
    return result


def simple_fix(code: str) -> str:
    """Apply a few safe, lightweight syntax fixes."""
    fixed_lines = []
    for line in code.splitlines():
        updated_line = _fix_print_syntax(line)
        updated_line = _fix_line_brackets(updated_line)
        fixed_lines.append(updated_line)

    fixed_code = "\n".join(fixed_lines)
    fixed_code = _fix_global_brackets(fixed_code)
    return fixed_code


def _extract_error_message(traceback_text: str) -> str:
    for line in reversed(traceback_text.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return "Unknown execution error."


def _fix_print_syntax(line: str) -> str:
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]

    if not stripped.startswith("print ") or stripped.startswith("print ("):
        return line

    if stripped.startswith("print("):
        return line

    content = stripped[len("print ") :].rstrip()
    if not content:
        return f"{indent}print()"

    comment = ""
    if "#" in content:
        candidate, marker, tail = content.partition("#")
        if candidate.count('"') % 2 == 0 and candidate.count("'") % 2 == 0:
            content = candidate.rstrip()
            comment = f" {marker}{tail}"

    if content.endswith(","):
        content = content[:-1].rstrip()

    return f"{indent}print({content}){comment}"


def _fix_line_brackets(line: str) -> str:
    stack: list[str] = []
    closing = {")": "(", "]": "[", "}": "{"}
    opening = {"(": ")", "[": "]", "{": "}"}

    in_single = False
    in_double = False
    escaped = False

    for char in line:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if char in opening:
            stack.append(char)
        elif char in closing and stack and stack[-1] == closing[char]:
            stack.pop()

    if not stack:
        return line

    suffix = "".join(opening[char] for char in reversed(stack))
    stripped = line.rstrip()
    if stripped.endswith(":"):
        return f"{stripped[:-1]}{suffix}:"
    return f"{stripped}{suffix}"


def _fix_global_brackets(code: str) -> str:
    opening = {"(": ")", "[": "]", "{": "}"}
    closing = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []

    try:
        tokens = ast.parse(code)
        _ = tokens  # Keeps the parse explicit without changing behavior.
        return code
    except SyntaxError:
        pass

    in_single = False
    in_double = False
    escaped = False

    for char in code:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if char in opening:
            stack.append(char)
        elif char in closing and stack and stack[-1] == closing[char]:
            stack.pop()

    if not stack:
        return code

    suffix = "".join(opening[char] for char in reversed(stack))
    return f"{code}{suffix}"
