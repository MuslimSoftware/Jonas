import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { ThemeProvider } from '@jonas/shared/src/theme/ThemeContext'
import { BrowserRouter } from 'react-router-dom'
import { WebStorage } from './lib/WebStorage'

import './index.css'

const webStorage = new WebStorage()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider storage={webStorage}>
        <App />
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
) 