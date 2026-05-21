from pathlib import Path

import click
import yaml


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--config",
    default="config/settings.yaml",
    show_default=True,
    type=click.Path(exists=True),
)
@click.option("--date", default=None, help="Report date (YYYY-MM-DD). Defaults to today.")
@click.option("--dry-run", is_flag=True, help="Validate inputs without producing a report.")
def generate_report(config: str, date: str | None, dry_run: bool):
    """Load data, compute risk metrics, and export an HTML report."""
    cfg = yaml.safe_load(Path(config).read_text())

    from qis_risk_report.data.loaders import load_returns
    returns_df = load_returns(cfg["data"]["returns_path"])

    if dry_run:
        click.echo("Dry run complete — inputs are valid.")
        return

    from qis_risk_report.reports.generator import generate
    generate(cfg, returns_df, run_date=date)


if __name__ == "__main__":
    cli()
