import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx' // Dòng này yêu cầu App.jsx phải có 'export default'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)