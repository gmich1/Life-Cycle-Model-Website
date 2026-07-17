# Standard-Deviation Bands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 95% percentile bands on the simulated charts with clamped ±1 standard-deviation bands, updating the constant, captions, and alt text accordingly.

**Architecture:** The band edges are recomputed in `simulate()` as `mean ± k·σ` with the lower edge clamped to 0 (stock share also caps its upper edge at 1). A single constant `BAND_SIGMAS` drives both the math and the label text, imported by the plotter. The policy figure, the results table, and `run.py` are untouched.

**Tech Stack:** Python 3, NumPy, Matplotlib (Agg), Vercel Python serverless function, Create React App frontend.

## Global Constraints

- Single source of truth: `BAND_SIGMAS = 1.0` defined once in `frontend/api/_model/solver.py`, imported by `plots.py`. Drives the band math AND the labels. Replaces the old `BAND_COVERAGE`.
- Band = clamped Method A, per age across paths: `lo = max(0, mean − BAND_SIGMAS·sd)`, `hi = mean + BAND_SIGMAS·sd`. **Stock share (`alpha`) additionally caps `hi` at 1.**
- Nine banded series: `C, W, Y, alpha, S, B, Cs, Ws, Ys`. Scaled (`Cs, Ws, Ys`) = the (already clamped) level band × the deterministic positive `cGPY` vector.
- Figure caption (appears on BOTH the lifecycle and composition figures), derived from `BAND_SIGMAS` and **must mention "clamped"**: for `BAND_SIGMAS = 1.0` it reads exactly `Shaded = within 1 standard deviation of the mean (clamped to feasible values)`.
- Composition figure alt text (hard-coded in `Inputs.js`): `Portfolio composition by age: mean stock and bond holdings, each with a ±1 standard deviation band showing the spread across households`.
- Unchanged: the **policy figure** (clean lines, no band, no scale change); the results table (bands still excluded from the table JSON); `run.py` (needs no change).
- Tests live in `Real/tests/`, run with plain `python` (no pytest). Use the `python` on PATH (has numpy AND matplotlib) — NOT `backend/venv`'s python.
- The solver prints per-period progress to stdout while solving; that noise is expected, not a failure.

---

### Task 1: Recompute bands as clamped ±BAND_SIGMAS·σ (backend)

**Files:**
- Modify: `frontend/api/_model/solver.py` (constant at lines 9–12; band block at ~lines 560–578)
- Modify: `frontend/api/_model/plots.py` (import at line 22; `_band_note()` at lines 41–44)
- Modify: `tests/test_bands_data.py` (rewrite)
- Modify: `tests/test_bands_render.py` (update the `_band_note()` assertion)

**Interfaces:**
- Consumes: `solve_model(inputDict)`, `simulate(params, grids, survprob, income, C, A, seed=42)`, `make_charts(params, grids, sim, C, A)`.
- Produces:
  - `solver.py` exports `BAND_SIGMAS = 1.0` (the old `BAND_COVERAGE` no longer exists).
  - `sim['bands']` still maps `C, W, Y, alpha, S, B, Cs, Ws, Ys` → `{'lo': ndarray(tn,), 'hi': ndarray(tn,)}`, now computed as clamped `mean ± BAND_SIGMAS·σ`.
  - `plots._band_note()` returns `"Shaded = within 1 standard deviation of the mean (clamped to feasible values)"`.

- [ ] **Step 1: Rewrite the data test to the new contract (failing)**

Replace the entire contents of `tests/test_bands_data.py` with:

```python
import os
import sys

import numpy as np

# Import the model package that lives inside the Vercel function dir.
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "api", "_model")
sys.path.insert(0, MODEL_DIR)

from solver import solve_model, simulate, BAND_SIGMAS  # noqa: E402

# Small grids so the solve is fast; behaviour is identical to full size.
SMALL = dict(
    tb=20, tr=66, td=100, rho=10.0, delta=0.97, psi=0.5, r=1.015, mu=0.04,
    sigr=0.2, smay=0.1, smav=0.1, corr_v=0.0, corr_y=0.0, ret_fac=0.68212,
    aa=0.530339, b1=0.16818, b2=-0.00323371, b3=1.9704e-5,
    ncash=15, na=15, nc=11, n=5, maxcash=200.0, mincash=0.25, nsim=400,
)

EXPECTED = {"C", "W", "Y", "alpha", "S", "B", "Cs", "Ws", "Ys"}


def main():
    assert BAND_SIGMAS == 1.0, BAND_SIGMAS

    params, grids, survprob, income, C, A, V = solve_model(SMALL)
    sim = simulate(params, grids, survprob, income, C, A)
    tn = params["tn"]

    assert "bands" in sim, "sim must include a 'bands' key"
    assert set(sim["bands"]) == EXPECTED, sorted(sim["bands"])

    means = {
        "C": sim["meanC"], "W": sim["meanW"], "Y": sim["meanY"],
        "alpha": sim["meanalpha"], "S": sim["meanS"], "B": sim["meanB"],
        "Cs": sim["meanCs"], "Ws": sim["meanWs"], "Ys": sim["meanYs"],
    }

    for key, band in sim["bands"].items():
        lo, hi, m = band["lo"], band["hi"], means[key]
        assert lo.shape == (tn,) and hi.shape == (tn,), (key, lo.shape, hi.shape)
        assert np.all(lo >= -1e-9), f"negative lo for {key}"      # clamped at 0
        assert np.all(lo <= m + 1e-9), f"lo>mean for {key}"
        assert np.all(hi >= m - 1e-9), f"hi<mean for {key}"

    # Stock share band stays within [0, 1].
    a = sim["bands"]["alpha"]
    assert np.all(a["hi"] <= 1.0 + 1e-9), "alpha hi>1"
    assert np.all(a["lo"] >= -1e-9), "alpha lo<0"

    # Symmetric mean +/- k*sd, then lower edge clamped at 0, implies
    #   lo == max(0, 2*mean - hi)
    # for every series whose hi is NOT capped (all but alpha). This verifies
    # the symmetry and the clamp without needing the per-path std.
    for key in ("C", "W", "Y", "S", "B", "Cs", "Ws", "Ys"):
        lo, hi, m = sim["bands"][key]["lo"], sim["bands"][key]["hi"], means[key]
        expected_lo = np.maximum(2.0 * m - hi, 0.0)
        assert np.allclose(lo, expected_lo, atol=1e-9), f"clamp/symmetry mismatch for {key}"

    # The results-table JSON (built like run.py) must exclude bands.
    table = {k: v.tolist() for k, v in sim.items() if k != "bands"}
    assert "bands" not in table
    assert "meanC" in table and "meanalpha" in table

    print("Task 1 tests passed")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the data test to verify it fails**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && python tests/test_bands_data.py`
Expected: FAIL — `ImportError: cannot import name 'BAND_SIGMAS' from 'solver'`.

- [ ] **Step 3: Rename the constant in `solver.py`**

In `frontend/api/_model/solver.py`, replace lines 9–12:

```python
# Central coverage of the uncertainty bands drawn on the simulated charts.
# Single source of truth: drives both the percentile math (here) and the
# chart labels (plots.py imports this). E.g. 0.95 -> 2.5th to 97.5th pct.
BAND_COVERAGE = 0.95
```

with:

```python
# Width of the uncertainty bands drawn on the simulated charts, in standard
# deviations. Single source of truth: drives both the band math (here) and the
# chart labels (plots.py imports this). E.g. 1.0 -> mean +/- 1 sigma.
BAND_SIGMAS = 1.0
```

- [ ] **Step 4: Replace the band computation in `simulate()`**

In `frontend/api/_model/solver.py`, replace the whole band block (currently the `# --- Percentile bands ...` comment through the `bands['Ys'] = ...` line, ~lines 560–578):

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

with:

```python
    # --- Bands: mean +/- BAND_SIGMAS standard deviations across paths ---
    # Lower edge clamped to 0 (all quantities are >= 0 in the model: the
    # no-borrowing constraint keeps wealth, consumption, income, stocks and
    # bonds non-negative); the stock share additionally caps its upper edge at
    # 1. Where clamping bites (young ages, share near its bounds) the drawn arm
    # is shorter than a full sigma, so the band is asymmetric there and not
    # literally +/-1 sigma on the clamped side.
    def _band(arr, hi_cap=None):
        m = arr.mean(axis=1)
        sd = arr.std(axis=1)
        lo = np.maximum(m - BAND_SIGMAS * sd, 0.0)
        hi = m + BAND_SIGMAS * sd
        if hi_cap is not None:
            hi = np.minimum(hi, hi_cap)
        return {'lo': lo, 'hi': hi}

    bands = {
        'C': _band(simC), 'W': _band(simW), 'Y': _band(simY),
        'alpha': _band(simA, hi_cap=1.0), 'S': _band(simS), 'B': _band(simB),
    }
    # Scaled series are mean*cGPY; cGPY is a positive deterministic factor, so
    # the scaled band is just the (already clamped) level band scaled by it.
    bands['Cs'] = {'lo': bands['C']['lo'] * cGPY, 'hi': bands['C']['hi'] * cGPY}
    bands['Ws'] = {'lo': bands['W']['lo'] * cGPY, 'hi': bands['W']['hi'] * cGPY}
    bands['Ys'] = {'lo': bands['Y']['lo'] * cGPY, 'hi': bands['Y']['hi'] * cGPY}
```

- [ ] **Step 5: Update the import and caption in `plots.py`**

In `frontend/api/_model/plots.py`, change the import (line 22):

```python
from solver import BAND_COVERAGE  # noqa: E402  (single source of truth)
```

to:

```python
from solver import BAND_SIGMAS  # noqa: E402  (single source of truth)
```

Then replace `_band_note()` (lines 41–44):

