# Uncertainty Bands on Simulated Charts — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shaded 95% percentile band around every simulation-derived line in the life-cycle charts, so viewers see the spread across households, not just the mean.

**Architecture:** Compute per-age percentile bounds across the simulated paths inside `simulate()` and return them under a reserved `bands` key. The Vercel function excludes `bands` from the results-table JSON and passes the full sim to the matplotlib plotter, which shades each line with `fill_between`. Coverage is a single constant driving both the math and the labels.

**Tech Stack:** Python 3, NumPy, Matplotlib (Agg backend), Vercel Python serverless function, Create React App frontend.

## Global Constraints

- Coverage constant is the single source of truth: `BAND_COVERAGE = 0.95`, defined once in `frontend/api/_model/solver.py` and imported by `plots.py`. Editing this one line must change both the shading and every label.
- Band = **empirical percentile coverage**, not mean ± k·σ. Lower edge = `(1 - BAND_COVERAGE)/2` percentile, upper edge = `1 - (1 - BAND_COVERAGE)/2` percentile (i.e. 2.5th–97.5th for 0.95).
- Bands apply only to simulation-derived lines: `C, W, Y, alpha, S, B, Cs, Ws, Ys`. The **policy-functions figure stays unchanged** (deterministic — no band).
- The `bands` key must never reach the results-table JSON (the table renders every sim key as a column).
- Composition chart is **unstacked** into two banded lines (Stocks `#003E74`, Bonds `#9ecae1`).
- Y-axis label on composition stays exactly `Amount held (normalized by income)` (values are normalized by permanent income, not dollars).
- Matplotlib must use the headless `Agg` backend (already set in `plots.py`).
- Tests live in `Real/tests/` (outside the Vercel root `Real/frontend`) so they are not bundled into the function. Run with plain `python` (no pytest in this environment).

---

### Task 1: Compute percentile bands in the simulation and keep them out of the table

**Files:**
- Modify: `frontend/api/_model/solver.py` (add `BAND_COVERAGE`; compute bands in `simulate()`)
- Modify: `frontend/api/run.py:54` (exclude `bands` from table JSON)
- Test: `Real/tests/test_bands_data.py` (create)

**Interfaces:**
- Consumes: existing `solve_model(inputDict)` → `(params, grids, survprob, income, C, A, V)`; existing `simulate(params, grids, survprob, income, C, A, seed=42)`.
- Produces:
  - Module constant `BAND_COVERAGE = 0.95` in `solver.py`.
  - `simulate(...)` return dict gains key `bands`: a dict mapping each of `C, W, Y, alpha, S, B, Cs, Ws, Ys` to `{'lo': np.ndarray(tn,), 'hi': np.ndarray(tn,)}`. All existing mean keys unchanged.
  - `run.py`'s table JSON excludes `bands`; charts still receive the full in-memory sim.

- [ ] **Step 1: Write the failing test**

Create `Real/tests/test_bands_data.py`:

```python
import os
import sys

import numpy as np

# Import the model package that lives inside the Vercel function dir.
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "api", "_model")
sys.path.insert(0, MODEL_DIR)

from solver import solve_model, simulate, BAND_COVERAGE  # noqa: E402

# Small grids so the solve is fast; behaviour is identical to full size.
SMALL = dict(
    tb=20, tr=66, td=100, rho=10.0, delta=0.97, psi=0.5, r=1.015, mu=0.04,
    sigr=0.2, smay=0.1, smav=0.1, corr_v=0.0, corr_y=0.0, ret_fac=0.68212,
    aa=0.530339, b1=0.16818, b2=-0.00323371, b3=1.9704e-5,
    ncash=15, na=15, nc=11, n=5, maxcash=200.0, mincash=0.25, nsim=400,
)

EXPECTED = {"C", "W", "Y", "alpha", "S", "B", "Cs", "Ws", "Ys"}


def main():
    assert BAND_COVERAGE == 0.95, BAND_COVERAGE

    params, grids, survprob, income, C, A, V = solve_model(SMALL)
    sim = simulate(params, grids, survprob, income, C, A)
    tn = params["tn"]

    assert "bands" in sim, "sim must include a 'bands' key"
    assert set(sim["bands"]) == EXPECTED, sorted(sim["bands"])

    for key, band in sim["bands"].items():
        assert band["lo"].shape == (tn,), (key, band["lo"].shape)
        assert band["hi"].shape == (tn,), (key, band["hi"].shape)
        assert np.all(band["lo"] <= band["hi"] + 1e-9), f"lo>hi for {key}"

    # Non-negative quantities never dip below zero.
    for key in ("W", "S", "B"):
        assert np.all(sim["bands"][key]["lo"] >= -1e-9), f"negative lo for {key}"

    # The results-table JSON (built like run.py) must exclude bands.
    table = {k: v.tolist() for k, v in sim.items() if k != "bands"}
    assert "bands" not in table
    assert "meanC" in table and "meanalpha" in table

    print("Task 1 tests passed")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && python tests/test_bands_data.py`
