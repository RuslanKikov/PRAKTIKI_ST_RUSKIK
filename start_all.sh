#!/bin/bash

# Переходим в директорию, где лежит сам скрипт (это делает его универсальным)
cd "$(dirname "$0")"

# Активируем виртуальное окружение
source venv/Scripts/activate

echo "Запуск Сервиса счётчиков (порт 8001)..."
cd assets-service
uvicorn main:app --port 8001 > /dev/null 2>&1 &
PID1=$!

echo "Запуск Сервиса показаний (порт 8002)..."
cd ../readings-service
uvicorn main:app --port 8002 > /dev/null 2>&1 &
PID2=$!

echo "Запуск Сайта (порт 8080)..."
cd ../frontend
python -m http.server 8080 > /dev/null 2>&1 &
PID3=$!

echo "========================================="
echo "Все сервисы успешно запущены!"
echo "Сайт доступен по адресу: http://localhost:8080"
echo "Для остановки нажмите Ctrl+C"
echo "========================================="

trap "echo 'Остановка всех сервисов...'; kill $PID1 $PID2 $PID3; exit" INT
wait
