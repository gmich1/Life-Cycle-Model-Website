import React, { useState } from 'react'
import './Inputs.css'
import ResultsTable from './ResultsTable'
import { CURRENCIES } from './currency'

// Ordered groups rendered as boxes. Each field below names its group id.
const GROUPS = [
  { id: 'horizon',     title: 'Life horizon' },
  { id: 'prefs',       title: 'Preferences' },
  { id: 'market',      title: 'Market & returns' },
  { id: 'incrisk',     title: 'Income risk' },
  { id: 'incprofile',  title: 'Income profile & retirement' },
  { id: 'solver',      title: 'Solver settings' },
]

// All model parameters: default, label, description and group.
// Editing this one list is enough to change the form.
const FIELDS = [
  { name: 'tb',      group: 'horizon',    label: 'Starting age (years)',                def: 20,
    desc: 'The age when the person started working.' },
  { name: 'tr',      group: 'horizon',    label: 'Retirement age (years)',              def: 66,
    desc: 'The age when the person retired. This data is collected since assets are safer to invest in while having an income.' },
  { name: 'td',      group: 'horizon',    label: 'Maximum age (years)',                 def: 100,
    desc: 'The age when the person is expected to pass away. This data is collected since all wealth will be planned to be spent by this year' },
  { name: 'rho',     group: 'prefs',      label: 'Relative risk aversion (γ)',          def: 10.0,
    desc: 'How much the person dislikes gambles over wealth; an economist estimates it from experimental choices or asset-pricing data, or a consumer just uses the standard textbook value of ~5–10. The lower this value is, the less they money will be put into stocks to \'play it safe.\'' },
  { name: 'delta',   group: 'prefs',      label: 'Discount factor (β)',                 def: 0.97,
    desc: 'How much the person values next year\'s utility relative to this year\'s (0.97 ≈ 3% annual impatience); inferred from savings behavior or simply set near 0.96–0.98. The higher this is, the more the person cares about the future, so they spend less today and save more for later.' },
  { name: 'psi',     group: 'prefs',      label: 'EIS (ψ)',                             def: 0.5,
    desc: 'Measures willingness to shift consumption across time in response to interest rates; estimated from how consumption growth responds to expected returns, or use the common calibration of ~0.5. The lower this is, the more the person wants their spending to stay flat and predictable year to year, rather than splurging now or later.' },
  { name: 'r',       group: 'market',     label: 'Gross risk-free rate',                def: 1.015,
    desc: 'The safe return; read it off inflation-protected government bond (TIPS) yields, or use the historical ~1–2% real average. The higher it is, the more the person can earn just by keeping their money somewhere safe — so there\'s less reason to gamble on stocks.' },
  { name: 'mu',      group: 'market',     label: 'Equity premium (μ)',                  def: 0.04,
    desc: 'The extra average return stocks earn over the safe asset; estimated from long-run stock-vs-bond return differences, or use the historical ~4–6%. The bigger the bonus stocks pay over safe assets, the more the person should load up on stocks.' },
  { name: 'sigr',    group: 'market',     label: 'Standard dev stock returns (σ_R)',    def: 0.2,
    desc: 'The volatility (riskiness) of equity returns; computed as the standard deviation of annual stock-index returns (historically ~18–20%). The more wildly stocks swing, the riskier they feel — so the person holds fewer of them.' },
  { name: 'smay',    group: 'incrisk',    label: 'Standard dev transitory income (σ_u)', def: 0.1,
    desc: 'Size of temporary, one-off income surprises (bonuses, short gaps); estimated from year-to-year fluctuations in panel earnings data (PSID), or use ~0.1. Bigger short-term surprises (a lost bonus, a brief gap) make people save a little extra as a cushion and take slightly less risk.' },
  { name: 'smav',    group: 'incrisk',    label: 'Standard dev permanent income (σ_z)', def: 0.1,
    desc: 'Size of lasting shocks that permanently reset the income level (promotion, disability); estimated from the growth of earnings dispersion with age, or use ~0.1. Because these changes stick for life (a promotion, an injury), they make future paychecks feel less reliable — so the person leans a bit more toward safe assets.' },
  { name: 'corr_v',  group: 'incrisk',    label: 'Corr(perm income, returns)',          def: 0.0,
    desc: 'Whether lasting income changes move with the stock market; estimated by correlating earnings shocks with market returns, or assume 0 (the baseline). At zero (the default), the person\'s income and the market are unrelated, so this does nothing. If they moved together, the person\'s job would already feel "stock-like," so they\'d buy fewer actual stocks to avoid doubling up on the same risk.' },
  { name: 'corr_y',  group: 'incrisk',    label: 'Corr(trans income, returns)',         def: 0.0,
    desc: 'Whether short-term income blips move with the market; same estimation as above, or assume 0. At zero (the default), the person\'s income and the market are unrelated, so this does nothing. If they moved together, the person\'s job would already feel "stock-like," so they\'d buy fewer actual stocks to avoid doubling up on the same risk.' },
  { name: 'ret_fac', group: 'incprofile', label: 'Retirement income factor (λ)',        def: 0.68212,
    desc: 'Fraction of pre-retirement income received as pension/Social Security (~68%); look at the subject\'s Social Security statement or national replacement-rate tables. The bigger their guaranteed pension, the safer they feel in retirement — so they can spend more freely and keep more in stocks even when old.' },
  { name: 'aa',      group: 'incprofile', label: 'Income intercept',                    def: 0.530339,
    combo: 'incomecurve', comboDesc: 'Coefficients of the hump-shaped age–earnings curve f(t); obtained by regressing log earnings on age, age², age³ in census/panel data (or just use these fitted values). Together they draw the typical earnings path: low at the start, rising through your career, peaking in middle age, then easing off. A big future paycheck is like owning a safe asset, which is exactly why young people — who have a whole career of earnings ahead — can afford to go heavily into stocks.' },
  { name: 'b1',      group: 'incprofile', label: 'Income age coefficient',              def: 0.16818,
    combo: 'incomecurve' },
  { name: 'b2',      group: 'incprofile', label: 'Income age² coefficient',             def: -0.00323371,
    combo: 'incomecurve' },
  { name: 'b3',      group: 'incprofile', label: 'Income age³ coefficient',             def: 1.9704e-5,
    combo: 'incomecurve' },
  { name: 'ncash',   group: 'solver',     label: 'Cash-on-hand grid size',              def: 51,
    desc: 'How many different wealth levels (from poor to rich) the model checks. More levels give a smoother, more precise answer but run slower.' },
  { name: 'na',      group: 'solver',     label: 'Allocation grid size',                def: 51,
    desc: 'How many different stock-versus-safe mixes the model tries, from 0% up to 100% in stocks. More options let it pin down the ideal stock share more exactly, at the cost of speed.' },
  { name: 'nc',      group: 'solver',     label: 'Consumption search grid',             def: 21,
    desc: 'How many different "how much to spend this year" amounts the model tests at each step. More amounts give a finer read on the best spending choice but run slower.' },
  { name: 'n',       group: 'solver',     label: 'Quadrature nodes',                    def: 5,
    desc: 'How many sample outcomes the model uses to average over an uncertain future, like good versus bad stock years. More samples make the estimate of the future more accurate but slower; 5 is a standard, efficient choice.' },
  { name: 'maxcash', group: 'solver',     label: 'Max cash-on-hand',                    def: 200.0,
    desc: 'The richest wealth level the model bothers to consider (200× a year\'s income). It just needs to be high enough that almost nobody realistically goes above it.' },
  { name: 'mincash', group: 'solver',     label: 'Min cash-on-hand',                    def: 0.25,
    desc: 'The poorest wealth level considered (a quarter of a year\'s income). It sits just above zero to keep the math well-behaved.' },
  { name: 'nsim',    group: 'solver',     label: 'Simulation paths',                    def: 10000,
    desc: 'How many pretend "life stories" the model runs to see how people typically end up. More lives give smoother, more reliable averages but take longer; 10,000 is enough for stable results.' },
]

