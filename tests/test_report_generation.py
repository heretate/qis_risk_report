"""Phase 4 — smoke test: CLI generate-report produces a non-empty HTML file."""
from datetime import date
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from qis_risk_report.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"
PROJECT_ROOT = Path(__file__).parent.parent
NOTEBOOK_TEMPLATE = PROJECT_ROOT / "notebooks" / "risk_report.ipynb"


@pytest.fixture
def smoke_config(tmp_path):
    """Minimal settings.yaml with absolute paths to fixture CSVs."""
    cfg = {
        "data": {
            "returns_path": str(FIXTURES / "returns_attribution_90d.csv"),
            "portfolio_returns_path": str(FIXTURES / "portfolio_returns.csv"),
            "weights_path": str(FIXTURES / "weights.csv"),
            "factors_path": str(FIXTURES / "factors_90d.csv"),
        },
        "reports": {
            "output_dir": str(tmp_path / "reports"),
            "notebook_template": str(NOTEBOOK_TEMPLATE),
        },
        "strategy": {
            "name": "Test QIS",
            "subcomponents": ["sub1", "sub2", "sub3", "sub4"],
        },
    }
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(yaml.dump(cfg))
    return str(config_path)


def test_generate_report_smoke(smoke_config, tmp_path):
    output_dir = str(tmp_path / "reports")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["generate-report", "--config", smoke_config, "--output-dir", output_dir],
    )
    assert result.exit_code == 0, f"CLI failed:\n{result.output}"

    date_str = date.today().strftime("%Y%m%d")
    html_path = Path(output_dir) / f"risk_report_{date_str}.html"
    assert html_path.exists(), f"Expected HTML not found: {html_path}"
    assert html_path.stat().st_size > 0, "HTML file is empty"

    html_path.unlink()
