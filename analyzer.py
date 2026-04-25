"""Domain detection logic and theme definitions for AUTOFLOW AI."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Theme:
    name: str
    description: str
    shape_family: str
    primary_color: str
    secondary_color: str
    start_end_shape: str
    process_shape: str
    decision_shape: str
    edge_color: str
    text_color: str = "#ffffff"


@dataclass(frozen=True)
class ThemeSuggestion:
    theme: Theme
    matched_keywords: tuple[str, ...]


DOMAIN_THEMES: dict[str, Theme] = {
    "Cybersecurity": Theme(
        name="Cybersecurity",
        description="Security-heavy code detected. The flowchart uses stronger, defensive visual cues.",
        shape_family="Octagons and secure alert forms",
        primary_color="#B91C1C",
        secondary_color="#1E3A8A",
        start_end_shape="doubleoctagon",
        process_shape="octagon",
        decision_shape="diamond",
        edge_color="#93C5FD",
    ),
    "Cloud": Theme(
        name="Cloud",
        description="Infrastructure keywords detected. The flowchart switches to a cloud-centric look.",
        shape_family="Clouds and rounded bubbles",
        primary_color="#38BDF8",
        secondary_color="#FFFFFF",
        start_end_shape="cloud",
        process_shape="oval",
        decision_shape="diamond",
        edge_color="#E0F2FE",
        text_color="#0f172a",
    ),
    "Environment": Theme(
        name="Environment",
        description="Nature or tree-related vocabulary detected. The flowchart adopts an organic theme.",
        shape_family="Leaf-like and organic silhouettes",
        primary_color="#059669",
        secondary_color="#7C4A21",
        start_end_shape="egg",
        process_shape="ellipse",
        decision_shape="diamond",
        edge_color="#D9F99D",
    ),
    "Default": Theme(
        name="Default",
        description="No strong domain match was found. A balanced neutral theme is used.",
        shape_family="Clean flowchart defaults",
        primary_color="#2563EB",
        secondary_color="#334155",
        start_end_shape="ellipse",
        process_shape="box",
        decision_shape="diamond",
        edge_color="#CBD5E1",
    ),
}


DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Cybersecurity": ("hash", "encrypt", "auth", "login"),
    "Cloud": ("cloud", "aws", "s3", "server"),
    "Environment": ("tree", "leaf", "forest", "environmental"),
}


def detect_domain_theme(code: str) -> ThemeSuggestion:
    """Detect the best theme by counting theme keyword matches in the code snippet."""
    lowered_code = code.lower()

    best_theme_name = "Default"
    best_keywords: tuple[str, ...] = ()
    best_score = 0

    for theme_name, keywords in DOMAIN_KEYWORDS.items():
        matched = tuple(keyword for keyword in keywords if re.search(rf"\b{re.escape(keyword)}\b", lowered_code))
        if len(matched) > best_score:
            best_theme_name = theme_name
            best_keywords = matched
            best_score = len(matched)

    return ThemeSuggestion(theme=DOMAIN_THEMES[best_theme_name], matched_keywords=best_keywords)


def normalize_color_override(color_value: str) -> str | None:
    """Validate an optional hex color override and normalize empty values to None."""
    cleaned = color_value.strip()
    if not cleaned:
        return None

    if re.fullmatch(r"#[0-9a-fA-F]{6}", cleaned):
        return cleaned.upper()

    raise ValueError("Color overrides must use hex format like #38BDF8.")


def apply_color_overrides(theme: Theme, primary: str | None = None, secondary: str | None = None) -> Theme:
    """Return a new theme instance with optional color overrides."""
    return replace(
        theme,
        primary_color=primary or theme.primary_color,
        secondary_color=secondary or theme.secondary_color,
    )
