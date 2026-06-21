.PHONY: help install dev test lint build up down seed

help:
	@echo "install  - install backend + frontend deps"
	@echo "test     - run backend tests"
	@echo "lint     - ruff check backend"
	@echo "up/down  - docker compose up/down"
	@echo "seed     - create an admin user (EMAIL=, PASSWORD=)"

install:
	cd backend && pip install -r requirements.txt && python -m playwright install chromium
	cd frontend && npm install

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check app

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

seed:
	docker compose exec api python -m app.cli create-user --email $(EMAIL) --password $(PASSWORD) --admin
