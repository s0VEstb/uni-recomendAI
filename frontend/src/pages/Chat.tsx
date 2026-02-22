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
  const [error, setError] = useState('')
  const [isListening, setIsListening] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const streamedRef = useRef('')

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingText])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setError('')
    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setStreamingText('')
    setLoading(true)

    streamedRef.current = ''
    await chatStream(
      q,
      { university_id: state?.universityId, top_k: 4 },
      {
        onChunk: (text) => {
          streamedRef.current += text
          setStreamingText(streamedRef.current)
        },
        onDone: () => {
          const fullText = streamedRef.current
          setMessages((prev) => [...prev, { role: 'assistant', text: fullText }])
          setStreamingText('')
          streamedRef.current = ''
          setLoading(false)
        },
        onError: (err) => {
          setError(err.message)
          setLoading(false)
        },
      }
    )
  }

  const startListening = () => {
    setError('')
    const SpeechRecognitionAPI = (window as unknown as { SpeechRecognition?: typeof SpeechRecognition; webkitSpeechRecognition?: typeof SpeechRecognition }).SpeechRecognition
      || (window as unknown as { webkitSpeechRecognition?: typeof SpeechRecognition }).webkitSpeechRecognition
    if (!SpeechRecognitionAPI) {
      setError('Распознавание речи не поддерживается в этом браузере')
      return
    }
    const recognition = new SpeechRecognitionAPI()
    recognition.lang = 'ru-RU'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onresult = (e: SpeechRecognitionEvent) => {
      const result = e.results[e.results.length - 1]
      if (!result?.length) return
      const alternative = result[0]
      const transcript = typeof alternative === 'object' && alternative !== null && 'transcript' in alternative
        ? (alternative as { transcript: string }).transcript
        : String(alternative)
      if (transcript?.trim()) {
        setInput((prev) => (prev ? `${prev} ${transcript.trim()}` : transcript.trim()))
      }
    }
    recognition.onerror = (e: { error: string }) => {
      if (e.error !== 'aborted') setError(`Ошибка: ${e.error}`)
      setIsListening(false)
    }
    recognition.onend = () => setIsListening(false)
    recognition.start()
    recognitionRef.current = recognition
    setIsListening(true)
  }

  const stopListening = () => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>
        Чат с ИИ-ассистентом
        {state?.universityName && (
          <span className={styles.context}> · {state.universityName}</span>
        )}
      </h1>

      <div className={styles.messages}>
        {messages.length === 0 && !streamingText && (
          <p className={styles.placeholder}>
            Задайте вопрос о поступлении, программах или стоимости обучения.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? styles.userMsg : styles.assistantMsg}>
            {m.text}
          </div>
        ))}
        {streamingText && (
          <div className={styles.assistantMsg}>
            {streamingText}
            <span className={styles.cursor}>▋</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && <p className={styles.error}>{error}</p>}

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputWrap}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Введите вопрос..."
            className={styles.input}
            disabled={loading}
          />
          <button
            type="button"
            className={`${styles.micButton} ${isListening ? styles.micButtonActive : ''}`}
            onClick={isListening ? stopListening : startListening}
            title={isListening ? 'Остановить' : 'Голосовой ввод'}
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
          {loading ? 'Отправка…' : 'Отправить'}
        </button>
      </form>
    </div>
  )
}
