"""
Box drawing utilities for styled panels and borders.

Provides a clean API for creating box-drawn elements without emojis.
"""



from .themes import Theme, ThemeManager

# =============================================================================
# BOX DIMENSIONS
# =============================================================================

MIN_PANEL_WIDTH = 60
DEFAULT_PANEL_WIDTH = 80
MAX_PANEL_WIDTH = 120


# =============================================================================
# PANEL BUILDER
# =============================================================================

class BoxBuilder:
    """Builds box-drawn panels with consistent styling."""

    def __init__(self, theme: Theme | None = None) -> None:
        self.theme = theme or ThemeManager().current
        self._content_lines: list[str] = []
        self._title: str | None = None
        self._subtitle: str | None = None
        self._width: int = DEFAULT_PANEL_WIDTH

    def title(self, text: str) -> "BoxBuilder":
        """Set panel title."""
        self._title = text
        return self

    def subtitle(self, text: str) -> "BoxBuilder":
        """Set panel subtitle."""
        self._subtitle = text
        return self

    def width(self, width: int) -> "BoxBuilder":
        """Set panel width."""
        self._width = max(MIN_PANEL_WIDTH, min(width, MAX_PANEL_WIDTH))
        return self

    def add_line(self, text: str, style: str | None = None) -> "BoxBuilder":
        """Add a content line."""
        self._content_lines.append((text, style or self.theme.colors.panel_content))
        return self

    def add_spacer(self, height: int = 1) -> "BoxBuilder":
        """Add blank lines."""
        for _ in range(height):
            self._content_lines.append(("", self.theme.colors.panel_content))
        return self

    def add_divider(self) -> "BoxBuilder":
        """Add a horizontal divider."""
        line = self.theme.box_chars.horizontal * (self._width - 2)
        self._content_lines.append((line, self.theme.colors.dim))
        return self

    def build(self) -> list[tuple[str, str]]:
        """Build the complete panel content as (text, style) tuples."""
        lines: list[tuple[str, str]] = []

        # Top border with optional title
        if self._title:
            title_text = f" {self._title} "
            lines.append((title_text, self.theme.colors.panel_title))
        else:
            top_line = (
                f"{self.theme.box_chars.top_left}"
                f"{self.theme.box_chars.horizontal * (self._width - 2)}"
                f"{self.theme.box_chars.top_right}"
            )
            lines.append((top_line, self.theme.colors.panel_border))

        # Content lines
        for text, style in self._content_lines:
            if text:
                # Pad line to width
                padded = f"{self.theme.box_chars.vertical} {text:<{self._width - 4}} {self.theme.box_chars.vertical}"
            else:
                padded = (
                    f"{self.theme.box_chars.vertical}"
                    f"{' ' * (self._width - 2)}"
                    f"{self.theme.box_chars.vertical}"
                )
            lines.append((padded, style))

        # Bottom border
        bottom_line = (
            f"{self.theme.box_chars.bottom_left}"
            f"{self.theme.box_chars.horizontal * (self._width - 2)}"
            f"{self.theme.box_chars.bottom_right}"
        )
        lines.append((bottom_line, self.theme.colors.panel_border))

        return lines

    def render(self) -> str:
        """Render panel as string (for debugging)."""
        return "\n".join(text for text, _ in self.build())


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_box(
    title: str | None = None,
    lines: list[tuple[str, str | None]] | None = None,
    theme: Theme | None = None,
    width: int = DEFAULT_PANEL_WIDTH,
) -> str:
    """
    Create a simple box with title and content lines.

    Args:
        title: Box title (optional)
        lines: List of (text, style) tuples
        theme: Theme to use
        width: Box width

    Returns:
        Rendered box as string
    """
    builder = BoxBuilder(theme).width(width)
    if title:
        builder.title(title)

    if lines:
        for text, style in lines:
            builder.add_line(text, style)

    return builder.render()


