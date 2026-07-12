import React, { useState } from 'react'

// All model parameters, with their defaults, meaning and units.
// Editing this one list is enough to change the form.
const FIELDS = [
  { name: 'tb',      label: 'Starting age (years)',                def: 20 },
  { name: 'tr',      label: 'Retirement age (years)',              def: 66 },
  { name: 'td',      label: 'Maximum age (years)',                 def: 100 },
  { name: 'rho',     label: 'Relative risk aversion (γ)',          def: 10.0 },
  { name: 'delta',   label: 'Discount factor (β)',                 def: 0.97 },
  { name: 'psi',     label: 'EIS (ψ)',                             def: 0.5 },
  { name: 'r',       label: 'Gross risk-free rate',                def: 1.015 },
  { name: 'mu',      label: 'Equity premium (μ)',                  def: 0.04 },
  { name: 'sigr',    label: 'Standard dev stock returns (σ_R)',    def: 0.2 },
  { name: 'smay',    label: 'Standard dev transitory income (σ_u)', def: 0.1 },
  { name: 'smav',    label: 'Standard dev permanent income (σ_z)', def: 0.1 },
  { name: 'corr_v',  label: 'Corr(perm income, returns)',          def: 0.0 },
  { name: 'corr_y',  label: 'Corr(trans income, returns)',         def: 0.0 },
  { name: 'ret_fac', label: 'Retirement income factor (λ)',        def: 0.68212 },
  { name: 'aa',      label: 'Income intercept',                    def: 0.530339 },
  { name: 'b1',      label: 'Income age coefficient',              def: 0.16818 },
  { name: 'b2',      label: 'Income age² coefficient',             def: -0.00323371 },
  { name: 'b3',      label: 'Income age³ coefficient',             def: 1.9704e-5 },
  { name: 'ncash',   label: 'Cash-on-hand grid size',              def: 51 },
  { name: 'na',      label: 'Allocation grid size',                def: 51 },
  { name: 'nc',      label: 'Consumption search grid',             def: 21 },
  { name: 'n',       label: 'Quadrature nodes',                    def: 5 },
  { name: 'maxcash', label: 'Max cash-on-hand',                    def: 200.0 },
  { name: 'mincash', label: 'Min cash-on-hand',                    def: 0.25 },
  { name: 'nsim',    label: 'Simulation paths',                    def: 10000 },
]

// Descriptions shown under each input, in the same order as FIELDS.
// Edit these freely — they are not tied to the variable definitions above.
const DESCRIPTIONS = [
  'The age when the person started working.',
  'The age when the person retired. This data is collected since assets are safer to invest in while having an income.',
  'The age when the person is expected to pass away. This data is collected since all wealth will be planned to be spent by this year',
  'How much the person dislikes gambles over wealth; an economist estimates it from experimental choices or asset-pricing data, or a consumer just uses the standard textbook value of ~5–10. The lower this value is, the less they money will be put into stocks to \'play it safe.\'',
  'How much the person values next year\'s utility relative to this year\'s (0.97 ≈ 3% annual impatience); inferred from savings behavior or simply set near 0.96–0.98. The higher this is, the more the person cares about the future, so they spend less today and save more for later.',
  'Measures willingness to shift consumption across time in response to interest rates; estimated from how consumption growth responds to expected returns, or use the common calibration of ~0.5. The lower this is, the more the person wants their spending to stay flat and predictable year to year, rather than splurging now or later.',
  'The safe return; read it off inflation-protected government bond (TIPS) yields, or use the historical ~1–2% real average. The higher it is, the more the person can earn just by keeping their money somewhere safe — so there\'s less reason to gamble on stocks.',
  'The extra average return stocks earn over the safe asset; estimated from long-run stock-vs-bond return differences, or use the historical ~4–6%. The bigger the bonus stocks pay over safe assets, the more the person should load up on stocks.',
  'The volatility (riskiness) of equity returns; computed as the standard deviation of annual stock-index returns (historically ~18–20%). The more wildly stocks swing, the riskier they feel — so the person holds fewer of them.',
  'Size of temporary, one-off income surprises (bonuses, short gaps); estimated from year-to-year fluctuations in panel earnings data (PSID), or use ~0.1. Bigger short-term surprises (a lost bonus, a brief gap) make people save a little extra as a cushion and take slightly less risk.',
  'Size of lasting shocks that permanently reset the income level (promotion, disability); estimated from the growth of earnings dispersion with age, or use ~0.1. Because these changes stick for life (a promotion, an injury), they make future paychecks feel less reliable — so the person leans a bit more toward safe assets.',
  'Whether lasting income changes move with the stock market; estimated by correlating earnings shocks with market returns, or assume 0 (the baseline). At zero (the default), the person\'s income and the market are unrelated, so this does nothing. If they moved together, the person\'s job would already feel "stock-like," so they\'d buy fewer actual stocks to avoid doubling up on the same risk.',
  'Whether short-term income blips move with the market; same estimation as above, or assume 0. At zero (the default), the person\'s income and the market are unrelated, so this does nothing. If they moved together, the person\'s job would already feel "stock-like," so they\'d buy fewer actual stocks to avoid doubling up on the same risk.',
  'Fraction of pre-retirement income received as pension/Social Security (~68%); look at the subject\'s Social Security statement or national replacement-rate tables. The bigger their guaranteed pension, the safer they feel in retirement — so they can spend more freely and keep more in stocks even when old.',
  '',
  '',
  '',
  'Coefficients of the hump-shaped age–earnings curve f(t); obtained by regressing log earnings on age, age², age³ in census/panel data (or just use these fitted values).',
  'How many different wealth levels (from poor to rich) the model checks. More levels give a smoother, more precise answer but run slower.',
  'How many different stock-versus-safe mixes the model tries, from 0% up to 100% in stocks. More options let it pin down the ideal stock share more exactly, at the cost of speed.',
  'How many different "how much to spend this year" amounts the model tests at each step. More amounts give a finer read on the best spending choice but run slower.',
  'How many sample outcomes the model uses to average over an uncertain future, like good versus bad stock years. More samples make the estimate of the future more accurate but slower; 5 is a standard, efficient choice.',
  'The richest wealth level the model bothers to consider (200× a year\'s income). It just needs to be high enough that almost nobody realistically goes above it.',
  'The poorest wealth level considered (a quarter of a year\'s income). It sits just above zero to keep the math well-behaved.',
  'How many pretend "life stories" the model runs to see how people typically end up. More lives give smoother, more reliable averages but take longer; 10,000 is enough for stable results.',
]

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

