"""
LaTeX to PDF compiler with support for multiple engines and error handling.

Supports:
- pdflatex
- xelatex
- lualatex
- Multiple compilation passes
- Error log parsing
- Automatic cleanup
"""

import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LaTeXEngine(str, Enum):
    """Supported LaTeX engines."""
    PDFLATEX = "pdflatex"
    XELATEX = "xelatex"
    LUALATEX = "lualatex"


class CompilationError(Exception):
    """Exception raised when LaTeX compilation fails."""
    pass


class PDFCompiler:
    """
    Compile LaTeX documents to PDF with error handling and cleanup.

    Features:
    - Multiple LaTeX engines (pdflatex, xelatex, lualatex)
    - Multi-pass compilation for references and TOC
    - Error detection and reporting
    - Log file parsing
    - Automatic cleanup of intermediate files
    """

    # Intermediate files to clean up
    INTERMEDIATE_EXTENSIONS = [
        '.aux', '.log', '.toc', '.lof', '.lot',
        '.out', '.nav', '.snm', '.vrb',
        '.fls', '.fdb_latexmk', '.synctex.gz',
        '.bbl', '.blg', '.bcf', '.run.xml'
    ]

    def __init__(
        self,
        engine: LaTeXEngine = LaTeXEngine.PDFLATEX,
        output_dir: Optional[str] = None,
        cleanup: bool = True
    ):
        """
        Initialize PDF compiler.

        Args:
            engine: LaTeX engine to use
            output_dir: Directory for output files (defaults to temp)
            cleanup: Whether to clean up intermediate files
        """
        self.engine = engine
        self.output_dir = Path(output_dir) if output_dir else None
        self.cleanup = cleanup

        # Check if LaTeX is installed
        if not self._check_latex_installed():
            raise RuntimeError(
                f"LaTeX engine '{engine}' not found. "
                "Please install a LaTeX distribution (e.g., TeX Live, MiKTeX)."
            )

    def _check_latex_installed(self) -> bool:
        """Check if the LaTeX engine is installed."""
        try:
            result = subprocess.run(
                [self.engine.value, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def compile(
        self,
        tex_file: str,
        passes: int = 2,
        halt_on_error: bool = True
    ) -> bytes:
        """
        Compile LaTeX file to PDF.

        Args:
            tex_file: Path to .tex file
            passes: Number of compilation passes (for references, TOC)
            halt_on_error: Stop on first error

        Returns:
            PDF file content as bytes

        Raises:
            CompilationError: If compilation fails
            FileNotFoundError: If tex file doesn't exist
        """
        tex_path = Path(tex_file)

        if not tex_path.exists():
            raise FileNotFoundError(f"TeX file not found: {tex_file}")

        # Set working directory
        work_dir = tex_path.parent
        tex_name = tex_path.name
        base_name = tex_path.stem

        logger.info(f"Compiling {tex_name} with {self.engine.value} ({passes} passes)")

        # Compile multiple times for references
        for pass_num in range(1, passes + 1):
            logger.debug(f"Compilation pass {pass_num}/{passes}")

            try:
                self._run_latex(
                    tex_name,
                    work_dir,
                    halt_on_error=halt_on_error,
                    pass_num=pass_num
                )
            except subprocess.CalledProcessError as e:
                # Parse log file for errors
                log_file = work_dir / f"{base_name}.log"
                errors = self._parse_log_file(log_file)

                error_msg = f"LaTeX compilation failed on pass {pass_num}"
                if errors:
                    error_msg += f":\n" + "\n".join(errors[:5])  # Show first 5 errors

                raise CompilationError(error_msg) from e

        # Read PDF output
        pdf_file = work_dir / f"{base_name}.pdf"

        if not pdf_file.exists():
            raise CompilationError(
                f"PDF file was not generated: {pdf_file}. "
                "Check the LaTeX log for errors."
            )

        with open(pdf_file, 'rb') as f:
            pdf_data = f.read()

        # Cleanup intermediate files
        if self.cleanup:
            self._cleanup_files(work_dir, base_name)

        logger.info(f"Successfully compiled {tex_name} to PDF ({len(pdf_data)} bytes)")

        return pdf_data

    def _run_latex(
        self,
        tex_file: str,
        work_dir: Path,
        halt_on_error: bool = True,
        pass_num: int = 1
    ):
        """
        Run LaTeX compilation command.

        Args:
            tex_file: Name of .tex file
            work_dir: Working directory
            halt_on_error: Stop on first error
            pass_num: Current pass number

        Raises:
            subprocess.CalledProcessError: If compilation fails
        """
        # Build command
        cmd = [
            self.engine.value,
            '-interaction=nonstopmode',  # Don't stop for errors
        ]

        if halt_on_error:
            cmd.append('-halt-on-error')

        # Additional engine-specific options
        if self.engine == LaTeXEngine.PDFLATEX:
            cmd.append('-file-line-error')

        # Output directory
        if self.output_dir:
            cmd.extend(['-output-directory', str(self.output_dir)])

        cmd.append(tex_file)

        # Run compilation
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"LaTeX compilation failed with return code {result.returncode}")
            logger.debug(f"STDOUT: {result.stdout.decode('utf-8', errors='ignore')}")
            logger.debug(f"STDERR: {result.stderr.decode('utf-8', errors='ignore')}")
            raise subprocess.CalledProcessError(
                result.returncode,
                cmd,
                result.stdout,
                result.stderr
            )

    def _parse_log_file(self, log_file: Path) -> List[str]:
        """
        Parse LaTeX log file to extract error messages.

        Args:
            log_file: Path to .log file

        Returns:
            List of error messages
        """
        if not log_file.exists():
            return ["Log file not found"]

        errors = []

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Pattern for LaTeX errors
            error_pattern = re.compile(
                r'! (.*?)$',
                re.MULTILINE
            )

            # Extract errors
            for match in error_pattern.finditer(content):
                error_msg = match.group(1).strip()
                if error_msg:
                    errors.append(error_msg)

            # Also look for common issues
            if 'Undefined control sequence' in content:
                errors.append("Undefined control sequence (check LaTeX commands)")

            if 'File not found' in content:
                errors.append("Missing file (check \\input or \\includegraphics)")

            if 'Package' in content and 'Error' in content:
                # Extract package errors
                pkg_errors = re.findall(
                    r'Package (\w+) Error: (.*?)$',
                    content,
                    re.MULTILINE
                )
                for pkg, msg in pkg_errors:
                    errors.append(f"Package {pkg}: {msg}")

        except Exception as e:
            logger.error(f"Error parsing log file: {e}")
            errors.append(f"Failed to parse log file: {e}")

        return errors

    def _cleanup_files(self, work_dir: Path, base_name: str):
        """
        Remove intermediate LaTeX files.

        Args:
            work_dir: Working directory
            base_name: Base name of the document (without extension)
        """
        logger.debug(f"Cleaning up intermediate files for {base_name}")

        for ext in self.INTERMEDIATE_EXTENSIONS:
            file_path = work_dir / f"{base_name}{ext}"
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.debug(f"Removed {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")

    def compile_string(
        self,
        latex_content: str,
        output_name: str = "document",
        passes: int = 2
    ) -> bytes:
        """
        Compile LaTeX content from string to PDF.

        Args:
            latex_content: LaTeX document content
            output_name: Base name for output file
            passes: Number of compilation passes

        Returns:
            PDF file content as bytes
        """
        import tempfile

        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write LaTeX content to file
            tex_file = tmpdir_path / f"{output_name}.tex"
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # Compile
            return self.compile(str(tex_file), passes=passes)

    @staticmethod
    def get_available_engines() -> List[LaTeXEngine]:
        """
        Get list of available LaTeX engines on the system.

        Returns:
            List of available engines
        """
        available = []

        for engine in LaTeXEngine:
            try:
                result = subprocess.run(
                    [engine.value, '--version'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    available.append(engine)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return available

    def get_compilation_info(self, log_file: Path) -> Dict[str, any]:
        """
        Extract compilation information from log file.

        Args:
            log_file: Path to .log file

        Returns:
            Dictionary with compilation info (pages, warnings, etc.)
        """
        info = {
            'pages': 0,
            'warnings': [],
            'overfull_hboxes': 0,
            'underfull_hboxes': 0,
        }

        if not log_file.exists():
            return info

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract page count
            page_match = re.search(r'Output written.*\((\d+) page', content)
            if page_match:
                info['pages'] = int(page_match.group(1))

            # Count warnings
            warnings = re.findall(r'LaTeX Warning: (.*?)$', content, re.MULTILINE)
            info['warnings'] = [w.strip() for w in warnings]

            # Count box issues
            info['overfull_hboxes'] = len(re.findall(r'Overfull \\hbox', content))
            info['underfull_hboxes'] = len(re.findall(r'Underfull \\hbox', content))

        except Exception as e:
            logger.error(f"Error extracting compilation info: {e}")

        return info
