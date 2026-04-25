# ──────────────────────────────────────────────────────────
# OpenEnv Data Pipeline Debugger — Makefile
# ──────────────────────────────────────────────────────────
# Usage:
#   make setup    — Install dependencies
#   make test     — Run test suite
#   make serve    — Start the environment server
#   make train    — Run curriculum training
#   make infer    — Run inference on all tasks
#   make demo     — Run demo mode (generate sample replays)
#   make bench    — Run benchmark comparison
#   make clean    — Remove generated files
# ──────────────────────────────────────────────────────────

.PHONY: setup test serve train infer demo bench clean lint help

# Default target
help:
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║    OpenEnv Data Pipeline Debugger — Commands        ║"
	@echo "╠══════════════════════════════════════════════════════╣"
	@echo "║  make setup     Install dependencies               ║"
	@echo "║  make test      Run test suite                     ║"
	@echo "║  make serve     Start environment server           ║"
	@echo "║  make train     Run curriculum training            ║"
	@echo "║  make infer     Run inference on all tasks         ║"
	@echo "║  make bench     Run benchmark comparison           ║"
	@echo "║  make demo      Generate sample replays            ║"
	@echo "║  make clean     Remove generated files             ║"
	@echo "╚══════════════════════════════════════════════════════╝"

# ── Setup ──────────────────────────────────────────────────
setup:
	pip install -r requirements.txt
	@echo ""
	@echo "✅  Dependencies installed."
	@echo "📝  Copy .env.example to .env and fill in your HF_TOKEN:"
	@echo "    cp .env.example .env"

# ── Test ───────────────────────────────────────────────────
test:
	python -m pytest tests/ -v --tb=short

# ── Serve ──────────────────────────────────────────────────
serve:
	python -m uvicorn app:app --host 0.0.0.0 --port 7860 --reload

# ── Train ──────────────────────────────────────────────────
train:
	python train.py --steps 50 --replay-dir replays/

# ── Inference ──────────────────────────────────────────────
infer:
	python inference.py

# ── Benchmark ──────────────────────────────────────────────
bench:
	python benchmarks/run_benchmarks.py

# ── Demo ───────────────────────────────────────────────────
demo:
	python train_replay_patch.py
	@echo "✅  Demo replay generated: replay_ep_test.html"

# ── Clean ──────────────────────────────────────────────────
clean:
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	rm -rf replays/ 2>/dev/null || true
	@echo "✅  Cleaned generated files."

# ── Lint ───────────────────────────────────────────────────
lint:
	python -m py_compile app.py
	python -m py_compile inference.py
	python -m py_compile train.py
	python -m py_compile multi_agent.py
	python -m py_compile curriculum.py
	python -m py_compile visualize.py
	python -m py_compile env/environment.py
	@echo "✅  All files compile OK."
