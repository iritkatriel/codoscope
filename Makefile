PYTHON ?= python3.13

.PHONY: test
test:
	$(PYTHON) -m unittest discover -s tests -v
