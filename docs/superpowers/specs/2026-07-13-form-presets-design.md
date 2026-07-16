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
  parameters (`r`, `mu`, `sigr`), maximum age (`td=100`), and all solver settings
  stay at their defaults so comparisons are apples-to-apples.
- Personas are full archetypes: they bundle **age/horizon**, **income risk**,
  **income–market correlation**, **retirement replacement**, **temperament**
  (risk aversion / patience / EIS), and — for the three education-showcase personas
  — the **income-curve polynomial** (No-HS / College vs the HS default).
- Selecting a preset **only populates the fields**. It does not auto-run and does
  not lock anything — every input remains editable afterward.
- Solver settings are never changed by a preset.
- Where real calibrations exist, values are grounded in the literature; otherwise
  they are reasoned choices on the same scale (documented in §4).

## 3. Which parameters a preset varies

Varied per persona: `tb`, `tr`, `rho`, `delta`, `psi`, `smay`, `smav`, `corr_v`,
`ret_fac`, and — for the three education-showcase personas only — the income-curve
polynomial `aa`, `b1`, `b2`, `b3` (see §4.3).

Held fixed at default for every persona:

- `td = 100`
- Market: `r = 1.015`, `mu = 0.04`, `sigr = 0.2`
- `corr_y = 0` for all personas — the model correlates only the **permanent
  aggregate** labour-income shock with stock returns; transitory shocks are
  idiosyncratic (CGM 2005, §2.1). Setting `corr_y` non-zero is not economically
  meaningful here.
- Solver: `ncash`, `na`, `nc`, `n`, `maxcash`, `mincash`, `nsim`.
- Income-curve polynomial `aa`/`b1`/`b2`/`b3` — held at the High-School default for
  Default, Public-sector lifer, Entrepreneur, and Gig; overridden with the real
  No-HS / College coefficients for Blue-collar / (Finance, Doctor) — see §4.3.

**On the income polynomial (correcting an earlier assumption).** Because the model
normalises every quantity by the deterministic income component `exp(f(t)+p_t)`
(confirmed in Gomes 2020), a pure income-*level* shift — a change in the constant
`aa` alone — washes out of the normalised policy. But the polynomial *shape*
(`b1`/`b2`/`b3`, the growth rate and hump of the income path) does **not** wash
out: it flows through the period-to-period income-growth factor and changes the
human-capital-to-wealth ratio over the life cycle, and hence the optimal stock
share. CGM (2005) Table 2 shows the College profile is materially steeper than the
High-School one (age coefficient 0.3194 vs 0.1682), not merely a level shift.
Wiring in the real education polynomials is therefore a genuine, output-relevant
enhancement — not cosmetic.

## 4. The personas

Seven presets: **Default** plus six archetypes. Values not listed below equal the
defaults in §3.

| Persona | Income poly | tb | tr | rho | delta | psi | smay | smav | corr_v | ret_fac |
|---|---|---|---|---|---|---|---|---|---|---|
| Default (HS baseline) | HS | 20 | 66 | 10 | 0.97 | 0.5 | 0.10 | 0.10 | 0.00 | 0.68212 |
| Public-sector lifer | HS | 22 | 66 | 12 | 0.98 | 0.5 | 0.15 | 0.09 | 0.00 | 0.85 |
| Finance professional | College | 24 | 62 | 6 | 0.95 | 0.6 | 0.242 | 0.130 | 0.52 | 0.45 |
| Entrepreneur | HS | 26 | 68 | 6 | 0.94 | 0.7 | 0.30 | 0.18 | 0.30 | 0.35 |
| Blue-collar (trades) | No-HS | 20 | 63 | 10 | 0.96 | 0.4 | 0.325 | 0.102 | 0.328 | 0.60 |
| Doctor | College | 30 | 67 | 8 | 0.98 | 0.5 | 0.242 | 0.130 | 0.10 | 0.55 |
| Gig / precarious | HS | 20 | 68 | 13 | 0.95 | 0.4 | 0.35 | 0.11 | 0.20 | 0.30 |

"Income poly" names which education polynomial package (§4.3) supplies `aa`/`b1`/
`b2`/`b3`. HS = the current default coefficients (no change).

