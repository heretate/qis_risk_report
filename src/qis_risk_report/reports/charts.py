"""Phase 5 — chart functions for the risk report notebook.

All public functions return a matplotlib.figure.Figure.
Color convention: total = black; subcomponents use seaborn tab10 first 4 colors.
"""
from __future__ import annotations

import itertools
from typing import Sequence

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from scipy.stats import norm

from qis_risk_report.risk import metrics as m
from qis_risk_report.risk.attribution import rolling_ols_attribution

_TOTAL_COLOR = "black"
_SUB_PALETTE = list(sns.color_palette("tab10", 4))


def _series_colors(columns: Sequence[str]) -> list:
    """Return a color per column: total=black, others cycle through tab10 first 4."""
    colors = []
    sub_idx = 0
    for col in columns:
        if col == "total":
            colors.append(_TOTAL_COLOR)
        else:
            colors.append(_SUB_PALETTE[sub_idx % len(_SUB_PALETTE)])
            sub_idx += 1
    return colors


# ---------------------------------------------------------------------------
# Section 1 — Performance
# ---------------------------------------------------------------------------

def plot_cumulative_return(returns_df: pd.DataFrame) -> Figure:
    """P-1: Cumulative return indexed to 100 at inception; one line per series."""
    indexed = (1 + returns_df).cumprod() * 100
    colors = _series_colors(indexed.columns)

    fig, ax = plt.subplots(figsize=(14, 5))
    for col, color in zip(indexed.columns, colors):
        lw = 2.0 if col == "total" else 1.2
        ax.plot(indexed.index, indexed[col], label=col, color=color, linewidth=lw)

    ax.axhline(100, color="grey", linewidth=0.6, linestyle="--")
    ax.set_title("Cumulative Return (Indexed to 100 at Inception)")
    ax.set_ylabel("Index")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_monthly_heatmap(returns_df: pd.DataFrame) -> Figure:
    """P-2: Calendar heatmap (year × month) for each series stacked vertically."""
    all_cols = list(returns_df.columns)
    n = len(all_cols)

    monthly = (1 + returns_df).resample("ME").prod() - 1
    monthly.index = monthly.index.to_period("M")

    years = sorted(monthly.index.year.unique())
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    vmax = monthly.abs().quantile(0.95).max()
    cmap = sns.diverging_palette(10, 130, as_cmap=True)

    fig, axes = plt.subplots(n, 1, figsize=(14, 3 * n + 1))
    if n == 1:
        axes = [axes]

    for ax, col in zip(axes, all_cols):
        grid = np.full((len(years), 12), np.nan)
        for i, yr in enumerate(years):
            for j in range(12):
                period = pd.Period(f"{yr}-{j + 1:02d}", "M")
                if period in monthly.index:
                    grid[i, j] = monthly.loc[period, col]

        mask = np.isnan(grid)
        annot = np.where(mask, "", np.vectorize(lambda v: f"{v:.1%}")(
            np.where(mask, 0.0, grid)
        ))
        sns.heatmap(
            grid,
            ax=ax,
            cmap=cmap,
            center=0,
            vmin=-vmax,
            vmax=vmax,
            xticklabels=month_labels,
            yticklabels=years,
            annot=annot,
            fmt="",
            mask=mask,
            linewidths=0.4,
            linecolor="white",
            cbar_kws={"shrink": 0.8},
        )
        ax.set_title(f"Monthly Returns — {col}")
        ax.set_ylabel("")

    fig.tight_layout()
    return fig


