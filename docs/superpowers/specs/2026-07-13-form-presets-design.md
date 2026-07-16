# Persona Presets & Selector Bar — Design

**Date:** 2026-07-13
**Component:** `Real/frontend/src/pages/Inputs.js` (+ `Inputs.css`)
**Status:** Approved for implementation planning

## 1. Purpose

The input form drives a life-cycle consumption/portfolio-choice model. Today the
form opens on a single set of "generally applicable" default values, and a user
has to understand every parameter to explore alternative scenarios.

This feature adds a **preset selector bar** at the top of the form offering a
small set of **persona presets** — stereotypical roles/positions in society —
that demonstrate how the model's output changes across life situations. Selecting
a persona fills the whole form with that persona's values; the user can then edit
anything and run the simulation as usual.

**Success criterion:** a non-expert can click through the personas, run each, and
*see* the model react (different consumption/wealth paths and, especially,
different optimal stock-share profiles) without touching individual parameters.

## 2. Scope & principles

- Personas differ by **job / human capital**, not by market conditions. Market
  parameters (`r`, `mu`, `sigr`), maximum age (`td=100`), the income-curve *shape*
  (`aa`, `b1`, `b2`, `b3`), and all solver settings stay at their defaults so
  comparisons are apples-to-apples.
- Personas are full archetypes: they bundle **age/horizon**, **income risk**,
  **income–market correlation**, **retirement replacement**, and **temperament**
  (risk aversion / patience / EIS).
- Selecting a preset **only populates the fields**. It does not auto-run and does
  not lock anything — every input remains editable afterward.
- Solver settings are never changed by a preset.
- Where real calibrations exist, values are grounded in the literature; otherwise
  they are reasoned choices on the same scale (documented in §4).

## 3. Which parameters a preset varies

Varied per persona: `tb`, `tr`, `rho`, `delta`, `psi`, `smay`, `smav`, `corr_v`,
`ret_fac`.

Held fixed at default for every persona:

- `td = 100`
- Market: `r = 1.015`, `mu = 0.04`, `sigr = 0.2`
- Income-curve shape/level: `aa = 0.530339`, `b1 = 0.16818`,
  `b2 = -0.00323371`, `b3 = 1.9704e-5`
- `corr_y = 0` for all personas — the model correlates only the **permanent
  aggregate** labour-income shock with stock returns; transitory shocks are
  idiosyncratic (CCGM 2001). Setting `corr_y` non-zero is not economically
  meaningful here.
- Solver: `ncash`, `na`, `nc`, `n`, `maxcash`, `mincash`, `nsim`.

Because the model normalises every quantity by the deterministic income component
`exp(f(t)+p_t)` (confirmed in Gomes 2020), a pure income-*level* shift washes out
of the normalised policy. The education difference that actually moves the
portfolio share therefore lives in the **shock variances** and the
**income–market correlation**, not in the polynomial. This is why no
education-specific income polynomial is required.

## 4. The personas

Seven presets: **Default** plus six archetypes. Values not listed below equal the
defaults in §3.

| Persona | tb | tr | rho | delta | psi | smay | smav | corr_v | ret_fac |
|---|---|---|---|---|---|---|---|---|---|
| Default (HS baseline) | 20 | 66 | 10 | 0.97 | 0.5 | 0.10 | 0.10 | 0.00 | 0.68212 |
| Public-sector lifer | 22 | 66 | 12 | 0.98 | 0.5 | 0.15 | 0.09 | 0.00 | 0.85 |
| Finance professional | 24 | 62 | 6 | 0.95 | 0.6 | 0.242 | 0.130 | 0.52 | 0.45 |
| Entrepreneur | 26 | 68 | 6 | 0.94 | 0.7 | 0.30 | 0.18 | 0.30 | 0.35 |
| Blue-collar (trades) | 18 | 63 | 10 | 0.96 | 0.4 | 0.325 | 0.102 | 0.328 | 0.60 |
| Doctor | 30 | 67 | 8 | 0.98 | 0.5 | 0.242 | 0.130 | 0.10 | 0.55 |
| Gig / precarious | 20 | 68 | 13 | 0.95 | 0.4 | 0.35 | 0.11 | 0.20 | 0.30 |

