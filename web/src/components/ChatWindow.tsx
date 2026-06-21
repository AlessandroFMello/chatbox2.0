import { useState } from 'react'
import type { Conversation, Message } from '../services/api'
import { sendUserMessage, clearMessages } from '../services/api'
import MessageList from './MessageList'
import MessageInput from './MessageInput'

interface Props {
  conversation: Conversation
  onSwitchUser: () => void
}

export default function ChatWindow({ conversation, onSwitchUser }: Props) {
  const [messages, setMessages] = useState<Message[]>(conversation.messages)
  const [isStreaming, setIsStreaming] = useState(false)
  void setIsStreaming // wired by useChatSocket in Phase 10
  const [error, setError] = useState<string | null>(null)

  async function handleSend(content: string) {
    setError(null)
    try {
      const saved = await sendUserMessage(conversation.id, content)
      setMessages(prev => [...prev, saved])
      // Phase 10: trigger WebSocket stream here
    } catch {
      setError('Falha ao enviar mensagem. Tente novamente.')
    }
  }

  async function handleClear() {
    setError(null)
    try {
      await clearMessages(conversation.id)
      setMessages([])
    } catch {
      setError('Falha ao limpar a conversa.')
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-white border-b border-gray-200 px-4 h-14 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-800 text-sm">{conversation.user_name}</span>
          <span className="text-gray-300">·</span>
          <span className="text-gray-400 text-xs">{conversation.user_email}</span>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleClear}
            disabled={isStreaming}
            className="text-xs text-gray-500 hover:text-gray-800 disabled:opacity-40 transition-colors"
          >
            Nova conversa
          </button>
          <button
            onClick={onSwitchUser}
            disabled={isStreaming}
            className="text-xs text-indigo-600 hover:text-indigo-800 disabled:opacity-40 transition-colors"
          >
            Trocar usuário
          </button>
        </div>
      </header>

      <MessageList messages={messages} />

      {error && (
        <p className="text-center text-red-500 text-xs py-1 bg-red-50">{error}</p>
      )}

      <MessageInput isStreaming={isStreaming} onSend={handleSend} />
    </div>
  )
}
