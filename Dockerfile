# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker/54763270#54763270
# Copyright (c) 2023  Parker Wahle - Licensed under MIT License (do whatever you want)

# Please note that this only pegs Python 3.12. It is very possible that a later patch version of 3.12 causes some
# breaking API changes.
FROM python:3.13-slim-bookworm AS base

# debian is used over alpine because google tesseract is not available in the alpine repositories, and I don't want to
# write an apk build script to compile it myself.

# In Python, the line between a compile-time and run-time dependency is blurry,
# so we play it safe by installing everything
RUN apt-get update \
    && apt-get install -y tzdata gcc libc6-dev libffi-dev libssl-dev ca-certificates make git curl libtesseract-dev libtesseract5 tesseract-ocr tesseract-ocr-all \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

# --------------------------------------
# ---------- Copy and compile ----------
# We use a multi-stage build to reduce the size of the final image
FROM base AS builder

# Configure env variables for build/install
# ENV no longer adds a layer in new Docker versions,
# so we don't need to chain these in a single line
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=120
ENV POETRY_VERSION=2.1.3

# Install system deps
RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /code
# Although it would be very convienient to only copy the pyproject.toml file so that we can cache the dependencies,
# Poetry requires the whole project to be present in order to install the dependencies
COPY . /code

# Install with poetry
# pip install would probably work, too, but we'd have to make sure it's a recent enough pip
# Don't bother creating a virtual env -- significant performance increase
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --only main

# Build the package
RUN poetry build

# --------------------------------------
# ---------- Install & run! ------------
FROM base AS runner

# Set labels

# See https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL name="vnc-mcp"
LABEL version="0.1.0"
LABEL vendor="Parker Wahle"
LABEL org.opencontainers.image.title="vnc-mcp"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.url="https://github.com/regulad/vnc-mcp"
LABEL org.opencontainers.image.documentation="https://vnc-mcp.readthedocs.io"

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV TZ=America/New_York

ARG USERNAME=vnc_mcp
ARG USER_UID=1008
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID --shell /bin/sh --create-home $USERNAME

# Switch to non-root user (for security)
# This makes dockerfile_lint complain, but it's fine
# dockerfile_lint - ignore
USER $USERNAME
ENV PATH="/home/$USERNAME/.local/bin:${PATH}"

# Install the package in the user space
COPY --from=builder /code/dist/vnc_mcp-*.whl /tmp/
RUN pip install --user /tmp/vnc_mcp-*.whl

# Now do something!
CMD ["vnc-mcp"]

# or expose a port:
# EXPOSE 8080/tcp
