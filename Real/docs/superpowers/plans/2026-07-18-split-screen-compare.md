# Split-Screen Two-Instance Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a top-of-page toggle that switches between one and two independent simulation panels (blue and red) shown in the same tab, laid out in three bands (forms side by side, charts side by side, tables stacked full width).

**Architecture:** Extract the current `Inputs` body into a self-contained `SimulationPanel` (own state, own run, own results) with a `variant` prop; `Inputs` becomes a thin container that renders a title, the instance toggle, and one or two panels inside a `grid-template-areas` layout. The red panel re-declares the theme CSS variables; panels use `display: contents` so their `form`/`charts`/`table` sections are placed by the container grid. Frontend-only — no backend/model/API change.

**Tech Stack:** React 18 (Create React App / react-scripts), Jest + React Testing Library, plain CSS. Static detail pages are hand-written HTML with a small inline `<script>`.

## Global Constraints

- All work is in `Real/frontend`. Run every command from that directory.
- Test command (one-shot): `npm test -- --watchAll=false --testPathPattern=<Pattern>`.
- Frontend-only: no changes to `api/`, the Python model, or `/api/run`.
- Charts are backend PNGs and are **not** recolored — the red variant recolors UI chrome only.
- Red panel colors (exact): `--imperial-blue: #C0272D`, `--imperial-blue-dark: #8B1E22`, `--imperial-light-blue: #E8686D`.
- Toggle labels are exactly `1 form` and `2 forms`; default is one instance.
- The second (red) panel is **created on first switch to two, then never unmounted** — hidden with `display: none` in single mode so its state persists.
- Results **tables stack full width even on wide screens**; forms and charts sit side by side; narrow screens collapse to one column in the order blue form, red form, blue charts, red charts, blue table, red table.
- Per-instance detail pages: blue writes `localStorage` key `lifecycleCharts:blue` (and the legacy `lifecycleCharts`), red writes `lifecycleCharts:red`; detail links carry `?variant=blue` / `?variant=red`.
- Do not touch `currency.js`, `ResultsTable.js`, or their tests — `SimulationPanel` imports them unchanged.

---

## File Structure

