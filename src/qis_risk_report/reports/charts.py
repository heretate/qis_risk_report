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

from qis_risk_report.risk import metrics as m

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

def plot_cumulative_return(qis_return_df: pd.DataFrame) -> Figure:
    """P-1: Cumulative return indexed to 100 at inception; one line per series."""
    indexed = (1 + qis_return_df).cumprod() * 100
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


def plot_monthly_heatmap(qis_return_df: pd.DataFrame) -> Figure:
    """P-2: Calendar heatmap (year × month) for each series stacked vertically."""
    all_cols = list(qis_return_df.columns)
    n = len(all_cols)

    monthly = (1 + qis_return_df).resample("ME").prod() - 1
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


def plot_daily_return_bars(qis_return_df: pd.DataFrame, window: int = 63) -> Figure:
    """P-3: Trailing `window` daily return bars + 20-day rolling average; 5 panels."""
    all_cols = list(qis_return_df.columns)
    n = len(all_cols)
    recent = qis_return_df.iloc[-window:]
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


def plot_rolling_sharpe(
    qis_return_df: pd.DataFrame,
    window: int = 252,
    risk_free: float = 0.0,
) -> Figure:
    """P-4: Rolling `window`-day annualised Sharpe ratio; one line per series."""
    all_cols = list(qis_return_df.columns)
    colors = _series_colors(all_cols)

    fig, ax = plt.subplots(figsize=(14, 4))
    for col, color in zip(all_cols, colors):
        s = qis_return_df[col]
        roll_mean = s.rolling(window).mean()
        roll_std = s.rolling(window).std(ddof=1)
        sharpe = (roll_mean * 252 - risk_free) / (roll_std * np.sqrt(252))
        lw = 2.0 if col == "total" else 1.0
        ax.plot(sharpe.index, sharpe, label=col, color=color, linewidth=lw)

    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.axhline(1, color="grey", linewidth=0.4, linestyle=":")
    ax.set_title(f"Rolling {window}-Day Sharpe Ratio (annualised)")
    ax.set_ylabel("Sharpe Ratio")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Section 2 — Risk Metrics
# ---------------------------------------------------------------------------

def plot_rolling_volatility(qis_return_df: pd.DataFrame) -> Figure:
    """R-1: 63-day (dashed) and 252-day (solid) annualised vol; one panel per series."""
    all_cols = list(qis_return_df.columns)
    n = len(all_cols)
    colors = _series_colors(all_cols)

    fig, axes = plt.subplots(n, 1, figsize=(14, 2.5 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, col, color in zip(axes, all_cols, colors):
        lw = 2.0 if col == "total" else 1.2
        vol63 = m.annualised_volatility(qis_return_df[col], window=63)
        vol252 = m.annualised_volatility(qis_return_df[col], window=252)
        ax.plot(vol63.index, vol63, color=color, linewidth=lw, linestyle="--",
                alpha=0.75, label="63d")
        ax.plot(vol252.index, vol252, color=color, linewidth=lw, linestyle="-",
                label="252d")
        ax.set_ylabel(col, rotation=0, ha="right", labelpad=55, fontsize=8)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.legend(fontsize=7)

    fig.suptitle("Rolling Annualised Volatility (dashed=63d, solid=252d)", fontsize=11)
    fig.tight_layout()
    return fig


def plot_underwater(qis_return_df: pd.DataFrame) -> Figure:
    """R-2: Top = cumulative return of total; bottom = drawdown depth; trough shaded."""
    s = qis_return_df["total"]
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
    qis_return_df: pd.DataFrame, confidence: float = 0.95
) -> Figure:
    """R-3: Histogram + KDE per series; VaR and CVaR 95% as vertical lines; faceted."""
    from scipy.stats import gaussian_kde

    sub_cols = [c for c in qis_return_df.columns if c != "total"]
    total_cols = [c for c in qis_return_df.columns if c == "total"]
    all_cols = sub_cols + total_cols
    colors = _series_colors(all_cols)

    fig, axes = plt.subplots(3, 2, figsize=(10, 12), sharey=False)
    flat_axes = axes.flatten()

    # hide the cell before last if total goes in last position and n == 5
    n = len(all_cols)
    n_cells = 6
    for i in range(n, n_cells):
        flat_axes[i].set_visible(False)
    # total goes in last cell (index 5); preceding empty cell hidden above
    if total_cols and n == 5:
        flat_axes[4].set_visible(False)
        plot_axes = list(flat_axes[:4]) + [flat_axes[5]]
    else:
        plot_axes = list(flat_axes[:n])

    for ax, col, color in zip(plot_axes, all_cols, colors):
        s = qis_return_df[col].dropna()
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


def plot_correlation_heatmap(qis_return_df: pd.DataFrame) -> Figure:
    """R-4: Pairwise correlation heatmaps — past 3 months (left) and full history (right)."""
    sub_cols = [c for c in qis_return_df.columns if c != "total"]
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    cutoff = qis_return_df.index.max() - pd.DateOffset(months=3)
    recent = qis_return_df.loc[qis_return_df.index >= cutoff, sub_cols]
    corr_recent = recent.corr()
    corr_full = qis_return_df[sub_cols].corr()

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(14, 6))
    heatmap_kwargs = dict(cmap=cmap, vmin=-1, vmax=1, center=0,
                          annot=True, fmt=".2f", square=True, linewidths=0.5)
    sns.heatmap(corr_recent, ax=ax_l, **heatmap_kwargs)
    ax_l.set_title("Subcomponent Correlation — Past 3 Months")
    sns.heatmap(corr_full, ax=ax_r, **heatmap_kwargs)
    ax_r.set_title("Subcomponent Correlation — Full History")

    fig.tight_layout()
    return fig


