# Uncertainty Bands on Simulated Charts — Design

**Date:** 2026-07-17
**Status:** Approved (design), pending implementation plan

## Problem

The life-cycle charts show only the *mean* across 10,000 simulated households.
Means hide how widely outcomes vary between households. We want each simulated
line to carry a shaded band showing the central **95%** range — i.e. 95% of
simulated households fall inside the band at each age.

## Scope

**In scope — bands added to every simulation-derived line:**

- Life-cycle profiles figure (`lifecycle`):
  - Panel 1: Consumption (`meanC`), Wealth (`meanW`), Income (`meanY`)
  - Panel 2: Average stock share (`meanalpha`)
  - Panel 3: Scaled Consumption/Wealth/Income (`meanCs`, `meanWs`, `meanYs`)
- Portfolio composition figure (`composition`): Stocks (`meanS`), Bonds (`meanB`)

**Out of scope:**

- **Policy-functions figure (`policy`)** — these are the *solved optimal policy*
  (deterministic functions of cash-on-hand and age), not simulated random
  outcomes. A "95% of the time" band is meaningless here. Left unchanged.
- No interactive/client-side charts. Charts remain backend-rendered matplotlib
  PNGs.
- No new form field. Coverage is a fixed constant (see below).

## Key decisions

1. **Band definition = empirical percentile coverage.** Not mean ± k·σ.
   Wealth is heavily right-skewed, so a symmetric σ band would misstate coverage
   and could go negative. Percentiles give true coverage and never go negative.
2. **Coverage = single source-of-truth constant** `BAND_COVERAGE = 0.95`,
   defined once in `solver.py`. It drives both the percentile math and the chart
   labels. Editing that one line changes the shading *and* every label.
3. **Composition chart unstacked** into two banded lines (Stocks, Bonds), each
   with its own 95% band. The previous stacked area cannot cleanly show bands.

## Percentile math

From the single constant:

- lower edge `= (1 − BAND_COVERAGE) / 2` → 0.025 → **2.5th** percentile
- upper edge `= 1 − (1 − BAND_COVERAGE) / 2` → 0.975 → **97.5th** percentile
- span between edges = 95% (the coverage)

Computed across paths (`axis=1`) for each per-path array, per age.

## Architecture / data flow

### `solver.py`

- Add module constant: `BAND_COVERAGE = 0.95`.
- In `simulate()`, **before** collapsing per-path arrays to means, compute
  percentile bounds across paths for each stochastic series:
  - Direct from per-path arrays: `simC`, `simW`, `simY`, `simA` (stock share),
    `simS`, `simB`.
  - Scaled series (`Cs`, `Ws`, `Ys`): the mean versions are `meanX * cGPY`
    where `cGPY` is deterministic. So the band bounds are the C/W/Y percentile
    bounds multiplied by the same `cGPY` vector.
- Return the bounds under a **reserved `bands` key** in the returned dict, kept
  separate from the mean series:

  ```
  sim['bands'] = {
    'C':  {'lo': ndarray(tn,), 'hi': ndarray(tn,)},
    'W':  {...}, 'Y': {...}, 'alpha': {...},
    'S':  {...}, 'B': {...},
    'Cs': {...}, 'Ws': {...}, 'Ys': {...},
  }
  ```

- The existing mean keys are unchanged.

### `run.py`

- The results table renders **every** key in `sim` as a column, so `bands`
  must not reach the table. Build the table JSON excluding it:

  ```python
  {k: v.tolist() for k, v in sim.items() if k != 'bands'}
  ```

- Pass the **full in-memory `sim`** (with `bands`) to `make_charts(...)`.
- Net: bands live only backend-side for plotting; the table is unaffected.

### `plots.py`

- `from solver import BAND_COVERAGE` and derive the label percentage as
  `int(round(BAND_COVERAGE * 100))`.
- For each stochastic line, draw the band behind the line:

  ```python
  ax.fill_between(x, lo, hi, color=<line color>, alpha=0.20, linewidth=0)
  ```

- **Composition figure:** replace `stackplot` with two lines — Stocks
  (imperial blue `#003E74`) and Bonds (light `#9ecae1`) — each with its band.
  Y-axis label unchanged ("Amount held (normalized by income)").
- Each banded figure carries a note (subtitle or legend entry) like
  *"shaded = central 95% of simulated households"*, with `95` from the constant.
- **Policy figure unchanged.**

### Frontend

- Only the composition `<figure>`'s `alt` text updated (it is no longer a
  "stacked" chart). No JS/CSS logic changes — charts are server images and the
  table is untouched.

## Edge cases

- **Stock-share band** naturally stays within [0, 1] (inputs are in [0, 1]).
- **Wealth band** never negative (percentiles of non-negative holdings).
- **Small `nsim`** (user-configurable): percentiles still defined; bands just
  noisier. Acceptable — no special handling.
- **Antithetic variates:** the simulation uses antithetic pairs (two halves).
  Percentiles across all `nsim` paths remain valid.
- Guarantee `lo ≤ hi` (holds by percentile ordering).

## Testing

Backend smoke test on small grids (small `ncash`, `na`, `nc`, `nsim`):

- `sim['bands']` exists and contains all expected series, each with `lo`/`hi`
  of shape `(tn,)`.
- For every series: `lo ≤ hi` elementwise; for `W`, `S`, `B`: `lo ≥ 0`.
- The table JSON (built as in `run.py`) contains **no** `bands` key.
- `make_charts(...)` returns three data-URIs (`lifecycle`, `policy`,
  `composition`) that decode as PNGs.

Then a real run to visually confirm the shading reads well and the composition
chart shows two banded lines.

## Out-of-scope / future

- Making coverage user-adjustable via a form field (currently a one-line
  constant edit + re-run).
- Bands on policy functions (not applicable — deterministic).
- Client-side interactive re-shading without a re-run.