```python
def _band_note():
    """Caption describing the shaded band, driven by BAND_COVERAGE."""
    pct = int(round(BAND_COVERAGE * 100))
    return f"Shaded = central {pct}% of simulated households"
```

with:

```python
def _band_note():
    """Caption describing the shaded band, driven by BAND_SIGMAS."""
    n = BAND_SIGMAS
    unit = "standard deviation" + ("" if n == 1 else "s")
    return f"Shaded = within {n:g} {unit} of the mean (clamped to feasible values)"
```

- [ ] **Step 6: Run the data test to verify it passes**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && python tests/test_bands_data.py`
Expected: PASS — prints `Task 1 tests passed`.

- [ ] **Step 7: Update the render test's caption assertion**

In `tests/test_bands_render.py`, change line 29:

```python
    assert _band_note() == "Shaded = central 95% of simulated households", _band_note()
```

to:

```python
    assert _band_note() == "Shaded = within 1 standard deviation of the mean (clamped to feasible values)", _band_note()
```

- [ ] **Step 8: Run the render test to verify it passes**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && python tests/test_bands_render.py`
Expected: PASS — prints `Task 2 tests passed`.

- [ ] **Step 9: Byte-compile the changed backend files**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real/frontend/api" && python -m py_compile _model/solver.py _model/plots.py && echo OK`
Expected: prints `OK`.

- [ ] **Step 10: Commit**

```bash
cd "C:/Users/George/OneDrive/Documents/Research/Real"
git add frontend/api/_model/solver.py frontend/api/_model/plots.py tests/test_bands_data.py tests/test_bands_render.py
git commit -m "feat: replace 95% percentile bands with clamped +/-1 SD bands"
```

---

### Task 2: Update the composition alt text (frontend)

**Files:**
- Modify: `frontend/src/pages/Inputs.js` (composition `<img>` alt, ~line 314)

**Interfaces:**
- Consumes: nothing from Task 1 at runtime (static string change).
- Produces: composition figure alt text reads "±1 standard deviation band…".

- [ ] **Step 1: Change the alt text**

In `frontend/src/pages/Inputs.js`, find the composition image and change:

```jsx
                   alt="Portfolio composition by age: mean stock and bond holdings, each with a 95% band showing the spread across households" />
```

to:

```jsx
                   alt="Portfolio composition by age: mean stock and bond holdings, each with a ±1 standard deviation band showing the spread across households" />
```

- [ ] **Step 2: Verify the change and confirm nothing else references the old copy**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && grep -rn "standard deviation band" frontend/src/pages/Inputs.js && ! grep -rn "95% band" frontend/src/pages/Inputs.js && echo OK`
Expected: prints the new alt line, then `OK` (no remaining "95% band").

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/George/OneDrive/Documents/Research/Real"
git add frontend/src/pages/Inputs.js
git commit -m "feat: composition alt text says +/-1 standard deviation"
```

---

### Task 3: End-to-end verification and finish

**Files:** none (verification only)

**Interfaces:** Consumes the finished backend + frontend from Tasks 1–2.

- [ ] **Step 1: Run both test scripts together**

Run:
```bash
cd "C:/Users/George/OneDrive/Documents/Research/Real"
python tests/test_bands_data.py && python tests/test_bands_render.py
```
Expected: prints `Task 1 tests passed` then `Task 2 tests passed`.

- [ ] **Step 2: Confirm the constant is the single lever and the old name is gone**

Run: `cd "C:/Users/George/OneDrive/Documents/Research/Real" && grep -rn "BAND_SIGMAS" frontend/api/_model/ && ! grep -rn "BAND_COVERAGE" frontend/api/_model/ frontend/api/run.py && echo OK`
Expected: shows `BAND_SIGMAS` defined in `solver.py` and imported in `plots.py`, then `OK` (no `BAND_COVERAGE` anywhere).

- [ ] **Step 3: Visual smoke check (manual, in the running app)**

Start the app (usual dev flow), submit a run, and confirm:
- Lifecycle and composition bands render, with the italic caption "Shaded = within 1 standard deviation of the mean (clamped to feasible values)".
- Mid-life wealth/consumption bands look roughly symmetric; near young ages / share bounds the lower edge sits at the floor (asymmetric — expected).
- Stock-share band stays within 0–1.
- Policy figure unchanged (no bands, same scale).
- Year-by-year table unchanged (no extra column, no error).

- [ ] **Step 4: Finish the branch**

Use superpowers:finishing-a-development-branch to verify tests and integrate (merge to `main` + push, per the project's deploy flow).

---

## Notes for the implementer

- Run everything with the `python` on PATH (numpy + matplotlib), not `backend/venv`'s python.
- `n:g` formats `1.0` as `1` and `2.0` as `2`; `n == 1` is true for the float `1.0`, so the singular "standard deviation" is used at the default.
- `run.py` already excludes `bands` from the table JSON and passes the full sim to `make_charts` — no change needed there.
- This change does not affect solve runtime and is unrelated to the separate Vercel deploy-timeout issue.