def plot_daily_return_bars(returns_df: pd.DataFrame, window: int = 63) -> Figure:
    """P-3: Trailing `window` daily return bars + 20-day rolling average; 5 panels."""
    all_cols = list(returns_df.columns)
    n = len(all_cols)
    recent = returns_df.iloc[-window:]
    colors = _series_colors(all_cols)

    fig, axes = plt.subplots(n, 1, figsize=(14, 2.5 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, col, base_color in zip(axes, all_cols, colors):
        s = recent[col]
        bar_colors = [base_color if v >= 0 else "firebrick" for v in s]
        ax.bar(s.index, s.values, color=bar_colors, alpha=0.7, width=0.8)
        roll20 = s.rolling(20).mean()
        ax.plot(s.index, roll20, color="black", linewidth=1.2, label="20d avg")
        ax.axhline(0, color="grey", linewidth=0.5)
        ax.set_ylabel(col, rotation=0, ha="right", labelpad=55, fontsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1%}"))

    axes[0].legend(fontsize=8)
    fig.suptitle(f"Daily Returns — trailing {window} trading days", fontsize=11)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Section 2 — Risk Metrics
# ---------------------------------------------------------------------------

def plot_rolling_volatility(returns_df: pd.DataFrame) -> Figure:
    """R-1: 63-day (dashed) and 252-day (solid) annualised vol for all series."""
    all_cols = list(returns_df.columns)
    colors = _series_colors(all_cols)

    fig, ax = plt.subplots(figsize=(14, 5))
    for col, color in zip(all_cols, colors):
        lw = 2.0 if col == "total" else 1.0
        vol63 = m.annualised_volatility(returns_df[col], window=63)
        vol252 = m.annualised_volatility(returns_df[col], window=252)
        ax.plot(vol63.index, vol63, color=color, linewidth=lw, linestyle="--",
                alpha=0.75, label=f"{col} 63d")
        ax.plot(vol252.index, vol252, color=color, linewidth=lw, linestyle="-",
                label=f"{col} 252d")

    ax.set_title("Rolling Annualised Volatility (dashed=63d, solid=252d)")
    ax.set_ylabel("Ann. Volatility")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    return fig


def plot_underwater(returns_df: pd.DataFrame) -> Figure:
    """R-2: Top = cumulative return of total; bottom = drawdown depth; trough shaded."""
    s = returns_df["total"]
    cum = (1 + s).cumprod() * 100
    dd = m.drawdown_series(s) * 100

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 7), sharex=True,
        gridspec_kw={"height_ratios": [2, 1]},
    )

    ax1.plot(cum.index, cum, color=_TOTAL_COLOR, linewidth=1.5)
    ax1.axhline(100, color="grey", linewidth=0.6, linestyle="--")
    ax1.set_title("QIS Total — Cumulative Return & Drawdown (Underwater)")
    ax1.set_ylabel("Index (100 = inception)")

    ax2.plot(dd.index, dd, color="firebrick", linewidth=1.0)
    ax2.fill_between(dd.index, dd, 0, alpha=0.3, color="firebrick")
    ax2.axhline(0, color="grey", linewidth=0.5)
    ax2.set_ylabel("Drawdown (%)")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))

    fig.tight_layout()
    return fig


def plot_return_distribution(
    returns_df: pd.DataFrame, confidence: float = 0.95
) -> Figure:
    """R-3: Histogram + KDE per series; VaR and CVaR 95% as vertical lines; faceted."""
    from scipy.stats import gaussian_kde

    all_cols = list(returns_df.columns)
    n = len(all_cols)
    colors = _series_colors(all_cols)

    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4), sharey=False)
    if n == 1:
        axes = [axes]

    for ax, col, color in zip(axes, all_cols, colors):
        s = returns_df[col].dropna()
        ax.hist(s, bins=50, density=True, alpha=0.35, color=color)
        kde = gaussian_kde(s)
        x_vals = np.linspace(s.min(), s.max(), 300)
        ax.plot(x_vals, kde(x_vals), color=color, linewidth=1.5)
        var_val = m.historical_var(s, confidence=confidence)
        cvar_val = m.expected_shortfall(s, confidence=confidence)
        ax.axvline(-var_val, color="darkorange", linewidth=1.2, linestyle="--",
                   label=f"VaR {confidence:.0%}")
        ax.axvline(-cvar_val, color="red", linewidth=1.2, linestyle=":",
                   label=f"CVaR {confidence:.0%}")
        ax.set_title(col)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.legend(fontsize=7)

    fig.suptitle(f"Daily Return Distribution — VaR/CVaR at {confidence:.0%}", fontsize=11)
    fig.tight_layout()
    return fig


def plot_correlation_heatmap(returns_df: pd.DataFrame) -> Figure:
    """R-4: Pairwise correlation of the 4 subcomponents (full history, no total)."""
    sub_cols = [c for c in returns_df.columns if c != "total"]
    corr = returns_df[sub_cols].corr()
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        corr, ax=ax, cmap=cmap, vmin=-1, vmax=1, center=0,
        annot=True, fmt=".2f", square=True, linewidths=0.5,
    )
    ax.set_title("Subcomponent Pairwise Correlation (Full History)")
    fig.tight_layout()
    return fig


def plot_rolling_pairwise_correlation(
    returns_df: pd.DataFrame, window: int = 252
) -> Figure:
    """R-5: 252-day rolling pairwise correlation — 6 lines (one per subcomponent pair)."""
    sub_cols = [c for c in returns_df.columns if c != "total"]
    pairs = list(itertools.combinations(sub_cols, 2))
    palette = sns.color_palette("tab10", len(pairs))

    fig, ax = plt.subplots(figsize=(14, 5))
    for (a, b), color in zip(pairs, palette):
        roll_corr = returns_df[a].rolling(window).corr(returns_df[b])
        ax.plot(roll_corr.index, roll_corr, label=f"{a} / {b}", color=color, linewidth=1.0)

    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_title(f"{window}-Day Rolling Pairwise Correlation")
    ax.set_ylabel("Pearson Correlation")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Section 3 — Factor Attribution