// Persona presets. Each `values` entry overrides a FIELDS default by name;
// any field not listed keeps its default. Only the three education-showcase
// personas (finance, bluecollar, doctor) override the income polynomial
// aa/b1/b2/b3. Values come from the design spec §4 and §4.3.
const PRESETS = [
  { id: 'default', label: 'Default',
    subtitle: 'Generally-applicable baseline settings',
    values: {} },
  { id: 'public', label: 'Public-sector lifer',
    subtitle: 'Stable, market-independent income; generous pension',
    values: { tb: 22, tr: 66, rho: 12, delta: 0.98, psi: 0.5, smay: 0.15, smav: 0.09, corr_v: 0, ret_fac: 0.85 } },
  { id: 'finance', label: 'Finance professional',
    subtitle: 'High pay that rides the stock market',
    values: { tb: 24, tr: 62, rho: 6, delta: 0.95, psi: 0.6, smay: 0.242, smav: 0.130, corr_v: 0.52, ret_fac: 0.45,
              aa: -1.9317, b1: 0.3194, b2: -0.00577, b3: 3.3e-5 } },
  { id: 'entrepreneur', label: 'Entrepreneur',
    subtitle: 'Volatile self-employment income; no pension',
    values: { tb: 26, tr: 68, rho: 6, delta: 0.94, psi: 0.7, smay: 0.30, smav: 0.18, corr_v: 0.30, ret_fac: 0.35 } },
  { id: 'bluecollar', label: 'Blue-collar (trades)',
    subtitle: 'Early start, cyclical manual work',
    values: { tb: 20, tr: 63, rho: 10, delta: 0.96, psi: 0.4, smay: 0.325, smav: 0.102, corr_v: 0.328, ret_fac: 0.60,
              aa: 0.4914, b1: 0.1684, b2: -0.00353, b3: 2.3e-5 } },
  { id: 'doctor', label: 'Doctor',
    subtitle: 'Late start, high and recession-proof income',
    values: { tb: 30, tr: 67, rho: 8, delta: 0.98, psi: 0.5, smay: 0.242, smav: 0.130, corr_v: 0.10, ret_fac: 0.55,
              aa: -1.9317, b1: 0.3194, b2: -0.00577, b3: 3.3e-5 } },
  { id: 'gig', label: 'Gig / precarious',
    subtitle: 'Insecure, spiky income; minimal safety net',
    values: { tb: 20, tr: 68, rho: 13, delta: 0.95, psi: 0.4, smay: 0.35, smav: 0.11, corr_v: 0.20, ret_fac: 0.30 } },
]

