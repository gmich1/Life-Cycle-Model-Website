import { render, screen } from '@testing-library/react'
import Inputs from './Inputs'

test('form renders with the current default parameter values', () => {
  render(<Inputs />)
  expect(screen.getByLabelText('Starting age (years)')).toHaveValue(20)
  expect(screen.getByLabelText('Retirement income factor (λ)')).toHaveValue(0.68212)
  expect(screen.getByLabelText('Income intercept')).toHaveValue(0.530339)
  expect(screen.getByLabelText('Cash-on-hand grid size')).toHaveValue(51)
})
