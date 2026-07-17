# Standard-Deviation Bands (replacing 95% percentile bands) — Design

**Date:** 2026-07-17
**Status:** Approved (design), pending implementation plan
**Supersedes the band definition in:** `2026-07-17-uncertainty-bands-design.md`

## Problem

The simulation charts currently shade the **central 95% percentile band**
(2.5th–97.5th) around each mean line, labelled "central 95% of simulated
households". We want the band to instead represent **±1 standard deviation**
around the mean, with labels and alt text updated to say so.

## Key statistical decision

"1 standard deviation" = the central ~68.27% of a normal distribution, **not**
84.13% (84.13% is the percentile of the *upper* edge alone; the band spans the
15.87th–84.13th percentiles).

We use **clamped Method A** — literal `mean ± k·σ`, with the lower edge floored
at what the model allows:

- Compute per age, across the simulated paths: `mean` and `sd`.
- `lo = mean − BAND_SIGMAS·sd`, `hi = mean + BAND_SIGMAS·sd`.
- **Clamp** `lo` to 0 for every series (all quantities are ≥ 0 in the model:
  no-borrowing constraint ⇒ wealth, consumption, income, stocks, bonds ≥ 0).
- **Stock share** additionally clamps `hi` to 1 (share ∈ [0, 1]).

This keeps the literal "1 standard deviation" meaning while refusing to draw
into impossible regions (negative wealth, share outside [0, 1]).

### Documented caveat (must appear in code comments and on the labels)

Where `lo` (or the share's `hi`) is clamped, the drawn arm is **shorter than a
full σ**, so the band is **asymmetric** there and is not literally ±1σ on the
clamped side. Example — wealth at age 25 with mean 1.5, σ 2.0: true ±1σ is
`[−0.5, 3.5]`; drawn (clamped) is `[0, 3.5]`, whose lower arm is only 0.75σ.
Clamping triggers mainly at young ages (wealth/consumption near 0) and for the
stock share near its bounds. Everywhere the mean sits comfortably above σ
(mid-life wealth/consumption/income) the band is a clean, symmetric, literal
±1σ. Because of this, the labels state that the band is **clamped**.

## Single source of truth

Replace the constant `BAND_COVERAGE = 0.95` in `solver.py` with:

```python
BAND_SIGMAS = 1.0   # number of standard deviations the band spans
```

It drives both the band math and the label text. Changing it (e.g. to `2.0`)
updates the shading and every caption together.

## Scope

**Changes:**
- Band computation in `simulate()` (percentiles → clamped `mean ± k·σ`).
- The constant (`BAND_COVERAGE` → `BAND_SIGMAS`) and its import in `plots.py`.
- The figure caption text (`_band_note()`).
- The composition figure's alt text in `Inputs.js` (the only alt mentioning
  "95%").
- The two backend test scripts.

**Unchanged:**
- **Policy figure** — stays clean deterministic lines, **no band, no scale
  change** (policy functions are deterministic; there is no σ to draw, and the
  user opted to leave the vertical scale as-is).
- The set of banded series: `C, W, Y, alpha, S, B, Cs, Ws, Ys`.
- The results table (bands still excluded from the table JSON).
- The composition chart being two unstacked lines (Stocks, Bonds).
- Runtime — `mean ± σ` costs the same as percentiles, so this is **orthogonal
  to the separate deploy-timeout issue** and neither fixes nor worsens it.

## Architecture / data flow

### `solver.py`

- Replace `BAND_COVERAGE = 0.95` with `BAND_SIGMAS = 1.0`.
- In `simulate()`, replace the percentile-based `_band(arr)` with:

  ```python
  def _band(arr, hi_cap=None):
      m = arr.mean(axis=1)
      sd = arr.std(axis=1)
      lo = np.maximum(m - BAND_SIGMAS * sd, 0.0)   # clamp to the 0 floor
      hi = m + BAND_SIGMAS * sd
      if hi_cap is not None:
          hi = np.minimum(hi, hi_cap)
      return {'lo': lo, 'hi': hi}
  ```

- Build the level bands, capping the share's upper edge at 1:

  ```python
  bands = {
      'C': _band(simC), 'W': _band(simW), 'Y': _band(simY),
      'alpha': _band(simA, hi_cap=1.0), 'S': _band(simS), 'B': _band(simB),
  }
  ```

- Scaled series unchanged in structure — the level band × the deterministic
  positive `cGPY` vector (clamp is preserved since `cGPY > 0`):

  ```python
  bands['Cs'] = {'lo': bands['C']['lo'] * cGPY, 'hi': bands['C']['hi'] * cGPY}
  bands['Ws'] = {'lo': bands['W']['lo'] * cGPY, 'hi': bands['W']['hi'] * cGPY}
  bands['Ys'] = {'lo': bands['Y']['lo'] * cGPY, 'hi': bands['Y']['hi'] * cGPY}
  ```

- The returned dict still carries `bands` under the reserved key; the mean keys
  are unchanged. `run.py` already excludes `bands` from the table JSON — no
  change needed there.

### `plots.py`

- Change the import to `from solver import BAND_SIGMAS`.
- Update `_band_note()` to derive the caption from `BAND_SIGMAS`, note the
  clamp, and pluralise correctly:

  ```python
  def _band_note():
      n = BAND_SIGMAS
      unit = "standard deviation" + ("" if n == 1 else "s")
      return f"Shaded = within {n:g} {unit} of the mean (clamped to feasible values)"
  ```

  → for `BAND_SIGMAS = 1.0`: **"Shaded = within 1 standard deviation of the
  mean (clamped to feasible values)"**.
- No other change: the caption already appears on both the lifecycle figure
  (`fig.text`) and the composition figure (`ax.text`); both update
  automatically. The policy figure has no caption and no band — untouched.

### `Inputs.js`

- Update the composition figure's alt text (currently "…each with a 95% band
  showing the spread across households") to:

  > "Portfolio composition by age: mean stock and bond holdings, each with a
  > ±1 standard deviation band showing the spread across households"

  Kept **hard-coded** (the previously-reverted backend-surfaced value is not
  reintroduced).

## Testing

Update `Real/tests/test_bands_data.py` (small grids, plain `python`):

- `sim['bands']` still contains all nine series with `lo`/`hi` of shape `(tn,)`.
- For every series: `lo ≤ mean ≤ hi` elementwise and `lo ≥ 0` (clamped).
- For `alpha`: `hi ≤ 1` and `lo ≥ 0` (share stays in [0, 1]).
- Recompute check on at least one series: `lo == max(0, mean − BAND_SIGMAS·sd)`
  and `hi == mean + BAND_SIGMAS·sd`, using the same `mean`/`std(axis=1)`.
- The table JSON (built as in `run.py`) still excludes `bands`.

Update `Real/tests/test_bands_render.py`:

- `_band_note()` returns exactly
  `"Shaded = within 1 standard deviation of the mean (clamped to feasible values)"`.
- `make_charts(...)` still returns three PNG data-URIs (`lifecycle`, `policy`,
  `composition`).

Then a real run to eyeball the shading (mid-life bands symmetric; young-age /
share-bound bands sit against the floor).

## Out of scope / future

- Making `BAND_SIGMAS` user-adjustable via a form field (currently a one-line
  constant edit + re-run).
- Bands on the policy figure (not applicable — deterministic).
- The Vercel deploy-timeout issue (tracked separately; unaffected by this
  change).