function SimulationPanel({ variant = 'blue', hidden = false }) {
  const [result, setResult] = useState(null)
  const [charts, setCharts] = useState(null)
  const [startAge, setStartAge] = useState(20)
  const [currency, setCurrency] = useState('none')
  const [salary, setSalary] = useState('1')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [activePreset, setActivePreset] = useState('default')
  const active = PRESETS.find((p) => p.id === activePreset) || PRESETS[0]

  // Expected solve time. The bar fills over this window and then holds at
  // 99% until the real result arrives (the run may finish sooner or later).
  const EXPECTED_MS = 50000

  async function handleSubmit(e) {
    e.preventDefault() // Prevent automatic page refresh by browser (otherwise would refresh on submit of form)
    setError(null)
    setResult(null)
    setCharts(null)
    setLoading(true)
    setProgress(0)

    // Advance an estimated progress bar from 0 → 99% over EXPECTED_MS.
    // It's a time estimate, not the true step count, so it caps at 99% and
    // only jumps to 100% once the response actually comes back.
    const startTime = Date.now()
    const timer = setInterval(() => {
      const pct = Math.min(99, ((Date.now() - startTime) / EXPECTED_MS) * 100)
      setProgress(pct)
    }, 200)

    // Read every named input straight from the form, converting to numbers.
    const formData = new FormData(e.target) // e.target is the form element
    const params = {}
    for (const [name, value] of formData.entries()) {
      params[name] = Number(value)
    }

    try {
      const response = await fetch('/api/run', {
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
      setProgress(100)
      setCharts(data.charts)
      // Share the freshly-generated figures with the static algorithm-detail
      // pages (same origin) so they show this run's charts instead of their
      // frozen defaults. Their inline scripts read this on load.
      try {
        window.localStorage.setItem('lifecycleCharts', JSON.stringify(data.charts))
      } catch (e) {
        console.warn('Could not cache charts for detail pages:', e)
      }
      setResult(data.sim)
    } catch (err) {
      console.error('Submit failed:', err)
      setError(err.message)
    } finally {
      clearInterval(timer)
      setLoading(false)
    }
  }

  return (
    <div className={`sim-panel sim-panel--${variant}${hidden ? ' sim-panel--hidden' : ''}`}>
      <div className="panel-form">
        <fieldset className="field-group">
          <legend>Data Presets</legend>
          <div className="preset-grid" role="group" aria-label="Persona presets">
            {PRESETS.map((p) => (
              <button
                type="button"
                key={p.id}
                className={`preset-pill${p.id === activePreset ? ' active' : ''}`}
                aria-pressed={p.id === activePreset}
                onClick={() => setActivePreset(p.id)}
              >
                <span className="preset-label">{p.label}</span>
                <span className="preset-subtitle">{p.subtitle}</span>
              </button>
            ))}
          </div>
        </fieldset>

        <form key={activePreset} method="post" onSubmit={handleSubmit}>
          {GROUPS.map((g) => {
            // Merge consecutive fields sharing a `combo` id into one block so
            // they stack together under a single shared description.
            const items = []
            for (const f of FIELDS.filter((x) => x.group === g.id)) {
              const last = items[items.length - 1]
              if (f.combo && last && last.combo === f.combo) {
                last.fields.push(f)
                if (!last.desc && f.comboDesc) last.desc = f.comboDesc
              } else if (f.combo) {
                items.push({ combo: f.combo, fields: [f], desc: f.comboDesc })
              } else {
                items.push({ field: f })
              }
            }

            const renderInput = (f) => (
              <input
                id={f.name}
                type="number"
                step="any"
                name={f.name}
                defaultValue={active.values[f.name] ?? f.def}
              />
            )

            return (
              <fieldset className="field-group" key={g.id}>
                <legend>{g.title}</legend>
                <div className="field-grid">
                  {items.map((item) =>
                    item.combo ? (
                      <div className="field field-combo" key={item.combo}>
                        {item.fields.map((f) => (
                          <div className="combo-row" key={f.name}>
                            <label htmlFor={f.name}>{f.label}</label>
                            {renderInput(f)}
                          </div>
                        ))}
                        {item.desc && <div className="field-desc">{item.desc}</div>}
                      </div>
                    ) : (
                      <div className="field" key={item.field.name}>
                        <label htmlFor={item.field.name}>{item.field.label}</label>
                        {renderInput(item.field)}
                        {item.field.desc && (
                          <div className="field-desc">{item.field.desc}</div>
                        )}
                      </div>
                    )
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
          })}

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Running…' : 'Submit'}
            </button>
            <a href="/algorithm_simple.html" target="_blank" rel="noopener noreferrer">
              <button type="button" className="btn btn-secondary">
                Simple Algorithm Details
              </button>
            </a>
            <a href="/algorithm.html" target="_blank" rel="noopener noreferrer">
              <button type="button" className="btn btn-secondary">
                Technical Algorithm Details
              </button>
            </a>
          </div>
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
            <div className="chart-grid">
              <figure className="chart">
                <img src={charts.lifecycle}
                     alt="Life-cycle profiles: consumption, wealth and income by age, average stock share by age, and profiles scaled by age-20 income" />
              </figure>
              <figure className="chart">
                <img src={charts.policy}
                     alt="Policy functions: optimal consumption and stock share versus cash-on-hand at ages 25, 45 and 65" />
              </figure>
              <figure className="chart chart-compact">
                <img src={charts.composition}
                     alt="Portfolio composition by age: mean stock and bond holdings, each with a ±1 standard deviation band showing the spread across households" />
              </figure>
            </div>
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
}

export default SimulationPanel
