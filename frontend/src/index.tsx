import React from 'react'
import ReactDOM from 'react-dom/client'
import SteelDashboard from './components/SteelDashboard'
import './index.css'

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
)

root.render(
  <React.StrictMode>
    <SteelDashboard />
  </React.StrictMode>
)
