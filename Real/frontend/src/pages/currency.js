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
