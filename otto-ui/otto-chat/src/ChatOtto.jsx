// ChatOtto.jsx – Bootstrap-Version
import React, { useState, useEffect, useRef } from 'react'

export default function ChatOtto() {
  const [messages, setMessages] = useState([
    { role: 'system', content: 'Du bist Otto, ein Projekt-KI-Assistent.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const sendMessage = async () => {
    if (!input.trim()) return

    const newMessages = [...messages, { role: 'user', content: input }]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages })
      })
      const data = await res.json()
      setMessages([...newMessages, { role: 'assistant', content: data.reply }])
    } catch {
      setMessages([...newMessages, { role: 'assistant', content: 'Fehler bei der Kommunikation mit Otto.' }])
    }

    setLoading(false)
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage()
    }
  }

  return (
    <div className="card shadow-sm h-100">
      <div className="card-header bg-primary text-white">
        Chat mit Otto
      </div>
      <div className="card-body overflow-auto" style={{ maxHeight: '300px' }}>
        <ul className="list-group list-group-flush">
          {messages.slice(1).map((m, i) => (
            <li key={i} className="list-group-item">
              <strong>{m.role}:</strong> {m.content}
            </li>
          ))}
          <div ref={messagesEndRef} />
        </ul>
      </div>
      <div className="card-footer">
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            placeholder="Nachricht eingeben..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <button className="btn btn-primary" onClick={sendMessage} disabled={loading}>
            ✈️
          </button>
        </div>
      </div>
    </div>
  )
}