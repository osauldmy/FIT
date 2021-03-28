FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

# Add this line in order to provide basic `docker run output`
# To be removed later!
CMD ["echo", "Hello World!"]
