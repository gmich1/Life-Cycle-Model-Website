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
