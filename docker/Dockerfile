# syntax=docker/dockerfile:1
# syntax directive is used to enable Docker BuildKit

ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim AS base

ARG PROJECT_DIR="/src"
ARG APP_USER="app"
ARG APP_GROUP="app"
ARG NEW_UID
ARG NEW_GID

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_CACHE_DIR=/tmp/poetry-cache \
    POETRY_VIRTUALENVS_CREATE=false

# Create a non-privileged user that the app will run under.
RUN groupadd --system ${APP_GROUP} --gid=${NEW_GID} && \
    adduser \
        --disabled-password \
        --gecos "" \
        --uid ${NEW_UID} \
        --gid ${NEW_GID} \
        ${APP_USER}

RUN apt update && \
    apt install -y \
        git \
        gnupg2 \
        libsqlite3-dev \
        build-essential \
        curl

RUN pip3 install --upgrade pip && \
    pip3 install poetry==1.7 --no-cache-dir

WORKDIR ${PROJECT_DIR}

FROM base AS builder

COPY ./pyproject.toml ./poetry.lock ./
RUN --mount=type=cache,target=${POETRY_CACHE_DIR} poetry install --no-root --no-interaction

FROM base AS final

COPY --chown=${APP_USER}:${APP_GROUP} --from=builder /usr/local /usr/local

# Somehow packages in this dir are not owned by the app user
RUN chown -R ${APP_USER}:${APP_GROUP} /usr/local/lib/python3.11/site-packages

USER ${APP_USER}

EXPOSE 8510:8510
WORKDIR ${PROJECT_DIR}

ENV PYTHONPATH=${PROJECT_DIR}

CMD docker/./init.sh