Expected: FAIL — `ImportError: cannot import name 'BAND_COVERAGE' from 'solver'` (constant not defined yet).

- [ ] **Step 3: Add the `BAND_COVERAGE` constant**

In `frontend/api/_model/solver.py`, directly below the module docstring / imports (after `from model import ...`), add:

```python
# Central coverage of the uncertainty bands drawn on the simulated charts.
# Single source of truth: drives both the percentile math (here) and the
# chart labels (plots.py imports this). E.g. 0.95 -> 2.5th to 97.5th pct.
BAND_COVERAGE = 0.95
```

- [ ] **Step 4: Compute the bands inside `simulate()`**

In `frontend/api/_model/solver.py`, in `simulate()`, find the block that computes the scaled series (ends with `meanYs = meanY * cGPY`) and the final `return { ... }`. Insert the band computation **after `meanYs` is defined and before the `return`**:

```python
    # --- Percentile bands across paths (central BAND_COVERAGE coverage) ---
    lo_pct = 100.0 * (1.0 - BAND_COVERAGE) / 2.0     # e.g. 2.5
    hi_pct = 100.0 * (1.0 + BAND_COVERAGE) / 2.0     # e.g. 97.5

    def _band(arr):
        return {
            'lo': np.percentile(arr, lo_pct, axis=1),
            'hi': np.percentile(arr, hi_pct, axis=1),
        }

    bands = {
        'C': _band(simC), 'W': _band(simW), 'Y': _band(simY),
        'alpha': _band(simA), 'S': _band(simS), 'B': _band(simB),
    }
    # Scaled series are mean*cGPY; cGPY is a positive deterministic factor,
    # so the scaled band is just the level band scaled by the same vector.
    bands['Cs'] = {'lo': bands['C']['lo'] * cGPY, 'hi': bands['C']['hi'] * cGPY}
    bands['Ws'] = {'lo': bands['W']['lo'] * cGPY, 'hi': bands['W']['hi'] * cGPY}
    bands['Ys'] = {'lo': bands['Y']['lo'] * cGPY, 'hi': bands['Y']['hi'] * cGPY}
```

Then add `bands` to the returned dict. Change:

```python
    return {
        'meanC': meanC, 'meanW': meanW, 'meanY': meanY, 'meanGPY': meanGPY,
        'meanS': meanS, 'meanB': meanB, 'meanalpha': meanalpha,
        'meanCs': meanCs, 'meanWs': meanWs, 'meanYs': meanYs,
        'cGPY': cGPY, 'meanWY': meanWY,
    }
```

to:

```python
    return {
        'meanC': meanC, 'meanW': meanW, 'meanY': meanY, 'meanGPY': meanGPY,
        'meanS': meanS, 'meanB': meanB, 'meanalpha': meanalpha,
        'meanCs': meanCs, 'meanWs': meanWs, 'meanYs': meanYs,
        'cGPY': cGPY, 'meanWY': meanWY,
        'bands': bands,
    }
```

- [ ] **Step 5: Exclude `bands` from the table JSON in `run.py`**

In `frontend/api/run.py`, in `_run_model`, change line 54 from:

```python
        "sim": {key: value.tolist() for key, value in sim.items()},
```

to:

```python
        "sim": {key: value.tolist() for key, value in sim.items() if key != "bands"},
```

(The `make_charts(params, grids, sim, C, A)` call on line 52 already receives the full in-memory `sim`, so the plotter still sees `bands`.)

- [ ] **Step 6: Run test to verify it passes**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && python tests/test_bands_data.py`
Expected: PASS — prints `Task 1 tests passed`.

- [ ] **Step 7: Byte-compile the changed backend files**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real/frontend/api" && python -m py_compile run.py _model/solver.py && echo OK`
Expected: prints `OK`.

- [ ] **Step 8: Commit**

```bash
cd "C:/Users/George/OneDrive/Documents/Research/Real"
git add frontend/api/_model/solver.py frontend/api/run.py tests/test_bands_data.py
git commit -m "feat: compute 95% percentile bands in simulate(), keep out of table"
```

---

### Task 2: Render the bands in the charts (and unstack composition)

**Files:**
- Modify: `frontend/api/_model/plots.py` (import `BAND_COVERAGE`; shade lifecycle panels; unstack composition into two banded lines; add coverage note)
- Modify: `frontend/src/pages/Inputs.js` (composition figure `alt` text — no longer "stacked")
- Test: `Real/tests/test_bands_render.py` (create)

