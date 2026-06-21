import { useState, useEffect, useRef, useCallback } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'

interface Options {
  conversationId: string
  onComplete: (fullContent: string) => void
  onError: (message: string) => void
}

interface UseChatSocketReturn {
  isStreaming: boolean
  streamingContent: string
  start: () => void
}

export function useChatSocket({ conversationId, onComplete, onError }: Options): UseChatSocketReturn {
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')

  const wsRef = useRef<WebSocket | null>(null)
  const accumulatorRef = useRef('')

  const onCompleteRef = useRef(onComplete)
  const onErrorRef = useRef(onError)
  useEffect(() => { onCompleteRef.current = onComplete }, [onComplete])
  useEffect(() => { onErrorRef.current = onError }, [onError])

  const resetStream = useCallback((streaming: boolean) => {
    accumulatorRef.current = ''
    setStreamingContent('')
    setIsStreaming(streaming)
  }, [])

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/conversations/${conversationId}`)
    wsRef.current = ws

    ws.onmessage = (event: MessageEvent) => {
      if (ws !== wsRef.current) return
      const data = JSON.parse(event.data as string) as { type: string; content?: string; message?: string }

      if (data.type === 'chunk' && data.content) {
        accumulatorRef.current += data.content
        setStreamingContent(prev => prev + data.content)
      } else if (data.type === 'end') {
        onCompleteRef.current(accumulatorRef.current)
        resetStream(false)
      } else if (data.type === 'error') {
        onErrorRef.current(data.message ?? 'Erro desconhecido do servidor.')
        resetStream(false)
      }
    }

    ws.onerror = () => {
      if (ws !== wsRef.current) return
      onErrorRef.current('Erro de conexão WebSocket.')
      resetStream(false)
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [conversationId, resetStream])

  const start = useCallback(() => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    resetStream(true)
    ws.send(JSON.stringify({ type: 'generate' }))
  }, [resetStream])

  return { isStreaming, streamingContent, start }
}
