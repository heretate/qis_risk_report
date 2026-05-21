"""Phase 4 — parameterised notebook execution and HTML export."""
from datetime import date as _date
from pathlib import Path

import pandas as pd


def generate(cfg: dict, returns_df: pd.DataFrame, run_date: str | None = None) -> Path:
    """Execute the report notebook and export it as HTML.

    Output: reports/risk_report_YYYYMMDD.html
    """
    import papermill as pm
    import nbconvert

    run_date = run_date or _date.today().isoformat()
    output_dir = Path(cfg["reports"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    executed_nb = output_dir / f"risk_report_{run_date}.ipynb"
    html_path = output_dir / f"risk_report_{run_date}.html"

    pm.execute_notebook(
        cfg["reports"]["notebook_template"],
        str(executed_nb),
        parameters={"run_date": run_date, "config_path": "config/settings.yaml"},
    )

    exporter = nbconvert.HTMLExporter()
    body, _ = exporter.from_filename(str(executed_nb))
    html_path.write_text(body, encoding="utf-8")
    executed_nb.unlink()

    return html_path
