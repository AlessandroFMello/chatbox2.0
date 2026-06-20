# ChatterBox 2.0 — Prova de Conceito

PoC para validar uma reescrita do ChatterBox como sistema desacoplado (API + Web) com IA generativa no lugar do chatbot de mercado atual.

## Contexto

Esta PoC valida o fluxo essencial: usuário inicia uma conversa, troca mensagens com uma IA que tem um objetivo fixo de persuasão (*"convencer o usuário que a Terra é plana"*), e as mensagens são exibidas em tempo real via streaming.

## Arquitetura

- **API** (Python / FastAPI / MongoDB): mantém as conversas e orquestra a chamada ao provedor de IA.
- **Web** (React + Vite): interface de chat, consome a API via REST + WebSocket.
- **Mongo**: persistência das conversas e mensagens.

Tudo sobe via Docker Compose como três serviços isolados, simulando a separação que o sistema real teria em produção (ainda que aqui estejam no mesmo repositório, por ser uma PoC).

> Detalhamento completo da arquitetura, fluxos e estrutura de pastas em [`ARCHITECTURE.md`](./ARCHITECTURE.md).

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12 + FastAPI + Motor (Mongo async) |
| Banco | MongoDB 7 |
| Frontend | React 18 + Vite + Tailwind CSS |
| IA | Google Gemini 2.5 Flash (tier gratuito do AI Studio) |
| Testes | pytest + pytest-asyncio |
| Infra local | Docker Compose |

## Como rodar

**Pré-requisitos:** Docker e Docker Compose instalados; chave de API do Google AI Studio (gratuita em <https://aistudio.google.com/apikey>).

```bash
# 1. Configurar variáveis de ambiente
cp api/.env.example api/.env
# Edite api/.env e preencha AI_API_KEY com sua chave do Google AI Studio

# 2. Subir tudo
docker compose up --build
```

- **API**: <http://localhost:8000> — Swagger em <http://localhost:8000/docs>
- **Web**: <http://localhost:5173>
- **MongoDB**: `mongodb://localhost:27017` (exposto para facilitar inspeção via Compass)

## Fluxo da aplicação

1. Usuário acessa a Web e informa **nome + e-mail** (identificação leve, sem senha).
2. Se o e-mail já tem conversa, ela é retomada; caso contrário, uma nova é criada.
3. Usuário envia mensagem → API persiste no Mongo → chama o Gemini com o histórico + system prompt fixo → resposta é transmitida ao vivo via WebSocket.
4. Ao final do stream, a mensagem completa da IA é persistida no Mongo.

## Demonstração

> *A ser adicionado após implementação: GIF curto mostrando o streaming ao vivo e uma troca de mensagens em que a IA defende a tese da Terra plana.*

## Decisões técnicas e trade-offs

### Provedor de IA: Google Gemini 2.5 Flash
Gratuito no tier do AI Studio, suporta streaming nativo via SDK Python. A chave fica isolada na API (variável de ambiente), nunca exposta ao frontend.

### Modelagem no Mongo
Mensagens embutidas como array dentro do documento de conversa, em vez de collection separada. Para o volume esperado de uma conversa de demonstração, isso é mais simples e mais alinhado ao modelo de documentos do Mongo. Em um cenário de conversas muito longas, separar em collection própria com paginação seria mais adequado.

### Contexto enviado à IA
O histórico completo da conversa é enviado a cada chamada ao modelo. Funciona bem no escopo desta PoC; em produção, precisaria de truncamento ou sumarização para conversas longas, por custo e limite de contexto.

### Streaming via WebSocket
A resposta da IA é transmitida token a token via WebSocket, dando a sensação de *"digitação ao vivo"*. A persistência no Mongo ocorre após o término do streaming, com a mensagem completa.

### Identificação sem autenticação
Como autenticação não é requisito, optei por uma tela inicial pedindo apenas **nome** e **e-mail**. O e-mail permite retomar conversas anteriores; o nome é usado pela IA para personalizar a conversa. Não há senha, sessão ou validação real — é identificação leve para fins de UX, não controle de acesso. Decisão alinhada com o arquiteto por e-mail.

### Organização do código (API)
Separação em camadas simples (`routers` → `services` → `repositories`), sem abstrações formais de interface/injeção de dependência. Suficiente para isolar responsabilidades sem o peso de Clean Architecture completa.

## O que considerei e decidi não aplicar

- **Clean Architecture / DDD / TDD completo**: adicionaria uma cerimônia (entidades, casos de uso, interfaces de repositório) desproporcional ao escopo de uma PoC com poucos endpoints. Optei por camadas simples e testes concentrados nos pontos de maior risco (integração com IA, streaming).
- **RAG**: faria sentido se a IA precisasse responder com base em uma base de conhecimento específica (produtos, políticas, etc). Como o objetivo aqui é um papel de persuasão fixo via system prompt, RAG não agrega valor — mas seria a escolha natural no ChatterBox 2.0 real, quando a IA precisar de conhecimento específico de cada cliente.
- **Next.js no lugar de React puro**: o principal ganho de Next.js seria uma camada de BFF para esconder chaves de API do client. Como a API Python já cumpre esse papel (a chave de IA nunca chega ao frontend), esse benefício não se aplica aqui, então mantive React puro (Vite).
- **TanStack Query / Zustand**: o fluxo de dados é simples o bastante (uma leitura de histórico, um envio de mensagem, um stream) para `useState` e `fetch` nativo, sem necessidade de cache ou estado global.

## O que foi deixado de fora intencionalmente

- Autenticação e autorização reais
- Múltiplos usuários simultâneos com permissões
- Retry/backoff em falhas do provedor de IA
- Rate limiting
- Deploy / CI

## Próximos passos (fora do escopo da PoC)

- Sumarização de histórico para conversas longas
- RAG para conhecimento específico por cliente
- Autenticação real
- Observabilidade (logs estruturados, métricas de latência da IA)
- Separação efetiva em dois repositórios / dois serviços com pipelines independentes

## Estrutura do repositório

Ver [`ARCHITECTURE.md`](./ARCHITECTURE.md) para detalhamento completo.

```
chatterbox-poc/
├── api/             # Backend FastAPI
├── web/             # Frontend React
├── docs/            # Imagens, GIFs e diagramas
├── docker-compose.yml
├── README.md        # (este arquivo)
├── ARCHITECTURE.md  # Detalhamento da arquitetura
├── CLAUDE.md        # Guia para desenvolvimento assistido por Claude Code
├── TASK_LIST.md     # Lista sequencial de tarefas de implementação
└── LICENSE
```

## Licença

MIT — ver [`LICENSE`](./LICENSE).
