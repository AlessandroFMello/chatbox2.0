import { useState, useEffect } from 'react'
import UserIdentityForm from './components/UserIdentityForm'
import { lookupConversation, createConversation, getConversation, type Conversation } from './services/api'

type IdentityStep = 'email' | 'name'

const SESSION_KEY = 'chatterbox_session'

export default function App() {
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [step, setStep] = useState<IdentityStep>('email')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Restore session from localStorage on mount
  useEffect(() => {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return
    const { conversationId } = JSON.parse(raw) as { conversationId: string }
    setIsLoading(true)
    getConversation(conversationId)
      .then(setConversation)
      .catch(() => localStorage.removeItem(SESSION_KEY))
      .finally(() => setIsLoading(false))
  }, [])

  // Persist session whenever conversation is set
  useEffect(() => {
    if (!conversation) return
    localStorage.setItem(SESSION_KEY, JSON.stringify({ conversationId: conversation.id }))
  }, [conversation])

  function handleSwitchUser() {
    localStorage.removeItem(SESSION_KEY)
    setConversation(null)
    setStep('email')
    setError(null)
  }

  async function handleLookup(email: string) {
    setIsLoading(true)
    setError(null)
    try {
      const found = await lookupConversation(email)
      if (found) {
        setConversation(found)
      } else {
        setStep('name')
      }
    } catch {
      setError('Não foi possível conectar à API. Tente novamente.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleCreate(name: string, email: string) {
    setIsLoading(true)
    setError(null)
    try {
      const created = await createConversation({ name, email })
      setConversation(created)
    } catch {
      setError('Erro ao criar conversa. Tente novamente.')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading && !conversation) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p className="text-gray-400 text-sm">Carregando…</p>
      </div>
    )
  }

  if (!conversation) {
    return (
      <>
        <UserIdentityForm
          step={step}
          isLoading={isLoading}
          onLookup={handleLookup}
          onCreate={handleCreate}
        />
        {error && (
          <p className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-red-100 text-red-700 text-sm px-4 py-2 rounded-lg shadow">
            {error}
          </p>
        )}
      </>
    )
  }

  // Placeholder — replaced by <ChatWindow> in Phase 9
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center gap-4">
      <p className="text-gray-600 text-sm">
        Olá, {conversation.user_name}! Chat em breve…
      </p>
      <button
        onClick={handleSwitchUser}
        className="text-xs text-indigo-600 hover:underline"
      >
        Trocar usuário
      </button>
    </div>
  )
}