// Shared cell styling for the summary table.
const thStyle = {
  border: '1px solid #ccc',
  padding: '3px 8px',
  textAlign: 'right',
  background: '#282c34',   // match site background so rows scroll behind cleanly
  position: 'sticky',
  top: 0,
}
const tdStyle = {
  border: '1px solid #eee',
  padding: '3px 8px',
  textAlign: 'right',
}

function Inputs() {
  const [result, setResult] = useState(null)
  const [startAge, setStartAge] = useState(20)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault() // Prevent automatic page refresh by browser (otherwise would refresh on submit of form)
    setError(null)
    setResult(null)

    // Read every named input straight from the form, converting to numbers.
    const formData = new FormData(e.target) // e.target is the form element
    const params = {}
    for (const [name, value] of formData.entries()) {
      params[name] = Number(value)
    }

    try {
      const response = await fetch('http://localhost:8000/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Request failed')
      }

      console.log('Server responded:', data)
      setStartAge(params.tb || 20)   // label table rows by real age
      setResult(data.sim)
    } catch (err) {
      console.error('Submit failed:', err)
      setError(err.message)
    }
  }

  return (
    <div>

      <form method="post" onSubmit={handleSubmit}>
        {FIELDS.map((f, i) => (
          <div key={f.name} style={{ marginBottom: '0.75rem' }}>
            <label>
              {f.label}:{' '}
              <input
                type="number"
                step="any"
                name={f.name}
                defaultValue={f.def}
              />
            </label>
            <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.15rem' }}>
              {DESCRIPTIONS[i]}
            </div>
          </div>
        ))}
        <button type="submit" style={{ marginBottom: '1rem' }}>Submit</button>
      </form>
      <a href="/algorithm_simple.html" target="_blank" rel="noopener noreferrer">
        <button type="button" style={{ marginBottom: '1rem' }}>
          Simple Algorithm Info
        </button>
      </a>
      <br></br>
      <a href="/algorithm.html" target="_blank" rel="noopener noreferrer">
        <button type="button" style={{ marginBottom: '1rem' }}>
          Detailed Algorithm Info
        </button>
      </a>

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {result && (
        <div>
          <h3>Year-by-year summary</h3>
          <div style={{ maxHeight: '500px', overflow: 'auto' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr>
                  <th style={thStyle}>Age</th>
                  {Object.keys(result).map((key) => (
                    <th key={key} style={thStyle}>
                      {LABELS[key] || key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result[Object.keys(result)[0]].map((_, i) => (
                  <tr key={i}>
                    <td style={tdStyle}>{startAge + i}</td>
                    {Object.keys(result).map((key) => (
                      <td key={key} style={tdStyle}>
                        {result[key][i].toFixed(4)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default Inputs