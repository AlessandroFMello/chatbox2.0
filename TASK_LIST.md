# Task List

Sequential implementation plan. Tasks are designed to be completed in order; each one leaves the repository in a working state (or as close to one as possible). Check items off as they are completed.

**Legend:** `[ ]` pending · `[x]` done · `[~]` in progress

---

## Phase 0 — Repository scaffolding

- [x] **0.1** Initialize Git repository; first commit contains only `README.md`, `ARCHITECTURE.md`, `TASK_LIST.md`, `LICENSE`, `.gitignore`.
- [x] **0.2** Create top-level folder structure: `api/`, `web/`, `docs/`.
- [x] **0.3** Commit `docker-compose.yml`, `api/Dockerfile`, `web/Dockerfile` (empty service builds OK at this stage).
- [x] **0.4** Verify `docker compose config` parses with no errors.

**Exit criteria:** Repository is on GitHub. Compose file is valid. Documentation files are visible.

---

## Phase 1 — Backend skeleton

- [x] **1.1** Create `api/requirements.txt` with: `fastapi`, `uvicorn[standard]`, `motor`, `pydantic-settings`, `google-genai`, `python-dotenv`, `pytest`, `pytest-asyncio`, `httpx`.
- [x] **1.2** Create `api/app/__init__.py` and `api/app/main.py` with a FastAPI app exposing `GET /health` returning `{"status": "ok"}`.
- [x] **1.3** Create `api/app/config.py` with a `Settings` class (Pydantic `BaseSettings`) reading `MONGO_URI`, `MONGO_DB`, `AI_API_KEY`, `AI_MODEL`, `CORS_ORIGINS`.
- [x] **1.4** Create `api/.env.example` with placeholders for every variable in `Settings`.
- [x] **1.5** Add CORS middleware to `main.py` using `Settings.CORS_ORIGINS`.
- [x] **1.6** Run `docker compose up api mongo --build`; verify `GET http://localhost:8000/health` returns 200 and `http://localhost:8000/docs` loads.

**Exit criteria:** API container starts cleanly, health endpoint responds, Swagger renders.

---

## Phase 2 — Database layer

- [x] **2.1** Create `api/app/database.py` with a Motor client initialized at module load using `Settings.MONGO_URI`; expose a `get_conversations_collection()` helper.
- [x] **2.2** Hook up `startup` and `shutdown` events in `main.py` to connect / disconnect the Motor client.
- [x] **2.3** On startup, create the unique index on `user_email` in the `conversations` collection.
- [x] **2.4** Create `api/app/models/message.py` with a `Message` Pydantic model (`role`, `content`, `timestamp`) and a `Role` enum (`user`, `assistant`).
- [x] **2.5** Create `api/app/models/conversation.py` with `Conversation` (document shape) and request/response schemas: `ConversationCreate` (name, email), `ConversationOut` (id, name, email, messages, timestamps).
- [x] **2.6** Create `api/app/repositories/conversation_repository.py` with methods: `get_by_email`, `create`, `get_by_id`, `append_message`. All async; all input/output as Pydantic models or primitives, never raw Mongo dicts at the boundary.

**Exit criteria:** Database connects on startup. Index is created. Models compile. Repository methods exist (not yet exercised end-to-end).

---

## Phase 3 — Conversation endpoints

- [x] **3.1** Create `api/app/services/conversation_service.py` with `get_or_create(name, email)` and `add_user_message(conversation_id, content)` methods.
- [x] **3.2** Create `api/app/routers/conversations.py` with:
  - `POST /conversations` → calls `get_or_create`, returns `ConversationOut`.
  - `GET /conversations/{id}` → returns the full conversation.
  - `POST /conversations/{id}/messages` → calls `add_user_message`, returns the saved message.
- [x] **3.3** Register the router in `main.py`.
- [x] **3.4** Manually verify via Swagger: create a conversation, fetch it, post a user message, fetch again to see the message persisted.

**Exit criteria:** Full REST flow works end-to-end (still no AI). Data persists across container restarts (Mongo volume).

---

## Phase 4 — AI integration

- [x] **4.1** Create `api/app/services/ai_service.py` with:
  - The fixed system prompt (flat-Earth advocate, addresses user by name, stays in character).
  - A method `build_prompt(user_name, messages)` that assembles the request payload (system instruction + history).
  - A method `stream_response(user_name, messages) -> AsyncIterator[str]` that calls Gemini in streaming mode and yields text chunks.
- [x] **4.2** Add error handling: if the SDK raises, the iterator raises a typed `AIServiceError` the WebSocket layer can catch.
- [x] **4.3** Smoke-test `ai_service` by writing a small script that prints chunks for a hard-coded message (do not commit the script).

**Exit criteria:** Calling `ai_service.stream_response(...)` from a Python REPL yields tokens from Gemini.

---

## Phase 5 — WebSocket streaming

- [x] **5.1** Create `api/app/routers/ws.py` with a `WebSocket /ws/conversations/{id}` endpoint.
- [x] **5.2** Protocol per client message: client sends `{"type": "generate"}` after posting a user message; server starts streaming `{"type": "chunk", "content": "..."}` frames; on completion, server persists the AI message and sends `{"type": "end"}`; on failure, `{"type": "error", "message": "..."}` then close.
- [x] **5.3** Add `conversation_service.persist_ai_message(conversation_id, full_content)` and call it at the end of the stream.
- [x] **5.4** Register the WS router in `main.py`.
- [x] **5.5** Manually verify with a WebSocket client (e.g. `websocat`, browser DevTools, or a temp HTML page) that streaming works.

**Exit criteria:** A user message followed by a WS `generate` event produces a streamed reply that ends with the full message persisted in Mongo.

---

## Phase 6 — Backend tests