### 4.1 One-line subtitles (shown on the pills)

- **Default** — Generally-applicable baseline settings.
- **Public-sector lifer** — Stable, market-independent income; generous pension.
- **Finance professional** — High pay that rides the stock market.
- **Entrepreneur** — Volatile self-employment income; no pension.
- **Blue-collar (trades)** — Early start, cyclical manual work.
- **Doctor** — Late start, high and recession-proof income.
- **Gig / precarious** — Insecure, spiky income; minimal safety net.

### 4.2 Grounding of the shock variances and correlation

Shock variances are the real CGM (2005) Table 3 / CCGM (2001) Table 11.1
education-group estimates (the two papers agree on these):

| Education group | σ²ε (transitory) → `smay` | σ²u (permanent) → `smav` |
|---|---|---|
| No high school | .1056 → 0.325 | .0105 → 0.102 |
| High school (baseline) | .0738 → 0.272 | .0106 → 0.103 |
| College | .0584 → 0.242 | .0169 → 0.130 |

- **Blue-collar** uses the No-High-School variances (`smay=0.325`, `smav=0.102`).
- **Finance professional** and **Doctor** both use the College variances
  (`smay=0.242`, `smav=0.130`).
- **Public-sector lifer**, **Entrepreneur**, **Gig** use reasoned values on the
  same scale, not direct table rows.
- **Default** intentionally keeps the rounded `smay=smav=0.10` baseline (Default
  reads as a smoothed textbook starting point). Decision on record: **leave Default
  scale unchanged.**

**Correlation `corr_v` is illustrative, not the CGM baseline — flagged explicitly.**
CGM (2005) estimate the *contemporaneous* income–stock correlation at essentially
**zero** for every education group (Table 3: −0.014 / +0.006 / −0.018; Table 4
benchmark sets `p = 0`). The larger `0.33 → 0.52` gradient comes from CCGM (2001)
using *lagged* stock returns, which the model deliberately omits (it would need an
extra state variable). We use non-zero `corr_v` values as a deliberate,
pedagogically-motivated illustration of the correlation channel — the mechanism
Bagliano-Fugazza-Nicodano study — anchored on the CCGM (2001) lagged gradient and
real-world occupation reasoning:

- Finance `corr_v = 0.52` — a trader's pay tracks the market (upper/college end).
- Doctor `corr_v = 0.10` — recession-resilient income (low end; CCGM Tables
  11.3/11.4 show wide within-college heterogeneity by industry).
- Blue-collar `corr_v = 0.328`, Entrepreneur `0.30`, Gig `0.20` — cyclical income.

This makes **finance-vs-doctor a clean teaching pair**: identical education,
income risk, and income profile, differing *only* in `corr_v`, so the change in
optimal stock share is attributable to that single lever. The spec records that
these correlations are illustrative overrides of the CGM zero-correlation
benchmark, chosen to demonstrate the mechanism.

### 4.3 Income-curve polynomials (CGM 2005, Table 2)

The deterministic log-income function is `f(t) = aa + b1·t + b2·t² + b3·t³` (age
`t`). CGM (2005) Table 2 reports third-order coefficients per education group; the
intercept used by the form is that group's Table 2 constant **plus** its Table 1
fixed-effects constant (this is exactly how the existing HS default is built:
`aa = -2.170042 + 2.700381 = 0.530339`). Resulting per-package field values:

| Field | No-HS (Blue-collar) | HS (default) | College (Finance, Doctor) |
|---|---|---|---|
| `aa` | 0.4914 | 0.530339 | -1.9317 |
| `b1` | 0.1684 | 0.16818 | 0.3194 |
| `b2` | -0.00353 | -0.00323371 | -0.00577 |
| `b3` | 2.3e-5 | 1.9704e-5 | 3.3e-5 |

Derivation of the intercepts: No-HS `= -2.1361 + 2.6275`; College `= -4.3148 +
2.3831`. `b2` is Table 2's "Age²/10" coefficient ÷ 10; `b3` is its "Age³/100"
coefficient ÷ 100 — matching the form's existing convention. HS keeps the form's
full-precision values (Table 2 prints the rounded 0.1682 / −0.0323 / 0.0020).