def format_code_block(
    code: str,
    language: str = "",
    theme: Theme | None = None,
    show_line_numbers: bool = True,
    max_lines: int = 50,
) -> str:
    """
    Format code within a box with optional syntax highlighting indicator.

    Args:
        code: Source code
        language: Programming language
        theme: Theme to use
        show_line_numbers: Whether to show line numbers
        max_lines: Max lines to display

    Returns:
        Formatted code block as string
    """
    theme = theme or ThemeManager().current

    if language:
        header = f" CODE ({language.upper()}) "
    else:
        header = " CODE "

    header_len = len(header)
    box_width = min(max(len(line) for line in code.split("\n")) + 6, MAX_PANEL_WIDTH)
    box_width = max(box_width, len(header) + 4)

    lines: list[str] = []

    # Header line
    header_line = f"{theme.box_chars.top_left}{theme.box_chars.horizontal * (box_width - 2)}{theme.box_chars.top_right}"
    lines.append(header_line)

    # Title
    title_content = f"{theme.box_chars.vertical}{header}{' ' * (box_width - header_len - 3)}{theme.box_chars.vertical}"
    lines.append(title_content)

    # Divider
    divider = f"{theme.box_chars.tee_right}{theme.box_chars.horizontal * (box_width - 2)}{theme.box_chars.tee_left}"
    lines.append(divider)

    # Code lines
    code_lines = code.split("\n")[:max_lines]
    for i, line in enumerate(code_lines, 1):
        if show_line_numbers:
            lineno = f"{i:3} │"
            line_content = f"{theme.box_chars.vertical} {lineno} {line:<{box_width - 10}} {theme.box_chars.vertical}"
        else:
            line_content = (
                f"{theme.box_chars.vertical} {line:<{box_width - 4}} {theme.box_chars.vertical}"
            )
        lines.append(line_content)

    # Bottom border
    bottom_line = (
        f"{theme.box_chars.bottom_left}"
        f"{theme.box_chars.horizontal * (box_width - 2)}"
        f"{theme.box_chars.bottom_right}"
    )
    lines.append(bottom_line)

    return "\n".join(lines)


def format_sources(
    sources: list[str],
    theme: Theme | None = None,
) -> str:
    """Format source attribution line."""
    theme = theme or ThemeManager().current
    if not sources:
        return ""
    unique_sources = list(dict.fromkeys(sources))  # preserve order, remove dupes
    source_text = ", ".join(unique_sources[:5])
    if len(unique_sources) > 5:
        source_text += f" (+{len(unique_sources) - 5} more)"
    return f"[{theme.colors.sources}]Sources: {source_text}[/{theme.colors.sources}]"


def format_metadata(
    latency_ms: float | None = None,
    tokens: int | None = None,
    theme: Theme | None = None,
) -> str:
    """Format metadata line (latency, tokens)."""
    theme = theme or ThemeManager().current
    parts: list[str] = []
    if latency_ms is not None:
        parts.append(f"{latency_ms:.1f}s")
    if tokens is not None:
        parts.append(f"{tokens} tokens")
    if not parts:
        return ""
    return f"[{theme.colors.metadata}]{' · '.join(parts)}[/{theme.colors.metadata}]"


def format_response_header(
    mode: str = "cloud",
    provider: str = "",
    model: str = "",
    theme: Theme | None = None,
) -> str:
    """Format response header with mode info."""
    theme = theme or ThemeManager().current
    parts = ["RESPONSE"]
    if mode:
        parts.append(f"[{mode.upper()}]")
    if provider:
        parts.append(f"@{provider}")
    return f" {theme.box_chars.vertical} ".join(parts)


def horizontal_rule(theme: Theme | None = None, width: int = DEFAULT_PANEL_WIDTH) -> str:
    """Generate a horizontal rule line."""
    theme = theme or ThemeManager().current
    return theme.box_chars.horizontal * (width - 2)
