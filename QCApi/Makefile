.PHONY: format lint test build run docker-build docker-run

format:
	@poetry run black .

lint:
	@poetry run flake8 qcapi

test:
	@poetry run pytest

build:
	@poetry build

run:
	@poetry run uvicorn qcapi.main:app --reload

docker-build:
	docker build -t qcapi .

docker-run:
	docker run -p 8000:8000 qcapi