**Interfaces:**
- Consumes: `make_charts(params, grids, sim, C, A)` where `sim` now contains `sim['bands']` (from Task 1); `BAND_COVERAGE` from `solver`.
- Produces: `make_charts(...)` still returns `{'lifecycle': uri, 'policy': uri, 'composition': uri}`; the `lifecycle` and `composition` PNGs now include shaded bands; `policy` unchanged.

- [ ] **Step 1: Write the failing test**

Create `Real/tests/test_bands_render.py`:

```python
import base64
import os
import sys

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "api", "_model")
sys.path.insert(0, MODEL_DIR)

from solver import solve_model, simulate  # noqa: E402
from plots import make_charts, _band_note  # noqa: E402

SMALL = dict(
    tb=20, tr=66, td=100, rho=10.0, delta=0.97, psi=0.5, r=1.015, mu=0.04,
    sigr=0.2, smay=0.1, smav=0.1, corr_v=0.0, corr_y=0.0, ret_fac=0.68212,
    aa=0.530339, b1=0.16818, b2=-0.00323371, b3=1.9704e-5,
    ncash=15, na=15, nc=11, n=5, maxcash=200.0, mincash=0.25, nsim=400,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _is_png(uri):
    assert uri.startswith("data:image/png;base64,"), uri[:40]
    raw = base64.b64decode(uri.split(",", 1)[1])
    return raw[:8] == PNG_MAGIC


def main():
    # The coverage note is derived from the constant, not hard-coded.
    assert _band_note() == "Shaded = central 95% of simulated households", _band_note()

    params, grids, survprob, income, C, A, V = solve_model(SMALL)
    sim = simulate(params, grids, survprob, income, C, A)
    charts = make_charts(params, grids, sim, C, A)

    assert set(charts) == {"lifecycle", "policy", "composition"}, sorted(charts)
    for key in charts:
        assert _is_png(charts[key]), key

    print("Task 2 tests passed")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && python tests/test_bands_render.py`
Expected: FAIL — `ImportError: cannot import name '_band_note' from 'plots'` (helper not defined yet).

- [ ] **Step 3: Import the constant and add the note helper in `plots.py`**

In `frontend/api/_model/plots.py`, add to the imports (below `import matplotlib.pyplot as plt`):

```python
from solver import BAND_COVERAGE  # noqa: E402  (single source of truth)
```

Then add this helper near `_policy_ages` (module level):

```python
def _band_note():
    """Caption describing the shaded band, driven by BAND_COVERAGE."""
    pct = int(round(BAND_COVERAGE * 100))
    return f"Shaded = central {pct}% of simulated households"
```

- [ ] **Step 4: Shade the life-cycle profile panels**

In `frontend/api/_model/plots.py`, inside `make_charts`, replace the entire "Figure 2: life-cycle profiles" block (the three `axes[0]/axes[1]/axes[2]` panels, from `ages = np.arange(...)` down to `lifecycle_uri = _fig_to_uri(fig)`) with:

```python
    # ---- Figure 2: life-cycle profiles (with percentile bands) ----
    ages = np.arange(tb, td + 1)
    bands = sim["bands"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Panel 1: consumption / wealth / income (levels)
    ax = axes[0]
    for key, color, style, lab in (("C", "red", "-", "Consumption"),
                                   ("W", "blue", "--", "Wealth"),
                                   ("Y", "black", ":", "Income")):
        ax.fill_between(ages, bands[key]["lo"], bands[key]["hi"],
                        color=color, alpha=0.15, linewidth=0)
        ax.plot(ages, sim["mean" + key], color=color, linestyle=style,
                linewidth=2, label=lab)
    ax.set_title("Life-Cycle Profiles (normalized)")
    ax.set_xlabel("Age")
    ax.legend()
    ax.set_xlim(tb, td)

    # Panel 2: average stock share
    ax = axes[1]
    ax.fill_between(ages, bands["alpha"]["lo"], bands["alpha"]["hi"],
                    color="blue", alpha=0.15, linewidth=0)
    ax.plot(ages, sim["meanalpha"], color="blue", linewidth=2)
    ax.set_title("Average Stock Share")
    ax.set_xlabel("Age")
    ax.set_ylabel("Share in stocks")
    ax.set_xlim(tb, td)
    ax.set_ylim(0, 1.1)

    # Panel 3: scaled by age-20 income
    ax = axes[2]
    for key, color, style, lab in (("Cs", "red", "-", "Consumption"),
                                   ("Ws", "blue", "--", "Wealth"),
                                   ("Ys", "black", ":", "Income")):
        ax.fill_between(ages, bands[key]["lo"], bands[key]["hi"],
                        color=color, alpha=0.15, linewidth=0)
        ax.plot(ages, sim["mean" + key], color=color, linestyle=style,
                linewidth=2, label=lab)
    ax.set_title("Scaled by Age-20 Income")
    ax.set_xlabel("Age")
    ax.legend()
    ax.set_xlim(tb, td)

    fig.text(0.5, -0.01, _band_note(), ha="center", va="top",
             fontsize=9, style="italic")
    fig.tight_layout()
    lifecycle_uri = _fig_to_uri(fig)
```

