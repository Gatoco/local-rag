"""
Theme system for REPL visual styling.

Provides consistent theming across all REPL components without emojis.
"""

from dataclasses import dataclass, field
from typing import Any

from rich.theme import Theme as RichTheme


@dataclass
class BoxChars:
    """Box-drawing characters for panel borders."""

    horizontal: str = "─"
    vertical: str = "│"
    top_left: str = "┌"
    top_right: str = "┐"
    bottom_left: str = "└"
    bottom_right: str = "┘"
    tee_right: str = "├"
    tee_left: str = "┤"
    cross: str = "┼"
    top_tee: str = "┬"
    bottom_tee: str = "┴"

    # Double-line variants
    double_horizontal: str = "═"
    double_vertical: str = "║"
    double_top_left: str = "╔"
    double_top_right: str = "╗"
    double_bottom_left: str = "╚"
    double_bottom_right: str = "╝"

    # Heavy variants
    heavy_horizontal: str = "━"
    heavy_vertical: str = "┃"


@dataclass
class SyntaxTheme:
    """Syntax highlighting colors for code blocks."""

    keyword: str = "cyan"
    string: str = "green"
    number: str = "yellow"
    comment: str = "dim"
    function: str = "blue"
    class_name: str = "magenta"
    operator: str = "red"
    punctuation: str = "white"
    background: str = ""

    def to_rich_style_map(self) -> dict[str, str]:
        return {
            "keyword": self.keyword,
            "string": self.string,
            "number": self.number,
            "comment": self.comment,
            "function": self.function,
            "class": self.class_name,
            "operator": self.operator,
            "punctuation": self.punctuation,
        }


@dataclass
class ThemeColors:
    """Color palette for a theme."""

    primary: str = "cyan"
    secondary: str = "blue"
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"
    dim: str = "dim"
    info: str = "cyan"

    # Special elements
    user_message: str = "bold cyan"
    assistant_message: str = "white"
    system_message: str = "dim yellow"
    prompt: str = "bold cyan"

    # Status bar
    status_mode_local: str = "bold green"
    status_mode_cloud: str = "bold cyan"
    status_rag_on: str = "bold green"
    status_rag_off: str = "yellow"
    status_docs: str = "yellow"
    status_provider: str = "cyan"
    status_model: str = "white"

    # Panels
    panel_border: str = "cyan"
    panel_title: str = "bold cyan"
    panel_content: str = "white"

    # Code blocks
    code_border: str = "blue"
    code_content: str = "white"
    code_lineno: str = "dim"

    # Sources/timestamps
    sources: str = "dim cyan"
    metadata: str = "dim"

    def to_rich_theme(self) -> RichTheme:
        """Convert to Rich Theme object."""
        return RichTheme(
            {
                "info": self.info,
                "warning": self.warning,
                "error": self.error,
                "success": self.success,
                "prompt": self.prompt,
                "dim": self.dim,
            }
        )


@dataclass
class Theme:
    """Complete theme definition."""

    name: str
    colors: ThemeColors
    box_chars: BoxChars = field(default_factory=BoxChars)
    syntax: SyntaxTheme = field(default_factory=SyntaxTheme)
    box_style: str = "single"  # "single", "double", "heavy"

    def get_box_line(self, length: int, position: str = "horizontal") -> str:
        """Generate a box line of given length."""
        char = getattr(self.box_chars, f"{position}_{self.box_style}") if hasattr(self.box_chars, f"{position}_{self.box_style}") else getattr(self.box_chars, position)
        return char * length

    def get_panel_border_style(self) -> str:
        """Get Rich-compatible border style."""
        return self.colors.panel_border


# =============================================================================
# PREDEFINED THEMES
# =============================================================================

