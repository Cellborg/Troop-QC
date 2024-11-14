FROM python:3.9

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN python -m pip install --upgrade pip
RUN pip install poetry==1.7.0
RUN poetry install --no-dev

COPY ./qcapi /app/qcapi

EXPOSE 8001

# Command to run the FastAPI app with Uvicorn
CMD ["poetry", "run", "uvicorn", "qcapi.main:app", "--host", "0.0.0.0", "--port", "8001"]
