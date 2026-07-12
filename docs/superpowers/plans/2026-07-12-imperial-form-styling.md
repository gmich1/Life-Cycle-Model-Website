# Imperial-Themed Grouped Input Form — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle `frontend/src/pages/Inputs.js` into six grouped, rounded "boxes" with a Light Imperial College London theme, including a rounded results table.

**Architecture:** Add a new `Inputs.css` holding all theme variables and layout. Restructure `Inputs.js` to carry `group` + `desc` metadata on each field and render one `<fieldset>` per group. Lighten `App.css`'s `.App-header` so the page reads as a light Imperial page. No logic changes to `handleSubmit`.

**Tech Stack:** React (create-react-app), plain CSS (CSS custom properties, CSS grid). No new dependencies.

## Global Constraints

- Palette (verbatim): `--imperial-blue: #003E74`, `--imperial-blue-dark: #002A52`, `--imperial-light-blue: #0091D4`, `--cool-grey: #EBEEEE`, `--border-grey: #d5dade`, `--text: #232333`, `--muted: #5b6470`.
- Corner rounding: `--radius: 10px` (boxes, header bar, table frame), `--radius-sm: 6px` (inputs, buttons). Every visible edge, including the results table, is rounded.
- Descriptions are **always visible** under each input (no tooltips/collapse).
- Fold the `DESCRIPTIONS` array into `FIELDS` as a `desc` key; delete `DESCRIPTIONS`.
- No new dependencies; no changes to `index.css`; no logic changes to `handleSubmit`.
- Verification is `npm run build` (must compile with no errors) + the stated visual check. Run npm commands from `frontend/`.

---

### Task 1: Create the Imperial theme stylesheet

**Files:**
- Create: `frontend/src/pages/Inputs.css`

**Interfaces:**
- Produces (class names consumed by Task 2): `inputs-page`, `inputs-header`, `field-group`, `field-grid`, `field`, `field-desc`, `form-actions`, `btn`, `btn-primary`, `btn-secondary`, `error-msg`, `results`, `table-wrap`, `results-table`.

- [ ] **Step 1: Write the full stylesheet**

Create `frontend/src/pages/Inputs.css` with exactly:

```css
/* Imperial College London themed input form */
:root {
  --imperial-blue: #003E74;
  --imperial-blue-dark: #002A52;
  --imperial-light-blue: #0091D4;
  --cool-grey: #EBEEEE;
  --border-grey: #d5dade;
  --text: #232333;
  --muted: #5b6470;
  --radius: 10px;
  --radius-sm: 6px;
}

.inputs-page {
  color: var(--text);
  text-align: left;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  padding: 0 1rem 3rem;
  font-size: 1rem;
}

.inputs-header {
  background: var(--imperial-blue);
  color: #fff;
  border-radius: var(--radius);
  padding: 1.1rem 1.4rem;
  margin: 1.5rem 0;
}
.inputs-header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}
.inputs-header p {
  margin: 0.35rem 0 0;
  font-size: 0.9rem;
  opacity: 0.85;
}

.field-group {
  background: #fff;
  border: 1px solid var(--border-grey);
  border-radius: var(--radius);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  padding: 0 1.25rem 1.25rem;
  margin: 0 0 1.5rem;
}
.field-group > legend {
  color: var(--imperial-blue);
  font-size: 1.1rem;
  font-weight: 600;
  padding: 0 0.5rem;
  margin-left: -0.5rem;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem 1.5rem;
  align-items: start;
  margin-top: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
}
.field label {
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.35rem;
}
.field input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.5rem 0.6rem;
  font-size: 0.95rem;
  color: var(--text);
  background: var(--cool-grey);
  border: 1px solid var(--border-grey);
  border-radius: var(--radius-sm);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.field input:focus {
  outline: none;
  border-color: var(--imperial-light-blue);
  box-shadow: 0 0 0 3px rgba(0, 145, 212, 0.25);
  background: #fff;
}
.field-desc {
  font-size: 0.78rem;
  color: var(--muted);
  margin-top: 0.3rem;
  line-height: 1.4;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin: 0.5rem 0 2rem;
}

.btn {
  font-size: 0.95rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid var(--imperial-blue);
  transition: background 0.15s, color 0.15s;
}
.btn-primary {
  background: var(--imperial-blue);
  color: #fff;
}
.btn-primary:hover {
  background: var(--imperial-blue-dark);
  border-color: var(--imperial-blue-dark);
}
.btn-secondary {
  background: #fff;
  color: var(--imperial-blue);
}
.btn-secondary:hover {
  background: var(--cool-grey);
}

.error-msg {
  color: #c0392b;
  background: #fdecea;
  border: 1px solid #f5c6c2;
  border-radius: var(--radius-sm);
  padding: 0.6rem 0.9rem;
  font-size: 0.9rem;
}

.results h3 {
  color: var(--imperial-blue);
}
.table-wrap {
  max-height: 500px;
  overflow: auto;
  border: 1px solid var(--border-grey);
  border-radius: var(--radius);
}
.results-table {
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.8rem;
  width: 100%;
}
.results-table th,
.results-table td {
  padding: 4px 10px;
  text-align: right;
  border-bottom: 1px solid var(--border-grey);
  border-right: 1px solid var(--border-grey);
  white-space: nowrap;
}
.results-table th:last-child,
.results-table td:last-child {
  border-right: none;
}
.results-table th {
  position: sticky;
  top: 0;
  background: var(--imperial-blue);
  color: #fff;
  font-weight: 600;
}
.results-table tbody tr:nth-child(even) {
  background: var(--cool-grey);
}
.results-table tbody tr:last-child td {
  border-bottom: none;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Inputs.css
git commit -m "feat: add Imperial-themed stylesheet for input form"
```

