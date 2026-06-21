import { useState } from 'react'

interface Props {
  isStreaming: boolean
  onSend: (content: string) => void
}

export default function MessageInput({ isStreaming, onSend }: Props) {
  const [value, setValue] = useState('')

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    const trimmed = value.trim()
    if (!trimmed || isStreaming) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3 flex gap-2 items-end">
      <textarea
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isStreaming}
        placeholder={isStreaming ? 'Aguarde a resposta…' : 'Digite uma mensagem…'}
        rows={1}
        className="flex-1 resize-none rounded-xl border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-50 disabled:text-gray-400 max-h-32 overflow-y-auto"
      />
      <button
        onClick={submit}
        disabled={isStreaming || !value.trim()}
        className="bg-indigo-600 text-white rounded-xl px-4 py-2 text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
      >
        Enviar
      </button>
    </div>
  )
}
