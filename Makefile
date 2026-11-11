PYTHON ?= python3
CONFIG ?= configs/dateutil.csv

.PHONY: run order test demo

run:
	$(PYTHON) -m src.main --config "$(CONFIG)"

test:
	$(PYTHON) -m pytest tests/ -q

demo:
	$(PYTHON) -m scripts.demo_stage5

order:
	$(PYTHON) -m src.main --config "$(CONFIG)" --order
