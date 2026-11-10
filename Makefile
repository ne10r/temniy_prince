PYTHON ?= python3
CONFIG ?= configs/pypi.csv

.PHONY: run test demo

run:
	$(PYTHON) -m src.main --config "$(CONFIG)"

test:
	$(PYTHON) -m pytest tests/ -q

demo:
	$(PYTHON) scripts/demo_stage2.py
