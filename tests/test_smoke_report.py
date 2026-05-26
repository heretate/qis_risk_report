"""End-to-end smoke test for the Phase 5 report pipeline.

Run with:
    pytest tests/test_smoke_report.py -m slow -v
"""
import numpy as np
import pandas as pd
import pytest
import yaml

pytest.importorskip("bs4", reason="beautifulsoup4 required for HTML assertions")
pytest.importorskip("papermill", reason="papermill required for notebook execution")
pytest.importorskip("nbconvert", reason="nbconvert required for HTML export")

_SECTION_HEADERS = [
    "1. Performance",
    "2. Risk Metrics",
    "3. Scenario Analysis",
    "4. Portfolio Risk Contribution",
]
_MIN_CHARTS = 12
_MIN_HTML_BYTES = 500_000


@pytest.fixture(scope="module")
def smoke_html(tmp_path_factory):
    """Generate a report from 3-year synthetic data; return the HTML Path."""
    tmp = tmp_path_factory.mktemp("smoke")
    data_dir = tmp / "data"
    data_dir.mkdir()
    reports_dir = tmp / "reports"
    reports_dir.mkdir()

    rng = np.random.default_rng(0)
    dates = pd.bdate_range("2020-01-01", "2022-12-31")
    n = len(dates)

    sub_ret = rng.normal(0.0003, 0.007, (n, 4))
    qis_returns_df = pd.DataFrame(sub_ret, index=dates, columns=["sub1", "sub2", "sub3", "sub4"])
    qis_returns_df.index.name = "date"
    qis_returns_df["total"] = qis_returns_df.mean(axis=1)
    qis_returns_df.to_csv(data_dir / "returns.csv")

    port_df = pd.DataFrame(
        rng.normal(0.0002, 0.010, (n, 5)),
        index=dates,
        columns=["inst1", "inst2", "inst3", "inst4", "inst5"],
    )
    port_df["qis_total"] = qis_returns_df["total"].values
    port_df.index.name = "date"
    port_df.to_csv(data_dir / "portfolio_returns.csv")

    weights_df = pd.DataFrame(
        [[0.20, 0.20, 0.15, 0.15, 0.10, 0.20]],
        index=[dates[-1]],
        columns=["inst1", "inst2", "inst3", "inst4", "inst5", "qis_total"],
    )
    weights_df.index.name = "date"
    weights_df.to_csv(data_dir / "weights.csv")

    cfg = {
        "data": {
            "qis_returns_path": str(data_dir / "returns.csv"),
            "portfolio_returns_path": str(data_dir / "portfolio_returns.csv"),
            "weights_path": str(data_dir / "weights.csv"),
        },
        "reports": {
            "output_dir": str(reports_dir),
            "notebook_template": "notebooks/risk_report.ipynb",
        },
        "strategy": {
            "name": "Test QIS",
            "subcomponents": ["sub1", "sub2", "sub3", "sub4"],
        },
        "risk_free_rate": 0.0,
        "synthetic_shocks": {
            "spot_shocks": [-0.05, 0.0, 0.05],
            "vol_shocks": [-0.20, 0.0, 0.20],
        },
    }
    cfg_path = tmp / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")

    from qis_risk_report.reports.generator import generate

    return generate(str(cfg_path), run_date="2022-12-31", output_dir=str(reports_dir))


@pytest.mark.slow
class TestSmokeReport:
    def test_html_file_exists(self, smoke_html):
        assert smoke_html.exists(), f"HTML not found at {smoke_html}"

    def test_html_file_name(self, smoke_html):
        assert smoke_html.name == "risk_report_20221231.html"

    def test_html_size(self, smoke_html):
        size = smoke_html.stat().st_size
        assert size >= _MIN_HTML_BYTES, (
            f"HTML too small: {size:,} bytes (expected ≥ {_MIN_HTML_BYTES:,})"
        )

    def test_section_headers(self, smoke_html):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(smoke_html.read_text(encoding="utf-8"), "html.parser")
        h2_texts = [
            h.get_text(strip=True).replace("¶", "")
            for h in soup.find_all("h2")
        ]
        for header in _SECTION_HEADERS:
            assert any(header in t for t in h2_texts), (
                f"Missing section header: {header!r}\nFound: {h2_texts}"
            )

    def test_chart_count(self, smoke_html):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(smoke_html.read_text(encoding="utf-8"), "html.parser")
        imgs = soup.find_all("img")
        assert len(imgs) >= _MIN_CHARTS, (
            f"Only {len(imgs)} <img> tags found (expected ≥ {_MIN_CHARTS})"
        )
