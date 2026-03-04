import { useState, useRef, useEffect, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import { chatStream, chatHistory, type ChatSessionData, type ChatMessageData } from '../api/client'
import styles from './Chat.module.css'

interface LocalMessage {
  role: 'user' | 'assistant'
  text: string
}

export default function Chat() {
  const location = useLocation()
  const locState = location.state as { universityId?: number; universityName?: string } | null

  // Sidebar
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatList, setChatList] = useState<ChatSessionData[]>([])
  const [activeSession, setActiveSession] = useState<ChatSessionData | null>(null)
  const activeSessionRef = useRef<ChatSessionData | null>(null)

  // Messages displayed in UI (loaded from server or built live)
  const [messages, setMessages] = useState<LocalMessage[]>([])
  const [streamingText, setStreamingText] = useState('')
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [listLoading, setListLoading] = useState(true)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const streamedRef = useRef('')

  // Keep ref in sync with state
  useEffect(() => {
    activeSessionRef.current = activeSession
  }, [activeSession])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingText, scrollToBottom])

  // ── Load session list on mount ──────────────────────────────
  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const res = await chatHistory.list()
        if (cancelled) return
        setChatList(res.sessions)

        if (locState?.universityId) {
          // Context chat: create new session with university context
          const session = await chatHistory.create({
            title: locState.universityName ? `Чат о ${locState.universityName}` : 'Новый чат',
            university_id: locState.universityId,
          })
          if (!cancelled) {
            setActiveSession(session)
            setMessages([])
            setChatList((prev) => [session, ...prev.filter((s) => s.id !== session.id)])
          }
        } else if (res.sessions.length > 0) {
          // Load most recent session
          const detail = await chatHistory.get(res.sessions[0].id)
          if (!cancelled) {
            setActiveSession(res.sessions[0])
            setMessages(detail.messages.map((m) => ({ role: m.role, text: m.content })))
          }
        }
        // else: no sessions, start empty
      } catch (e) {
        if (!cancelled) setError('Не удалось загрузить историю чатов')
      } finally {
        if (!cancelled) setListLoading(false)
      }
    }
    init()
    return () => { cancelled = true }
  }, [])

  // ── Send message ────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setError('')

    // Ensure we have an active session (create if first message)
    let session = activeSessionRef.current
    if (!session) {
      try {
        session = await chatHistory.create({
          title: q.slice(0, 50),
          university_id: locState?.universityId ?? null,
        })
        setActiveSession(session)
        setChatList((prev) => [session!, ...prev])
      } catch {
        setError('Не удалось создать сессию чата')
        return
      }
    }

    // Optimistically add user message to UI
    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setStreamingText('')
    setLoading(true)
    streamedRef.current = ''

    // Save user message to server (fire-and-forget, no await)
    chatHistory.addMessage(session.id, 'user', q).catch(() => {
      /* non-critical: streaming still works */
    })

    // Auto-title on first message (if still "Новый чат")
    if (session.title === 'Новый чат' && q.length > 0) {
      const newTitle = q.slice(0, 50) + (q.length > 50 ? '…' : '')
      chatHistory.rename(session.id, newTitle).then((updated) => {
        setActiveSession(updated)
        setChatList((prev) => prev.map((s) => (s.id === updated.id ? updated : s)))
      }).catch(() => { /* ignore */ })
    }

    // Stream response
    await chatStream(
      q,
      { university_id: session.university_id ?? undefined, top_k: 4 },
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

          // Save assistant message to server
          const sess = activeSessionRef.current
          if (sess) {
            chatHistory.addMessage(sess.id, 'assistant', fullText).catch(() => { /* ignore */ })
            // Refresh list to update updatedAt order
            chatHistory.list().then((res) => setChatList(res.sessions)).catch(() => { /* ignore */ })
          }
        },
        onError: (err) => {
          setError(err.message)
          setLoading(false)
        },
      }
    )
  }

  // ── Sidebar actions ─────────────────────────────────────────
  const handleNewChat = async () => {
    setSidebarOpen(false)
    setActiveSession(null)
    setMessages([])
    setStreamingText('')
    setError('')
  }

  const handleSelectChat = async (session: ChatSessionData) => {
    setSidebarOpen(false)
    setStreamingText('')
    setError('')
    setActiveSession(session)
    try {
      const detail = await chatHistory.get(session.id)
      setMessages(detail.messages.map((m: ChatMessageData) => ({ role: m.role, text: m.content })))
    } catch {
      setMessages([])
    }
  }

  const handleDeleteChat = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Удалить этот чат?')) return
    try {
      await chatHistory.delete(id)
      const res = await chatHistory.list()
      setChatList(res.sessions)
      if (activeSession?.id === id) {
        setActiveSession(null)
        setMessages([])
      }
    } catch {
      setError('Не удалось удалить чат')
    }
  }

  const handleClearAll = async () => {
    if (!confirm('Удалить всю историю чатов?')) return
    try {
      await Promise.all(chatList.map((s) => chatHistory.delete(s.id)))
      setChatList([])
      setActiveSession(null)
      setMessages([])
    } catch {
      setError('Не удалось очистить историю')
    }
  }

  // ── Voice input ─────────────────────────────────────────────
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
    <div className={styles.chatLayout}>
      {/* ── Sidebar overlay (mobile) ── */}
      {sidebarOpen && (
        <div className={styles.overlay} onClick={() => setSidebarOpen(false)} />
      )}

      {/* ── Sidebar ── */}
      <aside className={`${styles.sidebar} ${sidebarOpen ? styles.sidebarOpen : ''}`}>
        <div className={styles.sidebarHeader}>
          <span className={styles.sidebarTitle}>История чатов</span>
          <button type="button" className={styles.newChatBtn} onClick={handleNewChat}>
            + Новый чат
          </button>
        </div>

        <ul className={styles.chatList}>
          {listLoading && <li className={styles.emptySidebar}>Загрузка…</li>}
          {!listLoading && chatList.length === 0 && (
            <li className={styles.emptySidebar}>Истории нет</li>
          )}
          {chatList.map((chat) => (
            <li
              key={chat.id}
              className={`${styles.chatItem} ${activeSession?.id === chat.id ? styles.chatItemActive : ''}`}
              onClick={() => handleSelectChat(chat)}
            >
              <div className={styles.chatItemContent}>
                <span className={styles.chatItemTitle}>{chat.title}</span>
                <span className={styles.chatItemDate}>
                  {new Date(chat.updated_at).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' })}
                </span>
              </div>
              <button
                type="button"
                className={styles.deleteChatBtn}
                onClick={(e) => handleDeleteChat(chat.id, e)}
                title="Удалить чат"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>

        {chatList.length > 0 && (
          <div className={styles.sidebarFooter}>
            <button type="button" className={styles.clearBtn} onClick={handleClearAll}>
              🗑 Очистить историю
            </button>
          </div>
        )}
      </aside>

      {/* ── Main chat area ── */}
      <div className={styles.chatMain}>
        {/* Chat header */}
        <div className={styles.chatHeader}>
          <button
            type="button"
            className={styles.hamburger}
            onClick={() => setSidebarOpen((o) => !o)}
            aria-label="Открыть историю чатов"
          >
            ☰
          </button>
          <h1 className={styles.chatTitle}>
            Чат с ИИ-ассистентом
            {activeSession?.university_id && locState?.universityName && (
              <span className={styles.context}> · {locState.universityName}</span>
            )}
          </h1>
        </div>

        {/* Messages */}
        <div className={styles.messages}>
          {messages.length === 0 && !streamingText && (
            <div className={styles.placeholder}>
              <span className={styles.placeholderIcon}>💬</span>
              <p className={styles.placeholderText}>Задайте вопрос о поступлении, программах или стоимости обучения.</p>
            </div>
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

        {/* Error */}
        {error && <p className={styles.error}>{error}</p>}

        {/* Input area */}
        <form onSubmit={handleSubmit} className={styles.inputArea}>
          <div className={styles.inputWrap}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Введите вопрос…"
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
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                  <line x1="8" y1="22" x2="16" y2="22" />
                </svg>
              )}
            </button>
            <button type="submit" disabled={loading || !input.trim()} className={styles.sendButton}>
              {loading ? (
                <span className={styles.sendLoading}>…</span>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
