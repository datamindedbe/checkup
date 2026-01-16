.PHONY: format lint

format:
	ruff check --fix
	ruff format

lint:
	ruff check
