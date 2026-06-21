# Architecture

This document describes the architecture, folder structure, and main flows of the ChatterBox 2.0 PoC.

## 1. High-level overview

Three isolated services orchestrated by Docker Compose:

```
┌─────────────┐        REST + WS         ┌─────────────┐         ┌──────────┐
│             │ ───────────────────────▶ │             │ ──────▶ │          │
│  Web (5173) │                          │  API (8000) │         │  Mongo   │
│  React/Vite │ ◀─────────────────────── │   FastAPI   │ ◀────── │  (27017) │
│             │   streamed AI response   │             │         │          │
└─────────────┘                          └──────┬──────┘         └──────────┘
                                                │
                                                │ HTTPS (streaming)
                                                ▼
                                        ┌──────────────┐
                                        │  Google      │
                                        │  Gemini API  │
                                        └──────────────┘
```

The frontend never talks to the LLM provider directly — the API is the only component holding credentials. This is the same pattern a real BFF would provide, which is why a separate BFF layer (Next.js) was not added.

## 2. Folder structure

```
chatterbox-poc/
├── api/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI entrypoint, CORS, router registration
│   │   ├── config.py                     # Settings (Pydantic BaseSettings, reads .env)
│   │   ├── database.py                   # Motor client + collection accessors
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py           # Conversation document + Pydantic schemas
│   │   │   └── message.py                # Message subdocument + role enum
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── conversations.py          # POST/GET endpoints for conversations
│   │   │   └── ws.py                     # WebSocket endpoint for streaming
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py             # Wraps Gemini SDK, system prompt, streaming
│   │   │   └── conversation_service.py   # Business logic, orchestrates AI + persistence
│   │   └── repositories/
│   │       ├── __init__.py
│   │       └── conversation_repository.py # Sole Mongo access point
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                   # Fixtures (mocked AI, in-memory repo)
│   │   ├── test_conversation_service.py
│   │   └── test_ai_service.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── web/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx            # Main chat shell
│   │   │   ├── MessageBubble.tsx         # Single message (user/AI styled)
│   │   │   ├── MessageList.tsx           # Scrollable list with auto-scroll
│   │   │   ├── MessageInput.tsx          # Textarea + send button
│   │   │   └── UserIdentityForm.tsx      # Name/email entry screen
│   │   ├── hooks/
│   │   │   ├── useChatSocket.ts          # WebSocket lifecycle + token concat
│   │   │   └── useConversation.ts        # Load history, send message
│   │   ├── services/
│   │   │   └── api.ts                    # Typed fetch wrapper + shared types
│   │   ├── App.tsx                       # Routes between identity form and chat
│   │   ├── main.tsx                      # React entrypoint
│   │   ├── vite-env.d.ts                 # Vite env type declarations
│   │   └── index.css                     # Tailwind directives
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.ts
│   └── index.html
│
├── docs/                                 # Screenshots, GIFs, diagrams for README
│
├── docker-compose.yml
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── TASK_LIST.md
└── LICENSE
```

### Rationale for backend layering

- **`routers`** — receive HTTP/WS requests, parse input, delegate. No business rules.
- **`services`** — business logic: build the prompt context, decide what to persist, orchestrate the AI call.
- **`repositories`** — the only layer that knows MongoDB exists. Swapping the database means rewriting this layer only.
- **`models`** — Pydantic models doing double duty as API contracts and document shapes (acceptable simplification for a PoC; in production these would likely be split).

No formal ports/adapters, no dependency injection container, no use cases as classes. This is the explicit middle ground negotiated in the architecture decision: *"layered separation by responsibility, not Clean Architecture"*.

### Rationale for frontend organization

- **`components`** — pure UI, receive props, emit events. No data fetching.
- **`hooks`** — encapsulate side effects (WebSocket lifecycle, REST calls). Keeps components clean.
- **`services/api.js`** — single place where REST URLs and the fetch wrapper live.

## 3. Data model

### Conversation document (collection: `conversations`)

