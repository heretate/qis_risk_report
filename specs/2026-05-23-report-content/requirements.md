# Requirements — Phase 5: Report Content & Visualisations

## Scope

Implement the full set of metrics, summary tables, and charts for all five report sections inside the notebook template built in Phase 4. No new data inputs are introduced; all required values are derived from the existing contract (`returns_df`, `portfolio_returns_df`, `weights_df`, `factors_df`) and the Phase 1–3 computation modules.

The output of this phase is a generated HTML report that a portfolio manager can open and read without any additional tooling.

---

## Sections & Deliverables

All five sections are in scope. Section order is fixed by Phase 4 requirements and must not change.

### Section 0 — Report Header (KPI Strip)

A single styled table printed at the top of the report before any section header. Values are always for the strategy `total` series.

| KPI | Calculation |
|---|---|
| YTD Return | Cumulative return from Jan 1 of `run_date` year to `run_date` |
| 1Y Annualised Return | Geometric annualisation of trailing 252 trading-day return |
| Annualised Volatility (1Y) | Std dev of trailing 252-day returns × √252 |
| Sharpe Ratio (1Y) | Ann. return / Ann. vol; risk-free rate from `config/settings.yaml` (default 0.0) |
| Maximum Drawdown | Peak-to-trough from inception |
| Current Drawdown | Drawdown as of `run_date` |
| 1-day VaR 99% | Historical simulation, trailing 252 days |

---

### Section 1 — Performance

**Summary table** — strategy `total` + each subcomponent; periods: 1D, MTD, YTD, 1Y, since inception (all as total returns, not annualised, except the "1Y Ann." column).

**Charts**

| ID | Chart | Description |
|---|---|---|
| P-1 | Cumulative return | Indexed to 100 at inception; one line per subcomponent + `total`; single figure |
| P-2 | Monthly return heatmap | Calendar grid (year × month); shaded green/red; one grid per subcomponent + `total` (5 grids, stacked vertically in one figure) |
| P-3 | Daily return bar | Trailing 63 trading days; positive/negative bars; 20-day rolling average overlaid; one panel per subcomponent + `total` (5 panels, shared x-axis) |

---

### Section 2 — Risk Metrics

**Summary table** — strategy `total` + each subcomponent.

| Metric | Window |
|---|---|
| Annualised volatility | 252-day trailing, since inception |
| Sharpe ratio | 252-day trailing, since inception |
| Sortino ratio | 252-day trailing, since inception |
| Maximum drawdown | Since inception |
| Current drawdown | As-of `run_date` |
| Longest drawdown duration (days) | Since inception |
| 1-day VaR 95%, 99% | Historical, trailing 252 days |
| 10-day VaR 99% | Historical, scaled by √10 |
| CVaR / ES 95% | Historical, trailing 252 days |

**Charts**

| ID | Chart | Description |
|---|---|---|
| R-1 | Rolling volatility | 63-day and 252-day annualised vol; all subcomponents + `total` on one figure; two line styles to distinguish windows |
| R-2 | Drawdown (underwater) | Top panel: cumulative return of `total`; bottom panel: drawdown depth (negative); trough periods shaded |
| R-3 | Return distribution | Histogram + KDE for each subcomponent and `total`; VaR 95% and CVaR 95% marked as vertical lines; faceted (one subplot per series) |
| R-4 | Correlation heatmap | 4 subcomponents; pairwise; diverging palette centred at 0; annotated with coefficient values; computed over full history |
| R-5 | Rolling pairwise correlation | 252-day rolling; one line per subcomponent pair (6 lines); single figure |

---

### Section 3 — Factor Attribution

Factor data (`factors_df`) supplies carry, momentum, value, and volatility columns with the same `DatetimeIndex` as `returns_df`.

**Summary table** — per subcomponent: current 252-day factor betas, R², YTD return attributed to each factor, residual (alpha).

**Charts**

