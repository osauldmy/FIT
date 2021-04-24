FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN useradd -m user
USER user

CMD ["sh", "-c", "uvicorn apixy.app:app --host 0.0.0.0"]