def plot_rolling_pairwise_correlation(
    qis_return_df: pd.DataFrame, window: int = 252
) -> Figure:
    """R-5: 252-day rolling pairwise correlation — 6 lines (one per subcomponent pair)."""
    sub_cols = [c for c in qis_return_df.columns if c != "total"]
    pairs = list(itertools.combinations(sub_cols, 2))
    palette = sns.color_palette("tab10", len(pairs))

    fig, ax = plt.subplots(figsize=(14, 5))
    pair_series = []
    for (a, b), color in zip(pairs, palette):
        roll_corr = qis_return_df[a].rolling(window).corr(qis_return_df[b])
        pair_series.append(roll_corr)
        ax.plot(roll_corr.index, roll_corr, label=f"{a} / {b}", color=color, linewidth=1.0)

    avg_corr = pd.concat(pair_series, axis=1).mean(axis=1)
    ax.plot(avg_corr.index, avg_corr, label="Average", color="black",
            linewidth=2.0, linestyle="--", zorder=5)

    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_title(f"{window}-Day Rolling Pairwise Correlation")
    ax.set_ylabel("Pearson Correlation")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Section 3 — Scenario Analysis
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
    qis_return_df: pd.DataFrame,
    scenarios: list,
) -> Figure:
    """S-2: Cumulative P&L path day-by-day through a named event window."""
    scenario = next((s for s in scenarios if s.name == scenario_name), None)
    fig, ax = plt.subplots(figsize=(12, 4))

    if scenario is None:
        ax.text(0.5, 0.5, f"Scenario '{scenario_name}' not found",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    window = qis_return_df.loc[scenario.start : scenario.end]
    if window.empty:
        ax.text(0.5, 0.5, f"No data in history for '{scenario_name}'",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    cum_pnl = (1 + window).cumprod() - 1
    all_cols = list(qis_return_df.columns)
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
# Section 4 — Portfolio Risk Contribution
# ---------------------------------------------------------------------------

def plot_allocation_sensitivity(grid_df: pd.DataFrame) -> Figure:
    """C-1: Line chart of portfolio risk metrics across hypothetical QIS weight levels.

    x-axis = QIS weight %; one line per metric.
    Component VaR share and diversification benefit are plotted on the primary y-axis;
    marginal VaR and correlation on the secondary axis.
    """
    x_labels = list(grid_df.index)
    x = np.arange(len(x_labels))
    primary_cols = ["component_var_share", "diversification_benefit"]
    secondary_cols = ["marginal_var", "correlation"]
    palette = sns.color_palette("tab10", len(primary_cols) + len(secondary_cols))

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()

    for i, col in enumerate(primary_cols):
        if col in grid_df.columns:
            ax1.plot(x, grid_df[col].values, marker="o", label=col,
                     color=palette[i], linewidth=1.5)
    for i, col in enumerate(secondary_cols):
        if col in grid_df.columns:
            ax2.plot(x, grid_df[col].values, marker="s", linestyle="--",
                     label=col, color=palette[len(primary_cols) + i], linewidth=1.5)

    ax1.set_xticks(x)
    ax1.set_xticklabels(x_labels)
    ax1.set_xlabel("Hypothetical QIS Weight")
    ax1.set_ylabel("Component VaR Share / Diversification Benefit")
    ax2.set_ylabel("Marginal VaR / Correlation")
    ax1.set_title("Portfolio Risk Contribution — Allocation Sensitivity")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8)
    fig.tight_layout()
    return fig


def plot_rolling_qis_portfolio_correlation(
    qis_return_df: pd.DataFrame,
    portfolio_return_df: pd.DataFrame,
    port_weights: pd.Series,
    window: int = 252,
) -> Figure:
    """C-2: 252-day rolling correlation of QIS series against the portfolio aggregate."""
    w = port_weights.reindex(portfolio_return_df.columns).fillna(0)
    r_agg = portfolio_return_df @ w

    all_cols = list(qis_return_df.columns)
    colors = _series_colors(all_cols)

    fig, ax = plt.subplots(figsize=(14, 4))
    for col, color in zip(all_cols, colors):
        aligned = qis_return_df[col].reindex(r_agg.index)
        roll = aligned.rolling(window).corr(r_agg)
        lw = 2.0 if col == "total" else 1.0
        ax.plot(roll.index, roll, label=col, color=color, linewidth=lw)

    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_title(f"{window}-Day Rolling QIS–Portfolio Correlation")
    ax.set_ylabel("Pearson Correlation")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


