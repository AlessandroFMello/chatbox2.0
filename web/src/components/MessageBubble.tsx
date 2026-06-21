import type { Message } from '../services/api'

type Props = Pick<Message, 'role' | 'content'>

export default function MessageBubble({ role, content }: Props) {
  const isUser = role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap break-words ${
          isUser
            ? 'bg-indigo-600 text-white rounded-br-sm'
            : 'bg-white text-gray-800 shadow-sm rounded-bl-sm'
        }`}
      >
        {content}
      </div>
    </div>
  )
}