DARK_THEME = Theme(
    name="dark",
    colors=ThemeColors(
        primary="cyan",
        secondary="blue",
        success="green",
        warning="yellow",
        error="red",
        dim="dim",
        info="cyan",
        user_message="bold cyan",
        assistant_message="white",
        system_message="dim yellow",
        prompt="bold cyan",
        status_mode_local="bold green",
        status_mode_cloud="bold cyan",
        status_rag_on="bold green",
        status_rag_off="yellow",
        status_docs="yellow",
        status_provider="cyan",
        status_model="white",
        panel_border="cyan",
        panel_title="bold cyan",
        panel_content="white",
        code_border="blue",
        code_content="white",
        code_lineno="dim",
        sources="dim cyan",
        metadata="dim",
    ),
    box_chars=BoxChars(),
    syntax=SyntaxTheme(
        keyword="cyan",
        string="green",
        number="yellow",
        comment="dim",
        function="blue",
        class_name="magenta",
        operator="red",
    ),
    box_style="single",
)

LIGHT_THEME = Theme(
    name="light",
    colors=ThemeColors(
        primary="blue",
        secondary="cyan",
        success="green",
        warning="yellow",
        error="red",
        dim="dim black",
        info="blue",
        user_message="bold blue",
        assistant_message="black",
        system_message="dim black",
        prompt="bold blue",
        status_mode_local="bold green",
        status_mode_cloud="bold blue",
        status_rag_on="bold green",
        status_rag_off="yellow",
        status_docs="magenta",
        status_provider="blue",
        status_model="black",
        panel_border="blue",
        panel_title="bold blue",
        panel_content="black",
        code_border="blue",
        code_content="black",
        code_lineno="dim black",
        sources="dim blue",
        metadata="dim black",
    ),
    box_chars=BoxChars(
        horizontal="─",
        vertical="│",
        top_left="┌",
        top_right="┐",
        bottom_left="└",
        bottom_right="┘",
    ),
    syntax=SyntaxTheme(
        keyword="blue",
        string="green",
        number="magenta",
        comment="dim black",
        function="cyan",
        class_name="magenta",
        operator="red",
    ),
    box_style="single",
)

MINIMAL_THEME = Theme(
    name="minimal",
    colors=ThemeColors(
        primary="white",
        secondary="white",
        success="green",
        warning="yellow",
        error="red",
        dim="dim white",
        info="white",
        user_message="bold white",
        assistant_message="white",
        system_message="dim white",
        prompt="bold white",
        status_mode_local="bold white",
        status_mode_cloud="bold white",
        status_rag_on="bold white",
        status_rag_off="dim white",
        status_docs="white",
        status_provider="white",
        status_model="white",
        panel_border="white",
        panel_title="bold white",
        panel_content="white",
        code_border="white",
        code_content="white",
        code_lineno="dim white",
        sources="dim white",
        metadata="dim white",
    ),
    box_chars=BoxChars(
        horizontal="-",
        vertical="|",
        top_left="+",
        top_right="+",
        bottom_left="+",
        bottom_right="+",
    ),
    syntax=SyntaxTheme(
        keyword="white",
        string="green",
        number="yellow",
        comment="dim white",
        function="cyan",
        class_name="magenta",
        operator="white",
    ),
    box_style="single",
)


AVAILABLE_THEMES: dict[str, Theme] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "minimal": MINIMAL_THEME,
}


class ThemeManager:
    """Manages theme selection and application."""

    def __init__(self, initial_theme: str = "dark") -> None:
        self._current_theme_name = initial_theme
        self._themes = AVAILABLE_THEMES.copy()

    @property
    def current(self) -> Theme:
        """Get the current active theme."""
        return self._themes.get(self._current_theme_name, DARK_THEME)

    @property
    def current_name(self) -> str:
        """Get current theme name."""
        return self._current_theme_name

    def set_theme(self, name: str) -> bool:
        """Set active theme by name. Returns True if successful."""
        if name in self._themes:
            self._current_theme_name = name
            return True
        return False

    def get_available_themes(self) -> list[str]:
        """Get list of available theme names."""
        return list(self._themes.keys())

    def apply_to_console(self, console: Any) -> None:
        """Apply current theme colors to a Rich Console instance."""
        rich_theme = self.current.colors.to_rich_theme()
        console._theme = rich_theme  # noqa: SLF001
