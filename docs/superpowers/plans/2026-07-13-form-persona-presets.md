# Persona Presets & Selector Bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persona-preset selector bar to the top of the input form so a user can fill every parameter with one of seven life-scenario presets, then edit and run as usual.

**Architecture:** Presets are a static data array keyed by field name. Selecting a persona sets React state; a `key={activePreset}` on the `<form>` remounts it so each uncontrolled input re-applies its `defaultValue` from the active preset (Approach A). The existing submit path is untouched. Education-showcase personas additionally override the income-curve polynomial `aa`/`b1`/`b2`/`b3`.

**Tech Stack:** React 19 (Create React App / react-scripts 5), Jest + React Testing Library (`@testing-library/react` 16, `@testing-library/jest-dom` 6), plain CSS.

## Global Constraints

- All work is in `Real/frontend`. Run every command from that directory.
- Test command (one-shot, cross-platform): `npm test -- --watchAll=false --testPathPattern=Inputs`.
- Approach A only: keep inputs **uncontrolled** (`defaultValue` + `FormData`). Do NOT convert to controlled state.
- A preset changes ONLY the fields listed in its `values`. Every unlisted parameter falls back to its `FIELDS` default. This guarantees `td`, `corr_y`, all market params (`r`, `mu`, `sigr`), and all solver params (`ncash`, `na`, `nc`, `n`, `maxcash`, `mincash`, `nsim`) always stay at default.
- `corr_y` is never overridden by any preset (stays `0`).
- The income-curve polynomial (`aa`, `b1`, `b2`, `b3`) is overridden ONLY by the three education-showcase personas: Finance and Doctor use the College coefficients, Blue-collar uses the No-HS coefficients. All other personas leave them at the HS default.
- Selecting a preset only populates fields — it must not auto-run the simulation or disable editing.
- Exact preset values come from the approved spec `docs/superpowers/specs/2026-07-13-form-presets-design.md` §4 (table) and §4.3 (polynomials). Do not invent or round differently.
- Solver, market, and `td` inputs are never touched by presets.

---

## File Structure

- `Real/frontend/src/setupTests.js` — **create**. Loads `@testing-library/jest-dom` matchers for all tests (CRA auto-detects this file). One responsibility: test setup.
- `Real/frontend/src/pages/Inputs.test.js` — **create**. Unit tests for preset behavior against the `Inputs` component.
- `Real/frontend/src/pages/Inputs.js` — **modify**. Add `PRESETS` data, `activePreset` state, the selector-bar JSX, the `key` on the form, and preset-aware `defaultValue` resolution.
- `Real/frontend/src/pages/Inputs.css` — **modify**. Add styles for `.preset-bar` and `.preset-pill`.

---

### Task 1: Test harness

**Files:**
- Create: `Real/frontend/src/setupTests.js`
- Create: `Real/frontend/src/pages/Inputs.test.js`

**Interfaces:**
- Consumes: the existing default export `Inputs` from `Real/frontend/src/pages/Inputs.js`.
- Produces: a working Jest/RTL harness with jest-dom matchers; a smoke test other tasks extend.

This task bootstraps the test harness (none exists yet) and locks in the current
default-render behavior so later tasks have a baseline. The smoke test is expected
to PASS against the current component.

- [ ] **Step 1: Create the jest-dom setup file**

Create `Real/frontend/src/setupTests.js`:

```js
// Adds custom jest matchers (toHaveValue, toHaveAttribute, ...) for all tests.
import '@testing-library/jest-dom'
```

- [ ] **Step 2: Write the smoke test**

Create `Real/frontend/src/pages/Inputs.test.js`:

```jsx
import { render, screen } from '@testing-library/react'
import Inputs from './Inputs'

test('form renders with the current default parameter values', () => {
  render(<Inputs />)
  expect(screen.getByLabelText('Starting age (years)')).toHaveValue(20)
  expect(screen.getByLabelText('Retirement income factor (λ)')).toHaveValue(0.68212)
  expect(screen.getByLabelText('Income intercept')).toHaveValue(0.530339)
  expect(screen.getByLabelText('Cash-on-hand grid size')).toHaveValue(51)
})
```

