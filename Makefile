
# Makefile for Agentic Sales System

.PHONY: setup install-python install-node run-backend run-bridge test clean help

# Default target
help:
	@echo "Agentic Sales System - Automation Commands"
	@echo "------------------------------------------"
	@echo "make setup        - Install all dependencies (Python & Node.js) and setup .env"
	@echo "make run-backend  - Start the Python Brain (FastAPI)"
	@echo "make run-bridge   - Start the Node.js Bridge (WhatsApp)"
	@echo "make run-dashboard - Start the Product Manager Dashboard"
	@echo "make test         - Run all automated tests"
	@echo "make db-up        - Start Local Postgres DB (Docker)"
	@echo "make db-down      - Stop Local Postgres DB"
	@echo "make clean        - Remove cache and temporary files"

setup: install-python install-node .env

install-python:
	@echo "📦 Installing Python dependencies with uv..."
	uv sync

install-node:
	@echo "📦 Installing Node.js dependencies..."
	cd whatsapp-gateway && npm install

.env:
	@echo "📝 Creating .env from .env.example..."
	cp .env.example .env
	@echo "⚠️  Don't forget to add your OPENAI_API_KEY to .env!"

run-backend:
	@echo "🧠 Starting Python Brain..."
	uv run uvicorn app.main:app --port 8000 --reload

run-bridge:
	@echo "🌉 Starting Node.js Bridge..."
	cd whatsapp-gateway && node index.js

test:
	@echo "🧪 Running Tests..."
	PYTHONPATH=. uv run pytest tests/

clean:
	@echo "🧹 Cleaning up..."
	rm -rf __pycache__ .pytest_cache
	rm -rf app/__pycache__ app/*/__pycache__
	rm -rf tests/__pycache__
	@echo "✨ Clean complete."

run-dashboard:
	@echo "📊 Starting Dashboard..."
	uv run streamlit run dashboard.py

db-up:
	@echo "🐘 Starting PostgreSQL (pgvector)..."
	docker-compose up -d
	@echo "✅ Database running on localhost:5432"

db-down:
	@echo "🛑 Stopping PostgreSQL..."
	docker-compose down
