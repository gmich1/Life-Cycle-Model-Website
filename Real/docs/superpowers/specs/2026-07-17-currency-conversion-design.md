# Currency Conversion for the Results — Design

**Date:** 2026-07-17
**Status:** Approved (design), pending implementation plan

## Problem

The results report every quantity in the model's **normalized units** —
multiples of the worker's permanent labor income, with income at the starting
age set to `1.0`. This is standard for the Cocco–Gomes–Maenhout / Gomes (2020)
life-cycle model but opaque to a lay user, who would rather read "£69,032" than
"2.3010".

We want to let the user supply the real salary they earn at the starting age and
see their money results in **tangible currency**, while keeping the normalized
view as the default for anyone who doesn't pick a currency.

## Units background (why the conversion is what it is)

The simulation runs in units where **starting-age income = 1.0**. Permanent
income growth is divided out each period, so the reported quantities fall into
three kinds:

- **Normalized levels** (`meanC`, `meanW`, `meanY`, `meanS`, `meanB`) — multiples
  of *that year's* permanent income. `meanY` sits at ≈1.0 through working life
  and drops to `ret_fac` at retirement.
- **Scaled levels** (`meanCs`, `meanWs`, `meanYs`) — the normalized series ×
  `cGPY` (cumulative permanent-income growth). These are multiples of the
  **starting-age income** and carry the realistic hump-shaped earnings path.
- **Ratios / growth factors** (`meanalpha`, `meanGPY`, `cGPY`, `meanWY`) —
  dimensionless; never denominated in currency.

Only the **scaled** quantities become literal real money when multiplied by the
starting salary `S`. Multiplying a *normalized* level by `S` would give "money
in starting-salary units" (flat income every year) — not tangible currency.
This design therefore converts to **true real money** (the option chosen during
brainstorming), never a flat multiply.

## Key decision: true real money

With starting salary `S` (in the chosen currency) and the per-age `cGPY[i]`
factor the app already computes, the five money quantities are shown as:

| Quantity | Real-money value | Source series |
|---|---|---|
| Consumption | `meanCs[i] × S`          | scaled |
| Wealth      | `meanWs[i] × S`          | scaled |
| Income      | `meanYs[i] × S`          | scaled |
| Stocks      | `meanS[i] × cGPY[i] × S` | normalized × cGPY |
| Bonds       | `meanB[i] × cGPY[i] × S` | normalized × cGPY |

All five formulas are mutually consistent: they use the **same** `cGPY` the app
already uses to define its scaled series (`meanCs = meanC × cGPY`, etc.), so
`Stocks = meanS × cGPY × S` is on the same footing as
`Consumption = meanCs × S = meanC × cGPY × S`.

`cGPY` is the app's existing additive cumulative-growth approximation
(`cGPY[i] = cGPY[i-1] + (meanGPY[i] − 1)`); reusing it keeps every currency
figure consistent with the existing scaled series and the chart's
"Scaled by age-20 income" panel.

The dimensionless quantities — stock share, wealth/income, permanent-income
growth, cumulative growth — and the plain normalized consumption / wealth /
income are **never** given a currency symbol; they keep their current
normalized display.

## Frontend-only

The API already returns every series this needs (`meanCs`, `meanWs`, `meanYs`,
`meanS`, `meanB`, `cGPY` — see `run.py`, which serialises all `sim` keys except
`bands`). The conversion is a **pure render-time transform in `Inputs.js`**:

- **No backend / solver / `run.py` changes.**
- The model still runs entirely in normalized units.
- The two new inputs are **not** sent to `/api/run`.

## UI: two new inputs in the "Income profile & retirement" group

Rendered inside the existing `incprofile` fieldset as **controlled React state**
(like the existing `startAge`), so they persist across preset changes and are
excluded from the POST body. Each carries its **own** helper text (matching how
every other field carries its own `desc`) — not a combined note. Neither text
mentions a table or results layout, since the user hasn't seen any output when
filling the form.