| ID | Chart | Description |
|---|---|---|
| A-1 | Rolling factor betas | One figure per subcomponent (4 figures); four lines per figure (one per factor); 252-day rolling OLS |
| A-2 | YTD attribution stacked bar | One bar per subcomponent; segments = factor-attributed return + residual alpha; values in % |
| A-3 | Subcomponent contribution area | Area chart of each subcomponent's daily contribution to the total strategy return; trailing 252 days; areas sum to total |

---

### Section 4 — Scenario Analysis

Scenario data is produced by the Phase 2 `scenarios` module. The notebook calls `run_scenario` for each historical event and the configured synthetic shocks.

**Historical scenarios table** — one row per event; columns: event name, date range, strategy P&L, P&L per subcomponent, annualised volatility during the event.

Default historical events: GFC (Oct 2008 – Mar 2009), EUR sovereign debt crisis (May – Nov 2011), CNY devaluation (Aug 2015), COVID crash (Feb – Mar 2020), 2022 rate shock (Jan – Oct 2022).

**Charts**

| ID | Chart | Description |
|---|---|---|
| S-1 | Scenario impact bar chart | Grouped bars; one group per event; one bar per subcomponent + `total`; sorted by strategy P&L ascending |
| S-2 | Stress path chart | Cumulative P&L path day-by-day through the event window; one line per subcomponent + `total`; GFC and COVID rendered by default (two separate figures) |

**Synthetic shock table** — sensitivity grid: rows = spot shock (e.g. −5%, −2.5%, 0%, +2.5%, +5%), columns = vol shock (e.g. −20%, 0%, +20%); cells = strategy P&L impact. Defined by `synthetic_shocks` block in `config/settings.yaml`.

---

### Section 5 — Portfolio Risk Contribution

**Summary table**

| Metric |
|---|
| QIS weight in portfolio (from `weights_df`) |
| Standalone 1-day VaR 95% (QIS strategy) |
| Marginal VaR contribution of QIS |
| Component VaR share of QIS (% of total portfolio VaR) |
| Trailing 252-day correlation of QIS with rest of portfolio |
| Diversification benefit (standalone VaR − component VaR, in % of standalone) |

**Charts**

| ID | Chart | Description |
|---|---|---|
| C-1 | Component VaR decomposition | Horizontal bar chart; one bar per portfolio instrument; QIS bar further broken into 4 subcomponent bars; sorted by magnitude |
| C-2 | Rolling QIS–portfolio correlation | 252-day rolling; one line for `qis_total` vs. aggregate rest-of-portfolio; secondary lines for each subcomponent |
| C-3 | Diversification benefit over time | Line chart: `Σ standalone VaR − portfolio VaR` as % of portfolio VaR; 252-day rolling |

---

## Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Charting library | `matplotlib` + `seaborn` | Consistent with Phase 4 (no interactive JS in static HTML export) |
| Default rolling window | 252 trading days | Long-run view appropriate for a PM daily monitor; 63-day secondary window shown on rolling vol and rolling correlation charts only |
| Chart function signature | `plot_*(df, ...) -> matplotlib.figure.Figure` | Testable in isolation; notebook calls the function and displays the returned figure |
| Module location | `src/qis_risk_report/reports/charts.py` | Keeps chart logic separate from notebook; imported into the notebook template |
| Color convention | Fixed palette: `total` = black; subcomponents = a consistent 4-color qualitative set (e.g. seaborn `tab10` first 4) | Consistent across all figures so PM can track series across sections |
| Inline embedding | `plt.tight_layout(); plt.show()` in each notebook cell | nbconvert captures inline figures as base64 PNG; no separate image files needed |
| Risk-free rate | Read from `config/settings.yaml` key `risk_free_rate`; default `0.0` if absent | Avoids hard-coding; allows per-environment override |

---

## Out of Scope

- Interactive / JavaScript charts (plotly)
- Custom CSS or branding beyond nbconvert default theme
- New data sources beyond the existing contract
- Per-chart export (PNG / PDF) — full HTML only
- Automated email distribution of the report
