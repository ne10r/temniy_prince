PYTHON ?= python3
CONFIG ?= configs/pypi.csv

.PHONY: run order test demo

run:
	$(PYTHON) -m src.main --config "$(CONFIG)"

test:
	$(PYTHON) -m pytest tests/ -q

demo:
	$(PYTHON) scripts/demo_stage4.py

order:
	$(PYTHON) -m src.main --config "$(CONFIG)" --order