### 4.1 One-line subtitles (shown on the pills)

- **Default** — Generally-applicable baseline settings.
- **Public-sector lifer** — Stable, market-independent income; generous pension.
- **Finance professional** — High pay that rides the stock market.
- **Entrepreneur** — Volatile self-employment income; no pension.
- **Blue-collar (trades)** — Early start, cyclical manual work.
- **Doctor** — Late start, high and recession-proof income.
- **Gig / precarious** — Insecure, spiky income; minimal safety net.

### 4.2 Grounding of the values

Real, cited anchors (Campbell, Cocco, Gomes & Maenhout 2001, Table 11.1 — the
education-group calibration):

| Education group | σ²ε (transitory) → `smay` | σ²u (permanent) → `smav` | `corr_v` |
|---|---|---|---|
| No high school | .1056 → 0.325 | .0105 → 0.102 | 0.328 |
| High school (baseline) | .0738 → 0.272 | .0106 → 0.103 | 0.371 |
| College | .0584 → 0.242 | .0169 → 0.130 | 0.516 |

- **Blue-collar** uses the No-High-School row exactly (`smay=0.325`, `smav=0.102`,
  `corr_v=0.328`).
- **Finance professional** and **Doctor** both use the College income-risk row
  (`smay=0.242`, `smav=0.130`). They differ **only** in `corr_v`:
  - Finance `corr_v = 0.52` — the actual college-group average; a trader's income
    tracks the market.
  - Doctor `corr_v = 0.10` — a deliberate low-correlation choice (not a printed
    number). Supported by CCGM Tables 11.3/11.4, which show large within-college
    heterogeneity by industry; medicine sits at the stable, recession-resilient
    end. This makes finance-vs-doctor a clean teaching pair: identical education
    and income risk, differing only in market correlation, so the resulting change
    in optimal stock share is attributable to that single lever.
- **Public-sector lifer**, **Entrepreneur**, **Gig** use reasoned values on the
  same scale (high transitory risk and low pension for gig/entrepreneur; very
  stable income and a large replacement ratio for the public-sector persona), not
  direct table rows.
- **Default** intentionally keeps the rounded `smay=smav=0.10` CGM-2005 baseline.
  It therefore shows less income risk than the empirically-calibrated personas;
  this is accepted and understood (Default reads as a smoothed textbook starting
  point). Decision on record: **leave Default scale unchanged.**

The economic narratives each persona is meant to demonstrate:

- **Public-sector lifer** — safe, bond-like human capital pushes the stock share
  up; high risk aversion pulls it down.
- **Finance professional** — income already carries market risk, so the model
  trims equities despite a bold temperament (the counter-intuitive showpiece).
- **Entrepreneur** — large income risk plus no pension → heavy precautionary
  saving, lower stock share.
- **Blue-collar** — early start, earlier retirement, cyclical (moderately
  correlated) income.
- **Doctor** — late start after training, but very safe high income → large human
  capital → aggressive early-career stock share.
- **Gig worker** — severe transitory insecurity and minimal safety net → large
  buffer saving, low stock share.

## 5. UI design — the selector bar

- A horizontal row of **pill buttons** placed at the top of the form, above the
  "Life horizon" fieldset.
- **Default** is active on initial load (form shows the current defaults, exactly
  as today).
- Each pill shows the persona name; the one-line subtitle (§4.1) appears beneath
  or as a caption for the active/hovered pill.
- The active persona is visually highlighted (Imperial-blue fill, matching the
  existing `.btn-primary` treatment); inactive pills use the `.btn-secondary`
  treatment.
- On mobile the row wraps or scrolls horizontally; no fixed heights.
- Styling reuses existing CSS variables (`--imperial-blue`, `--cool-grey`,
  `--radius`, etc.). No new colour system.

## 6. Mechanism — populate the form (Approach A)

The form currently uses **uncontrolled** inputs (`defaultValue` + `FormData` on
submit). Presets are wired in with a **remount**, keeping that model:

- Presets live as a plain data structure keyed by field name, colocated with the
  existing `FIELDS` list:
  ```js
  const PRESETS = [
    { id: 'default', label: 'Default', subtitle: '…', values: { /* only overrides */ } },
    { id: 'public',  label: 'Public-sector lifer', subtitle: '…', values: { tb:22, tr:66, rho:12, delta:0.98, psi:0.5, smay:0.15, smav:0.09, corr_v:0, ret_fac:0.85 } },
    // …
  ]
  ```
  A preset's `values` overrides the `FIELDS` defaults; any field not named falls
  back to its `FIELDS.def`. This keeps presets terse and guarantees every unlisted
  parameter (market, solver, income curve, `td`, `corr_y`) stays at default.
- `activePreset` is held in React state (default `'default'`).
- The `<form>` gets `key={activePreset}`. Selecting a persona changes the key,
  React remounts the form, and every input re-applies its `defaultValue` from the
  now-active preset. After remount the inputs are uncontrolled again, so the user
  edits freely.
- Each input's `defaultValue` becomes `presetValue(name) ?? FIELDS.def`.
- The existing submit path (`handleSubmit`, `FormData`, fetch to `/run`) is
  unchanged.

**Rejected alternative:** converting all 25 inputs to controlled state. Larger
rewrite of a working form with no benefit for this feature (YAGNI).

### 6.1 Interaction with the income-curve combo block

The four income-curve coefficients (`aa`, `b1`, `b2`, `b3`) already render as one
grouped block. No persona overrides them, so they always show their defaults after
a remount. No special handling required.

## 7. Data flow

1. User clicks a persona pill → `setActivePreset(id)`.
2. State change re-renders; `<form key={id}>` remounts.
3. Inputs mount with `defaultValue` resolved from the active preset (overrides)
   falling back to `FIELDS.def`.
4. User optionally edits any field (uncontrolled, as today).
5. User clicks Submit → `FormData` reads current field values → fetch to backend
   `/run` → results table renders. Unchanged from current behaviour.

## 8. Edge cases & notes

- **Editing then switching:** switching personas remounts the form and discards
  in-progress edits for the previous persona. This is intended (a clean reset per
  persona) and matches the approved behaviour ("populate and do nothing else").
- **`startAge` label state:** the results table labels rows using `tb` captured at
  submit time (`setStartAge(params.tb)`), so persona changes to `tb` (e.g. Doctor
  `tb=30`) flow through correctly on the next run. No change needed.
- **No backend change.** Personas are purely front-end presets; the backend
  contract is untouched.
- **Values are display-consistent:** presets use the same units/precision as the
  existing `def` values (e.g. `ret_fac` to 2–5 dp).

## 9. Out of scope

- Persisting the selected persona across reloads.
- Auto-running the simulation on persona selection.
- Comparing two personas side by side in one view.
- Education-specific income *polynomials* (unnecessary — see §3).
- Any change to market or solver parameters.

## 10. Testing / verification

- Manual: load form → Default active, values match current defaults. Click each
  persona → every listed field updates to the table in §4; market, solver, `td`,
  `corr_y`, and the income-curve coefficients remain at defaults. Edit a field,
  switch persona, confirm reset. Submit for two contrasting personas (Finance vs
  Doctor) and confirm the results table differs, with a visibly different stock
  share.
- Sanity: Finance (`corr_v=0.52`) should show a lower optimal stock share than
  Doctor (`corr_v=0.10`) at comparable ages, all else equal.

## Sources

- Gomes (2020), "Portfolio Choice Over the Life Cycle: A Survey" — local
  `1/1/input/G-Gomes.pdf` (confirms default = High-School income profile;
  normalisation by `exp(f(t)+p_t)`).
- Campbell, Cocco, Gomes & Maenhout (2001), "Investing Retirement Wealth: A
  Life-Cycle Model," Table 11.1 — education-group shock variances and
  income–stock correlations (PDF supplied by user).
- Cocco, Gomes & Maenhout (2005), baseline calibration — source of the default
  parameter values already in the form.
