FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements ./requirements

RUN pip install -r requirements/base.txt

COPY . .