# ---------------------------------------------------------------------------

def plot_rolling_factor_betas(
    returns: pd.Series,
    factors_df: pd.DataFrame,
    window: int = 252,
) -> Figure:
    """A-1: Rolling factor betas for a single subcomponent (4 lines, one per factor)."""
    attr = rolling_ols_attribution(returns, factors_df, window=window)
    factor_cols = [c for c in attr.columns if c != "r_squared"]
    palette = sns.color_palette("tab10", len(factor_cols))

    fig, ax = plt.subplots(figsize=(14, 4))
    for col, color in zip(factor_cols, palette):
        ax.plot(attr.index, attr[col], label=col, color=color, linewidth=1.2)
    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_title(f"Rolling {window}-Day Factor Betas — {returns.name}")
    ax.set_ylabel("Beta")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_ytd_attribution_bar(
    returns_df: pd.DataFrame,
    factors_df: pd.DataFrame,
    run_date: str,
    window: int = 252,
) -> Figure:
    """A-2: YTD return attribution stacked bar per subcomponent."""
    sub_cols = [c for c in returns_df.columns if c != "total"]
    year_start = pd.Timestamp(run_date).replace(month=1, day=1)
    ytd_factors = factors_df.loc[year_start:run_date]
    ytd_rets = returns_df.loc[year_start:run_date]
    factor_cols = list(factors_df.columns)

    data: dict[str, dict[str, float]] = {}
    for col in sub_cols:
        attr = rolling_ols_attribution(returns_df[col], factors_df, window=window)
        latest_betas = attr.drop(columns="r_squared").iloc[-1]
        fc_contribs = {
            fc: float(latest_betas.get(fc, 0.0) * ytd_factors[fc].sum())
            for fc in factor_cols
        }
        total_ytd = float(ytd_rets[col].sum())
        fc_contribs["alpha"] = total_ytd - sum(fc_contribs.values())
        data[col] = fc_contribs

    df_plot = pd.DataFrame(data).T
    all_seg = list(df_plot.columns)
    palette = sns.color_palette("tab10", len(all_seg))

    fig, ax = plt.subplots(figsize=(10, 5))
    bottom = np.zeros(len(df_plot))
    for seg, color in zip(all_seg, palette):
        vals = df_plot[seg].values * 100
        ax.bar(df_plot.index, vals, bottom=bottom, label=seg, color=color, alpha=0.85)
        bottom += vals

    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_title("YTD Return Attribution by Factor")
    ax.set_ylabel("Return (%)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_contribution_area(
    returns_df: pd.DataFrame, window: int = 252
) -> Figure:
    """A-3: Stacked area of each subcomponent's daily return contribution; trailing window."""
    sub_cols = [c for c in returns_df.columns if c != "total"]
    recent = returns_df.iloc[-window:]
    colors = [c for c in _series_colors(sub_cols)]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.stackplot(
        recent.index,
        [recent[c].values for c in sub_cols],
        labels=sub_cols,
        colors=colors,
        alpha=0.75,
    )
    ax.plot(recent.index, recent["total"], color=_TOTAL_COLOR, linewidth=1.5,
            linestyle="--", label="total")
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_title(f"Subcomponent Contribution to Total Return (trailing {window} days)")
    ax.set_ylabel("Daily Return")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Section 4 — Scenario Analysis
# ---------------------------------------------------------------------------

