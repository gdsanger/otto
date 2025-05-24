import { useState, useEffect, useRef } from 'react'

export default function ChatOtto() {
  const [context, setContext] = useState('global')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    const path = window.location.pathname
    let newContext = 'global'
    const projektMatch = path.match(/\/(projekt|project)\/([^\/]+)/)
    const aufgabeMatch = path.match(/\/aufgabe\/([^\/]+)/)
    const meetingMatch = path.match(/\/meeting\/([^\/]+)/)

    if (projektMatch) newContext = 'projekt_' + projektMatch[2]
    else if (aufgabeMatch) newContext = 'aufgabe_' + aufgabeMatch[1]
    else if (meetingMatch) newContext = 'meeting_' + meetingMatch[1]

    setContext(newContext)
  }, [])

  useEffect(() => {
    const ctxInfo = window.ottoContext
    const promptContext = ctxInfo
      ? `${ctxInfo.type} „${ctxInfo.name}“ (ID: ${ctxInfo.id})`
      : context

    const systemPrompt = {
      role: 'system',
      content: `Du bist Otto, ein Projekt-KI-Assistent. Wir befinden uns im Kontext ${promptContext}.`
    }

    const saved = localStorage.getItem('ottoChatMessages_' + context)
    setMessages(saved ? JSON.parse(saved) : [systemPrompt])
  }, [context])

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
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (context && messages.length > 0) {
      localStorage.setItem('ottoChatMessages_' + context, JSON.stringify(messages))
    }
  }, [messages, context])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const newHeight = Math.min(textareaRef.current.scrollHeight, 160)
      textareaRef.current.style.height = `${newHeight}px`
    }
  }, [input])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="d-flex flex-column border rounded overflow-hidden vh-100">
      <div className="flex-grow-1 overflow-auto p-3 bg-white">
        {messages.slice(1).map((m, i) => (
          <div
            key={i}
            className={`mb-2 p-2 rounded ${
              m.role === 'user'
                ? 'bg-light text-end ms-auto w-75'
                : 'bg-body-secondary text-start w-75'
            }`}
          >
            {m.content}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          sendMessage()
        }}
        className="border-top bg-white p-3"
      >
        <div className="d-flex align-items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nachricht an Otto..."
            disabled={loading}
            rows={1}
            className="form-control me-2"
            style={{ resize: 'none' }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn btn-success"
          >
            ✈️
          </button>
        </div>
      </form>
    </div>
  )
}
