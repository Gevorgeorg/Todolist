FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry 2.0.1
ENV POETRY_VERSION=2.0.1
RUN pip install "poetry==$POETRY_VERSION"

# Отключаем создание виртуального окружения
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml ./

# Создаем poetry.lock и устанавливаем зависимости
RUN poetry lock --no-interaction && \
    poetry install --no-interaction --no-ansi --no-root

# Устанавливаем django-cors-headers отдельно (если нужно)
RUN pip install django-cors-headers

# Копируем остальной код
COPY . .

# Создаем папки
RUN mkdir -p /app/staticfiles /app/media

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]