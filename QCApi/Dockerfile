FROM python:3.10

WORKDIR /app
RUN touch /app/README.md

COPY pyproject.toml poetry.lock /app/

RUN python -m pip install --upgrade pip
RUN pip install poetry==1.7.0
RUN poetry install --no-dev

COPY ./qcapi /app/qcapi

RUN poetry build

EXPOSE 8001

# Command to run the FastAPI app with Uvicorn
CMD ["poetry", "run", "uvicorn", "qcapi.main:app", "--host", "0.0.0.0", "--port", "8001"]
