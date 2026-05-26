from pathlib import Path

import click
import yaml


@click.group()
def cli():
    pass


@cli.command("generate-report")
@click.option(
    "--config",
    default="config/settings.yaml",
    show_default=True,
    type=click.Path(exists=True),
)
@click.option(
    "--date", "run_date", default=None, help="Report date (YYYY-MM-DD). Defaults to today."
)
@click.option(
    "--output-dir", default=None, help="Output directory. Defaults to reports/ from config."
)
@click.option("--dry-run", is_flag=True, help="Validate inputs without producing a report.")
def generate_report(config: str, run_date: str | None, output_dir: str | None, dry_run: bool):
    """Load data, compute risk metrics, and export an HTML report."""
    cfg = yaml.safe_load(Path(config).read_text(encoding="utf-8-sig"))

    from qis_risk_report.data.loaders import load_returns
    load_returns(cfg["data"]["qis_returns_path"])

    if dry_run:
        click.echo("Dry run complete — inputs are valid.")
        return

    try:
        from qis_risk_report.reports.generator import generate
        html_path = generate(config, run_date=run_date, output_dir=output_dir)
        click.echo(f"Report generated: {html_path}")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