1. **Currency** — `<select>`, default `none`:
   - `None (units)` (value `none`) · `£ GBP` (`GBP`) · `$ USD` (`USD`) ·
     `€ EUR` (`EUR`) · `¥ JPY` (`JPY`). More ISO codes can be added to the one
     list; `Intl.NumberFormat` supplies each symbol and formatting.
   - Helper text: *"The currency your salary is paid in. Choose 'None (units)'
     to keep results in the model's normalized units (multiples of income) — the
     default."*

2. **Starting annual salary** — `type="number"`, `step="any"`, default `1`:
   - Helper text: *"Your annual pay at the starting age. Enter it in the currency
     chosen above to see your results as real money instead of multiples of
     income. If you're unsure, set Currency to 'None (units)' and leave this at
     1."*

### Exclusion from the POST

`handleSubmit` builds `params` from the form's `FormData`. Because Currency and
Salary are controlled state (read from React, not from `FormData`), they stay
out of the request. If they are given `name` attributes for accessibility, the
`FormData` loop skips the keys `currency` and `salary` explicitly.

## Rendering behaviour

**`None (units)` mode (default):** results render exactly as today —
`toFixed(4)`, no currency symbols, stocks/bonds shown normalized. The salary
value is ignored. This is the safe fallback.

**Currency mode (any code other than `none`):**
- The five money quantities convert per the table above and are **currency-
  formatted** with symbol + thousands separators via
  `Intl.NumberFormat(undefined, { style: 'currency', currency: code,
  maximumFractionDigits: 0 })` — e.g. `£69,032`. Their headers gain the currency
  symbol (e.g. `Income (£)`).
- Stock share, wealth/income, permanent-income growth, cumulative growth, and
  the normalized consumption / wealth / income keep their current display
  (`toFixed(4)`, no symbol).
- The results layout is otherwise **identical between modes** — nothing is added
  or removed; only the five money quantities' values and headers change.

### Small decisions (called out, easy to flip later)

- **Stocks/Bonds convert in place.** In currency mode their basis switches from
  normalized to real money, rather than showing both a normalized and a
  currency figure. This is the one place a quantity's *basis* differs between
  modes.
- **Normalized consumption / wealth / income stay** as unit-less multiples in
  currency mode, alongside the scaled money figures, exactly as they sit
  together today.

## Scope

**Changes:**
- Two controlled inputs + their helper text in the `incprofile` group of
  `Inputs.js`.
- Currency + salary React state.
- Render-time conversion + `Intl.NumberFormat` currency formatting for the five
  money quantities in the results.
- Exclusion of the two inputs from the `/api/run` POST body.

**Unchanged:**
- **Backend** — `run.py`, `solver.py`, `model.py`, `plots.py`: no edits. The
  model runs in normalized units and returns the same JSON.
- **Charts** — all three matplotlib figures are untouched. The life-cycle figure
  already has a "Scaled by age-20 income" panel; converting charts to currency
  would require backend edits and is **out of scope** (possible follow-up).
- The preset system, the progress bar, and the rest of the form.

## Testing

- **None mode:** results identical to current output (4 decimals, no symbols,
  stocks/bonds normalized). Salary value has no effect.
- **Currency mode (e.g. GBP, S = 30000):**
  - Income at a mid-career age ≈ `meanYs[i] × 30000` and shows the hump (well
    above £30k in mid-life, `≈ ret_fac × cGPY × 30000` in retirement).
  - Stocks = `meanS[i] × cGPY[i] × 30000`; Bonds likewise.
  - Consumption = `meanCs[i] × 30000`.
  - Dimensionless quantities unchanged; stock share still in `[0, 1]`.
  - The five money figures show `£` with thousands separators.
- **Consistency:** in currency mode, converted Consumption equals
  `meanC × cGPY × S` — i.e. it matches normalized consumption × cumulative
  growth × S, confirming the scaled and normalized bases agree.
- The two new inputs do **not** appear in the network request to `/api/run`.
- Switching Currency back to `None (units)` restores the original display.

## Out of scope / future

- Converting the charts (life-cycle / composition) to currency — needs backend
  edits.
- Per-currency locale formatting beyond symbol + grouping, and
  inflation / real-vs-nominal adjustments.
- Remembering the chosen currency / salary across sessions.
