FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем зависимости Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Указываем порт
EXPOSE 8000

# Команда по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
