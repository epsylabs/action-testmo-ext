FROM python:3-slim

ADD . /app

WORKDIR /app

RUN pip install --target=/app -r requirements.txt

ENV PYTHONPATH /app

ENTRYPOINT ["python", "/app/testmo_wcli/cli.py"]
