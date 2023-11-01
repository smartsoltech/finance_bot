#!/bin/bash

# Остановить контейнеры
docker-compose down

# Получить последние обновления
git pull

# Пересобрать и запустить контейнеры
docker-compose up --build -d
