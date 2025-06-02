import { useState, useEffect, useRef } from 'react'

export default function ChatOtto() {
  const [context, setContext] = useState('global')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [availableFunctions, setAvailableFunctions] = useState([])
  const [selectedFunction, setSelectedFunction] = useState('')
  const endRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    const ctx = window.ottoContext

    if (ctx?.id) {
      setContext(`${ctx.type}_${ctx.id}`)
    } else {
      const path = window.location.pathname
      let newContext = 'global'
      const projektMatch = path.match(/\/(projekt|project)\/([^\/]+)/)
      const aufgabeMatch = path.match(/\/aufgabe\/([^\/]+)/)
      const meetingMatch = path.match(/\/meeting\/([^\/]+)/)

      if (projektMatch) newContext = 'projekt_' + projektMatch[2]
      else if (aufgabeMatch) newContext = 'aufgabe_' + aufgabeMatch[1]
      else if (meetingMatch) newContext = 'meeting_' + meetingMatch[1]

      setContext(newContext)
    }
  }, [])

  useEffect(() => {
    const ctxInfo = window.ottoContext    
    const promptContext = ctxInfo
  ? `${ctxInfo.type} „Name: ${ctxInfo.name}“ (ID: ${ctxInfo.id}${
      ctxInfo.project_id ? `, project_id: ${ctxInfo.project_id}` : ''
    }${ctxInfo.requester_id ? `, requester_id: ${ctxInfo.requester_id}` : ''})`
  : context;

    const availableFunctions = ctxInfo?.gptFunctions?.length
      ? `Verfügbare Funktionen: ${ctxInfo.gptFunctions.join(", ")}.`
      : ""

    const extraContext = ctxInfo?.context ? ` Kontext: ${ctxInfo.context}` : ""

    const systemPrompt = {
      role: 'system',
      content: `Du bist Otto, ein Projekt-KI-Assistent. Gib strukturierte, klare Antworten in HTML oder Tabellenform. Nutze Listen und Zwischenüberschriften. Wir befinden uns im Kontext: ${promptContext}.${extraContext ? extraContext : ''} ${availableFunctions}`
    }

    const saved = localStorage.getItem('ottoChatMessages_' + context)
    setMessages(saved ? JSON.parse(saved) : [systemPrompt])
  }, [context])

  useEffect(() => {
    const ctxType = window.ottoContext?.type || 'global'
    fetch(`${window.location.origin}/template?type=${ctxType}`)
      .then(res => res.json())
      .then(data => setAvailableFunctions(data))
  }, [])

  const sendMessage = async () => {
    if (!input.trim()) return

    const ctxInfo = window.ottoContext    
   const promptContext = ctxInfo
  ? `${ctxInfo.type} „Name: ${ctxInfo.name}“ (ID: ${ctxInfo.id}${
      ctxInfo.project_id ? `, Projekt-ID: ${ctxInfo.project_id}` : ''
    }${ctxInfo.requester_id ? `, Requester-ID: ${ctxInfo.requester_id}` : ''})`
  : context;

    const extraContext = ctxInfo?.context ? ` Kontext: ${ctxInfo.context}` : ""

    const systemPrompt = {
      role: 'system',
      content: `Du bist Otto, ein Projekt-KI-Assistent. Gib strukturierte, klare Antworten in HTML oder Tabellenform. Nutze Listen und Zwischenüberschriften. Wir befinden uns im Kontext ${promptContext}.${extraContext ? extraContext : ''}`
    }

    const userContent = selectedFunction
      ? `⤷ Verwende bitte folgende Funktion für diese Nachricht: ${selectedFunction}\n\n${input}`
      : input

    const fullMessages = [systemPrompt, ...messages.slice(1), { role: 'user', content: userContent }]
    setMessages([...messages, { role: 'user', content: input }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: fullMessages })
      })
      const data = await res.json()
      if (data.action === 'open_project_form' && window.ottoUI?.openProjectForm) {
        window.ottoUI.openProjectForm(data.values || {})
      } else if (data.action === 'open_task_form' && window.ottoUI?.openTaskForm) {
        window.ottoUI.openTaskForm(data.values || {})
      }
      setMessages([...messages, { role: 'user', content: input }, { role: 'assistant', content: data.reply }])
    } catch {
      setMessages([...messages, { role: 'user', content: input }, { role: 'assistant', content: 'Fehler bei der Kommunikation mit Otto.' }])
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
    <div className="d-flex flex-column border rounded overflow-hidden h-100">
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
            {/<\/?[a-z][\s\S]*>/i.test(m.content)
              ? <div dangerouslySetInnerHTML={{ __html: m.content }} />
              : m.content}
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
        <div className="d-flex flex-column gap-2">
          <select
            className="form-select"
            value={selectedFunction}
            onChange={(e) => setSelectedFunction(e.target.value)}
          >
            <option value="">Funktion auswählen (optional)</option>
            {availableFunctions.map((fn) => (
              <option key={fn} value={fn}>{fn}</option>
            ))}
          </select>

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
        </div>
      </form>
    </div>
  )
}
