.PHONY: install env format lint test eval check run run-api run-ui run-bot docker-up docker-down

install:
	poetry install

env:
	cp .env.example .env

format:
	poetry run black src/ tests/
	poetry run ruff format src/ tests/

lint:
	poetry run ruff check src/ tests/
	poetry run mypy --strict src/

test:
	poetry run pytest tests/ -v

eval:
	poetry run pytest tests/test_golden_cases_eval.py -v

check: lint test eval

run:
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

run-api:
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000

run-ui:
	poetry run streamlit run src/ui/streamlit_app.py --server.port 8501

run-bot:
	poetry run python -m src.bot.telegram_bot

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down
