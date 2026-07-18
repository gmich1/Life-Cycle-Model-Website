import React from 'react'
import './Inputs.css'
import SimulationPanel from './SimulationPanel'

function Inputs() {
  return (
    <div className="inputs-page">
      <div className="inputs-header">
        <h1>Life-Cycle Portfolio Model</h1>
        <p>Set the model parameters below and run the simulation.</p>
      </div>
      <SimulationPanel variant="blue" />
    </div>
  )
}

export default Inputs
