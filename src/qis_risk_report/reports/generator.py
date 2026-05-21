"""Phase 4 — parameterised notebook execution and HTML export."""
from datetime import date as _date
from pathlib import Path

import yaml


def execute_notebook(config_path: str, run_date: str, executed_nb_path: str) -> Path:
    """Execute the report notebook via papermill, saving to executed_nb_path."""
    import papermill as pm

    cfg = yaml.safe_load(Path(config_path).read_text())
    template = cfg["reports"]["notebook_template"]
    pm.execute_notebook(
        template,
        executed_nb_path,
        parameters={"run_date": run_date, "config_path": config_path},
    )
    return Path(executed_nb_path)


def export_html(executed_nb_path: str, html_output_path: str) -> Path:
    """Convert an executed notebook to an HTML file using nbconvert."""
    from nbconvert import HTMLExporter

    exporter = HTMLExporter()
    body, _ = exporter.from_filename(executed_nb_path)
    out = Path(html_output_path)
    out.write_text(body, encoding="utf-8")
    return out


def generate(
    config_path: str,
    run_date: str | None = None,
    output_dir: str | None = None,
) -> Path:
    """Execute notebook and export HTML. Returns the HTML path.

    Output naming: <output_dir>/risk_report_YYYYMMDD.html
    The executed notebook is written to a temp .ipynb alongside the HTML then deleted.
    """
    run_date = run_date or _date.today().isoformat()
    date_compact = run_date.replace("-", "")

    cfg = yaml.safe_load(Path(config_path).read_text())
    out_dir = Path(output_dir or cfg["reports"].get("output_dir", "reports"))
    out_dir.mkdir(parents=True, exist_ok=True)

    executed_nb = out_dir / f"risk_report_{date_compact}.ipynb"
    html_path = out_dir / f"risk_report_{date_compact}.html"

    execute_notebook(config_path, run_date, str(executed_nb))
    export_html(str(executed_nb), str(html_path))
    executed_nb.unlink()

    return html_path