- [ ] **Step 3: Run the smoke test**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: PASS (1 test). This confirms the harness and matchers work.

- [ ] **Step 4: Commit**

```bash
git add Real/frontend/src/setupTests.js Real/frontend/src/pages/Inputs.test.js
git commit -m "test: add RTL harness and Inputs default-render smoke test"
```

---

### Task 2: Presets data, selector bar, and wiring

**Files:**
- Modify: `Real/frontend/src/pages/Inputs.js`
- Modify: `Real/frontend/src/pages/Inputs.test.js`

**Interfaces:**
- Consumes: `Inputs` component; `FIELDS` list already defined at `Inputs.js:16-67`.
- Produces:
  - `PRESETS` array — each item `{ id: string, label: string, subtitle: string, values: object }` where `values` maps field `name` → number override.
  - `activePreset` state (string id, default `'default'`) and `setActivePreset`.
  - A `.preset-bar` of `<button type="button">` pills; the active one has class `active` and `aria-pressed="true"`.
  - Each input's `defaultValue` resolves to `active.values[name] ?? f.def`.
  - `<form key={activePreset} ...>`.

- [ ] **Step 1: Write the failing behavior tests**

Append to `Real/frontend/src/pages/Inputs.test.js`:

```jsx
import { fireEvent } from '@testing-library/react'

test('Default preset is active on load', () => {
  render(<Inputs />)
  expect(screen.getByRole('button', { name: /Default/ })).toHaveAttribute('aria-pressed', 'true')
})

test('selecting Doctor populates its parameters including the College income polynomial', () => {
  render(<Inputs />)
  fireEvent.click(screen.getByRole('button', { name: /Doctor/ }))
  expect(screen.getByLabelText('Starting age (years)')).toHaveValue(30)
  expect(screen.getByLabelText('Retirement age (years)')).toHaveValue(67)
  expect(screen.getByLabelText('Relative risk aversion (γ)')).toHaveValue(8)
  expect(screen.getByLabelText('Corr(perm income, returns)')).toHaveValue(0.1)
  expect(screen.getByLabelText('Retirement income factor (λ)')).toHaveValue(0.55)
  expect(screen.getByLabelText('Income intercept')).toHaveValue(-1.9317)
  expect(screen.getByLabelText('Income age coefficient')).toHaveValue(0.3194)
})

test('selecting Public-sector lifer leaves polynomial, market, and solver at defaults', () => {
  render(<Inputs />)
  fireEvent.click(screen.getByRole('button', { name: /Public-sector lifer/ }))
  expect(screen.getByLabelText('Retirement income factor (λ)')).toHaveValue(0.85)
  expect(screen.getByLabelText('Income intercept')).toHaveValue(0.530339) // HS default
  expect(screen.getByLabelText('Corr(trans income, returns)')).toHaveValue(0) // corr_y fixed
  expect(screen.getByLabelText('Gross risk-free rate')).toHaveValue(1.015) // market fixed
  expect(screen.getByLabelText('Cash-on-hand grid size')).toHaveValue(51) // solver fixed
})

test('switching from Doctor to Public-sector resets the income polynomial', () => {
  render(<Inputs />)
  fireEvent.click(screen.getByRole('button', { name: /Doctor/ }))
  expect(screen.getByLabelText('Income intercept')).toHaveValue(-1.9317)
  fireEvent.click(screen.getByRole('button', { name: /Public-sector lifer/ }))
  expect(screen.getByLabelText('Income intercept')).toHaveValue(0.530339)
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: the 4 new tests FAIL (no preset buttons found — "Unable to find role button with name /Default/"). The Task 1 smoke test still passes.

- [ ] **Step 3: Add the PRESETS data**

In `Real/frontend/src/pages/Inputs.js`, insert this block immediately after the
`LABELS` object (after `Inputs.js:84`, before `function Inputs()`):

```jsx
// Persona presets. Each `values` entry overrides a FIELDS default by name;
// any field not listed keeps its default. Only the three education-showcase
// personas (finance, bluecollar, doctor) override the income polynomial
// aa/b1/b2/b3. Values come from the design spec §4 and §4.3.
const PRESETS = [
  { id: 'default', label: 'Default',
    subtitle: 'Generally-applicable baseline settings',
    values: {} },
  { id: 'public', label: 'Public-sector lifer',
    subtitle: 'Stable, market-independent income; generous pension',
    values: { tb: 22, tr: 66, rho: 12, delta: 0.98, psi: 0.5, smay: 0.15, smav: 0.09, corr_v: 0, ret_fac: 0.85 } },
  { id: 'finance', label: 'Finance professional',
    subtitle: 'High pay that rides the stock market',
    values: { tb: 24, tr: 62, rho: 6, delta: 0.95, psi: 0.6, smay: 0.242, smav: 0.130, corr_v: 0.52, ret_fac: 0.45,
              aa: -1.9317, b1: 0.3194, b2: -0.00577, b3: 3.3e-5 } },
  { id: 'entrepreneur', label: 'Entrepreneur',
    subtitle: 'Volatile self-employment income; no pension',
    values: { tb: 26, tr: 68, rho: 6, delta: 0.94, psi: 0.7, smay: 0.30, smav: 0.18, corr_v: 0.30, ret_fac: 0.35 } },
  { id: 'bluecollar', label: 'Blue-collar (trades)',
    subtitle: 'Early start, cyclical manual work',
    values: { tb: 20, tr: 63, rho: 10, delta: 0.96, psi: 0.4, smay: 0.325, smav: 0.102, corr_v: 0.328, ret_fac: 0.60,
              aa: 0.4914, b1: 0.1684, b2: -0.00353, b3: 2.3e-5 } },
  { id: 'doctor', label: 'Doctor',
    subtitle: 'Late start, high and recession-proof income',
    values: { tb: 30, tr: 67, rho: 8, delta: 0.98, psi: 0.5, smay: 0.242, smav: 0.130, corr_v: 0.10, ret_fac: 0.55,
              aa: -1.9317, b1: 0.3194, b2: -0.00577, b3: 3.3e-5 } },
  { id: 'gig', label: 'Gig / precarious',
    subtitle: 'Insecure, spiky income; minimal safety net',
    values: { tb: 20, tr: 68, rho: 13, delta: 0.95, psi: 0.4, smay: 0.35, smav: 0.11, corr_v: 0.20, ret_fac: 0.30 } },
]
```

- [ ] **Step 4: Add state and value resolution**

In `Real/frontend/src/pages/Inputs.js`, add the state and helper. Change the state
block (currently `Inputs.js:87-92`) so it also declares `activePreset`. Add these
two lines immediately after the existing `const [progress, setProgress] = useState(0)`
line:

```jsx
  const [activePreset, setActivePreset] = useState('default')
  const active = PRESETS.find((p) => p.id === activePreset) || PRESETS[0]
