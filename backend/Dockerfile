FROM python:3.12.9-alpine AS builder

# Don't buffer `stdout`:
ENV PYTHONUNBUFFERED=1
# Don't create `.pyc` files:
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
ADD pyproject.toml poetry.lock /app/

RUN apk add build-base libffi-dev curl

# # Rust Compiler Installation
# Get Rust; NOTE: using sh for better compatibility with other base images
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
# Add .cargo/bin to PATH
RUN echo '. $HOME/.cargo/env' >> $HOME/.bashrc
ENV PATH="/root/.cargo/bin:${PATH}"
# Check cargo is visible
RUN cargo --help
RUN rustc --version

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.in-project true
# Install Dependencies
RUN poetry install --no-ansi --without dev

RUN ls -a /app/

# ---

FROM python:3.12.9-alpine
WORKDIR /app

RUN apk add libgcc

COPY --from=builder /app /app
COPY --from=builder /app/.venv/lib/python3.12/site-packages/ /app/.venv/lib/python3.12/site-packages/
ADD . /app

ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
