"""Phase 2 — historical and synthetic scenario analysis."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ScenarioResult:
    name: str
    pnl_total: float
    pnl_by_component: dict[str, float]
    metadata: dict = field(default_factory=dict)


@dataclass
class HistoricalScenario:
    name: str
    start: str
    end: str


@dataclass
class ShockParams:
    spot_shock: float | None = None   # additive shift applied to all returns
    vol_shock: float | None = None    # multiplicative scaling of all returns
    # blend weight toward cross-sectional mean (0=no change, 1=full blend)
    corr_shock: float | None = None


def default_scenarios() -> list[HistoricalScenario]:
    """Default historical scenario registry (can be extended via settings.yaml)."""
    return [
        HistoricalScenario("GFC",                "2008-10-01", "2009-03-31"),
        HistoricalScenario("EUR Sovereign Debt", "2011-05-01", "2011-11-30"),
        HistoricalScenario("CNY Devaluation",    "2015-08-01", "2015-08-31"),
        HistoricalScenario("COVID Crash",        "2020-02-01", "2020-03-31"),
        HistoricalScenario("2022 Rate Shock",    "2022-01-03", "2022-10-31"),
    ]


def replay_scenario(
    scenario: HistoricalScenario,
    returns_df: pd.DataFrame,
) -> ScenarioResult:
    """Filter returns_df to the scenario date range and compute P&L."""
    window = returns_df.loc[scenario.start : scenario.end]
    sub_cols = [c for c in window.columns if c != "total"]

    pnl_by_component = {col: float(window[col].sum()) for col in sub_cols}
    if "total" in window.columns:
        pnl_total = float(window["total"].sum())
    else:
        pnl_total = sum(pnl_by_component.values()) / len(pnl_by_component)

    return ScenarioResult(
        name=scenario.name,
        pnl_total=pnl_total,
        pnl_by_component=pnl_by_component,
        metadata={"start": scenario.start, "end": scenario.end, "n_days": len(window)},
    )


def replay_all(
    scenarios: list[HistoricalScenario],
    returns_df: pd.DataFrame,
) -> list[ScenarioResult]:
    """Replay all scenarios and return a list of ScenarioResults."""
    return [replay_scenario(s, returns_df) for s in scenarios]


def run_scenario(
    portfolio: pd.DataFrame,
    shock_params: ShockParams,
) -> ScenarioResult:
    """Apply shocks to portfolio returns and compute P&L.

    spot_shock  — additive parallel shift: r + shock
    vol_shock   — multiplicative scaling: r * (1 + shock)
    corr_shock  — blend each column toward cross-sectional mean by weight shock
    """
    shocked = portfolio.copy().astype(float)

    if shock_params.spot_shock is not None:
        shocked = shocked + shock_params.spot_shock

    if shock_params.vol_shock is not None:
        shocked = shocked * (1.0 + shock_params.vol_shock)

    if shock_params.corr_shock is not None:
        cross_mean = shocked.mean(axis=1)
        alpha = shock_params.corr_shock
        for col in shocked.columns:
            shocked[col] = shocked[col] * (1.0 - alpha) + cross_mean * alpha

    n = len(shocked.columns)
    pnl_by_component = {col: float(shocked[col].sum()) for col in shocked.columns}
    pnl_total = sum(pnl_by_component.values()) / n

    return ScenarioResult(
        name="synthetic",
        pnl_total=pnl_total,
        pnl_by_component=pnl_by_component,
        metadata={"shock_params": shock_params},
    )
