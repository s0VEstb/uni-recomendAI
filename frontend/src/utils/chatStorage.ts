// chatStorage.ts — localStorage-based chat history manager

export interface ChatMessage {
    role: 'user' | 'assistant'
    text: string
    timestamp: string
}

export interface ChatSession {
    id: string
    title: string
    messages: ChatMessage[]
    universityId?: number
    universityName?: string
    createdAt: string
    updatedAt: string
}

const KEY = 'chat_history'
const MAX_CHATS = 50

function genId(): string {
    try {
        return crypto.randomUUID()
    } catch {
        return Date.now().toString(36) + Math.random().toString(36).slice(2)
    }
}

export function loadChats(): ChatSession[] {
    try {
        const raw = localStorage.getItem(KEY)
        return raw ? (JSON.parse(raw) as ChatSession[]) : []
    } catch {
        return []
    }
}

function saveChats(chats: ChatSession[]): void {
    try {
        localStorage.setItem(KEY, JSON.stringify(chats))
    } catch {
        // storage full — ignore
    }
}

export function createChat(opts?: { universityId?: number; universityName?: string }): ChatSession {
    const now = new Date().toISOString()
    return {
        id: genId(),
        title: 'Новый чат',
        messages: [],
        universityId: opts?.universityId,
        universityName: opts?.universityName,
        createdAt: now,
        updatedAt: now,
    }
}

export function saveChat(session: ChatSession): void {
    const chats = loadChats().filter((c) => c.id !== session.id)
    const updated = [{ ...session, updatedAt: new Date().toISOString() }, ...chats]
    saveChats(updated.slice(0, MAX_CHATS))
}

export function deleteChat(id: string): void {
    saveChats(loadChats().filter((c) => c.id !== id))
}

export function clearAllChats(): void {
    localStorage.removeItem(KEY)
}

export function addMessage(session: ChatSession, msg: Omit<ChatMessage, 'timestamp'>): ChatSession {
    const message: ChatMessage = { ...msg, timestamp: new Date().toISOString() }
    const messages = [...session.messages, message]
    // Auto-title from first user message
    let title = session.title
    if (title === 'Новый чат' && msg.role === 'user') {
        title = msg.text.slice(0, 50) + (msg.text.length > 50 ? '…' : '')
    }
    return { ...session, messages, title }
}
