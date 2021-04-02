# Apixy Backend

This repository contains the backend component of Apixy.

## Local development

In order to start development right away:

```shell
git clone git@gitlab.fit.cvut.cz:apixy/apixy-be
cd apixy-be
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pre-commit
pre-commit install
git checkout your_branch # optional step
pre-commit run --all-files # optional step to create cache
```

## Docker

Building a docker image:

```shell
docker build -t apixy-be .
```

Running a docker container:

```shell
docker run --rm apixy
```

## Running the web server locally

Copy the .env.sample file and edit the values:

```shell
cp .env.sample .env
```

Run the db and migrate containers:

```shell
docker-compose up --build db migrate
```

Run the api component locally (--reload for autoreload on file change):

```shell
uvicorn apixy.app:app --reload
```

## Running the entire app in docker

Copy the .env.sample file and edit the values:

```shell
cp .env.sample .env
```

Run the app:

```shell
docker-compose up --build
```
