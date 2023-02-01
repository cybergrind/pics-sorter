PICS_DIR ?=
MESSAGE ?=

backend/requirements.txt: backend/requirements.in
	pip-compile -o backend/requirements.txt backend/requirements.in

venv: backend/requirements.txt
	python3.11 -m venv venv
	./venv/bin/pip install -r backend/requirements.txt
	touch venv

.PHONY: run

run: venv frontend/pics-sorter/build/index.html
	uvicorn --host=0.0.0.0 --port=8113 --reload --reload-dir backend/pics_sorter --factory 'pics_sorter.__main__:main'

run_python:
	python3 -m pics_sorter $(PICS_DIR)


build-front: frontend/pics-sorter/build/index.html


frontend/pics-sorter/build/index.html: frontend/pics-sorter/src/**/*
	cd frontend/pics-sorter && pnpm run build


generate-migration:
	@if [ -z "$(MESSAGE)" ]; then echo "MESSAGE is not defined"; exit 1; fi
	alembic revision --autogenerate -m "$(MESSAGE)"

migrate:
	alembic upgrade head
