PYTHON = python3
UV = uv
VENV = .venv
RUN_PY = $(VENV)/bin/python

.PHONY: all install run debug clean lint lint-strict

all: install

install:
		$(UV) venv $(VENV)
		$(UV) pip install -e . --extra dev

run:
		@if [ -z "$(MAP)" ]; then \
				echo "Uso: make run MAP=caminho/para/mapa.txt"; \
				exit 1; \
		fi
		$(RUN_PY) main.py $(MAP)

debug:
		@if [ -z "$(MAP)" ]; then \
				echo "Uso: make run MAP=caminho/para/mapa.txt"; \
				exit 1; \
		fi
		$(RUN_PY) -m pdb main.py $(MAP)

clean:
		rm -rf $(VENV)
		rm -rf .mypy_cache .pytest_cache
		find . -type d -name "__pycache__" -exec rm -rf {} +
		find . -type f -name "*.pyc" -delete

lint:
		$(RUN_PY) -m flake8 .
		$(RUN_PY) -m mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs src/ main.py

lint-strict:
		$(RUN_PY) -m flake8 .
		$(RUN_PY) -m mypy --strict src/ main.py