- [ ] **Step 5: Unstack the composition figure into two banded lines**

In `frontend/api/_model/plots.py`, replace the entire "Figure 3: portfolio composition" block (from the `fig, ax = plt.subplots(figsize=(10, 5))` for composition down to `composition_uri = _fig_to_uri(fig)`) with:

```python
    # ---- Figure 3: portfolio composition (stocks & bonds, each banded) ----
    # Unstacked so each holding can carry its own percentile band.
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.fill_between(ages, bands["S"]["lo"], bands["S"]["hi"],
                    color="#003E74", alpha=0.15, linewidth=0)
    ax.plot(ages, np.asarray(sim["meanS"]), color="#003E74",
            linewidth=2, label="Stocks")

    ax.fill_between(ages, bands["B"]["lo"], bands["B"]["hi"],
                    color="#9ecae1", alpha=0.30, linewidth=0)
    ax.plot(ages, np.asarray(sim["meanB"]), color="#9ecae1",
            linewidth=2, label="Bonds")

    ax.set_title("Portfolio Composition: Stocks vs Bonds")
    ax.set_xlabel("Age")
    ax.set_ylabel("Amount held (normalized by income)")
    ax.legend(loc="upper left")
    ax.set_xlim(tb, td)
    ax.set_ylim(bottom=0)
    ax.text(0.99, 0.02, _band_note(), transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, style="italic")
    fig.tight_layout()
    composition_uri = _fig_to_uri(fig)
```

(The `return {"lifecycle": ..., "policy": ..., "composition": ...}` at the end of `make_charts` is unchanged. The "Figure 1: policy functions" block is unchanged.)

- [ ] **Step 6: Run test to verify it passes**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && python tests/test_bands_render.py`
Expected: PASS — prints `Task 2 tests passed`.

- [ ] **Step 7: Update the composition figure's alt text**

In `frontend/src/pages/Inputs.js`, find the composition `<img>` and change its `alt` from:

```jsx
                   alt="Portfolio composition by age: stock and bond holdings stacked to show the split of savings at each age" />
```

to:

```jsx
                   alt="Portfolio composition by age: mean stock and bond holdings, each with a 95% band showing the spread across households" />
```

- [ ] **Step 8: Byte-compile the changed plotter**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real/frontend/api" && python -m py_compile _model/plots.py && echo OK`
Expected: prints `OK`.

- [ ] **Step 9: Commit**

```bash
cd "C:/Users/George/OneDrive/Documents/Research/Real"
git add frontend/api/_model/plots.py frontend/src/pages/Inputs.js tests/test_bands_render.py
git commit -m "feat: shade 95% bands on lifecycle and composition charts"
```

---

### Task 3: End-to-end verification and push

**Files:** none (verification only)

**Interfaces:** Consumes the finished backend + frontend from Tasks 1–2.

- [ ] **Step 1: Run both test scripts together**

Run:
```bash
cd "C:/Users/George/OneDrive/Documents/Research/Real"
python tests/test_bands_data.py && python tests/test_bands_render.py
```
Expected: prints `Task 1 tests passed` then `Task 2 tests passed`.

- [ ] **Step 2: Confirm the coverage constant is the single lever (manual grep)**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && grep -rn "BAND_COVERAGE" frontend/api/_model/`
Expected: `solver.py` defines it once; `plots.py` imports it. No hard-coded `95`/`0.95`/`2.5`/`97.5` for the band elsewhere in `plots.py`.

- [ ] **Step 3: Visual smoke check in the running app**

Start the app (per the project's usual dev flow), submit a run, and confirm:
- Life-cycle profile lines each sit inside a soft shaded band; the italic caption reads "Shaded = central 95% of simulated households".
- Stock-share band stays within 0–1.
- Composition chart shows two lines (Stocks, Bonds), each with a band, no stacked area.
- The policy-functions figure is unchanged (no bands).
- The year-by-year table is unchanged (no extra "bands" column, no errors).

- [ ] **Step 4: Push**

```bash
cd "C:/Users/George/OneDrive/Documents/Research/Real"
git push
```
Expected: `main` updated on the remote; Vercel starts a deploy.

---

## Notes for the implementer

- Run everything with the `python` on PATH (the environment that has `numpy` and `matplotlib`), not the `backend/venv` python (which lacks matplotlib).
- The solve for `SMALL` prints per-period progress lines to stderr/stdout — that's expected noise, not a failure.
- If `fig.text(...)` caption appears clipped, it is still captured because `_fig_to_uri` saves with `bbox_inches="tight"`.
