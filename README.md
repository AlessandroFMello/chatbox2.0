# ChatterBox 2.0 — Prova de Conceito

PoC para validar uma reescrita do ChatterBox como sistema desacoplado (API + Web) com IA generativa no lugar do chatbot de mercado atual.

---

## Sumário

- [Contexto](#contexto)
- [Arquitetura](#arquitetura)
- [Stack](#stack)
- [Como rodar](#como-rodar)
- [Fluxo da aplicação](#fluxo-da-aplicação)
- [Demonstração](#demonstração)
- [Decisões técnicas e trade-offs](#decisões-técnicas-e-trade-offs)
- [Problemas encontrados e como foram resolvidos](#problemas-encontrados-e-como-foram-resolvidos)
- [O que considerei e decidi não aplicar](#o-que-considerei-e-decidi-não-aplicar)
- [O que foi deixado de fora intencionalmente](#o-que-foi-deixado-de-fora-intencionalmente)
- [Próximos passos](#próximos-passos-fora-do-escopo-da-poc)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Licença](#licença)

---

<a name="contexto"></a>
<details>
<summary><strong>Contexto</strong></summary>

Esta PoC valida o fluxo essencial: usuário inicia uma conversa, troca mensagens com uma IA que tem um objetivo fixo de persuasão (*"convencer o usuário que a Terra é plana"*), e as mensagens são exibidas em tempo real via streaming.

</details>

---

<a name="arquitetura"></a>
<details>
<summary><strong>Arquitetura</strong></summary>

- **API** (Python / FastAPI / MongoDB): mantém as conversas e orquestra a chamada ao provedor de IA.
- **Web** (React + Vite): interface de chat, consome a API via REST + WebSocket.
- **Mongo**: persistência das conversas e mensagens.

Tudo sobe via Docker Compose como três serviços isolados, simulando a separação que o sistema real teria em produção (ainda que aqui estejam no mesmo repositório, por ser uma PoC).

> Detalhamento completo da arquitetura, fluxos e estrutura de pastas em [`ARCHITECTURE.md`](./ARCHITECTURE.md).

</details>

---

<a name="stack"></a>
<details>
<summary><strong>Stack</strong></summary>

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12 + FastAPI + Motor (Mongo async) |
| Banco | MongoDB 7 |
| Frontend | React 18 + Vite + Tailwind CSS |
| IA | Google Gemini 2.5 Flash (tier gratuito do AI Studio) |
| Testes | pytest + pytest-asyncio |
| Infra local | Docker Compose |

</details>

---

<a name="como-rodar"></a>
<details>
<summary><strong>Como rodar</strong></summary>

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

</details>

---

<a name="fluxo-da-aplicação"></a>
<details>
<summary><strong>Fluxo da aplicação</strong></summary>

1. Usuário acessa a Web e informa **nome + e-mail** (identificação leve, sem senha).
2. Se o e-mail já tem conversa, ela é retomada; caso contrário, uma nova é criada.
3. Usuário envia mensagem → API persiste no Mongo → chama o Gemini com o histórico + system prompt fixo → resposta é transmitida ao vivo via WebSocket.
4. Ao final do stream, a mensagem completa da IA é persistida no Mongo.

</details>

---

<a name="demonstração"></a>
<details>
<summary><strong>Demonstração</strong></summary>

> *A ser adicionado após implementação: GIF curto mostrando o streaming ao vivo e uma troca de mensagens em que a IA defende a tese da Terra plana.*

</details>

---

<a name="decisões-técnicas-e-trade-offs"></a>
<details>
<summary><strong>Decisões técnicas e trade-offs</strong></summary>

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

### Motor: cliente singleton no nível de módulo
O cliente Motor (driver async do MongoDB) é instanciado uma única vez na inicialização da aplicação, não por requisição. Isso garante reutilização do pool de conexões interno do Motor. Criar um cliente por requisição resultaria em overhead desnecessário e potencial esgotamento de conexões.

### Persistência da mensagem da IA após o stream
A mensagem gerada pela IA é persistida no MongoDB apenas após o término completo do stream, com o conteúdo concatenado. Persistir token a token seria mais complexo, mais custoso em operações de escrita e deixaria documentos em estado parcial em caso de falha a meio do stream.

### REST para escrita + WebSocket apenas para streaming
Mensagens do usuário são enviadas via REST (`POST /conversations/{id}/messages`) antes de acionar o WebSocket. O WebSocket recebe apenas o sinal de geração (`{"type": "generate"}`) e transmite os chunks da IA. Essa separação mantém cada protocolo na função em que é mais adequado: REST para operações com garantias claras de status HTTP, WebSocket para transmissão contínua.

### Conversa única por e-mail
O e-mail é a chave única da conversa, garantido por índice único no MongoDB. Se o usuário retornar com o mesmo e-mail, a conversa existente é retomada. Isso simplifica o modelo de dados para o escopo da PoC; em produção, múltiplas conversas por usuário seriam o caminho natural.

### System prompt estruturado e testável
O system prompt da IA foi dividido em seções explícitas (persona, objetivo, regras de comportamento, estilo de resposta, tratamento de desafios, desvios de assunto e idioma) em vez de um parágrafo genérico. Isso torna cada comportamento esperado verificável individualmente e facilita ajustes sem quebrar outras partes da instrução.

### Organização do código (API)
Separação em camadas simples (`routers` → `services` → `repositories`), sem abstrações formais de interface/injeção de dependência. Suficiente para isolar responsabilidades sem o peso de Clean Architecture completa.

</details>

---

<a name="problemas-encontrados-e-como-foram-resolvidos"></a>
<details>
<summary><strong>Problemas encontrados e como foram resolvidos</strong></summary>

### `generate_content_stream` exige `await` antes da iteração
O método de streaming do SDK do Google Gemini retorna uma corrotina (não um iterador assíncrono diretamente). Tentar iterar com `async for chunk in client.aio.models.generate_content_stream(...)` sem o `await` resulta em `TypeError: 'async for' requires an object with __aiter__ method, got coroutine`. A correção é `async for chunk in await client.aio.models.generate_content_stream(...)`.

### Frames vazios do WebSocket causavam `JSONDecodeError`
Clientes como Insomnia (e alguns browsers) enviam um frame de texto vazio ao estabelecer a conexão WebSocket. `receive_json()` tentava fazer `json.loads("")` e levantava `JSONDecodeError`, encerrando a conexão antes da primeira mensagem real. A solução foi trocar para `receive_text()` com uma verificação `if not text.strip(): continue` para ignorar frames vazios silenciosamente.

### Gemini respondendo perguntas fora do personagem
O modelo respondia a perguntas completamente fora do escopo (ex: receitas de comida) em vez de redirecionar para o tema da Terra plana, apesar do system prompt. O prompt foi ajustado com uma seção explícita de "Off-topic requests" instruindo o modelo a não atender requisições não relacionadas e redirecionar a conversa de volta ao tema central.

### Conversa única por e-mail impedia recomeçar do zero
Percebido após a API estar finalizada: como cada e-mail tem exatamente uma conversa, o usuário que quisesse testar um chat limpo ou simplesmente começar uma nova conversa ficava preso no histórico acumulado. Não havia como limpar sem acessar o banco diretamente.

**Solução:** botão "Nova conversa" na interface do chat. Ao clicar, o frontend chama um novo endpoint (`DELETE /conversations/{id}/messages`) que apaga apenas o array de mensagens do documento no MongoDB, preservando o registro do usuário (nome, e-mail, `_id`). Nenhuma regra de negócio é alterada; a conversa simplesmente recomeça vazia.

Cogitei um comando de texto (`/clear`) digitado no próprio chat, mas descartei: intuitivo apenas para desenvolvedores. Um botão visível é a escolha certa para qualquer perfil de usuário.

### Formulário de entrada pedia nome e e-mail juntos, mas nome era ignorado no retorno
Percebido após a API estar finalizada: o formulário inicial solicitava **nome + e-mail** de uma vez. Para usuários novos, funciona; para usuários que retornam, o campo de nome era inútil — o `conversation_service` ignora o nome se o e-mail já existe. Pior: se o usuário digitasse um nome diferente do que usou na primeira vez, o dado seria silenciosamente descartado.

**Solução:** fluxo em duas etapas no frontend + novo endpoint `GET /conversations/lookup?email=...` na API:
1. Frontend pede apenas o e-mail.
2. Chama o endpoint de lookup.
3. Se a conversa existe (`200`) → carrega o histórico e abre o chat diretamente, sem pedir nome.
4. Se não existe (`404`) → exibe o campo de nome → cria a conversa via `POST /conversations`.

O endpoint de lookup é somente leitura e não altera nenhuma lógica existente.

</details>

---

<a name="o-que-considerei-e-decidi-não-aplicar"></a>
<details>
<summary><strong>O que considerei e decidi não aplicar</strong></summary>

- **Clean Architecture / DDD / TDD completo**: adicionaria uma cerimônia (entidades, casos de uso, interfaces de repositório) desproporcional ao escopo de uma PoC com poucos endpoints. Optei por camadas simples e testes concentrados nos pontos de maior risco (integração com IA, streaming).
- **RAG**: faria sentido se a IA precisasse responder com base em uma base de conhecimento específica (produtos, políticas, etc). Como o objetivo aqui é um papel de persuasão fixo via system prompt, RAG não agrega valor — mas seria a escolha natural no ChatterBox 2.0 real, quando a IA precisar de conhecimento específico de cada cliente.
- **Next.js no lugar de React puro**: o principal ganho de Next.js seria uma camada de BFF para esconder chaves de API do client. Como a API Python já cumpre esse papel (a chave de IA nunca chega ao frontend), esse benefício não se aplica aqui, então mantive React puro (Vite).
- **TanStack Query / Zustand**: o fluxo de dados é simples o bastante (uma leitura de histórico, um envio de mensagem, um stream) para `useState` e `fetch` nativo, sem necessidade de cache ou estado global.

</details>

---

<a name="o-que-foi-deixado-de-fora-intencionalmente"></a>
<details>
<summary><strong>O que foi deixado de fora intencionalmente</strong></summary>

- Autenticação e autorização reais
- Múltiplos usuários simultâneos com permissões
- Retry/backoff em falhas do provedor de IA
- Rate limiting
- Deploy / CI

</details>

---

<a name="próximos-passos-fora-do-escopo-da-poc"></a>
<details>
<summary><strong>Próximos passos (fora do escopo da PoC)</strong></summary>

- Sumarização de histórico para conversas longas
- RAG para conhecimento específico por cliente
- Autenticação real
- Observabilidade (logs estruturados, métricas de latência da IA)
- Separação efetiva em dois repositórios / dois serviços com pipelines independentes

</details>

---

<a name="estrutura-do-repositório"></a>
<details>
<summary><strong>Estrutura do repositório</strong></summary>

Ver [`ARCHITECTURE.md`](./ARCHITECTURE.md) para detalhamento completo.

```
chatterbox-poc/
├── api/             # Backend FastAPI
├── web/             # Frontend React
├── docs/            # Imagens, GIFs e diagramas
├── docker-compose.yml
├── README.md        # (este arquivo)
├── ARCHITECTURE.md  # Detalhamento da arquitetura
├── TASK_LIST.md     # Lista sequencial de tarefas de implementação
└── LICENSE
```

</details>

---

<a name="licença"></a>
<details>
<summary><strong>Licença</strong></summary>

MIT — ver [`LICENSE`](./LICENSE).

</details>
