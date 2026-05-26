# Requirements — Data Contract Realignment

## Scope

Adapt the codebase to match the actual data availability:

- `qis_return_df` — daily returns for the QIS strategy (4 subcomponents + `total`) from 2008 to today
- `portfolio_return_df` — daily returns for broader portfolio instruments (non-QIS) from 2020 to today
- `weights_df` — current portfolio weights snapshot (no historical weights); QIS weight is currently **zero**
- `factor_returns_df` — deferred; out of scope for this feature

This realignment has cascading effects on report sections, loader code, settings, and tests.

---

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| DataFrame rename | `returns_df` → `qis_return_df`; `portfolio_returns_df` → `portfolio_return_df` | Matches the actual feed names as confirmed by the data owner |
| Portfolio risk contribution | Sensitivity grid across hypothetical QIS allocation levels (e.g. 1%, 2.5%, 5%, 10%) | QIS weight is currently zero; a grid lets the PM evaluate impact before committing to an allocation |
| Pre-2020 historical scenarios | Show QIS returns only; mark portfolio columns as N/A | Portfolio data starts 2020; pre-2020 events (GFC, EUR crisis, CNY devaluation) still have full QIS history |
| Factor Attribution section | Omit entirely | `factor_returns_df` is not yet available; the section will be re-introduced in a future spec |
| Hypothetical allocation levels | Configurable via `settings.yaml` key `hypothetical_qis_weights` (list of floats) | Allows the PM to adjust the grid without a code change |

---

## Context

The previous data contract assumed:
- A unified `returns_df` covering QIS subcomponents and `total`
- `portfolio_returns_df` that included a `qis_total` column representing the QIS within the portfolio
- Historical portfolio weights available to compute time-series portfolio returns

None of these assumptions hold. The actual feeds separate QIS data from portfolio data, portfolio data only goes back to 2020, and there are no historical weights. The QIS is not yet allocated within the portfolio.

---

## Out of Scope

- Sourcing or generating `factor_returns_df`
- Historical portfolio weights reconstruction
- Computing time-series blended portfolio returns (only point-in-time hypothetical blending is supported)
- Automated email or distribution of the report
