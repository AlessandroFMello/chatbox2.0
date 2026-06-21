import { useEffect, useRef } from 'react'
import type { Message } from '../services/api'
import MessageBubble from './MessageBubble'

interface Props {
  messages: Message[]
  streamingContent?: string
}

export default function MessageList({ messages, streamingContent }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3">
      {messages.map((msg, i) => (
        <MessageBubble key={i} role={msg.role} content={msg.content} />
      ))}
      {streamingContent !== undefined && streamingContent !== '' && (
        <MessageBubble role="assistant" content={streamingContent} />
      )}
      <div ref={bottomRef} />
    </div>
  )
}
