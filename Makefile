.PHONY: help build up down logs backend-test frontend-build demo

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

build: ## Build all docker images
	docker compose build

up: ## Start the full stack
	docker compose up -d --build

down: ## Stop containers
	docker compose down

logs: ## Tail combined logs
	docker compose logs -f

backend-test: ## Run backend pytest suite
	docker compose run --rm backend pytest -q

backend-shell: ## Open a shell in the backend container
	docker compose run --rm backend bash

frontend-build: ## Build the frontend static bundle
	docker compose run --rm frontend npm run build

demo: ## Run a headless pipeline demo through the API (requires stack up)
	python backend/scripts/run_demo.py

clean: ## Remove containers and volumes
	docker compose down -v
