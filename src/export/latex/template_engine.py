"""
Jinja2-based LaTeX template engine with proper escaping and advanced features.

Handles:
- Variable substitution with LaTeX-safe escaping
- Loop and conditional logic
- Graphics, tables, and equations
- Custom LaTeX commands and packages
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from jinja2.exceptions import TemplateError, TemplateSyntaxError


class LaTeXTemplateEngine:
    """
    Jinja2 template engine optimized for LaTeX document generation.

    Features:
    - Automatic LaTeX escaping for special characters
    - Custom filters for formatting
    - Support for includes and macros
    - Variable blocks for graphics, tables, and equations
    """

    # LaTeX special characters that need escaping
    LATEX_SPECIAL_CHARS = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }

    def __init__(self, template_dir: str, autoescape: bool = False):
        """
        Initialize the LaTeX template engine.

        Args:
            template_dir: Directory containing LaTeX templates
            autoescape: Enable automatic HTML escaping (usually False for LaTeX)
        """
        self.template_dir = Path(template_dir)

        if not self.template_dir.exists():
            raise ValueError(f"Template directory does not exist: {template_dir}")

        # Create Jinja2 environment with LaTeX-specific settings
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=autoescape,
            block_start_string='\\BLOCK{',
            block_end_string='}',
            variable_start_string='\\VAR{',
            variable_end_string='}',
            comment_start_string='\\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self._register_filters()

    def _register_filters(self):
        """Register custom Jinja2 filters for LaTeX."""
        self.env.filters['latex_escape'] = self.latex_escape
        self.env.filters['latex_safe'] = self.latex_safe
        self.env.filters['format_number'] = self.format_number
        self.env.filters['format_date'] = self.format_date
        self.env.filters['format_datetime'] = self.format_datetime
        self.env.filters['bold'] = lambda x: f"\\textbf{{{x}}}"
        self.env.filters['italic'] = lambda x: f"\\textit{{{x}}}"
        self.env.filters['underline'] = lambda x: f"\\underline{{{x}}}"
        self.env.filters['monospace'] = lambda x: f"\\texttt{{{x}}}"
        self.env.filters['color'] = lambda x, c: f"\\textcolor{{{c}}}{{{x}}}"
        self.env.filters['pass_fail'] = self.format_pass_fail

    @staticmethod
    def latex_escape(text: str) -> str:
        """
        Escape LaTeX special characters in text.

        Args:
            text: Text to escape

        Returns:
            LaTeX-safe escaped text
        """
        if not isinstance(text, str):
            text = str(text)

        # Replace special characters
        for char, replacement in LaTeXTemplateEngine.LATEX_SPECIAL_CHARS.items():
            text = text.replace(char, replacement)

        return text

    @staticmethod
    def latex_safe(text: str) -> str:
        """
        Mark text as LaTeX-safe (no escaping).
        Use this for LaTeX commands that should not be escaped.

        Args:
            text: LaTeX command or text

        Returns:
            Unchanged text
        """
        return text

    @staticmethod
    def format_number(value: float, decimals: int = 2, unit: str = "") -> str:
        """
        Format a number with specified decimal places and optional unit.

        Args:
            value: Numeric value
            decimals: Number of decimal places
            unit: Unit string (e.g., "V", "A", "W")

        Returns:
            Formatted number string
        """
        formatted = f"{value:.{decimals}f}"
        if unit:
            # Use siunitx package format
            return f"\\SI{{{formatted}}}{{{unit}}}"
        return formatted

    @staticmethod
    def format_date(date_obj, format_str: str = "%Y-%m-%d") -> str:
        """
        Format a datetime object as a date string.

        Args:
            date_obj: datetime object
            format_str: strftime format string

        Returns:
            Formatted date string
        """
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime(format_str)
        return str(date_obj)

    @staticmethod
    def format_datetime(date_obj, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format a datetime object as a datetime string.

        Args:
            date_obj: datetime object
            format_str: strftime format string

        Returns:
            Formatted datetime string
        """
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime(format_str)
        return str(date_obj)

    @staticmethod
    def format_pass_fail(result: str) -> str:
        """
        Format pass/fail result with color.

        Args:
            result: Test result (PASS, FAIL, etc.)

        Returns:
            LaTeX formatted result with color
        """
        result_upper = str(result).upper()

        if result_upper == "PASS":
            return "\\textcolor{ForestGreen}{\\textbf{PASS}}"
        elif result_upper == "FAIL":
            return "\\textcolor{red}{\\textbf{FAIL}}"
        elif result_upper == "CONDITIONAL":
            return "\\textcolor{orange}{\\textbf{CONDITIONAL}}"
        else:
            return f"\\textcolor{gray}{{{result}}}"

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        escape_all: bool = True
    ) -> str:
        """
        Render a LaTeX template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary of template variables
            escape_all: Automatically escape all string values

        Returns:
            Rendered LaTeX document as string

        Raises:
            TemplateError: If template rendering fails
        """
        try:
            # Load template
            template = self.env.get_template(template_name)

            # Optionally escape all string values in context
            if escape_all:
                context = self._escape_context(context)

            # Render template
            rendered = template.render(**context)

            return rendered

        except TemplateSyntaxError as e:
            raise TemplateError(f"Template syntax error in {template_name}: {e}")
        except Exception as e:
            raise TemplateError(f"Error rendering template {template_name}: {e}")

    def render_string(
        self,
        template_string: str,
        context: Dict[str, Any],
        escape_all: bool = True
    ) -> str:
        """
        Render a LaTeX template from a string.

        Args:
            template_string: LaTeX template as string
            context: Dictionary of template variables
            escape_all: Automatically escape all string values

        Returns:
            Rendered LaTeX document as string
        """
        try:
            template = self.env.from_string(template_string)

            if escape_all:
                context = self._escape_context(context)

            return template.render(**context)

        except Exception as e:
            raise TemplateError(f"Error rendering template string: {e}")

    def _escape_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively escape all string values in context dictionary.

        Args:
            context: Context dictionary

        Returns:
            Dictionary with escaped string values
        """
        escaped = {}

        for key, value in context.items():
            if isinstance(value, str):
                # Don't escape if marked as safe
                if not key.endswith('_safe'):
                    escaped[key] = self.latex_escape(value)
                else:
                    escaped[key] = value
            elif isinstance(value, dict):
                escaped[key] = self._escape_context(value)
            elif isinstance(value, list):
                escaped[key] = [
                    self._escape_context(item) if isinstance(item, dict)
                    else self.latex_escape(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                escaped[key] = value

        return escaped

    def add_filter(self, name: str, func):
        """
        Add a custom filter to the template engine.

        Args:
            name: Filter name
            func: Filter function
        """
        self.env.filters[name] = func

    def add_global(self, name: str, value: Any):
        """
        Add a global variable to the template environment.

        Args:
            name: Variable name
            value: Variable value
        """
        self.env.globals[name] = value

    @staticmethod
    def create_table(
        headers: List[str],
        rows: List[List[Any]],
        alignment: Optional[str] = None,
        caption: Optional[str] = None,
        label: Optional[str] = None
    ) -> str:
        """
        Generate LaTeX table code.

        Args:
            headers: List of column headers
            rows: List of row data
            alignment: Column alignment string (e.g., 'lrc')
            caption: Table caption
            label: Table label for referencing

        Returns:
            LaTeX table code
        """
        if not alignment:
            alignment = 'l' * len(headers)

        # Build table
        table_lines = [
            "\\begin{table}[htbp]",
            "\\centering",
        ]

        if caption:
            table_lines.append(f"\\caption{{{caption}}}")

        if label:
            table_lines.append(f"\\label{{{label}}}")

        table_lines.extend([
            f"\\begin{{tabular}}{{{alignment}}}",
            "\\toprule",
        ])

        # Headers
        header_row = " & ".join(headers) + " \\\\"
        table_lines.append(header_row)
        table_lines.append("\\midrule")

        # Data rows
        for row in rows:
            row_str = " & ".join(str(cell) for cell in row) + " \\\\"
            table_lines.append(row_str)

        table_lines.extend([
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
        ])

        return "\n".join(table_lines)

    @staticmethod
    def include_graphic(
        image_path: str,
        width: str = "0.8\\textwidth",
        caption: Optional[str] = None,
        label: Optional[str] = None,
        centering: bool = True
    ) -> str:
        """
        Generate LaTeX code to include a graphic.

        Args:
            image_path: Path to image file
            width: Width specification (e.g., '0.8\\textwidth')
            caption: Figure caption
            label: Figure label for referencing
            centering: Center the figure

        Returns:
            LaTeX figure code
        """
        figure_lines = [
            "\\begin{figure}[htbp]",
        ]

        if centering:
            figure_lines.append("\\centering")

        figure_lines.append(f"\\includegraphics[width={width}]{{{image_path}}}")

        if caption:
            figure_lines.append(f"\\caption{{{caption}}}")

        if label:
            figure_lines.append(f"\\label{{{label}}}")

        figure_lines.append("\\end{figure}")

        return "\n".join(figure_lines)
