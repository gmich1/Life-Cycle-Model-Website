# Currency Conversion for the Results — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user enter a starting-age salary and currency on the form and see the results table's money quantities as tangible real money instead of normalized multiples of income.

**Architecture:** Purely a frontend (React) change in `Real/frontend/src/pages`. Conversion logic is extracted into pure helpers (`currency.js`) and a presentational component (`ResultsTable.js`) so it is unit-testable without mocking `fetch`. `Inputs.js` gains two controlled inputs (currency + salary) and delegates table rendering to `ResultsTable`. The model, backend, and charts are untouched — the API already returns every series needed (`meanCs`, `meanWs`, `meanYs`, `meanS`, `meanB`, `cGPY`).

**Tech Stack:** React 19, create-react-app (`react-scripts` 5.0.1), Jest + React Testing Library (`@testing-library/react`, `@testing-library/jest-dom`), `Intl.NumberFormat` for currency formatting.

## Global Constraints

- Frontend-only. **No** edits to `api/`, `solver.py`, `model.py`, `plots.py`, or any backend file.
- **No new npm dependencies.** Use built-in `Intl.NumberFormat`.
- The two new inputs (`Currency`, `Starting annual salary`) must **not** be sent in the `/api/run` POST body. They carry no `name` attribute, so the form's `FormData` naturally excludes them.
- Conversion rule (single rule for all five money quantities): `real money = normalized × cGPY × salary`. The scaled series `meanCs`/`meanWs`/`meanYs` already include `cGPY` (factor 1); `meanS`/`meanB` apply `× cGPY[i]` inline.
- Money quantities: `meanCs`, `meanWs`, `meanYs`, `meanS`, `meanB`. All other columns (ratios, growth factors, normalized C/W/I) keep their current 4-decimal display and never get a currency symbol.
- `cGPY` stays **additive** (the app's existing definition) — decided fork, see spec.
- Default state is `Currency = none`, `salary = 1`; in `none` mode the table must render **exactly** as it does today (`toFixed(4)`, no symbols, stocks/bonds normalized).
- Currency formatting: `Intl.NumberFormat(undefined, { style: 'currency', currency: code, maximumFractionDigits: 0 })`.
- All commands run from `Real/frontend/`. Run tests once (non-watch) with the `CI=true … --watchAll=false` form shown in each task.

---

## File Structure

- **Create** `Real/frontend/src/pages/currency.js` — pure helpers + data: `LABELS` (moved from `Inputs.js`), `CURRENCIES`, `MONEY_KEYS`, `symbolFor`, `toCurrency`, `headerLabel`, `formatCell`.
- **Create** `Real/frontend/src/pages/currency.test.js` — unit tests for the helpers.
- **Create** `Real/frontend/src/pages/ResultsTable.js` — presentational table component using `currency.js`.
- **Create** `Real/frontend/src/pages/ResultsTable.test.js` — render tests for the table (none mode + currency mode).
- **Modify** `Real/frontend/src/pages/Inputs.js` — remove local `LABELS`; add `currency`/`salary` state; render the two controls in the `incprofile` fieldset; replace the inline results table with `<ResultsTable />`.
- **Modify** `Real/frontend/src/pages/Inputs.test.js` — add a test that the two controls render with defaults and have no `name` attribute.

---

## Task 1: Currency helpers (`currency.js`)

**Files:**
- Create: `Real/frontend/src/pages/currency.js`
- Test: `Real/frontend/src/pages/currency.test.js`

**Interfaces:**
- Consumes: nothing (leaf module).
- Produces:
  - `LABELS: Record<string,string>` — sim-key → column header.
  - `CURRENCIES: Array<{code, label, symbol}>` — includes `{code:'none', symbol:''}` first.
  - `MONEY_KEYS: Record<string,{label, needsCgpy}>` — the five money keys.
  - `symbolFor(code: string) => string`
  - `toCurrency(key, value, i, cGPY, salary) => number`
  - `headerLabel(key: string, code: string) => string`
  - `formatCell(key, value, i, {code, salary, cGPY}) => string`

- [ ] **Step 1: Write the failing test**

Create `Real/frontend/src/pages/currency.test.js`:

```javascript
import { symbolFor, headerLabel, formatCell, toCurrency } from './currency'

const GBP = new Intl.NumberFormat(undefined, {
  style: 'currency', currency: 'GBP', maximumFractionDigits: 0,
})

test('symbolFor returns the currency symbol, empty for none', () => {
  expect(symbolFor('GBP')).toBe('£')
  expect(symbolFor('none')).toBe('')
})

test('headerLabel: none mode keeps normalized labels', () => {
  expect(headerLabel('meanCs', 'none')).toBe('Consumption (scaled)')
  expect(headerLabel('meanS', 'none')).toBe('Stocks')
  expect(headerLabel('meanalpha', 'none')).toBe('Stock share')
})

test('headerLabel: currency mode adds the symbol to money columns only', () => {
  expect(headerLabel('meanCs', 'GBP')).toBe('Consumption (£)')
  expect(headerLabel('meanS', 'GBP')).toBe('Stocks (£)')
  expect(headerLabel('meanalpha', 'GBP')).toBe('Stock share') // ratio unchanged
})

test('formatCell: none mode is 4-decimal, no symbol', () => {
  expect(formatCell('meanS', 2.388, 1, { code: 'none', salary: 30000, cGPY: [1, 2] }))
    .toBe('2.3880')
})

test('formatCell: scaled money key is value × salary (cGPY already baked in)', () => {
  expect(formatCell('meanYs', 2.0, 0, { code: 'GBP', salary: 30000, cGPY: [1.6, 2.0] }))
    .toBe(GBP.format(2.0 * 30000))
})

test('formatCell: stocks/bonds are value × cGPY[i] × salary', () => {
  expect(formatCell('meanS', 2.388, 1, { code: 'GBP', salary: 30000, cGPY: [1.6, 2.021] }))
    .toBe(GBP.format(2.388 * 2.021 * 30000))
})

test('formatCell: ratio columns unchanged in currency mode', () => {
  expect(formatCell('meanalpha', 0.42, 0, { code: 'GBP', salary: 30000, cGPY: [1] }))
    .toBe('0.4200')
})

test('toCurrency applies cGPY only to stocks/bonds', () => {
  expect(toCurrency('meanYs', 2.0, 0, [1.6], 30000)).toBe(2.0 * 30000)
  expect(toCurrency('meanS', 2.0, 0, [1.6], 30000)).toBe(2.0 * 1.6 * 30000)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Real/frontend && CI=true npx react-scripts test src/pages/currency.test.js --watchAll=false`
Expected: FAIL — `Cannot find module './currency'`.

- [ ] **Step 3: Write minimal implementation**

Create `Real/frontend/src/pages/currency.js`:

```javascript
// Currency conversion helpers for the results table (display-only).
// The model runs in normalized units; these turn selected quantities into real
// money via `normalized × cGPY × salary`. See the design spec:
// docs/superpowers/specs/2026-07-17-currency-conversion-design.md

// Friendly column headers for the sim series (moved here from Inputs.js so the
// table and these helpers share one source).
export const LABELS = {
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

// Selectable currencies. `none` keeps the table in normalized units.
export const CURRENCIES = [
  { code: 'none', label: 'None (units)', symbol: '' },
  { code: 'GBP', label: '£ GBP', symbol: '£' },
  { code: 'USD', label: '$ USD', symbol: '$' },
  { code: 'EUR', label: '€ EUR', symbol: '€' },
  { code: 'JPY', label: '¥ JPY', symbol: '¥' },
]

// The five money quantities converted to currency.
//   label     – base name shown with the currency symbol in currency mode.
//   needsCgpy – multiply by cGPY[i] inline (stocks/bonds); the scaled series
//               (meanCs/Ws/Ys) already include cGPY, so their factor is 1.
export const MONEY_KEYS = {
  meanCs: { label: 'Consumption', needsCgpy: false },
  meanWs: { label: 'Wealth', needsCgpy: false },
  meanYs: { label: 'Income', needsCgpy: false },
  meanS: { label: 'Stocks', needsCgpy: true },
  meanB: { label: 'Bonds', needsCgpy: true },
}

export function symbolFor(code) {
  const c = CURRENCIES.find((x) => x.code === code)
  return c ? c.symbol : ''
}

// Real-money amount: normalized × cGPY × salary. Scaled keys already carry
// cGPY, so their inline factor is 1.
export function toCurrency(key, value, i, cGPY, salary) {
  const factor = MONEY_KEYS[key].needsCgpy ? cGPY[i] : 1
  return value * factor * salary
}

// Header text for a column. Money columns gain the currency symbol in currency
// mode; everything else keeps its normalized label.
export function headerLabel(key, code) {
  if (code !== 'none' && MONEY_KEYS[key]) {
    return `${MONEY_KEYS[key].label} (${symbolFor(code)})`
  }
  return LABELS[key] || key
}

// Cell text. In `none` mode, or for non-money columns, keep the 4-decimal
// normalized display. Otherwise format as currency with no decimals.
export function formatCell(key, value, i, { code, salary, cGPY }) {
  if (code === 'none' || !MONEY_KEYS[key]) {
    return value.toFixed(4)
  }
  const amount = toCurrency(key, value, i, cGPY, salary)
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: code,
    maximumFractionDigits: 0,
  }).format(amount)
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Real/frontend && CI=true npx react-scripts test src/pages/currency.test.js --watchAll=false`
Expected: PASS — 8 tests pass.

- [ ] **Step 5: Commit**

```bash
cd Real/frontend
git add src/pages/currency.js src/pages/currency.test.js
git commit -m "feat: currency conversion helpers for results table"
```

---

## Task 2: Results table component (`ResultsTable.js`)

**Files:**
- Create: `Real/frontend/src/pages/ResultsTable.js`
- Test: `Real/frontend/src/pages/ResultsTable.test.js`

**Interfaces:**
- Consumes from Task 1: `headerLabel(key, code)`, `formatCell(key, value, i, {code, salary, cGPY})`.
- Produces: default export `ResultsTable` — a component with props `{ result, startAge, currency, salary }`. `result` is an object of equal-length numeric arrays (the sim payload); `result.cGPY` must be present; `currency` is a code or `'none'`; `salary` is a number (used only in currency mode).

- [ ] **Step 1: Write the failing test**

Create `Real/frontend/src/pages/ResultsTable.test.js`:

```javascript
import { render, screen } from '@testing-library/react'
import ResultsTable from './ResultsTable'

const GBP = new Intl.NumberFormat(undefined, {
  style: 'currency', currency: 'GBP', maximumFractionDigits: 0,
})

const result = {
  meanY: [1, 1],
  meanYs: [1.6, 2.0],
  meanS: [0.3, 0.4],
  meanalpha: [0.5, 0.6],
  cGPY: [1.6, 2.0],
}

test('none mode: normalized labels, 4-decimal values, ages from startAge', () => {
  render(<ResultsTable result={result} startAge={20} currency="none" salary={1} />)
  expect(screen.getByText('Income (scaled)')).toBeInTheDocument()
  expect(screen.getByText('Stocks')).toBeInTheDocument()
  expect(screen.getByText('0.3000')).toBeInTheDocument() // meanS[0], unique
  expect(screen.getByText('0.6000')).toBeInTheDocument() // meanalpha[1], unique
  expect(screen.getByText('20')).toBeInTheDocument()
  expect(screen.getByText('21')).toBeInTheDocument()
})

test('currency mode: money columns show currency, ratios/normalized unchanged', () => {
  render(<ResultsTable result={result} startAge={20} currency="GBP" salary={30000} />)
  expect(screen.getByText('Income (£)')).toBeInTheDocument()
  expect(screen.getByText('Stocks (£)')).toBeInTheDocument()
  // scaled income × salary (age 20)
  expect(screen.getByText(GBP.format(1.6 * 30000))).toBeInTheDocument()
  // stocks × cGPY × salary (age 20)
  expect(screen.getByText(GBP.format(0.3 * 1.6 * 30000))).toBeInTheDocument()
  // normalized income unchanged (two rows of 1.0000)
  expect(screen.getAllByText('1.0000').length).toBe(2)
  // stock share unchanged
  expect(screen.getByText('0.5000')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Real/frontend && CI=true npx react-scripts test src/pages/ResultsTable.test.js --watchAll=false`
Expected: FAIL — `Cannot find module './ResultsTable'`.

- [ ] **Step 3: Write minimal implementation**

Create `Real/frontend/src/pages/ResultsTable.js`:

```javascript
import React from 'react'
import { headerLabel, formatCell } from './currency'

// Presentational results table. `result` is the sim payload (object of
// equal-length arrays); `currency` is a currency code (or 'none'); `salary` is
// the numeric starting salary used only in currency mode.
function ResultsTable({ result, startAge, currency, salary }) {
  const keys = Object.keys(result)
  const cGPY = result.cGPY
  const rows = result[keys[0]]

  return (
    <div className="table-wrap">
      <table className="results-table">
        <thead>
          <tr>
            <th>Age</th>
            {keys.map((key) => (
              <th key={key}>{headerLabel(key, currency)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((_, i) => (
            <tr key={i}>
              <td>{startAge + i}</td>
              {keys.map((key) => (
                <td key={key}>
                  {formatCell(key, result[key][i], i, { code: currency, salary, cGPY })}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ResultsTable
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd Real/frontend && CI=true npx react-scripts test src/pages/ResultsTable.test.js --watchAll=false`
Expected: PASS — 2 tests pass.

- [ ] **Step 5: Commit**

```bash
cd Real/frontend
git add src/pages/ResultsTable.js src/pages/ResultsTable.test.js
git commit -m "feat: presentational ResultsTable using currency helpers"
```

---

## Task 3: Wire currency + salary into `Inputs.js`

**Files:**
- Modify: `Real/frontend/src/pages/Inputs.js`
- Modify: `Real/frontend/src/pages/Inputs.test.js`

**Interfaces:**
- Consumes from Task 1: `CURRENCIES`. Consumes from Task 2: `ResultsTable` (default import).
- Produces: no new exports. Adds `currency`/`salary` React state and renders the two controls inside the `incprofile` fieldset; renders `<ResultsTable />` in place of the inline table.

- [ ] **Step 1: Write the failing test**

Add to `Real/frontend/src/pages/Inputs.test.js` (append at end of file):

```javascript
test('currency and salary controls render with defaults, excluded from POST (no name attr)', () => {
  render(<Inputs />)
  const currency = screen.getByLabelText('Currency')
  const salary = screen.getByLabelText('Starting annual salary')
  expect(currency).toHaveValue('none')
  expect(salary).toHaveValue(1)
  expect(currency).not.toHaveAttribute('name')
  expect(salary).not.toHaveAttribute('name')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd Real/frontend && CI=true npx react-scripts test src/pages/Inputs.test.js --watchAll=false`
Expected: FAIL — `Unable to find a label with the text of: Currency`.

- [ ] **Step 3: Implement the `Inputs.js` changes**

3a. **Add imports** — at the top of `Real/frontend/src/pages/Inputs.js`, below the existing `import './Inputs.css'`:

```javascript
import ResultsTable from './ResultsTable'
import { CURRENCIES } from './currency'
```

3b. **Delete the local `LABELS` block** — remove these lines (now provided by `currency.js`):

```javascript
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
```

3c. **Add state** — directly after the existing `const [startAge, setStartAge] = useState(20)` line inside `Inputs()`:

```javascript
  const [currency, setCurrency] = useState('none')
  const [salary, setSalary] = useState('1')
```

3d. **Render the two controls in the `incprofile` fieldset.** Find the `GROUPS.map((g) => { … })` block that returns each `<fieldset>`. Its `return` currently ends:

```javascript
              <div className="field-grid">
                {items.map((item) =>
                  /* ... existing field rendering ... */
                )}
              </div>
            </fieldset>
          )
```

Insert the currency/salary block **between** the closing `</div>` of `field-grid` and `</fieldset>`, so it reads:

```javascript
              <div className="field-grid">
                {items.map((item) =>
                  /* ... existing field rendering (unchanged) ... */
                )}
              </div>
              {g.id === 'incprofile' && (
                <div className="field-grid">
                  <div className="field">
                    <label htmlFor="currency">Currency</label>
                    <select
                      id="currency"
                      value={currency}
                      onChange={(e) => setCurrency(e.target.value)}
                    >
                      {CURRENCIES.map((c) => (
                        <option key={c.code} value={c.code}>{c.label}</option>
                      ))}
                    </select>
                    <div className="field-desc">
                      The currency your salary is paid in. Choose 'None (units)'
                      to keep results in the model's normalized units (multiples
                      of income) — the default.
                    </div>
                  </div>
                  <div className="field">
                    <label htmlFor="salary">Starting annual salary</label>
                    <input
                      id="salary"
                      type="number"
                      step="any"
                      value={salary}
                      onChange={(e) => setSalary(e.target.value)}
                    />
                    <div className="field-desc">
                      Your annual pay at the starting age. Enter it in the
                      currency chosen above to see your results as real money
                      instead of multiples of income. If you're unsure, set
                      Currency to 'None (units)' and leave this at 1.
                    </div>
                  </div>
                </div>
              )}
            </fieldset>
          )
```

(The `<select>` and `<input>` have **`id` but no `name`**, so `FormData` in `handleSubmit` excludes them from the POST — no change to `handleSubmit` needed.)

3e. **Replace the inline results table.** Find this block near the end of the component:

```javascript
      {result && (
        <div className="results">
          <h3>The Life Cycle Model Quantified</h3>
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
```

Replace it with:

```javascript
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
```

- [ ] **Step 4: Run the full test suite to verify everything passes**

Run: `cd Real/frontend && CI=true npx react-scripts test --watchAll=false`
Expected: PASS — all suites (`currency.test.js`, `ResultsTable.test.js`, `Inputs.test.js`) green, including the pre-existing preset/form tests (they don't touch the table, so removing local `LABELS` and swapping in `ResultsTable` leaves them passing).

- [ ] **Step 5: Commit**

```bash
cd Real/frontend
git add src/pages/Inputs.js src/pages/Inputs.test.js
git commit -m "feat: add currency + salary inputs and currency-aware results table"
```

---

## Task 4: Manual smoke test (verification before done)

**Files:** none (verification only).

- [ ] **Step 1: Build to confirm no compile/lint errors**

Run: `cd Real/frontend && CI=true npx react-scripts build`
Expected: "Compiled successfully" (CRA treats ESLint warnings as errors when `CI=true`, so this also catches unused-import / lint issues).

- [ ] **Step 2: Run the dev server and eyeball**

Run: `cd Real/frontend && npm start` (opens http://localhost:3000).

Verify, using the **Default** preset:
- The **Income profile & retirement** group shows a **Currency** dropdown (default *None (units)*) and a **Starting annual salary** field (default 1), each with its own helper text.
- Submit with `Currency = None (units)` → the "Quantified" table looks exactly as before (4-decimal values, `Consumption (scaled)` / `Stocks` headers, no symbols).
- Set `Currency = £ GBP`, `Starting annual salary = 30000`, submit again → the five money columns show `£…` with thousands separators and headers like `Income (£)`, `Stocks (£)`; `Stock share`, `Wealth / income`, growth columns, and the normalized `Consumption`/`Wealth`/`Income` columns stay as 4-decimal numbers. Mid-career `Income (£)` shows the hump (well above £30k).
- Confirm in DevTools → Network → the `/api/run` request body has **no** `currency` or `salary` keys.
- Switch `Currency` back to `None (units)` → table returns to the original normalized display.

- [ ] **Step 3: Stop the dev server** (Ctrl-C).

---

## Self-Review

**Spec coverage:**
- Two inputs in the income-profile group with separate helper text → Task 3 (3d). ✔
- True-real-money conversion (`normalized × cGPY × salary`; scaled keys factor 1, stocks/bonds `× cGPY`) → Task 1 (`toCurrency`/`formatCell`) + tests. ✔
- Frontend-only, inputs excluded from POST (no `name` attr) → Task 3; verified in Task 3 test + Task 4 Network check. ✔
- Symbol + thousands separators formatting → Task 1 `formatCell`; verified in Task 2 tests. ✔
- `none` mode reproduces current table exactly → Task 2 none-mode test + Task 4 eyeball. ✔
- Additive `cGPY` kept (no backend change) → Global Constraints; no backend file touched. ✔
- Charts out of scope → no task touches `plots.py`/chart rendering. ✔

**Placeholder scan:** No TBD/TODO; every code step contains full content. ✔

**Type consistency:** `headerLabel(key, code)` and `formatCell(key, value, i, {code, salary, cGPY})` signatures match between Task 1 (definition), Task 1 tests, and Task 2 usage. `ResultsTable` props `{result, startAge, currency, salary}` match between Task 2 (definition/tests) and Task 3 (3e usage). `CURRENCIES` item shape `{code,label,symbol}` matches Task 3 `<option>` rendering. ✔
