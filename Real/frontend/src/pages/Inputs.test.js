import { render, screen } from '@testing-library/react'
import Inputs from './Inputs'

test('form renders with the current default parameter values', () => {
  render(<Inputs />)
  expect(screen.getByLabelText('Starting age (years)')).toHaveValue(20)
  expect(screen.getByLabelText('Retirement income factor (λ)')).toHaveValue(0.68212)
  expect(screen.getByLabelText('Income intercept')).toHaveValue(0.530339)
  expect(screen.getByLabelText('Cash-on-hand grid size')).toHaveValue(51)
})

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

test('selecting Blue-collar (trades) populates the No-HS income polynomial', () => {
  render(<Inputs />)
  fireEvent.click(screen.getByRole('button', { name: /Blue-collar/ }))
  expect(screen.getByLabelText('Retirement age (years)')).toHaveValue(63)
  expect(screen.getByLabelText('Standard dev transitory income (σ_u)')).toHaveValue(0.325)
  expect(screen.getByLabelText('Corr(perm income, returns)')).toHaveValue(0.328)
  expect(screen.getByLabelText('Income intercept')).toHaveValue(0.4914)
  expect(screen.getByLabelText('Income age coefficient')).toHaveValue(0.1684)
  expect(screen.getByLabelText('Income age² coefficient')).toHaveValue(-0.00353)
  expect(screen.getByLabelText('Income age³ coefficient')).toHaveValue(2.3e-5)
})

test('currency and salary controls render with defaults, excluded from POST (no name attr)', () => {
  render(<Inputs />)
  const currency = screen.getByLabelText('Currency')
  const salary = screen.getByLabelText('Starting annual salary')
  expect(currency).toHaveValue('none')
  expect(salary).toHaveValue(1)
  expect(currency).not.toHaveAttribute('name')
  expect(salary).not.toHaveAttribute('name')
})
