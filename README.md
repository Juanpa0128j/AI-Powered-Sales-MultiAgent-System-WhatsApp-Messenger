# AI-Powered Sales Multi-Agent System (WhatsApp & Messenger)

A sophisticated conversational commerce engine built with **LangChain**, **LangGraph**, and **FastAPI**. This system acts as an "Artificial Salesperson" capable of maintaining persistent negotiation states, reasoning about user intent, and executing omnichannel sales flows across WhatsApp and Facebook Messenger.

## 🚀 Key Features

- **Omnichannel Support**: Unified ingestion layer for WhatsApp Business and Facebook Messenger via Twilio.
- **Agentic Orchestration**: Uses **LangGraph** to handle complex, non-deterministic sales flows and stateful negotiations.
- **Persistent State**: Maintains user context, current product discussions, and negotiation stages across sessions.
- **Tool-Enabled Reasoning**: Equipped with tools for product lookup, inventory checks, and sending multimedia notifications.
- **RAG Integration**: Ready for Retrieval-Augmented Generation to provide accurate product information from structured catalogs.
- **Human-in-the-Loop**: Designed to escalate complex queries to human agents when necessary.

## 🏗️ Architecture

The system is organized into several key modules:

- `app/agent/`: Core logic for the AI agent, including the state definition and graph orchestration.
- `app/gateways/`: Omnichannel ingestion layer (Twilio integration).
- `app/tools/`: Functional tools for the agent (Product search, Notifications, etc.).
- `app/database/`: Persistence layer for storing conversation history and agent states.
- `app/main.py`: FastAPI entry point and webhook management.

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **AI Orchestration**: [LangGraph](https://python.langchain.com/docs/langgraph) & [LangChain](https://python.langchain.com/)
- **Messaging Gateway**: [Twilio Business API](https://www.twilio.com/)
- **Models**: OpenAI (GPT-4o / GPT-4-turbo)
- **Database**: SQL-based persistence (PostgreSQL recommended)

## 🚦 Getting Started

### Prerequisites

- Python 3.11+
- Twilio Account (SID, Auth Token, and WhatsApp-enabled number)
- OpenAI API Key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Juanpa0128j/-AI-Powered-Sales-MultiAgent-System-WhatsApp-Messenger.git
   cd AI-Powered-Sales-MultiAgent-System-WhatsApp-Messenger
   ```

2. Install dependencies (using uv or pip):
   ```bash
   pip install -e .
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Fill in your TWILIO_*, OPENAI_API_KEY, and DATABASE_URL
   ```

4. Run the development server:
   ```bash
   fastapi dev app/main.py
   ```

## 📝 Roadmap

- [ ] Implement full LangGraph state machine for pricing negotiation.
- [ ] Integrate Vector Database for semantic product search.
- [ ] Add support for multimedia response handling (sending images/PDFs).
- [ ] Develop a Dashboard for real-time monitoring of agent performance.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
