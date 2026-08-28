import { useState, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { chatStream } from '../api/client'
import styles from './Chat.module.css'

export default function Chat() {
  const location = useLocation()
  const state = location.state as { universityId?: number; universityName?: string } | null
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; text: string }[]>([])
  const [streamingText, setStreamingText] = useState('')
  const [loading, setLoading] = useState(false)
  const [typing, setTyping] = useState(false)
  const [error, setError] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [interimText, setInterimText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const streamedRef = useRef('')

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })

  useEffect(() => { scrollToBottom() }, [messages, streamingText, typing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setInterimText('')
    setError('')
    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setStreamingText('')
    setLoading(true)
    setTyping(true)
    streamedRef.current = ''

    await chatStream(q, { university_id: state?.universityId, top_k: 4 }, {
      onChunk: (text) => {
        setTyping(false)
        streamedRef.current += text
        setStreamingText(streamedRef.current)
      },
      onDone: () => {
        setMessages((prev) => [...prev, { role: 'assistant', text: streamedRef.current }])
        setStreamingText('')
        streamedRef.current = ''
        setLoading(false)
        setTyping(false)
      },
      onError: (err) => {
        setError(err.message)
        setLoading(false)
        setTyping(false)
      },
    })
  }

  const startListening = () => {
    setError('')
    const API =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition

    if (!API) {
      setError('Голосовой ввод не поддерживается. Используйте Chrome или Edge.')
      return
    }
    if (recognitionRef.current) recognitionRef.current.abort()

    const r = new API()
    r.lang = 'ru-RU'
    r.continuous = true
    r.interimResults = true

    r.onresult = (e: SpeechRecognitionEvent) => {
      let interim = '', final = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = (e.results[i][0] as any).transcript || ''
        e.results[i].isFinal ? (final += t) : (interim += t)
      }
      if (final.trim()) {
        setInput((p) => p ? `${p} ${final.trim()}` : final.trim())
        setInterimText('')
      } else { setInterimText(interim) }
    }

    r.onerror = (e: any) => {
      if (e.error === 'not-allowed') setError('Доступ к микрофону запрещён. Разрешите в настройках браузера.')
      else if (e.error !== 'aborted' && e.error !== 'no-speech') setError(`Ошибка: ${e.error}`)
      setIsListening(false); setInterimText('')
    }
    r.onend = () => { setIsListening(false); setInterimText('') }
    r.start()
    recognitionRef.current = r
    setIsListening(true)
  }

  const stopListening = () => {
    recognitionRef.current?.stop()
    setIsListening(false)
    setInterimText('')
  }

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>
        Чат с ИИ-ассистентом
        {state?.universityName && <span className={styles.context}> · {state.universityName}</span>}
      </h1>

      <div className={styles.messages}>
        {messages.length === 0 && !streamingText && !typing && (
          <p className={styles.placeholder}>Задайте вопрос о поступлении, программах или стоимости обучения.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? styles.userMsg : styles.assistantMsg}>{m.text}</div>
        ))}

        {typing && !streamingText && (
          <div className={`${styles.assistantMsg} ${styles.typingMsg}`}>
            <span className={styles.typingDots}><span /><span /><span /></span>
          </div>
        )}

        {streamingText && (
          <div className={styles.assistantMsg}>
            {streamingText}<span className={styles.cursor}>▋</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && <p className={styles.error}>{error}</p>}
      {isListening && interimText && <p className={styles.interimText}>🎤 {interimText}</p>}

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputWrap}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isListening ? 'Говорите...' : 'Введите вопрос...'}
            className={`${styles.input} ${isListening ? styles.inputListening : ''}`}
            disabled={loading}
          />
          <button
            type="button"
            className={`${styles.micButton} ${isListening ? styles.micButtonActive : ''}`}
            onClick={isListening ? stopListening : startListening}
            title={isListening ? 'Остановить запись' : 'Голосовой ввод (Chrome/Edge)'}
            aria-label={isListening ? 'Остановить запись' : 'Голосовой ввод'}
          >
            {isListening ? (
              <svg className={styles.micIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              <svg className={styles.micIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </svg>
            )}
          </button>
        </div>
        <button type="submit" disabled={loading || !input.trim()} className={styles.submit}>
          {loading ? 'Ответ…' : 'Отправить'}
        </button>
      </form>
    </div>
  )
}