import { render, screen } from '@testing-library/react'
import Inputs from './Inputs'
import SimulationPanel from './SimulationPanel'

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

test('red variant applies the sim-panel--red class', () => {
  const { container } = render(<SimulationPanel variant="red" />)
  expect(container.querySelector('.sim-panel--red')).not.toBeNull()
})

test('blue variant applies the sim-panel--blue class', () => {
  const { container } = render(<SimulationPanel variant="blue" />)
  expect(container.querySelector('.sim-panel--blue')).not.toBeNull()
})

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