```

Then, inside the `GROUPS.map` callback, change `renderInput` (currently
`Inputs.js:181-189`) so the input's `defaultValue` resolves from the active preset.
Replace:

```jsx
          const renderInput = (f) => (
            <input
              id={f.name}
              type="number"
              step="any"
              name={f.name}
              defaultValue={f.def}
            />
          )
```

with:

```jsx
          const renderInput = (f) => (
            <input
              id={f.name}
              type="number"
              step="any"
              name={f.name}
              defaultValue={active.values[f.name] ?? f.def}
            />
          )
```

- [ ] **Step 5: Add the selector bar and key the form**

In `Real/frontend/src/pages/Inputs.js`, insert the selector bar between the
`inputs-header` div and the `<form>` (after `Inputs.js:162`, before the `<form>`):

```jsx
      <div className="preset-bar" role="group" aria-label="Persona presets">
        {PRESETS.map((p) => (
          <button
            type="button"
            key={p.id}
            className={`preset-pill${p.id === activePreset ? ' active' : ''}`}
            aria-pressed={p.id === activePreset}
            onClick={() => setActivePreset(p.id)}
          >
            <span className="preset-label">{p.label}</span>
            <span className="preset-subtitle">{p.subtitle}</span>
          </button>
        ))}
      </div>
