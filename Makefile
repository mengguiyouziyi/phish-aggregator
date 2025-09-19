install:
	python -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt

run:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

fetch-rules:
	python scripts/fetch_rules.py

fetch-models:
	python scripts/fetch_models.py --all

demo:
	bash scripts/demo_run.sh
