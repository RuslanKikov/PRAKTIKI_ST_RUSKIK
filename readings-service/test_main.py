from fastapi.testclient import TestClient
from main import app
from database import Base, engine
from datetime import datetime, timedelta

client = TestClient(app)

def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_add_reading_success():
    """Тест 1: Успешный ввод показаний"""
    response = client.post("/readings/", json={
        "meter_id": "TEST-METER",
        "value": 100,
        "reading_date": datetime.now().isoformat(),
        "source": "TEST"
    })
    assert response.status_code == 200
    assert response.json()["reading"]["status"] == "ACCEPTED"

def test_add_reading_anomaly():
    """Тест 2: Срабатывание аномалии (значение меньше предыдущего)"""
    # Вводим 50, хотя предыдущее было 100
    response = client.post("/readings/", json={
        "meter_id": "TEST-METER",
        "value": 50,
        "reading_date": (datetime.now() + timedelta(hours=1)).isoformat(),
        "source": "TEST"
    })
    assert response.status_code == 200
    assert response.json()["reading"]["status"] == "ANOMALY"
    assert "аномалия" in response.json()["warning"]

def test_fix_reading_success():
    """Тест 3: Успешное исправление аномалии"""
    # Получаем историю и находим аномалию
    res_get = client.get("/readings/TEST-METER")
    readings = res_get.json()
    anomaly_reading = next(r for r in readings if r["status"] == "ANOMALY")
    
    # Исправляем на 150 (больше предыдущего 100)
    res_put = client.put(f"/readings/{anomaly_reading['id']}", json={
        "value": 150,
        "reading_date": datetime.now().isoformat()
    })
    assert res_put.status_code == 200
    assert res_put.json()["reading"]["status"] == "CORRECTED"

def test_fix_reading_fail():
    """Тест 4: Запрет исправления на значение меньше предыдущего"""
    res_get = client.get("/readings/TEST-METER")
    readings = res_get.json()
    corrected_reading = next(r for r in readings if r["status"] == "CORRECTED")
    
    # Пытаемся исправить на 80 (что меньше первого показания 100)
    res_put = client.put(f"/readings/{corrected_reading['id']}", json={
        "value": 80,
        "reading_date": datetime.now().isoformat()
    })
    assert res_put.status_code == 400
    assert "Нельзя исправить" in res_put.json()["detail"]
