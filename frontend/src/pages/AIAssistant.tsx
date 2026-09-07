import { useState, useRef, useEffect } from 'react'
import { PageWrapper, Button } from '../components/ui'
import { Send, MessageCircle } from 'lucide-react'
import type { ChatMessage } from '../types'
import { sendChatMessage } from '../services/chatService'

const welcomeMessage: ChatMessage = {
  id: 'msg-0',
  role: 'assistant',
  content: `Hello, I'm your HealthOS AI Assistant, powered by Qwen. I have access to your health profile, lab results, nutrition, hydration, and sleep data.\n\nYou can ask me questions like:\n• "Why am I feeling tired?"\n• "What does my hemoglobin result mean?"\n• "How can I improve my Vitamin D levels?"\n\nI provide health education and information — not medical diagnoses. Always consult a qualified healthcare professional for medical advice.`,
  timestamp: new Date().toISOString(),
}

function renderContent(text: string) {
  return text.split('\n').map((line, i) => {
    if (line === '') return <div key={i} className="mt-2" />
    // Replace **...**  with <strong> inline — handles headers and mid-sentence bold
    const parts: React.ReactNode[] = []
    const re = /\*\*(.+?)\*\*/g
    let last = 0
    let match
    while ((match = re.exec(line)) !== null) {
      if (match.index > last) parts.push(line.slice(last, match.index))
      parts.push(<strong key={match.index} className="text-text-primary">{match[1]}</strong>)
      last = re.lastIndex
    }
    if (last < line.length) parts.push(line.slice(last))
    // Italic *...*  (but not **)
    const italicRe = /(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g
    const finalParts: React.ReactNode[] = []
    parts.forEach((part, pi) => {
      if (typeof part !== 'string') { finalParts.push(part); return }
      let s = part, iLast = 0
      let iMatch
      while ((iMatch = italicRe.exec(s)) !== null) {
        if (iMatch.index > iLast) finalParts.push(s.slice(iLast, iMatch.index))
        finalParts.push(<em key={`${pi}-${iMatch.index}`} className="text-text-secondary">{iMatch[1]}</em>)
        iLast = italicRe.lastIndex
      }
      if (iLast < s.length) finalParts.push(s.slice(iLast))
    })
    return <p key={i}>{finalParts.length ? finalParts : parts}</p>
  })
}

function ProviderBadge({ provider }: { provider?: string }) {
  if (!provider) return null
  const isQwen = provider === 'qwen'
  return (
    <span className={[
      'text-[10px] font-medium px-1.5 py-0.5 rounded-full border ml-1',
      isQwen
        ? 'text-accent bg-accent/10 border-accent/20'
        : 'text-text-muted bg-bg-elevated border-border-subtle',
    ].join(' ')}>
      {isQwen ? 'Qwen' : 'HealthOS'}
    </span>
  )
}

interface ExtendedMessage extends ChatMessage {
  provider?: string
}

export function AIAssistant() {
  const [messages, setMessages] = useState<ExtendedMessage[]>([welcomeMessage])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    setError('')

    const userMsg: ExtendedMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }
    const currentInput = input
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    // Send last 6 messages as history (3 exchanges) to bound token usage
    const history = messages
      .slice(-6)
      .map(m => ({ role: m.role, content: m.content }))

    try {
      const result = await sendChatMessage(currentInput, history)
      const assistantMsg: ExtendedMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: result.reply,
        timestamp: new Date().toISOString(),
        provider: result.provider,
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch {
      setError('Unable to reach the AI service. Please check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageWrapper
      title="AI Health Assistant"
      subtitle="Ask questions about your health data"
    >
      <div className="flex flex-col h-[calc(100vh-180px)]">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="flex flex-col items-center mr-2 shrink-0">
                  <div className="w-7 h-7 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center mt-1">
                    <span className="text-primary text-[10px] font-bold">AI</span>
                  </div>
                  {msg.provider && <ProviderBadge provider={msg.provider} />}
                </div>
              )}
              <div className={[
                'max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed',
                msg.role === 'user'
                  ? 'bg-primary text-white rounded-br-sm'
                  : 'bg-bg-surface border border-border text-text-primary rounded-bl-sm',
              ].join(' ')}>
                {renderContent(msg.content)}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="w-7 h-7 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0 mr-2 mt-1">
                <span className="text-primary text-[10px] font-bold">AI</span>
              </div>
              <div className="bg-bg-surface border border-border rounded-xl px-4 py-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse [animation-delay:300ms]" />
              </div>
            </div>
          )}

          {error && (
            <div className="bg-danger/10 border border-danger/30 rounded-xl px-4 py-3 text-danger text-sm">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Quick prompts */}
        <div className="flex gap-2 flex-wrap mb-3">
          {[
            'Why am I feeling tired?',
            'Explain my hemoglobin result',
            'How can I improve my Vitamin D?',
          ].map(q => (
            <button
              key={q}
              onClick={() => { setInput(q) }}
              className="text-xs bg-bg-surface border border-border text-text-secondary rounded-full px-3 py-1.5 hover:border-primary hover:text-primary transition-colors"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-2">
          <div className="flex-1 flex items-center gap-2 bg-bg-surface border border-border rounded-xl px-4 py-3 focus-within:border-primary transition-colors">
            <MessageCircle size={14} className="text-text-muted shrink-0" />
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask about your health data..."
              className="flex-1 bg-transparent text-sm text-text-primary placeholder-text-muted outline-none"
            />
          </div>
          <Button onClick={handleSend} disabled={!input.trim() || loading}>
            <Send size={14} />
          </Button>
        </div>

        <p className="text-text-muted text-xs text-center mt-2">
          AI responses are for educational purposes only. Not a substitute for professional medical advice.
        </p>
      </div>
    </PageWrapper>
  )
}
