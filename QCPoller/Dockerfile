FROM python:3.10-slim

RUN mkdir /app
WORKDIR /app

# Install necessary Python packages
RUN python -m pip install --upgrade pip
RUN pip install requests boto3

COPY QCPoller.py /app/QCPoller.py

# Command to run the Python script
CMD ["python", "/app/QCPoller.py"]
