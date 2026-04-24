PYTHON ?= python3.13
WEB_PORT ?= 8000
CPY_VERSION ?= 3.15

.PHONY: test web web-sync web-kill web-restart
test:
	$(PYTHON) -m unittest discover -s tests -v

web-sync:
	@test -d _site || (echo "_site/ not found. Build/stage the web site first." && exit 1)
	cp web/index.html _site/index.html
	cp web/driver.py _site/driver.py
	cp web/python.worker.mjs _site/python.worker.mjs
	@mkdir -p _site/cpython/$(CPY_VERSION)
	@for f in python.mjs python.wasm python$(CPY_VERSION).zip; do \
		if [ -f _site/$$f ] && [ ! -e _site/cpython/$(CPY_VERSION)/$$f ]; then \
			mv _site/$$f _site/cpython/$(CPY_VERSION)/$$f; \
		fi; \
	done

web: web-sync
	@echo "Serving codoscope web UI at http://localhost:$(WEB_PORT)"
	cd _site && $(PYTHON) -m http.server $(WEB_PORT)

web-kill:
	@pids=$$(lsof -t -iTCP:$(WEB_PORT) -sTCP:LISTEN 2>/dev/null); \
	if [ -z "$$pids" ]; then \
		echo "No web server listening on port $(WEB_PORT)"; \
	else \
		echo "Stopping process(es) on port $(WEB_PORT): $$pids"; \
		kill $$pids; \
	fi

web-restart: web-kill web
