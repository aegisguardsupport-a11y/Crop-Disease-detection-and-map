.PHONY: install lint fmt typecheck test smoke clean help

help:
	@echo "Targets:"
	@echo "  install   - install dev dependencies into the active venv"
	@echo "  lint      - ruff check"
	@echo "  fmt       - ruff format + auto-fix"
	@echo "  typecheck - mypy on src/"
	@echo "  test      - pytest, excluding @slow tests"
	@echo "  smoke     - pytest -m slow (loads the model)"
	@echo "  clean     - remove caches"

install:
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	pip install -e .

lint:
	ruff check src tests

fmt:
	ruff format src tests
	ruff check --fix src tests

typecheck:
	mypy src

test:
	pytest -m "not slow"

smoke:
	pytest -m slow -v tests/test_model_loader.py

serve:
	python -m uvicorn cpl_crop.api.app:create_app --factory --host 127.0.0.1 --port 8000

serve-reload:
	python -m uvicorn cpl_crop.api.app:create_app --factory --host 127.0.0.1 --port 8000 --reload

ui:
	python -m streamlit run streamlit_app/streamlit_app.py --server.port 8501

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
