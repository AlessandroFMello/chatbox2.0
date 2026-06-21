const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface Conversation {
  id: string
  user_name: string
  user_email: string
  messages: Message[]
  created_at: string
  updated_at: string
}

class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) throw new ApiError(`API error ${res.status}`, res.status)
  if (res.status === 204) return null as T
  return res.json() as Promise<T>
}

/** Check whether a conversation already exists for the given email.
 *  First step of the two-step identity flow. Returns null on 404. */
export async function lookupConversation(email: string): Promise<Conversation | null> {
  try {
    return await apiFetch<Conversation>(`/conversations/lookup?email=${encodeURIComponent(email)}`)
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null
    throw err
  }
}

/** Create a new conversation. Only call after lookupConversation returns null. */
export async function createConversation(params: { name: string; email: string }): Promise<Conversation> {
  return apiFetch<Conversation>('/conversations', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

/** Fetch a conversation and its full message history by ID. */
export async function getConversation(id: string): Promise<Conversation> {
  return apiFetch<Conversation>(`/conversations/${id}`)
}

/** Persist a user message. Call this before triggering the WebSocket stream. */
export async function sendUserMessage(id: string, content: string): Promise<Message> {
  return apiFetch<Message>(`/conversations/${id}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  })
}

/** Delete all messages from a conversation without removing the user record.
 *  Triggered by the "Nova conversa" button. */
export async function clearMessages(id: string): Promise<void> {
  await apiFetch<null>(`/conversations/${id}/messages`, { method: 'DELETE' })
}
