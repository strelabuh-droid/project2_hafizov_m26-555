.PHONY: install run lint format build

install:
	uv sync --locked

run:
	uv run database

lint:
	uv run ruff check .

format:
	uv run ruff format .

build:
	uv build