```

Then add `key={activePreset}` to the form tag. Change (`Inputs.js:164`):

```jsx
      <form method="post" onSubmit={handleSubmit}>
```

to:

```jsx
      <form key={activePreset} method="post" onSubmit={handleSubmit}>
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: PASS (all 5 tests — smoke test plus the 4 preset tests).

- [ ] **Step 7: Commit**

```bash
git add Real/frontend/src/pages/Inputs.js Real/frontend/src/pages/Inputs.test.js
git commit -m "feat: add persona preset selector to the input form"
```

---

### Task 3: Style the selector bar

**Files:**
- Modify: `Real/frontend/src/pages/Inputs.css`

**Interfaces:**
- Consumes: class names `preset-bar`, `preset-pill`, `preset-pill.active`,
  `preset-label`, `preset-subtitle` emitted by Task 2. Existing CSS variables
  (`--imperial-blue`, `--imperial-light-blue`, `--border-grey`, `--text`,
  `--radius-sm`) defined at `Inputs.css:2-12`.
- Produces: visual styling only. No interface consumed by later tasks.

This is a visual-only task; verification is a production build plus a manual look.

- [ ] **Step 1: Add the selector-bar styles**

Append to `Real/frontend/src/pages/Inputs.css`:

```css
/* Persona preset selector bar */
.preset-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin: 0 0 1.5rem;
}
.preset-pill {
  flex: 1 1 auto;
  min-width: 150px;
  text-align: left;
  padding: 0.55rem 0.8rem;
  background: #fff;
  color: var(--text);
  border: 1px solid var(--border-grey);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
}
.preset-pill:hover {
  border-color: var(--imperial-light-blue);
}
.preset-pill.active {
  background: var(--imperial-blue);
  border-color: var(--imperial-blue);
  color: #fff;
}
.preset-label {
  display: block;
  font-weight: 600;
  font-size: 0.9rem;
}
.preset-subtitle {
  display: block;
  font-size: 0.72rem;
  opacity: 0.8;
  margin-top: 0.15rem;
}
```

- [ ] **Step 2: Verify the build compiles**

Run: `npm run build`
Expected: "Compiled successfully" (warnings about bundle size are fine; there must
be no errors).

- [ ] **Step 3: Manual visual check**

Run: `npm start`, open the app. Confirm: a row of persona pills sits above the "Life
horizon" box; "Default" is highlighted in Imperial blue on load; clicking a pill
highlights it and fills the form; each pill shows its subtitle. Stop the dev server
when done.

- [ ] **Step 4: Commit**

```bash
git add Real/frontend/src/pages/Inputs.css
git commit -m "style: style the persona preset selector bar"
```

---

## Final Verification (manual, no commit)

Confirms the spec's end-to-end sanity checks (§10). Requires the backend running.

- [ ] Start the backend, then `npm start` the frontend.
- [ ] Select **Doctor**, click Submit, let it run. Note the average stock-share chart.
- [ ] Select **Finance professional**, Submit. Its optimal stock share should be
      **lower** than the Doctor's at comparable ages — Doctor and Finance share the
      same College income profile and risk, so the gap isolates the `corr_v` channel
      (0.52 vs 0.10).
- [ ] Select **Blue-collar (trades)** and **Doctor** in turn; their income and
      consumption paths should differ visibly, reflecting the steeper College income
      polynomial vs the flatter No-HS one.
- [ ] Edit any field, switch personas, confirm the form resets to the new persona's
      values (no leftover edits).

---

## Notes for the implementer

- The results/loading/charts blocks live **outside** and after the `<form>`; keying
  the form does not remount them, so in-progress results survive a persona switch.
- Row labelling in the results table already reads `tb` at submit time
  (`setStartAge(params.tb)`), so a persona's `tb` (e.g. Doctor 30) flows through on
  the next run with no extra work.
- `?? f.def` (nullish coalescing) is deliberate — a preset value of `0` (a legitimate
  override) must not fall through to the default.
- No backend change. Presets are purely front-end.
