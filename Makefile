.PHONY: help data demo eval calibrate test lint clean

help:
	@echo "make data   - regenerate the synthetic case fixtures"
	@echo "make demo   - run the pipeline over the synthetic cases"
	@echo "make eval   - score routing against reviewer labels"
	@echo "make calibrate - sweep routing bands and show the trade-off"
	@echo "make test   - run the test suite (standard library only)"
	@echo "make lint   - run ruff, if installed"

data:
	python3 -m kyc_pipeline.synthetic --out data/synthetic/cases.json

demo:
	python3 -m kyc_pipeline.demo

eval:
	python3 -m kyc_pipeline.evaluation

calibrate:
	python3 -m kyc_pipeline.calibration

test:
	python3 -m unittest discover -s tests -v

lint:
	ruff check kyc_pipeline tests

clean:
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