- `src/pages/SimulationPanel.js` — **new**. One simulation: preset bar, form, currency inputs, submit-to-`/api/run`, progress, error, charts, results table. Owns all state. Props: `variant` (`'blue'`|`'red'`), `hidden` (bool).
- `src/pages/Inputs.js` — **becomes the container**: title, instance toggle, compare-grid holding one/two `SimulationPanel`s.
- `src/pages/Inputs.css` — add red-variant variable override, `--focus-ring`, panel sections + `display: contents`, the compare grid (`grid-template-areas`, wide + narrow), toggle styles, hidden-panel rule.
- `src/pages/Inputs.test.js` — keep the existing preset tests (they still pass via the container's single default panel); add tests for the red variant, toggle behavior, and per-variant detail links.
- `public/algorithm.html`, `public/algorithm_simple.html` — variant-aware `localStorage` key selection (~3 lines each).

---

### Task 1: Extract `SimulationPanel` (behavior-preserving)

**Files:**
- Create: `src/pages/SimulationPanel.js`
- Modify: `src/pages/Inputs.js`

**Interfaces:**
- Produces: `SimulationPanel` — `export default function SimulationPanel({ variant = 'blue' })`. Renders one full simulation, wrapped in `<div className={`sim-panel sim-panel--${variant}`}>`.
- Produces: `Inputs` — unchanged default export; now renders the page title and one `<SimulationPanel variant="blue" />`.

This task is a pure move: the app must look and behave exactly as it does now (one panel). No visual change.

- [ ] **Step 1: Confirm current tests pass (baseline)**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: PASS (the current `Inputs.test.js` suite). Record the count.

- [ ] **Step 2: Create `src/pages/SimulationPanel.js`**

Move the current `Inputs.js` content into a new `SimulationPanel.js` with these exact changes, leaving everything else verbatim:

1. Keep the imports as-is:
   ```js
   import React, { useState } from 'react'
   import './Inputs.css'
   import ResultsTable from './ResultsTable'
   import { CURRENCIES } from './currency'
   ```
2. Move the `GROUPS`, `FIELDS`, and `PRESETS` constants **verbatim** (unchanged).
3. Rename the component and add the prop. Change `function Inputs() {` to:
   ```js
   function SimulationPanel({ variant = 'blue' }) {
   ```
4. In the returned JSX, **replace the outer wrapper** `<div className="inputs-page">` with:
   ```jsx
   <div className={`sim-panel sim-panel--${variant}`}>
   ```
   and its matching closing `</div>` stays as-is.
5. **Delete the header block** (it moves to the container):
   ```jsx
   <div className="inputs-header">
     <h1>Life-Cycle Portfolio Model</h1>
     <p>Set the model parameters below and run the simulation.</p>
   </div>
   ```
6. Everything else inside (the `Data Presets` fieldset, the `<form>`, loading, error, the two `.results` blocks) stays **verbatim**.
7. Change the export to:
   ```js
   export default SimulationPanel
   ```

- [ ] **Step 3: Rewrite `src/pages/Inputs.js` as the container**

Replace the entire file with:

```jsx
import React from 'react'
import './Inputs.css'
import SimulationPanel from './SimulationPanel'

function Inputs() {
  return (
    <div className="inputs-page">
      <div className="inputs-header">
        <h1>Life-Cycle Portfolio Model</h1>
        <p>Set the model parameters below and run the simulation.</p>
      </div>
      <SimulationPanel variant="blue" />
    </div>
  )
}

export default Inputs
```

- [ ] **Step 4: Run the existing tests (still green after refactor)**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: PASS — same count as Step 1. (The suite renders `<Inputs>`, which now renders one `SimulationPanel`; the single form and preset pills are unchanged, so every assertion still resolves to exactly one match.)

- [ ] **Step 5: Verify the build compiles**

Run: `npm run build`
Expected: "Compiled successfully."

- [ ] **Step 6: Commit**

```bash
git add src/pages/SimulationPanel.js src/pages/Inputs.js
git commit -m "refactor: extract SimulationPanel from Inputs (behavior-preserving)"
```

---

### Task 2: Red variant theming

**Files:**
- Modify: `src/pages/Inputs.css`
- Modify: `src/pages/Inputs.test.js`

**Interfaces:**
- Consumes: the `sim-panel--red` / `sim-panel--blue` class emitted by `SimulationPanel` (Task 1).
- Produces: CSS so any subtree under `.sim-panel--red` renders red; `--focus-ring` variable for themed focus rings.

- [ ] **Step 1: Write the failing test**

Add to `src/pages/Inputs.test.js`:

```jsx
import SimulationPanel from './SimulationPanel'

test('red variant applies the sim-panel--red class', () => {
  const { container } = render(<SimulationPanel variant="red" />)
  expect(container.querySelector('.sim-panel--red')).not.toBeNull()
})

test('blue variant applies the sim-panel--blue class', () => {
  const { container } = render(<SimulationPanel variant="blue" />)
  expect(container.querySelector('.sim-panel--blue')).not.toBeNull()
})
```

(If `render` is not yet imported in the file, ensure the top has
`import { render, screen, fireEvent } from '@testing-library/react'`.)

- [ ] **Step 2: Run tests to confirm the variant tests pass but note focus-ring is not yet themed**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: the two new tests PASS (the class is already emitted from Task 1). This task's substance is the CSS; the tests lock the class contract.

- [ ] **Step 3: Add the red variable override and focus-ring variable**

In `src/pages/Inputs.css`, add `--focus-ring` to the existing `:root` block (add the one line):

```css
:root {
  /* ...existing variables... */
  --focus-ring: rgba(0, 145, 212, 0.25);
}
```

Change the `.field input:focus` rule's hardcoded shadow to the variable:

```css
.field input:focus {
  outline: none;
  border-color: var(--imperial-light-blue);
  box-shadow: 0 0 0 3px var(--focus-ring);
  background: #fff;
}
```

Append the red override:

```css
/* Red simulation panel: re-declare the theme variables so the whole
   subtree (header, legends, buttons, active pills, table header, progress
   bar, focus rings) renders red. Charts are backend PNGs and unaffected. */
.sim-panel--red {
  --imperial-blue: #C0272D;
  --imperial-blue-dark: #8B1E22;
  --imperial-light-blue: #E8686D;
  --focus-ring: rgba(192, 39, 45, 0.25);
}
```

- [ ] **Step 4: Run tests and build**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: PASS (all, including the two variant tests).
Run: `npm run build`
Expected: "Compiled successfully."

- [ ] **Step 5: Commit**

```bash
git add src/pages/Inputs.css src/pages/Inputs.test.js
git commit -m "feat: red variant theming via CSS-variable override"
```

---

### Task 3: Split the panel into form / charts / table sections

**Files:**
- Modify: `src/pages/SimulationPanel.js`
- Modify: `src/pages/Inputs.css`

**Interfaces:**
- Produces: `SimulationPanel` now renders exactly three block sections inside `.sim-panel` — `.panel-form`, `.panel-charts`, `.panel-table` — and the `.sim-panel` wrapper is `display: contents`. Grid-area assignments per variant/section are defined but only take effect under a grid (Task 4), so single-panel layout is unchanged.

- [ ] **Step 1: Wrap the three regions in sections**

In `SimulationPanel.js`, change the returned JSX so the wrapper's children are exactly three sections. The form section holds the presets, the `<form>`, and the loading/error blocks; the charts section holds the charts `.results`; the table section holds the table `.results`:

```jsx
  return (
    <div className={`sim-panel sim-panel--${variant}`}>
      <div className="panel-form">
        <fieldset className="field-group">
          <legend>Data Presets</legend>
          {/* ...preset-grid unchanged... */}
        </fieldset>

        <form key={activePreset} method="post" onSubmit={handleSubmit}>
          {/* ...form body unchanged... */}
        </form>

        {loading && (
          <div className="loading">
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <p>Running simulation… {Math.floor(progress)}%</p>
          </div>
        )}

        {error && <p className="error-msg">Error: {error}</p>}
      </div>

      <div className="panel-charts">
        {charts && (
          <div className="results">
            <h3>The Life Cycle Model Visualized</h3>
            {/* ...chart-grid unchanged... */}
          </div>
        )}
      </div>

      <div className="panel-table">
        {result && (
          <div className="results">
            <h3>The Life Cycle Model Quantified</h3>
            <ResultsTable
              result={result}
              startAge={startAge}
              currency={currency}
              salary={
                Number.isFinite(Number(salary)) && Number(salary) > 0
                  ? Number(salary)
                  : 1
              }
            />
          </div>
        )}
      </div>
    </div>
  )
```

Keep the inner contents (`preset-grid`, form body, `chart-grid`) exactly as they are — only the three wrapping `<div className="panel-*">` elements are new.

- [ ] **Step 2: Add section CSS (display:contents + area map)**

Append to `src/pages/Inputs.css`:

```css
/* Panels contribute their three sections directly to the compare grid.
   display:contents removes the wrapper box; custom-property inheritance
   (the red override) still cascades through it. In single-instance mode
   there is no grid, so the sections just flow normally — unchanged layout. */
.sim-panel { display: contents; }

.sim-panel--blue .panel-form   { grid-area: blue-form; }
.sim-panel--blue .panel-charts { grid-area: blue-charts; }
.sim-panel--blue .panel-table  { grid-area: blue-table; }
.sim-panel--red  .panel-form   { grid-area: red-form; }
.sim-panel--red  .panel-charts { grid-area: red-charts; }
.sim-panel--red  .panel-table  { grid-area: red-table; }
```

- [ ] **Step 3: Run tests and build; confirm single-panel layout unchanged**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: PASS (unchanged — the form and labels still resolve).
Run: `npm run build`
Expected: "Compiled successfully."
Then `npm start` and confirm the page looks identical to before (title, presets, form, and — after a run — charts then the full-width table). Stop the dev server.

- [ ] **Step 4: Commit**

```bash
git add src/pages/SimulationPanel.js src/pages/Inputs.css
git commit -m "refactor: split SimulationPanel into form/charts/table sections"
```

---

### Task 4: Instance toggle, second panel, and compare grid

**Files:**
- Modify: `src/pages/Inputs.js`
- Modify: `src/pages/SimulationPanel.js`
- Modify: `src/pages/Inputs.css`
- Modify: `src/pages/Inputs.test.js`

**Interfaces:**
- Consumes: `SimulationPanel({ variant, hidden })` and the `.panel-*` grid-area classes (Task 3).
- Produces: container with `instances` state (`1`|`2`), a `redEverShown` latch, the `1 form`/`2 forms` toggle, and a `.compare-grid` wrapper that becomes a two-column `grid-template-areas` layout when `instances === 2`.

- [ ] **Step 1: Add the `hidden` prop to `SimulationPanel`**

In `SimulationPanel.js`, change the signature and wrapper class:

```jsx
function SimulationPanel({ variant = 'blue', hidden = false }) {
```
```jsx
    <div className={`sim-panel sim-panel--${variant}${hidden ? ' sim-panel--hidden' : ''}`}>
```

- [ ] **Step 2: Write the failing toggle tests**

Add to `src/pages/Inputs.test.js`:

```jsx
test('shows one form by default and no red panel', () => {
  const { container } = render(<Inputs />)
  expect(container.querySelectorAll('.sim-panel--blue').length).toBe(1)
  expect(container.querySelector('.sim-panel--red')).toBeNull()
  expect(screen.getByRole('button', { name: '1 form' })).toHaveAttribute('aria-pressed', 'true')
})

test('switching to 2 forms adds a red panel', () => {
  const { container } = render(<Inputs />)
  fireEvent.click(screen.getByRole('button', { name: '2 forms' }))
  expect(container.querySelector('.sim-panel--red')).not.toBeNull()
  expect(container.querySelector('.sim-panel--red.sim-panel--hidden')).toBeNull()
})

test('red panel is hidden but retained (state persists) after toggling 2 -> 1 -> 2', () => {
  const { container } = render(<Inputs />)
  // create the red panel and edit one of its inputs
  fireEvent.click(screen.getByRole('button', { name: '2 forms' }))
  // two inputs share id #tb once both panels exist; scope to the red panel
  const redPanel = container.querySelector('.sim-panel--red')
  const redTb = redPanel.querySelector('#tb')
  fireEvent.change(redTb, { target: { value: '41' } })
  // hide it
  fireEvent.click(screen.getByRole('button', { name: '1 form' }))
  expect(container.querySelector('.sim-panel--red.sim-panel--hidden')).not.toBeNull()
  // show again — the edited value survived (panel was hidden, not unmounted)
  fireEvent.click(screen.getByRole('button', { name: '2 forms' }))
  expect(container.querySelector('.sim-panel--red').querySelector('#tb')).toHaveValue(41)
})
```

- [ ] **Step 3: Run the tests to confirm they fail**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: the three new tests FAIL (no toggle buttons yet).

- [ ] **Step 4: Rewrite `Inputs.js` as the toggling container**

```jsx
import React, { useState } from 'react'
import './Inputs.css'
import SimulationPanel from './SimulationPanel'

function Inputs() {
  const [instances, setInstances] = useState(1)
  const [redEverShown, setRedEverShown] = useState(false)

  function setCount(n) {
    setInstances(n)
    if (n === 2) setRedEverShown(true)
  }

  const twoUp = instances === 2

  return (
    <div className="inputs-page">
      <div className="inputs-header">
        <h1>Life-Cycle Portfolio Model</h1>
        <p>Set the model parameters below and run the simulation.</p>
      </div>

      <div className="instance-toggle" role="group" aria-label="Number of forms">
        {[1, 2].map((n) => (
          <button
            key={n}
            type="button"
            className={`toggle-pill${instances === n ? ' active' : ''}`}
            aria-pressed={instances === n}
            onClick={() => setCount(n)}
          >
            {n === 1 ? '1 form' : '2 forms'}
          </button>
        ))}
      </div>

      <div className={`compare-grid${twoUp ? ' compare-grid--two' : ''}`}>
        <SimulationPanel variant="blue" />
        {(twoUp || redEverShown) && (
          <SimulationPanel variant="red" hidden={!twoUp} />
        )}
      </div>
    </div>
  )
}

export default Inputs
```

- [ ] **Step 5: Add the toggle, grid, and hidden CSS**

Append to `src/pages/Inputs.css`:

```css
/* Instance toggle */
.instance-toggle {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin: 0 0 1.5rem;
}
.toggle-pill {
  padding: 0.5rem 1.1rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--imperial-blue);
  background: #fff;
  border: 1px solid var(--imperial-blue);
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.toggle-pill.active {
  background: var(--imperial-blue);
  color: #fff;
}

/* Hidden (retained) panel */
.sim-panel--hidden { display: none; }

/* Two-instance compare layout. The grid breaks out of the 960px column so
   two forms fit; the two table areas span both columns (full-width, stacked). */
.compare-grid--two {
  width: 96vw;
  position: relative;
  left: 50%;
  transform: translateX(-50%);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 1.5rem;
  grid-template-areas:
    "blue-form   red-form"
    "blue-charts red-charts"
    "blue-table  blue-table"
    "red-table   red-table";
}
/* Inside the compare grid the results must not do their single-mode 96vw
   break-out; the grid areas control width instead. */
.compare-grid--two .results {
  width: auto;
  left: auto;
  transform: none;
}

/* Narrow screens: one column, band grouping preserved. */
@media (max-width: 900px) {
  .compare-grid--two {
    grid-template-columns: 1fr;
    grid-template-areas:
      "blue-form"
      "red-form"
      "blue-charts"
      "red-charts"
      "blue-table"
      "red-table";
  }
}
```

- [ ] **Step 6: Run the tests to confirm they pass**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: PASS (all — the three toggle tests plus the earlier ones).

- [ ] **Step 7: Build and eyeball**

Run: `npm run build` → "Compiled successfully."
Then `npm start`: confirm the toggle shows; `2 forms` puts blue and red forms side by side with red chrome, charts side by side, and (after running each) the two tables stacked full width with blue vs red headers; resize narrow to confirm the single-column order. Stop the dev server.

- [ ] **Step 8: Commit**

```bash
git add src/pages/Inputs.js src/pages/SimulationPanel.js src/pages/Inputs.css src/pages/Inputs.test.js
git commit -m "feat: 1/2-instance toggle with side-by-side compare layout"
```

---

### Task 5: Per-instance detail pages

**Files:**
- Modify: `src/pages/SimulationPanel.js`
- Modify: `public/algorithm.html`
- Modify: `public/algorithm_simple.html`
- Modify: `src/pages/Inputs.test.js`

**Interfaces:**
- Consumes: the `variant` prop.
- Produces: each panel writes charts to `lifecycleCharts:<variant>` (blue also writes legacy `lifecycleCharts`); its detail links carry `?variant=<variant>`; the detail pages read the matching key.

- [ ] **Step 1: Write the failing detail-link tests**

Add to `src/pages/Inputs.test.js`:

```jsx
test('blue panel detail links carry ?variant=blue', () => {
  const { container } = render(<SimulationPanel variant="blue" />)
  const hrefs = [...container.querySelectorAll('a')].map((a) => a.getAttribute('href'))
  expect(hrefs).toContain('/algorithm.html?variant=blue')
  expect(hrefs).toContain('/algorithm_simple.html?variant=blue')
})

test('red panel detail links carry ?variant=red', () => {
  const { container } = render(<SimulationPanel variant="red" />)
  const hrefs = [...container.querySelectorAll('a')].map((a) => a.getAttribute('href'))
  expect(hrefs).toContain('/algorithm.html?variant=red')
  expect(hrefs).toContain('/algorithm_simple.html?variant=red')
})
```

- [ ] **Step 2: Run to confirm they fail**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: the two new tests FAIL (links have no query param yet).

- [ ] **Step 3: Make the detail links variant-aware**

In `SimulationPanel.js`, change the two detail-link `href`s in the `form-actions` block:

```jsx
          <a href={`/algorithm_simple.html?variant=${variant}`} target="_blank" rel="noopener noreferrer">
            <button type="button" className="btn btn-secondary">
              Simple Algorithm Details
            </button>
          </a>
          <a href={`/algorithm.html?variant=${variant}`} target="_blank" rel="noopener noreferrer">
            <button type="button" className="btn btn-secondary">
              Technical Algorithm Details
            </button>
          </a>
```

- [ ] **Step 4: Write charts to a variant-scoped key**

In `SimulationPanel.js` `handleSubmit`, replace the single `localStorage.setItem` line with variant-scoped writes (blue also keeps the legacy key for old links):

```jsx
      try {
        window.localStorage.setItem(
          `lifecycleCharts:${variant}`,
          JSON.stringify(data.charts)
        )
        if (variant === 'blue') {
          window.localStorage.setItem('lifecycleCharts', JSON.stringify(data.charts))
        }
      } catch (e) {
        console.warn('Could not cache charts for detail pages:', e)
      }
```

- [ ] **Step 5: Make the detail pages read the variant key**

In both `public/algorithm.html` and `public/algorithm_simple.html`, find the line:

```js
    var charts = JSON.parse(localStorage.getItem("lifecycleCharts") || "null");
```

Replace it with:

```js
    var variant = new URLSearchParams(location.search).get("variant");
    var key = variant ? "lifecycleCharts:" + variant : "lifecycleCharts";
    var charts = JSON.parse(localStorage.getItem(key) || "null");
```

(Leave the rest of each script unchanged.)

- [ ] **Step 6: Run tests and build**

Run: `npm test -- --watchAll=false --testPathPattern=Inputs`
Expected: PASS (all, including the two detail-link tests).
Run: `npm run build`
Expected: "Compiled successfully."

- [ ] **Step 7: Commit**

```bash
git add src/pages/SimulationPanel.js src/pages/Inputs.test.js public/algorithm.html public/algorithm_simple.html
git commit -m "feat: per-instance detail pages via variant-scoped chart keys"
```

---

## Final Verification (manual)

- Toggle to `2 forms`. Configure blue and red differently (e.g., blue Default, red Doctor). Run **both**; confirm two independent progress bars and two result sets, with the two tables stacked full width, blue-headed above red-headed.
- Open blue's *Technical Algorithm Details* and red's; confirm each shows **its own** run's charts (not the other's).
- Toggle back to `1 form`: red panel disappears; toggle to `2 forms`: red's inputs/results are still there.
- Resize to a phone width: bands collapse to one column in order blue form, red form, blue charts, red charts, blue table, red table; nothing overflows the screen.

## Notes for the implementer

- The `display: contents` wrapper is what lets each self-contained panel place its three sections into the container grid; keep the red variable override on `.sim-panel--red` (custom properties still inherit through `display: contents`).
- Two inputs share each `id` (e.g. `#tb`) once both panels exist. That's acceptable for uncontrolled inputs, but in tests always scope queries to a panel (`container.querySelector('.sim-panel--red').querySelector('#tb')`) rather than `getByLabelText`, which would throw on duplicates.
- No backend, model, or `/api/run` changes anywhere in this plan.
