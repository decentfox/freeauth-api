FROM python:3.11

ARG PIP_INDEX_URL
ENV PIP_INDEX_URL=${PIP_INDEX_URL:-https://mirrors.aliyun.com/pypi/simple/}

WORKDIR /code
COPY .. /code/

WORKDIR /code/freeauth-admin

RUN pip install -U pip poetry
RUN poetry config virtualenvs.create false
RUN poetry install --without dev