- [x] **6.1** Create `api/tests/conftest.py` with fixtures:
  - `in_memory_repository` — a fake repository implementing the same interface.
  - `fake_ai_service` — yields a fixed sequence of chunks.
- [x] **6.2** Write `tests/test_conversation_service.py` covering: get_or_create returns existing on duplicate email; new email creates a conversation; add_user_message appends correctly; persist_ai_message appends with role=assistant.
- [x] **6.3** Write `tests/test_ai_service.py` covering: system prompt includes the user's name; prompt includes full message history; chunks are forwarded in order; SDK exception is wrapped in `AIServiceError`.
- [ ] **6.4** Verify `cd api && pytest` is green.

**Exit criteria:** Tests pass. Coverage of the two critical services is meaningful.

---

## Phase 7 — Frontend scaffolding

- [ ] **7.1** Inside `web/`, scaffold a Vite + React project (`npm create vite@latest . -- --template react`).
- [ ] **7.2** Install Tailwind and configure `tailwind.config.js`, `postcss.config.js`, and `src/index.css` with the three Tailwind directives.
- [ ] **7.3** Create `src/services/api.js` with `createOrGetConversation({name, email})`, `getConversation(id)`, `sendUserMessage(id, content)`. Single `apiFetch` helper using native `fetch`.
- [ ] **7.4** Wire the `web` service in Docker Compose; confirm `http://localhost:5173` shows the default Vite page.

**Exit criteria:** Frontend container builds and serves a page. Tailwind classes work in a smoke test (e.g. `bg-red-500` on the root div).

---

## Phase 8 — Identity flow

- [ ] **8.1** Create `src/components/UserIdentityForm.jsx` with two fields (name, email), basic email format validation, a submit button.
- [ ] **8.2** In `App.jsx`, manage `currentConversation` state: if absent, render the identity form; on submit, call `createOrGetConversation`, store the returned conversation, then render the chat shell.
- [ ] **8.3** Persist `{conversationId, name, email}` in `localStorage` so a page reload skips the form. Add a "Trocar usuário" link to clear it.

**Exit criteria:** Form submission creates/retrieves a conversation. Reloading the page keeps the user in their chat.

---

## Phase 9 — Chat UI

- [ ] **9.1** Create `src/components/MessageBubble.jsx`: takes `{role, content}`; user messages right-aligned with one color, AI left-aligned with another, Tailwind classes only.
- [ ] **9.2** Create `src/components/MessageList.jsx`: takes `messages`, renders bubbles, auto-scrolls to bottom when the list grows.
- [ ] **9.3** Create `src/components/MessageInput.jsx`: textarea + send button; `Enter` sends, `Shift+Enter` newline; disables while a stream is in progress.
- [ ] **9.4** Create `src/components/ChatWindow.jsx` composing the three above plus a header showing the user's name.
- [ ] **9.5** Render `ChatWindow` from `App.jsx` once a conversation exists.

**Exit criteria:** Existing messages from a conversation are visible. Typing and pressing send adds a user message via REST (no streaming yet).

---

## Phase 10 — WebSocket streaming on the client

- [ ] **10.1** Create `src/hooks/useChatSocket.js`: opens a WS to `/ws/conversations/{id}`; exposes `isStreaming`, `streamingContent`, `start()`, and an `onComplete(fullContent)` callback.
- [ ] **10.2** In `ChatWindow.jsx`: after `sendUserMessage` resolves, call `start()` to begin streaming. Show a placeholder AI bubble whose content is `streamingContent` while streaming.
- [ ] **10.3** On `onComplete`, replace the placeholder with a real message in the list.
- [ ] **10.4** Handle WS errors visibly (small red banner; don't crash the app).

**Exit criteria:** Sending a user message triggers a streamed AI reply visible token by token. Refreshing the page shows the full reply persisted in Mongo.

---

## Phase 11 — Polish and trade-offs documentation

- [ ] **11.1** Add a loading state on initial conversation fetch.
- [ ] **11.2** Add a basic empty state ("Diga oi para começar a conversa") when the conversation has zero messages.
- [ ] **11.3** Ensure error messages from the API are surfaced (not silently swallowed).
- [ ] **11.4** Take screenshots / record a short GIF of the streaming in action; place in `docs/`.
- [ ] **11.5** Update `README.md` "Demonstração" section with the GIF/screenshots.
- [ ] **11.6** Final pass on `README.md` — make sure every trade-off mentioned in earlier conversations is documented.
- [ ] **11.7** Run `docker compose down -v && docker compose up --build` from a clean state; ensure everything still works.
- [ ] **11.8** Read `CLAUDE.md` Section 9 ("Definition of done") and check off every box.

**Exit criteria:** Project meets the definition of done. README is presentation-ready.

---

## Phase 12 — Pre-delivery

- [ ] **12.1** Verify all secrets (`.env`, API keys) are out of Git history.
- [ ] **12.2** Push final commits to GitHub.
- [ ] **12.3** Open Swagger and walk through every endpoint manually — the architect will likely do the same.
- [ ] **12.4** Open the running app and rehearse the demo flow: identity form → chat → stream → reload → history.
- [ ] **12.5** Prepare a 2-3 minute mental script of what to show in the presentation, in this order: (a) the architecture diagram, (b) the README trade-offs, (c) the live demo, (d) the test suite, (e) a quick code walkthrough of `conversation_service` and `ai_service`.
- [ ] **12.6** Send the delivery email to Thayna and Gustavo with the GitHub link and a one-paragraph summary of what was delivered, what was deferred, and the trade-offs documented in the README.

**Exit criteria:** Email sent. Repository public (or shared with Gustavo's account). Mental rehearsal done.

---

## Buffer

Reserved for unexpected issues. **If everything is done by Monday night, deliver Monday night** — surprising positively is better than waiting.
