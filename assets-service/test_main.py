from fastapi.testclient import TestClient
from main import app
from database import Base, engine

# Создаем тестовый клиент, который имитирует браузер
client = TestClient(app)

def setup_module(module):
    # ВАЖНО: Перед тестами мы очищаем базу данных, чтобы тесты не мешали друг другу
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_create_object_success():
    """Тест 1: Успешное создание объекта"""
    response = client.post("/objects/", json={"name": "Тестовая квартира", "address": "Улица Тестовая"})
    assert response.status_code == 200
    assert response.json()["name"] == "Тестовая квартира"

def test_duplicate_object_error():
    """Тест 2: Проверка защиты от дубликатов"""
    # Создаем объект в первый раз
    client.post("/objects/", json={"name": "Дубль", "address": "Улица"})
    # Пытаемся создать точно такой же объект во второй раз
    response = client.post("/objects/", json={"name": "Дубль", "address": "Улица"})
    # Ожидаем ошибку 400 Bad Request
    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]
