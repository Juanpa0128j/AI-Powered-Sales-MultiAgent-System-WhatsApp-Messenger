# AI-Powered Sales Multi-Agent System (WhatsApp & Messenger)

A sophisticated conversational commerce engine built with **LangChain**, **LangGraph**, and **FastAPI**. This system acts as an "Artificial Salesperson" capable of maintaining persistent negotiation states, reasoning about user intent, and executing omnichannel sales flows across WhatsApp and Facebook Messenger.

## 🚀 Key Features

- **WhatsApp Bridge**: Uses a local Node.js bridge (`whatsapp-web.js`) to control a real WhatsApp instance, avoiding Business API costs and approval delays.
- **Agentic Orchestration**: Uses **LangGraph** to handle complex, non-deterministic sales flows and stateful negotiations.
- **Persistent State**: Maintains user context, current product discussions, and negotiation stages across sessions.
- **Tool-Enabled Reasoning**: Equipped with tools for product lookup, inventory checks, and sending multimedia notifications.
- **RAG Integration**: Ready for Retrieval-Augmented Generation to provide accurate product information from structured catalogs.
- **Human-in-the-Loop**: Escalates to human agents via `/mute` command or sales detection. Default "Muted" state gives humans control first.
- **Media Support**: Handles incoming media (downloads to disk) and outgoing media (sends via URL).
- **Group Filter**: Automatically ignores group chats to focus on 1-on-1 customer service.

## 🏗️ Architecture

### High-Level Flow

The system uses a **Hybrid Architecture** where a Node.js process manages the real-time websocket connection to WhatsApp, while a Python process handles the intelligence, state management, and reasoning.

```mermaid
graph TD
    User([User]) <-->|WhatsApp| Phone[WhatsApp Mobile App]
    Phone <-->|E2E Encrypted| Bridge[Node.js Bridge<br>whatsapp-web.js]
    
    subgraph "Server (Local or Cloud)"
        Bridge <-->|HTTP JSON| API[FastAPI Gateway<br>Python]
        
        API -->|Invoke| Brain[LangGraph Agent]
        Brain <-->|R/W| DB[(ChromaDB / Memory)]
        
        Brain -- Call --> Tools
        subgraph "Tools Layer"
            Tools[Toolbox]
            Tools -->|Search| Web[Tavily / Google]
            Tools -->|Lookup| Catalog[Product Catalog]
        end
    end
```

### 📂 Codebase Structure

| Directory / File | Description |
| :--- | :--- |
| **`app/`** | **Python Core Logic** (The Brain) |
| `app/agent/` | Contains the LangGraph definition. |
| &nbsp;&nbsp; ├── `graph.py` | Defines the StateGraph, nodes, and edges (the "wiring"). |
| &nbsp;&nbsp; ├── `nodes.py` | Implements the logic for each step (chatbot, call_tool, etc.). |
| &nbsp;&nbsp; └── `state.py` | Defines the `SalesState` (conversation history, variables). |
| `app/gateways/` | **I/O Layer** - Adapters for message conversion. |
| &nbsp;&nbsp; ├── `http_adapter.py` | Normalizes incoming JSON from Node.js into internal objects. |
| &nbsp;&nbsp; └── `bridge_client.py` | Client for sending text/media back to the Node.js Bridge. |
| `app/tools/` | **Capabilities** - Functions the agent can call. |
| &nbsp;&nbsp; ├── `product_tools.py` | RAG implementation (matches query to product info). |
| &nbsp;&nbsp; ├── `search_tools.py` | External web search for broader context. |
| &nbsp;&nbsp; └── `notification_tools.py` | Escalation logic (notifying human admins). |
| `app/main.py` | **Entry Point** - FastAPI app, Webhook handler, and Rate Limiter. |
| | |
| **`whatsapp-gateway/`** | **Node.js Bridge** ( The Body) |
| `whatsapp-gateway/index.js` | Runs the headless Chrome/Puppeteer instance to connect to WhatsApp Web. |
| | |
| **`tests/`** | **Verification** |
| `tests/test_e2e_flows.py` | End-to-End simulation of sales conversations. |
| `tests/test_gateway.py` | Unit tests for the HTTP Adapter layer. |

### 🧠 Agent Logic Flow

