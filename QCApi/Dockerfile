FROM python:3.12

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN pip install poetry && poetry install --no-dev

COPY ./qcapi /app/qcapi

EXPOSE 8001

# Command to run the FastAPI app with Uvicorn
CMD ["poetry", "run", "uvicorn", "qcapi.main:app", "--host", "0.0.0.0", "--port", "8001"]