Note: this file is not imported yet, so there is nothing visual to verify in isolation — it is exercised in Task 2. It contains no JS, so it cannot break the build on its own.

---

### Task 2: Restructure Inputs.js into grouped boxes

**Files:**
- Modify: `frontend/src/pages/Inputs.js` (whole file replaced)

**Interfaces:**
- Consumes (from Task 1): all class names listed in Task 1's Produces block.
- Produces: no exported interface changes — still `export default Inputs`.

- [ ] **Step 1: Replace the entire file**

Replace the full contents of `frontend/src/pages/Inputs.js` with exactly:

```jsx
import React, { useState } from 'react'
import './Inputs.css'

// Ordered groups rendered as boxes. Each field below names its group id.
const GROUPS = [
  { id: 'horizon',     title: 'Life horizon' },
  { id: 'prefs',       title: 'Preferences' },
  { id: 'market',      title: 'Market & returns' },
  { id: 'incrisk',     title: 'Income risk' },
  { id: 'incprofile',  title: 'Income profile & retirement' },
  { id: 'solver',      title: 'Solver settings' },
]

// All model parameters: default, label, description and group.
// Editing this one list is enough to change the form.
const FIELDS = [
  { name: 'tb',      group: 'horizon',    label: 'Starting age (years)',                def: 20,
    desc: 'The age when the person started working.' },
  { name: 'tr',      group: 'horizon',    label: 'Retirement age (years)',              def: 66,
    desc: 'The age when the person retired. This data is collected since assets are safer to invest in while having an income.' },
  { name: 'td',      group: 'horizon',    label: 'Maximum age (years)',                 def: 100,
    desc: 'The age when the person is expected to pass away. This data is collected since all wealth will be planned to be spent by this year' },
  { name: 'rho',     group: 'prefs',      label: 'Relative risk aversion (γ)',          def: 10.0,
    desc: 'How much the person dislikes gambles over wealth; an economist estimates it from experimental choices or asset-pricing data, or a consumer just uses the standard textbook value of ~5–10. The lower this value is, the less they money will be put into stocks to \'play it safe.\'' },
  { name: 'delta',   group: 'prefs',      label: 'Discount factor (β)',                 def: 0.97,
    desc: 'How much the person values next year\'s utility relative to this year\'s (0.97 ≈ 3% annual impatience); inferred from savings behavior or simply set near 0.96–0.98. The higher this is, the more the person cares about the future, so they spend less today and save more for later.' },
  { name: 'psi',     group: 'prefs',      label: 'EIS (ψ)',                             def: 0.5,
    desc: 'Measures willingness to shift consumption across time in response to interest rates; estimated from how consumption growth responds to expected returns, or use the common calibration of ~0.5. The lower this is, the more the person wants their spending to stay flat and predictable year to year, rather than splurging now or later.' },
  { name: 'r',       group: 'market',     label: 'Gross risk-free rate',                def: 1.015,
    desc: 'The safe return; read it off inflation-protected government bond (TIPS) yields, or use the historical ~1–2% real average. The higher it is, the more the person can earn just by keeping their money somewhere safe — so there\'s less reason to gamble on stocks.' },
  { name: 'mu',      group: 'market',     label: 'Equity premium (μ)',                  def: 0.04,
    desc: 'The extra average return stocks earn over the safe asset; estimated from long-run stock-vs-bond return differences, or use the historical ~4–6%. The bigger the bonus stocks pay over safe assets, the more the person should load up on stocks.' },
  { name: 'sigr',    group: 'market',     label: 'Standard dev stock returns (σ_R)',    def: 0.2,
    desc: 'The volatility (riskiness) of equity returns; computed as the standard deviation of annual stock-index returns (historically ~18–20%). The more wildly stocks swing, the riskier they feel — so the person holds fewer of them.' },
  { name: 'smay',    group: 'incrisk',    label: 'Standard dev transitory income (σ_u)', def: 0.1,
    desc: 'Size of temporary, one-off income surprises (bonuses, short gaps); estimated from year-to-year fluctuations in panel earnings data (PSID), or use ~0.1. Bigger short-term surprises (a lost bonus, a brief gap) make people save a little extra as a cushion and take slightly less risk.' },
  { name: 'smav',    group: 'incrisk',    label: 'Standard dev permanent income (σ_z)', def: 0.1,
    desc: 'Size of lasting shocks that permanently reset the income level (promotion, disability); estimated from the growth of earnings dispersion with age, or use ~0.1. Because these changes stick for life (a promotion, an injury), they make future paychecks feel less reliable — so the person leans a bit more toward safe assets.' },
  { name: 'corr_v',  group: 'incrisk',    label: 'Corr(perm income, returns)',          def: 0.0,
    desc: 'Whether lasting income changes move with the stock market; estimated by correlating earnings shocks with market returns, or assume 0 (the baseline). At zero (the default), the person\'s income and the market are unrelated, so this does nothing. If they moved together, the person\'s job would already feel "stock-like," so they\'d buy fewer actual stocks to avoid doubling up on the same risk.' },
  { name: 'corr_y',  group: 'incrisk',    label: 'Corr(trans income, returns)',         def: 0.0,
    desc: 'Whether short-term income blips move with the market; same estimation as above, or assume 0. At zero (the default), the person\'s income and the market are unrelated, so this does nothing. If they moved together, the person\'s job would already feel "stock-like," so they\'d buy fewer actual stocks to avoid doubling up on the same risk.' },
  { name: 'ret_fac', group: 'incprofile', label: 'Retirement income factor (λ)',        def: 0.68212,
    desc: 'Fraction of pre-retirement income received as pension/Social Security (~68%); look at the subject\'s Social Security statement or national replacement-rate tables. The bigger their guaranteed pension, the safer they feel in retirement — so they can spend more freely and keep more in stocks even when old.' },
  { name: 'aa',      group: 'incprofile', label: 'Income intercept',                    def: 0.530339,
    desc: '' },
  { name: 'b1',      group: 'incprofile', label: 'Income age coefficient',              def: 0.16818,
    desc: '' },
  { name: 'b2',      group: 'incprofile', label: 'Income age² coefficient',             def: -0.00323371,
    desc: '' },
  { name: 'b3',      group: 'incprofile', label: 'Income age³ coefficient',             def: 1.9704e-5,
    desc: 'Coefficients of the hump-shaped age–earnings curve f(t); obtained by regressing log earnings on age, age², age³ in census/panel data (or just use these fitted values).' },
  { name: 'ncash',   group: 'solver',     label: 'Cash-on-hand grid size',              def: 51,
    desc: 'How many different wealth levels (from poor to rich) the model checks. More levels give a smoother, more precise answer but run slower.' },
  { name: 'na',      group: 'solver',     label: 'Allocation grid size',                def: 51,
    desc: 'How many different stock-versus-safe mixes the model tries, from 0% up to 100% in stocks. More options let it pin down the ideal stock share more exactly, at the cost of speed.' },
  { name: 'nc',      group: 'solver',     label: 'Consumption search grid',             def: 21,
    desc: 'How many different "how much to spend this year" amounts the model tests at each step. More amounts give a finer read on the best spending choice but run slower.' },
  { name: 'n',       group: 'solver',     label: 'Quadrature nodes',                    def: 5,
    desc: 'How many sample outcomes the model uses to average over an uncertain future, like good versus bad stock years. More samples make the estimate of the future more accurate but slower; 5 is a standard, efficient choice.' },
  { name: 'maxcash', group: 'solver',     label: 'Max cash-on-hand',                    def: 200.0,
    desc: 'The richest wealth level the model bothers to consider (200× a year\'s income). It just needs to be high enough that almost nobody realistically goes above it.' },
  { name: 'mincash', group: 'solver',     label: 'Min cash-on-hand',                    def: 0.25,
    desc: 'The poorest wealth level considered (a quarter of a year\'s income). It sits just above zero to keep the math well-behaved.' },
  { name: 'nsim',    group: 'solver',     label: 'Simulation paths',                    def: 10000,
    desc: 'How many pretend "life stories" the model runs to see how people typically end up. More lives give smoother, more reliable averages but take longer; 10,000 is enough for stable results.' },
]

// Friendly column headers for the sim series. Any key not listed here
// falls back to its raw name, so the table still works if you add series.
const LABELS = {
  meanC: 'Consumption',
  meanW: 'Wealth',
  meanY: 'Income',
  meanGPY: 'Perm. income growth',
  meanS: 'Stocks',
  meanB: 'Bonds',
  meanalpha: 'Stock share',
  meanCs: 'Consumption (scaled)',
  meanWs: 'Wealth (scaled)',
  meanYs: 'Income (scaled)',
  cGPY: 'Cumulative growth',
  meanWY: 'Wealth / income',
}

function Inputs() {
  const [result, setResult] = useState(null)
  const [startAge, setStartAge] = useState(20)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault() // Prevent automatic page refresh by browser (otherwise would refresh on submit of form)
    setError(null)
    setResult(null)

    // Read every named input straight from the form, converting to numbers.
    const formData = new FormData(e.target) // e.target is the form element
    const params = {}
    for (const [name, value] of formData.entries()) {
      params[name] = Number(value)
    }

    try {
      const response = await fetch('http://localhost:8000/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Request failed')
      }

      console.log('Server responded:', data)
      setStartAge(params.tb || 20)   // label table rows by real age
      setResult(data.sim)
    } catch (err) {
      console.error('Submit failed:', err)
      setError(err.message)
    }
  }

  return (
    <div className="inputs-page">
      <div className="inputs-header">
        <h1>Life-Cycle Portfolio Model</h1>
        <p>Set the model parameters below and run the simulation.</p>
      </div>

      <form method="post" onSubmit={handleSubmit}>
        {GROUPS.map((g) => (
          <fieldset className="field-group" key={g.id}>
            <legend>{g.title}</legend>
            <div className="field-grid">
              {FIELDS.filter((f) => f.group === g.id).map((f) => (
                <div className="field" key={f.name}>
                  <label htmlFor={f.name}>{f.label}</label>
                  <input
                    id={f.name}
                    type="number"
                    step="any"
                    name={f.name}
                    defaultValue={f.def}
                  />
                  {f.desc && <div className="field-desc">{f.desc}</div>}
                </div>
              ))}
            </div>
          </fieldset>
        ))}

        <div className="form-actions">
          <button type="submit" className="btn btn-primary">Submit</button>
          <a href="/algorithm_simple.html" target="_blank" rel="noopener noreferrer">
            <button type="button" className="btn btn-secondary">
              Simple Algorithm Details
            </button>
          </a>
          <a href="/algorithm.html" target="_blank" rel="noopener noreferrer">
            <button type="button" className="btn btn-secondary">
              Technical Algorithm Details
            </button>
          </a>
        </div>
      </form>

      {error && <p className="error-msg">Error: {error}</p>}

      {result && (
        <div className="results">
          <h3>Year-by-year summary</h3>
          <div className="table-wrap">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Age</th>
                  {Object.keys(result).map((key) => (
                    <th key={key}>{LABELS[key] || key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result[Object.keys(result)[0]].map((_, i) => (
                  <tr key={i}>
                    <td>{startAge + i}</td>
                    {Object.keys(result).map((key) => (
                      <td key={key}>{result[key][i].toFixed(4)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default Inputs
```