```json
{
  "_id": "ObjectId(...)",
  "user_email": "alessandro@example.com",
  "user_name": "Alessandro",
  "created_at": "2026-06-20T20:00:00Z",
  "updated_at": "2026-06-20T20:05:30Z",
  "messages": [
    {
      "role": "user",
      "content": "Por que você acha que a Terra é plana?",
      "timestamp": "2026-06-20T20:00:10Z"
    },
    {
      "role": "assistant",
      "content": "Que pergunta excelente, Alessandro! ...",
      "timestamp": "2026-06-20T20:00:15Z"
    }
  ]
}
```

**Index:** unique on `user_email` (one ongoing conversation per email, for the PoC).

### Message subdocument

| Field | Type | Notes |
|-------|------|-------|
| `role` | `"user"` \| `"assistant"` | matches LLM convention |
| `content` | string | full message text |
| `timestamp` | datetime (UTC) | server-assigned on persistence |

## 4. API surface

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/conversations` | Create or retrieve conversation by `{name, email}` |
| `GET` | `/conversations/{id}` | Fetch full conversation with message history |
| `GET` | `/conversations/lookup` | Check if a conversation exists by `?email=...`; returns it or 404 |
| `POST` | `/conversations/{id}/messages` | Send a user message; returns the saved user message |
| `DELETE` | `/conversations/{id}/messages` | Clear all messages; user record (name, email) is preserved |
| `WS` | `/ws/conversations/{id}` | Stream AI response tokens after a user message is sent |
| `GET` | `/health` | Liveness probe |
| `GET` | `/docs` | Swagger UI (auto-generated by FastAPI) |

### Streaming flow (most important sequence)

1. Client POSTs the user message → API persists it and returns 200.
2. Client opens (or reuses) the WebSocket on `/ws/conversations/{id}`.
3. Server reads the conversation history, builds the prompt, calls Gemini in streaming mode.
4. Server forwards each token chunk to the client as JSON frames: `{"type": "chunk", "content": "..."}`.
5. When the stream ends, the server persists the full AI message and sends `{"type": "end"}`.
6. Client keeps the socket open for subsequent messages in the same session (one connection per chat session).

## 5. AI integration

- **Provider:** Google Gemini 2.5 Flash via the official `google-genai` Python SDK.
- **System prompt (fixed):** instructs the model to play the role of *"a passionate flat-earth advocate"*, address the user by their first name, and never break character.
- **Context window strategy:** the full conversation history is sent on each call. Acceptable for a demo; flagged in the README as a production gap.
- **Failure handling:** if the SDK raises, the WebSocket sends `{"type": "error", "message": "..."}` and closes; the user message remains persisted (it is not "lost").

## 6. Environment configuration

| Variable | Where | Purpose |
|----------|-------|---------|
| `MONGO_URI` | api | Mongo connection string (defaults to `mongodb://mongo:27017` inside Docker) |
| `MONGO_DB` | api | Database name (default: `chatterbox`) |
| `AI_API_KEY` | api | Google AI Studio key — **required**, no default |
| `AI_MODEL` | api | Gemini model id (default: `gemini-2.5-flash`) |
| `CORS_ORIGINS` | api | Comma-separated allowed origins (default: `http://localhost:5173`) |
| `VITE_API_URL` | web | Base URL for REST calls (default: `http://localhost:8000`) |
| `VITE_WS_URL` | web | Base URL for WebSocket (default: `ws://localhost:8000`) |

## 7. Testing strategy

Tests are concentrated on the highest-risk areas:

- **`conversation_service`** — orchestration logic with a mocked AI service and an in-memory repository (no real Mongo needed).
- **`ai_service`** — prompt assembly and streaming chunk handling, with the SDK call mocked.

Repository and routers are not exhaustively unit-tested — they are exercised implicitly by the service tests and by manual smoke testing via Swagger.

## 8. What is intentionally absent

- Authentication, sessions, CSRF
- Multi-tenant isolation
- Retries / circuit breakers around the AI provider
- Structured logging / tracing
- Production deployment artifacts (only local Docker Compose is provided)
