# Mini Prometheus — containerized verifier (mirrors the Velith M0 verifier pattern).
#
# This image is the reproducible shell that runs the project's quality gate INSIDE a pinned Linux
# container, so the host is never the source of truth for a verdict. Base image is pinned (no `latest`).
#
# Run (builds then runs the default gate — pytest — to green):
#   docker compose run --rm --build verifier
FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# Install dependencies first for better layer caching: the hatchling build needs the metadata + source.
COPY pyproject.toml ./
COPY src/ ./src/
# Mini Prometheus resolves `contracts.python.*` and reads `contracts/schemas/*` at runtime via the
# repo-root pythonpath, so the contracts tree must be present in the image (it is NOT part of the wheel).
COPY contracts/ ./contracts/
RUN pip install ".[dev]"

# Tests + fixtures are not part of the installed package; copy them in for execution.
COPY tests/ ./tests/

# Default action: run the test suite inside the pinned container (the currently-green gate).
# Override at the CLI for the other steps, e.g.:
#   docker compose run --rm verifier mypy src
#   docker compose run --rm verifier ruff check .      # red until the formatting normalization chore
CMD ["pytest", "-q"]
