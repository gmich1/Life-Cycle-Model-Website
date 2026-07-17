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
