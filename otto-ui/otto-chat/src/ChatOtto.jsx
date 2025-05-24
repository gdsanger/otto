import { useState, useEffect, useRef } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export default function ChatOtto() {
  const [messages, setMessages] = useState([
    { role: 'system', content: 'Du bist Otto, ein Projekt-KI-Assistent.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

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

  return (
    <Card className="h-full flex flex-col">
      <CardContent className="flex-1 overflow-y-auto space-y-2 p-4">
        {messages.slice(1).map((m, i) => (
          <div
            key={i}
            className={`rounded-xl px-4 py-2 max-w-[80%] whitespace-pre-wrap ${
              m.role === 'user' ? 'ml-auto bg-primary text-white' : 'bg-muted text-muted-foreground'
            }`}
          >
            {m.content}
          </div>
        ))}
        <div ref={endRef} />
      </CardContent>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          sendMessage()
        }}
        className="flex gap-2 p-2 border-t"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Nachricht an Otto..."
          disabled={loading}
        />
        <Button type="submit" disabled={loading || !input.trim()}>
          ✈️
        </Button>
      </form>
    </Card>
  )
}
