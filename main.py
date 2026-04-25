"""Desktop UI for AUTOFLOW AI theme detection and themed flowchart generation."""

from __future__ import annotations

import webbrowser
from pathlib import Path

import customtkinter as ctk

from analyzer import DOMAIN_THEMES, ThemeSuggestion, detect_domain_theme, normalize_color_override
from visualizer import generate_flowchart

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

OUTPUT_DIR = Path(__file__).resolve().parent / "generated_flowcharts"


class AutoFlowApp(ctk.CTk):
    """Main customtkinter application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title("AUTOFLOW AI")
        self.geometry("1220x780")
        self.minsize(1080, 720)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.analysis_job: str | None = None
        self.suggestion: ThemeSuggestion = detect_domain_theme("")
        self.generated_file: Path | None = None

        self.theme_choice = ctk.StringVar(value="Suggested Theme")
        self.primary_color_var = ctk.StringVar(value="")
        self.secondary_color_var = ctk.StringVar(value="")

        self._build_layout()
        self._update_theme_display()

    def _build_layout(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="#111827", corner_radius=24)
        wrapper.grid(row=0, column=0, padx=18, pady=18, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(24, 14), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="AUTOFLOW AI",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#f8fafc",
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Analyze Python code, detect its domain, and generate a themed Graphviz flowchart.",
            font=ctk.CTkFont(size=15),
            text_color="#94a3b8",
        )
        subtitle.grid(row=1, column=0, pady=(6, 0), sticky="w")

        content = ctk.CTkFrame(wrapper, fg_color="transparent")
        content.grid(row=1, column=0, padx=24, pady=(0, 24), sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        self._build_editor_panel(content)
        self._build_sidebar(content)

    def _build_editor_panel(self, parent: ctk.CTkFrame) -> None:
        editor_panel = ctk.CTkFrame(parent, fg_color="#1f2937", corner_radius=22)
        editor_panel.grid(row=0, column=0, padx=(0, 14), sticky="nsew")
        editor_panel.grid_columnconfigure(0, weight=1)
        editor_panel.grid_rowconfigure(1, weight=1)

        panel_header = ctk.CTkFrame(editor_panel, fg_color="transparent")
        panel_header.grid(row=0, column=0, padx=20, pady=(18, 12), sticky="ew")
        panel_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel_header,
            text="Python Snippet",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e2e8f0",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            panel_header,
            text="Paste code here. The suggested theme updates automatically.",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
        ).grid(row=1, column=0, pady=(4, 0), sticky="w")

        self.code_text = ctk.CTkTextbox(
            editor_panel,
            fg_color="#0f172a",
            border_width=1,
            border_color="#334155",
            corner_radius=18,
            font=("Consolas", 15),
            text_color="#f8fafc",
            wrap="none",
        )
        self.code_text.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="nsew")
        self.code_text.insert(
            "1.0",
            "def hash_user_password(password):\n"
            "    encrypted = password.encode('utf-8')\n"
            "    if login_attempts > 3:\n"
            "        auth_result = 'blocked'\n"
            "    else:\n"
            "        auth_result = 'allowed'\n"
            "    return auth_result\n",
        )
        self.code_text.bind("<KeyRelease>", self._schedule_analysis)

    def _build_sidebar(self, parent: ctk.CTkFrame) -> None:
        sidebar = ctk.CTkFrame(parent, fg_color="#172033", corner_radius=22)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="Theme Controls",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e2e8f0",
        ).grid(row=0, column=0, padx=20, pady=(18, 6), sticky="w")

        ctk.CTkLabel(
            sidebar,
            text="Suggested Theme",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8",
        ).grid(row=1, column=0, padx=20, sticky="w")

        self.theme_badge = ctk.CTkLabel(
            sidebar,
            text="Default",
            corner_radius=16,
            width=180,
            height=34,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.theme_badge.grid(row=2, column=0, padx=20, pady=(8, 14), sticky="w")

        self.matched_keywords_label = ctk.CTkLabel(
            sidebar,
            text="Matched Keywords: none",
            justify="left",
            text_color="#cbd5e1",
            font=ctk.CTkFont(size=13),
        )
        self.matched_keywords_label.grid(row=3, column=0, padx=20, sticky="w")

        self.theme_summary_label = ctk.CTkLabel(
            sidebar,
            text="Theme style information will appear here.",
            justify="left",
            wraplength=360,
            text_color="#94a3b8",
            font=ctk.CTkFont(size=13),
        )
        self.theme_summary_label.grid(row=4, column=0, padx=20, pady=(10, 18), sticky="w")

        ctk.CTkLabel(
            sidebar,
            text="Theme To Apply",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8",
        ).grid(row=5, column=0, padx=20, sticky="w")

        self.theme_option = ctk.CTkOptionMenu(
            sidebar,
            values=["Suggested Theme", "Cybersecurity", "Cloud", "Environment", "Default"],
            variable=self.theme_choice,
            fg_color="#0ea5e9",
            button_color="#0284c7",
            button_hover_color="#0369a1",
        )
        self.theme_option.grid(row=6, column=0, padx=20, pady=(8, 18), sticky="ew")

        ctk.CTkLabel(
            sidebar,
            text="Primary Color Override",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8",
        ).grid(row=7, column=0, padx=20, sticky="w")

        self.primary_entry = ctk.CTkEntry(
            sidebar,
            textvariable=self.primary_color_var,
            placeholder_text="#B91C1C",
        )
        self.primary_entry.grid(row=8, column=0, padx=20, pady=(8, 14), sticky="ew")

        ctk.CTkLabel(
            sidebar,
            text="Secondary Color Override",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8",
        ).grid(row=9, column=0, padx=20, sticky="w")

        self.secondary_entry = ctk.CTkEntry(
            sidebar,
            textvariable=self.secondary_color_var,
            placeholder_text="#1E3A8A",
        )
        self.secondary_entry.grid(row=10, column=0, padx=20, pady=(8, 18), sticky="ew")

        actions = ctk.CTkFrame(sidebar, fg_color="transparent")
        actions.grid(row=11, column=0, padx=20, pady=(0, 18), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        analyze_button = ctk.CTkButton(
            actions,
            text="Analyze Theme",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._run_analysis,
        )
        analyze_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        generate_button = ctk.CTkButton(
            actions,
            text="Generate Flowchart",
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._generate_flowchart,
        )
        generate_button.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.output_label = ctk.CTkLabel(
            sidebar,
            text="No flowchart generated yet.",
            justify="left",
            wraplength=360,
            text_color="#e2e8f0",
            font=ctk.CTkFont(size=13),
        )
        self.output_label.grid(row=12, column=0, padx=20, sticky="w")

        self.open_button = ctk.CTkButton(
            sidebar,
            text="Open Generated Flowchart",
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            state="disabled",
            command=self._open_generated_flowchart,
        )
        self.open_button.grid(row=13, column=0, padx=20, pady=(16, 20), sticky="ew")

    def _schedule_analysis(self, _: object) -> None:
        if self.analysis_job is not None:
            self.after_cancel(self.analysis_job)
        self.analysis_job = self.after(250, self._run_analysis)

    def _run_analysis(self) -> None:
        code = self.code_text.get("1.0", "end").strip()
        self.suggestion = detect_domain_theme(code)
        self._update_theme_display()

    def _update_theme_display(self) -> None:
        theme = self.suggestion.theme
        matched = ", ".join(self.suggestion.matched_keywords) if self.suggestion.matched_keywords else "none"

        self.theme_badge.configure(
            text=theme.name,
            fg_color=theme.primary_color,
            text_color="#ffffff" if theme.name != "Cloud" else "#0f172a",
        )
        self.matched_keywords_label.configure(text=f"Matched Keywords: {matched}")
        self.theme_summary_label.configure(
            text=(
                f"{theme.description}\n"
                f"Shapes: {theme.shape_family}\n"
                f"Colors: {theme.primary_color} and {theme.secondary_color}"
            )
        )

    def _resolve_theme_name(self) -> str:
        selected = self.theme_choice.get()
        if selected == "Suggested Theme":
            return self.suggestion.theme.name
        return selected

    def _generate_flowchart(self) -> None:
        code = self.code_text.get("1.0", "end").strip()
        if not code:
            self.output_label.configure(text="Paste Python code before generating a flowchart.")
            return

        theme_name = self._resolve_theme_name()
        theme = DOMAIN_THEMES[theme_name]

        primary_override = normalize_color_override(self.primary_color_var.get())
        secondary_override = normalize_color_override(self.secondary_color_var.get())

        try:
            output_file = generate_flowchart(
                code=code,
                theme=theme,
                output_dir=OUTPUT_DIR,
                primary_override=primary_override,
                secondary_override=secondary_override,
            )
        except ValueError as exc:
            self.output_label.configure(text=str(exc))
            self.open_button.configure(state="disabled")
            self.generated_file = None
            return
        except Exception as exc:  # pragma: no cover - defensive guard
            self.output_label.configure(text=f"Flowchart generation failed: {exc}")
            self.open_button.configure(state="disabled")
            self.generated_file = None
            return

        self.generated_file = output_file
        self.output_label.configure(
            text=(
                f"Applied Theme: {theme_name}\n"
                f"Primary Color: {primary_override or theme.primary_color}\n"
                f"Secondary Color: {secondary_override or theme.secondary_color}\n"
                f"Saved To: {output_file}"
            )
        )
        self.open_button.configure(state="normal")

    def _open_generated_flowchart(self) -> None:
        if self.generated_file is None:
            return
        webbrowser.open(self.generated_file.resolve().as_uri())


def main() -> None:
    app = AutoFlowApp()
    app.mainloop()


if __name__ == "__main__":
    main()
