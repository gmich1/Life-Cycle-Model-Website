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
