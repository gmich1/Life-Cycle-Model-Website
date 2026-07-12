const express = require('express')
const app = express()

const PORT = 5000

// Parse incoming JSON request bodies (populates req.body)
app.use(express.json())

// Allow the React dev server (localhost:3000) to call this API (CORS)
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', 'http://localhost:3000')
  res.header('Access-Control-Allow-Headers', 'Content-Type')
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200) // respond to the browser's preflight check
  }
  next()
})

// The model parameters the form is expected to send.
const FIELD_NAMES = [
  'tb', 'tr', 'td', 'rho', 'delta', 'psi', 'r', 'mu', 'sigr', 'smay',
  'smav', 'corr_v', 'corr_y', 'ret_fac', 'aa', 'b1', 'b2', 'b3', 'ncash',
  'na', 'nc', 'n', 'maxcash', 'mincash', 'nsim',
]

// The form submits here
app.post('/api/inputs', (req, res) => {
  // Validate every field: present and a finite number.
  const received = []
  for (const name of FIELD_NAMES) {
    const value = Number(req.body[name])
    if (req.body[name] === undefined || req.body[name] === '' || Number.isNaN(value)) {
      return res.status(400).json({ error: `${name} is required and must be a number` })
    }
    received.push({ name, value })
  }

  console.log('Received inputs:', received)

  // Save inputs to inputs variable, send response
  const inputs = {received}
  res.status(201).json(response)


  /* run the model shit here and then when yoiu get the results pass them back into the frontend*/
})

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`)
})
