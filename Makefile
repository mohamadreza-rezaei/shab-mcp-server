# Shab MCP — local dev helpers
.DEFAULT_GOAL := help
.SHELL := /bin/bash

.PHONY: help sync test test-live lint run run-stdio health

help: ## Show targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_.-]+:.*?## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

sync: ## Install runtime + dev deps (uv)
	uv sync --extra dev

test: ## Run unit tests (mocked; default)
	uv sync --extra dev
	uv run pytest -q

test-live: ## Run unit + live API tests (needs network)
	uv sync --extra dev
	uv run pytest -q -m ''

lint: ## Ruff check
	uv sync --extra dev
	uv run ruff check src tests

run: ## Run MCP Streamable HTTP (default :8000)
	uv run shab-mcp

run-stdio: ## Run MCP over stdio
	SHAB_MCP_TRANSPORT=stdio uv run shab-mcp

health: ## GET /health on local server
	curl -sS "http://127.0.0.1:$${SHAB_MCP_PORT:-8000}/health" | python3 -m json.tool
