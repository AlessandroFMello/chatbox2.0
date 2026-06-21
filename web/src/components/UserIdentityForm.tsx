import { useState } from 'react'

interface Props {
  step: 'email' | 'name'
  email: string
  isLoading: boolean
  onEmailChange: (email: string) => void
  onLookup: () => void
  onCreate: (name: string) => void
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function UserIdentityForm({
  step,
  email,
  isLoading,
  onEmailChange,
  onLookup,
  onCreate,
}: Props) {
  const [name, setName] = useState('')
  const [emailError, setEmailError] = useState('')

  function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!EMAIL_RE.test(email)) {
      setEmailError('Insira um e-mail válido.')
      return
    }
    setEmailError('')
    onLookup()
  }

  function handleNameSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    onCreate(name.trim())
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">ChatterBox</h1>
        <p className="text-gray-500 text-sm mb-6">
          {step === 'email'
            ? 'Insira seu e-mail para entrar ou criar uma conversa.'
            : 'Parece que é sua primeira vez aqui. Como você se chama?'}
        </p>

        {step === 'email' ? (
          <form onSubmit={handleEmailSubmit} className="flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                E-mail
              </label>
              <input
                type="email"
                value={email}
                onChange={e => onEmailChange(e.target.value)}
                placeholder="voce@exemplo.com"
                autoFocus
                required
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {emailError && (
                <p className="text-red-500 text-xs mt-1">{emailError}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={isLoading || !email}
              className="bg-indigo-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Verificando...' : 'Continuar'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleNameSubmit} className="flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome
              </label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Seu nome"
                autoFocus
                required
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !name.trim()}
              className="bg-indigo-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Criando...' : 'Começar'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