```mermaid
stateDiagram-v2
    direction LR
    [*] --> InboundMessage
    InboundMessage --> RateLimiter
    
    state RateLimiter {
        [*] --> CheckLimit
        CheckLimit --> Blocked: Exceeded
        CheckLimit --> Allowed: OK
    }
    
    Allowed --> AdminCommandCheck
    
    state AdminCommandCheck {
        [*] --> IsCommand
        IsCommand --> ExecuteCommand: Yes
        IsCommand --> HandoffCheck: No
    }
    
    HandoffCheck --> HumanMode: Handoff Active?
    HandoffCheck --> AgentGraph: No
    
    state AgentGraph {
        [*] --> AnalyzeIntent
        AnalyzeIntent --> UseTool: Needs Info?
        AnalyzeIntent --> Respond: Has Info?
        
        UseTool --> ExecuteTool
        ExecuteTool --> AnalyzeIntent: Loop with Result
    }
    
    AgentGraph --> OutboundMessage
    OutboundMessage --> [*]
```

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **AI Orchestration**: [LangGraph](https://python.langchain.com/docs/langgraph) & [LangChain](https://python.langchain.com/)
- **Messaging Gateway**: Node.js + [whatsapp-web.js](https://wwebjs.dev/)
- **Models**: OpenAI (GPT-4o / GPT-4-turbo)
- **Database**: SQL-based persistence (PostgreSQL recommended)

## 🎮 Admin & Control

The system includes built-in commands for human oversight. You can send these commands from your own WhatsApp number (Self-Command) to any customer chat.

### Commands

| Command | Description |
| :--- | :--- |
| `/activate` | **Enable** the AI agent for this chat. (Aliases: `/unmute`) |
| `/deactivate` | **Disable** the AI agent for this chat. (Aliases: `/mute`) |
| `/status` | Check if the system is ONLINE and if the current thread is active. |
| `/stop` | **Global Kill Switch**. Stops the AI for ALL users immediately. |
| `/start` | **Global Resume**. Reactivates the system. |

### ⚠️ Important Behaviors

1.  **Default Muted**: New conversations start with the AI **deactivated**. You must explicitly send `/activate` to let the bot take over.
2.  **Groups Ignored**: The system automatically ignores all messages from group chats (`@g.us`).
3.  **Self-Commands**: You can send commands to a customer *from your own phone*. The system detects the command and applies it to that customer's thread.

## 🚦 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for the Bridge)
- OpenAI API Key

### Installation

### Installation (Automated)

1. Clone the repository:

   ```bash
   git clone https://github.com/Juanpa0128j/-AI-Powered-Sales-MultiAgent-System-WhatsApp-Messenger.git
   cd AI-Powered-Sales-MultiAgent-System-WhatsApp-Messenger
   ```

2. **One-Command Setup**:
   
   Run the following to install all Python/Node.js dependencies and create your `.env` file:

   ```bash
   make setup
   ```

   *Note: Remember to edit `.env` and add your `OPENAI_API_KEY`.*

### Installation (Manual)

If you prefer manual setup:

<details>
<summary>Click to expand manual steps</summary>

1. **Python Setup**:

   ```bash
   uv sync
   ```

2. **Node.js Bridge Setup**:

   ```bash
   cd whatsapp-gateway && npm install
   ```

3. **Environment**:

   ```bash
   cp .env.example .env
   ```

</details>

### 🚀 Running the System

You need two terminals:

#### Terminal 1: The Brain (Python)

```bash
make run-backend
# Or: uv run uvicorn app.main:app --port 8000
```

#### Terminal 2: The Bridge (Node.js)

```bash
make run-bridge
# Or: cd whatsapp-gateway && node index.js
```

*Scan the QR Code that appears in this terminal using your WhatsApp Mobile App (Linked Devices).*

## 📝 Roadmap

- [x] Integrate Vector Database for semantic product search.
- [x] Basic Multimedia response support (System Prompt).
- [x] **Bridge Enhancement**: Support sending images/video files via Node.js Bridge.
- [x] **Bridge Enhancement**: Auto-reconnection logic (handled via `LocalAuth`).
- [ ] Develop a Dashboard for real-time monitoring of agent performance.
- [ ] Dockerize the Node.js Bridge for easier deployment.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
