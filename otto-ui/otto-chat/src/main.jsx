import React from 'react'
import ReactDOM from 'react-dom/client'
import ChatOtto from './ChatOtto'

document.addEventListener('DOMContentLoaded', () => {
  const rootElement = document.getElementById('otto-chat')
  if (rootElement) {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <ChatOtto />
      </React.StrictMode>
    )
  }
})