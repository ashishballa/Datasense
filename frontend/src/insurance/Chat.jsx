import { useState, useRef, useEffect } from 'react'
import { sendChatStream } from './api'

export default function Chat({ token, onHistoryChange }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! Ask me anything about home insurance — coverage, deductibles, claims, or your policy options.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(e) {
    e.preventDefault()
    if (!input.trim() || loading) return
    const userMsg = { role: 'user', content: input }
    const updated = [...messages, userMsg]
    setMessages(updated)
    setInput('')
    setLoading(true)
    // Add empty assistant message to stream into
    const withPlaceholder = [...updated, { role: 'assistant', content: '' }]
    setMessages(withPlaceholder)
    try {
      let fullText = ''
      const newSessionId = await sendChatStream(token, input, sessionId, (token) => {
        fullText += token
        setMessages(prev => {
          const copy = [...prev]
          copy[copy.length - 1] = { role: 'assistant', content: fullText }
          return copy
        })
      })
      if (!sessionId) setSessionId(newSessionId)
      const final = [...updated, { role: 'assistant', content: fullText }]
      onHistoryChange(final.slice(1))
    } catch (err) {
      setMessages([...updated, { role: 'assistant', content: `Error: ${err.message}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ins-chat">
      <div className="ins-chat-header">Insurance Assistant</div>
      <div className="ins-chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`ins-msg ins-msg-${m.role}`}>
            <span className="ins-msg-label">{m.role === 'user' ? 'You' : 'Assistant'}</span>
            <p dangerouslySetInnerHTML={{ __html: m.content
              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              .replace(/\*(.*?)\*/g, '$1')
              .replace(/^[*-] /gm, '• ')
              .replace(/\n/g, '<br/>')
            }} />
          </div>
        ))}
        {loading && (
          <div className="ins-msg ins-msg-assistant">
            <span className="ins-msg-label">Assistant</span>
            <p className="ins-typing">Thinking…</p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} className="ins-chat-input">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask about coverage, deductibles, claims…"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>Send</button>
      </form>
    </div>
  )
}
