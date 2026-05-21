"""Report generation: Excel and HTML/PDF output."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader


class ReportGenerator:
    """Render risk summaries to Excel or HTML/PDF."""

    def __init__(self, output_dir: str | Path, template_dir: str | Path | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._env: Environment | None = None
        if template_dir is not None:
            self._env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)

    def to_excel(self, data: dict[str, pd.DataFrame], filename: str) -> Path:
        """Write multiple DataFrames as sheets in a single workbook."""
        out = self.output_dir / filename
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name)
        return out

    def to_html(self, template_name: str, context: dict[str, object], filename: str) -> Path:
        if self._env is None:
            raise RuntimeError("template_dir must be set to render HTML reports.")
        out = self.output_dir / filename
        html = self._env.get_template(template_name).render(**context)
        out.write_text(html, encoding="utf-8")
        return out

    def to_pdf(self, template_name: str, context: dict[str, object], filename: str) -> Path:
        """Render HTML template and convert to PDF via WeasyPrint."""
        from weasyprint import HTML  # type: ignore[import]

        html_path = self.to_html(template_name, context, filename.replace(".pdf", ".html"))
        pdf_path = self.output_dir / filename
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return pdf_path