- [ ] **Step 2: Build to verify it compiles**

Run (from `frontend/`): `npm run build`
Expected: `Compiled successfully.` (warnings about source maps are fine; there must be **no errors**, and no "DESCRIPTIONS is not defined" or unused-var error — `DESCRIPTIONS` and `thStyle`/`tdStyle` are fully removed).

- [ ] **Step 3: Visual check**

Run (from `frontend/`): `npm start`, open `http://localhost:3000`.
Expected: light page; a blue rounded header bar reading "Life-Cycle Portfolio Model"; six rounded white boxes with blue titles (Life horizon, Preferences, Market & returns, Income risk, Income profile & retirement, Solver settings); inputs in a 2-column grid that collapses to 1 column when the window is narrowed; blue focus ring when an input is focused; rounded blue Submit button and two outlined secondary buttons on one row. Confirm all 25 fields appear (3+3+3+4+5+7) and the `aa`/`b1`/`b2` fields show no empty description line.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Inputs.js
git commit -m "feat: group input form into Imperial-themed boxes"
```

---

### Task 3: Lighten the page background in App.css

**Files:**
- Modify: `frontend/src/App.css:16-25` (the `.App-header` rule)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing — purely presentational.

- [ ] **Step 1: Replace the `.App-header` rule**

In `frontend/src/App.css`, replace the existing `.App-header` block:

```css
.App-header {
  background-color: #282c34;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
  color: white;
}
```

with:

```css
.App-header {
  background-color: #f7f9fa;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  font-size: 1rem;
  color: #232333;
}
```

(Leave every other rule in `App.css` unchanged.)

- [ ] **Step 2: Build to verify it compiles**

Run (from `frontend/`): `npm run build`
Expected: `Compiled successfully.` with no errors.

- [ ] **Step 3: Visual check**

Run (from `frontend/`): `npm start`, open `http://localhost:3000`.
Expected: page background is now light (`#f7f9fa`), content starts at the top (not vertically centered), body font is normal-sized (not the oversized hero text), and the boxes/text from Task 2 read cleanly against the light background.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.css
git commit -m "style: lighten App-header for Imperial light theme"
```

---

## Self-Review

**1. Spec coverage:**
- Light Imperial theme → Task 1 (variables/colors) + Task 3 (light page). ✓
- Header bar with title → Task 2 render + Task 1 `.inputs-header`. ✓
- Six grouped `<fieldset>` boxes, 2-col responsive grid, top-aligned → Task 1 `.field-group`/`.field-grid` + Task 2 `GROUPS`/render. ✓
- Fold `desc` into `FIELDS`, delete `DESCRIPTIONS` → Task 2. ✓
- Always-visible descriptions → Task 2 renders `.field-desc` unconditionally (guarded only for empty strings). ✓
- Rounded corners everywhere incl. table → Task 1 `--radius`/`--radius-sm`, `.table-wrap` (radius + overflow clip), buttons, inputs, boxes. ✓
- Buttons (primary + two secondary on one row) → Task 1 `.btn*` + Task 2 `.form-actions`. ✓
- Results table → classes → Task 1 `.results-table` + Task 2 (inline `thStyle`/`tdStyle` removed). ✓
- Error message styled → Task 1 `.error-msg` + Task 2. ✓
- Files: new `Inputs.css` (T1), edit `Inputs.js` (T2), edit `App.css` (T3). ✓

**2. Placeholder scan:** No TBD/TODO; all code shown in full. ✓

**3. Type/name consistency:** Class names produced in Task 1 exactly match those consumed in Task 2 (`inputs-page`, `inputs-header`, `field-group`, `field-grid`, `field`, `field-desc`, `form-actions`, `btn`/`btn-primary`/`btn-secondary`, `error-msg`, `results`, `table-wrap`, `results-table`). Group ids in `GROUPS` (`horizon`, `prefs`, `market`, `incrisk`, `incprofile`, `solver`) exactly match every `group:` value in `FIELDS`. ✓