Sanity check (evaluated `exp(f(t))`): all three profiles are positive and
hump-shaped over ages 20–65; College is the steepest and highest-peaking, No-HS
the flattest and lowest — the expected ordering. The College negative `aa` is only
a polynomial constant (it pairs with the steeper slope); it is **not** a negative
income and, on its own, would wash out under normalisation — the steeper *slope* is
what changes the output.

**Replacement rates.** CGM (2005) Table 2 also reports real education replacement
rates (No-HS `0.88983`, HS `0.68212`, College `0.938873`). The personas do **not**
adopt these; `ret_fac` is treated as an occupation/pension-scheme lever
(persona-craft) because pension arrangements track employer/job type more than
education, and the occupation narratives (e.g. the public-sector persona's generous
pension, the entrepreneur's absent one) depend on it. Decision on record:
**`ret_fac` is illustrative per-occupation; the real education replacement rates
are available if fuller education-package fidelity is later preferred.**

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
    // Education-showcase personas additionally override the income polynomial:
    { id: 'doctor',  label: 'Doctor', subtitle: '…', values: { tb:30, tr:67, rho:8, delta:0.98, psi:0.5, smay:0.242, smav:0.130, corr_v:0.10, ret_fac:0.55, aa:-1.9317, b1:0.3194, b2:-0.00577, b3:3.3e-5 } },
    // …
  ]
  ```
  A preset's `values` overrides the `FIELDS` defaults; any field not named falls
  back to its `FIELDS.def`. This keeps presets terse and guarantees every unlisted
  parameter (market, solver, `td`, `corr_y`, and — for non-education personas — the
  income curve) stays at default. The three education-showcase personas
  (Blue-collar, Finance, Doctor) additionally list `aa`/`b1`/`b2`/`b3` per §4.3.
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
grouped block. The three education-showcase personas override these values; because
the block's inputs are ordinary `defaultValue`-driven fields, the keyed remount
re-applies the persona's coefficients with no special handling. Non-education
personas leave them at the HS default. The shared description under the block is
unchanged.

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
- Adopting the real education replacement rates (§4.3) — `ret_fac` stays
  occupation-craft for now.
- Any change to market or solver parameters.

## 10. Testing / verification

- Manual: load form → Default active, values match current defaults. Click each
  persona → every listed field updates to the table in §4; market, solver, `td`,
  and `corr_y` remain at defaults. For Blue-collar/Finance/Doctor confirm the
  income-curve block (`aa`/`b1`/`b2`/`b3`) updates to the §4.3 values; for the
  other personas confirm it stays at the HS default. Edit a field, switch persona,
  confirm reset. Submit for two contrasting personas and confirm the results table
  differs.
- Sanity: Finance (`corr_v=0.52`) should show a lower optimal stock share than
  Doctor (`corr_v=0.10`) at comparable ages (same income profile and risk, so the
  gap isolates the correlation channel).
- Sanity: Doctor vs Blue-collar should differ visibly in the income/consumption
  paths, reflecting the steeper College income polynomial vs the flatter No-HS one.

## Sources

- Cocco, Gomes & Maenhout (2005), "Consumption and Portfolio Choice over the Life
  Cycle," *RFS* 18(2) — **primary calibration source** (PDF supplied by user).
  Table 1 (fixed-effects constants), Table 2 (age-polynomial coefficients and
  replacement rates per education group), Table 3 (shock variances; contemporaneous
  correlation ≈ 0), Table 4 (benchmark = High-School group, `p=0`).
- Gomes (2020), "Portfolio Choice Over the Life Cycle: A Survey" — local
  `1/1/input/G-Gomes.pdf` (confirms default = High-School income profile;
  normalisation by `exp(f(t)+p_t)`).
- Campbell, Cocco, Gomes & Maenhout (2001), "Investing Retirement Wealth: A
  Life-Cycle Model," Table 11.1 — the *lagged*-return income–stock correlation
  gradient (0.33 → 0.52) used illustratively for `corr_v` (§4.2).
- Bagliano, Fugazza & Nicodano (no. 266) — motivates the correlation channel as
  the driver of the age-profile of the optimal stock share.
