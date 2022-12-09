PICS_DIR ?=

backend/requirements.txt: backend/requirements.in
	pip-compile -o backend/requirements.txt backend/requirements.in

venv: backend/requirements.txt
	python3 -m venv venv
	./venv/bin/pip install -r backend/requirements.txt
	touch venv

.PHONY: run

run: venv
	uvicorn --reload --reload-dir backend/pics_sorter --factory 'pics_sorter.__main__:main'

run_python:
	python3 -m pics_sorter $(PICS_DIR)
