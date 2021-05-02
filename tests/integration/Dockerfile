FROM python:3.9-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /tests

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "python -m pytest ."]
