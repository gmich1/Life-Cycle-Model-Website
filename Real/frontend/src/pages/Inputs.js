import React, { useState } from 'react'
import './Inputs.css'
import SimulationPanel from './SimulationPanel'

function Inputs() {
  const [instances, setInstances] = useState(1)
  const [redEverShown, setRedEverShown] = useState(false)

  function setCount(n) {
    setInstances(n)
    if (n === 2) setRedEverShown(true)
  }

  const twoUp = instances === 2

  return (
    <div className="inputs-page">
      <div className="inputs-header">
        <h1>Life-Cycle Portfolio Model</h1>
        <p>Set the model parameters below and run the simulation.</p>
      </div>

      <div className="instance-toggle" role="group" aria-label="Number of forms">
        {[1, 2].map((n) => (
          <button
            key={n}
            type="button"
            className={`toggle-pill${instances === n ? ' active' : ''}`}
            aria-pressed={instances === n}
            onClick={() => setCount(n)}
          >
            {n === 1 ? '1 form' : '2 forms'}
          </button>
        ))}
      </div>

      <div className={`compare-grid${twoUp ? ' compare-grid--two' : ''}`}>
        <SimulationPanel variant="blue" />
        {(twoUp || redEverShown) && (
          <SimulationPanel variant="red" hidden={!twoUp} />
        )}
      </div>
    </div>
  )
}

export default Inputs
