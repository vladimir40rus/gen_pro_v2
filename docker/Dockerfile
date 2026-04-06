FROM python:3.12-slim-bookworm

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/app

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev python3-dev curl\
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /opt

# Копируем requirements
COPY src/requirements.txt .

## Устанавливаем зависимости Python
#RUN pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
#    && pip install --no-cache-dir \
##    -i https://mirrors.aliyun.com/pypi/simple/ \
##    --trusted-host mirrors.aliyun.com \
#    -r requirements.txt
#
## Копируем исходный код
#COPY src/ .
##COPY tests/ ./tests/
#
## Создаем не-root пользователя
#RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /opt/app \
#    && chown -R appuser:appuser /opt/app
#USER appuser
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем всю папку src
COPY src/ .