def plot_scenario_impact(results: list) -> Figure:
    """S-1: Grouped bar chart — one group per scenario, sorted by strategy P&L ascending."""
    if not results:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No scenario data", ha="center", va="center",
                transform=ax.transAxes)
        return fig

    sub_cols = list(results[0].pnl_by_component.keys())
    all_series = sub_cols + ["total"]
    results_sorted = sorted(results, key=lambda r: r.pnl_total)
    n_groups = len(results_sorted)
    n_bars = len(all_series)
    x = np.arange(n_groups)
    width = 0.8 / n_bars
    colors = _series_colors(all_series)

    fig, ax = plt.subplots(figsize=(max(10, n_groups * 2.2), 5))
    for i, (col, color) in enumerate(zip(all_series, colors)):
        offsets = x + (i - n_bars / 2 + 0.5) * width
        if col == "total":
            vals = [r.pnl_total * 100 for r in results_sorted]
        else:
            vals = [r.pnl_by_component.get(col, 0.0) * 100 for r in results_sorted]
        ax.bar(offsets, vals, width=width * 0.9, label=col, color=color, alpha=0.85)

    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([r.name for r in results_sorted], rotation=20, ha="right")
    ax.set_title("Historical Scenario P&L Impact")
    ax.set_ylabel("P&L (%)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_stress_path(
    scenario_name: str,
    returns_df: pd.DataFrame,
    scenarios: list,
) -> Figure:
    """S-2: Cumulative P&L path day-by-day through a named event window."""
    scenario = next((s for s in scenarios if s.name == scenario_name), None)
    fig, ax = plt.subplots(figsize=(12, 4))

    if scenario is None:
        ax.text(0.5, 0.5, f"Scenario '{scenario_name}' not found",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    window = returns_df.loc[scenario.start : scenario.end]
    if window.empty:
        ax.text(0.5, 0.5, f"No data in history for '{scenario_name}'",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    cum_pnl = (1 + window).cumprod() - 1
    all_cols = list(returns_df.columns)
    colors = _series_colors(all_cols)

    for col, color in zip(all_cols, colors):
        lw = 2.0 if col == "total" else 1.0
        ax.plot(cum_pnl.index, cum_pnl[col] * 100, label=col, color=color, linewidth=lw)

    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_title(
        f"Stress Path — {scenario_name} ({scenario.start} to {scenario.end})"
    )
    ax.set_ylabel("Cumulative P&L (%)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Section 5 — Portfolio Risk Contribution
# ---------------------------------------------------------------------------

def plot_component_var_decomposition(
    component_var_portfolio: pd.Series,
    component_var_qis_subs: pd.Series,
) -> Figure:
    """C-1: Horizontal bar — portfolio instruments; QIS bar split into subcomponents."""
    items: dict[str, float] = {}
    for k, v in component_var_portfolio.items():
        if k != "qis_total":
            items[str(k)] = abs(float(v))
    for k, v in component_var_qis_subs.items():
        items[str(k)] = abs(float(v))

    sorted_items = sorted(items.items(), key=lambda kv: kv[1])
    labels = [kv[0] for kv in sorted_items]
    values = [kv[1] for kv in sorted_items]

    sub_names = list(component_var_qis_subs.index)
    sub_color_map = dict(zip(sub_names, _series_colors(sub_names)))
    bar_colors = [sub_color_map.get(lbl, "steelblue") for lbl in labels]

    fig, ax = plt.subplots(figsize=(9, max(4, len(labels) * 0.55)))
    ax.barh(labels, values, color=bar_colors, alpha=0.85)
    ax.set_title("Component VaR Decomposition")
    ax.set_xlabel("Component VaR")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    fig.tight_layout()
    return fig


def plot_rolling_qis_portfolio_correlation(
    returns_df: pd.DataFrame,
    portfolio_returns_df: pd.DataFrame,
    port_weights: pd.Series,
    window: int = 252,
) -> Figure:
    """C-2: 252-day rolling correlation of QIS series against the portfolio aggregate."""
    w = port_weights.reindex(portfolio_returns_df.columns).fillna(0)
    r_agg = portfolio_returns_df @ w

    all_cols = list(returns_df.columns)
    colors = _series_colors(all_cols)

    fig, ax = plt.subplots(figsize=(14, 4))
    for col, color in zip(all_cols, colors):
        aligned = returns_df[col].reindex(r_agg.index)
        roll = aligned.rolling(window).corr(r_agg)
        lw = 2.0 if col == "total" else 1.0
        ax.plot(roll.index, roll, label=col, color=color, linewidth=lw)

    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_title(f"{window}-Day Rolling QIS–Portfolio Correlation")
    ax.set_ylabel("Pearson Correlation")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_diversification_benefit_over_time(
    portfolio_returns_df: pd.DataFrame,
    weights_df: pd.DataFrame,
    window: int = 252,
    confidence: float = 0.95,
) -> Figure:
    """C-3: Rolling diversification benefit (standalone VaR sum − portfolio VaR) as % of portfolio VaR."""
    z = norm.ppf(confidence)
    w = weights_df.iloc[-1].reindex(portfolio_returns_df.columns).fillna(0)

    roll_std = portfolio_returns_df.rolling(window).std()
    standalone_sum = (roll_std * w.values).sum(axis=1) * z

    r_p = portfolio_returns_df @ w
    port_vol = r_p.rolling(window).std()
    port_var_series = port_vol * z

    benefit = (standalone_sum - port_var_series) / port_var_series.replace(0, np.nan) * 100
    benefit = benefit.replace([np.inf, -np.inf], np.nan)

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(benefit.index, benefit, color="steelblue", linewidth=1.2)
    ax.fill_between(benefit.index, benefit, 0, alpha=0.2, color="steelblue",
                    where=~benefit.isna())
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_title(f"{window}-Day Rolling Diversification Benefit (% of Portfolio VaR)")
    ax.set_ylabel("% of Portfolio VaR")
    fig.tight_layout()
    return fig
