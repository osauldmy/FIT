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
