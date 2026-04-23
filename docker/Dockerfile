# syntax=docker/dockerfile:1
# syntax directive is used to enable Docker BuildKit

ARG PYTHON_VERSION=3.14

FROM python:${PYTHON_VERSION}-slim AS base

ARG PROJECT_DIR="/src"
ARG APP_USER="app"
ARG APP_GROUP="app"
ARG NEW_UID
ARG NEW_GID

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2

# Create a non-privileged user that the app will run under.
RUN groupadd --system ${APP_GROUP} --gid=${NEW_GID} && \
    adduser \
        --disabled-password \
        --gecos "" \
        --uid ${NEW_UID} \
        --gid ${NEW_GID} \
        ${APP_USER}

# Runtime-only system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssl \
        libssl3 \
        libsodium23 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${PROJECT_DIR}

# Builder stage for compilation and dependencies
FROM base AS builder

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        pkg-config \
        libssl-dev \
        libsodium-dev \
        build-essential \
        swig \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install poetry==${POETRY_VERSION}

# Compile liboprf
WORKDIR /liboprf
RUN git clone --depth 1 --branch v0.9.3 https://github.com/stef/liboprf.git . && \
    cd src && \
    make

# Install Python dependencies into a virtualenv
WORKDIR ${PROJECT_DIR}
COPY ./pyproject.toml ./poetry.lock ./

ENV POETRY_CACHE_DIR=/tmp/poetry-cache \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true

RUN --mount=type=cache,target=${POETRY_CACHE_DIR} \
    poetry install --no-root --no-interaction --only main

# Final stage
FROM base AS final

# Copy compiled libraries
COPY --from=builder /liboprf/src/noise_xk/lib*.so /usr/local/lib/
COPY --from=builder /liboprf/src/lib*.so /usr/local/lib/
RUN ldconfig

# Set different virtualenv path for runtime to avoid issues when mounting source code
ENV VIRTUAL_ENV="/opt/app/docker-venv"
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# Copy only the virtualenv — no pip, no poetry, no build tools
COPY --from=builder --chown=${APP_USER}:${APP_GROUP} /src/.venv ${VIRTUAL_ENV}

# Copy only what the app needs at runtime (no tests, docs, CI artifacts, etc.)
COPY --chown=${APP_USER}:${APP_GROUP} app/ /src/app/
COPY --chown=${APP_USER}:${APP_GROUP} app.conf.example /src/

# version.json is generated from build args so CI workspace artifacts never leak in
ARG RELEASE_VERSION=dev
ARG GIT_SHA=unknown
RUN echo "{\"version\": \"${RELEASE_VERSION}\", \"git_ref\": \"${GIT_SHA}\"}" > /src/version.json \
    && chown ${APP_USER}:${APP_GROUP} /src/version.json

COPY --chmod=755 ./docker/init-standalone.sh /usr/local/bin/
COPY --chmod=755 ./docker/init.sh /usr/local/bin/

ARG standalone=false

RUN if [ "$standalone" = "true" ] ; then \
    ln -sf /usr/local/bin/init-standalone.sh /docker-entrypoint.sh; \
  else \
    ln -sf /usr/local/bin/init.sh /docker-entrypoint.sh ; \
  fi

USER ${APP_USER}

EXPOSE 8515
WORKDIR ${PROJECT_DIR}

CMD ["/docker-entrypoint.sh"]
