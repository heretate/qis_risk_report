"""CLI entry point: qis-risk-report <command>."""

import click


@click.group()
def main() -> None:
    """QIS Risk Report generation tool."""


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--format", "fmt", default="excel", type=click.Choice(["excel", "html", "pdf"]))
@click.option("--output-dir", default="output", show_default=True)
def generate(input_file: str, fmt: str, output_dir: str) -> None:
    """Generate a risk report from INPUT_FILE (CSV or Excel)."""
    from .data import load_csv, load_excel
    from .risk import RiskMetrics
    from .reports import ReportGenerator

    loader = load_csv if input_file.endswith(".csv") else load_excel
    returns = loader(input_file, index_col=0, parse_dates=True)

    metrics = RiskMetrics(returns).summary()
    generator = ReportGenerator(output_dir)

    if fmt == "excel":
        out = generator.to_excel({"Risk Summary": metrics}, "risk_report.xlsx")
        click.echo(f"Report written to {out}")
    else:
        click.echo(f"Format '{fmt}' requires a Jinja2 template — add one to config/templates/.")
