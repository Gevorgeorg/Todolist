FROM python:3.12-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
ENV POETRY_VERSION=2.0.1
RUN pip install "poetry==$POETRY_VERSION"
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1

WORKDIR /app

# Зависимости
COPY pyproject.toml ./
RUN poetry lock --no-interaction && poetry install --no-interaction --no-ansi --no-root

# Устанавливаем gunicorn и curl (для healthcheck)
RUN pip install gunicorn

# Копируем код
COPY . .

# Папки
RUN mkdir -p /app/staticfiles /app/media

EXPOSE 8000