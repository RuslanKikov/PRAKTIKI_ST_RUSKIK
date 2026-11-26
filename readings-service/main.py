from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import models, schemas, broker
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Readings Service")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.post("/readings/")
def add_reading(reading: schemas.ReadingCreate, db: Session = Depends(get_db)):
    if reading.value <= 0:
        raise HTTPException(status_code=400, detail="Значение должно быть > 0")

    last_reading = db.query(models.Reading).filter(
        models.Reading.meter_id == reading.meter_id
    ).order_by(models.Reading.reading_date.desc()).first()
    
    status = "ACCEPTED"
    warning = None
    if last_reading and reading.value < last_reading.value:
        status = "ANOMALY"
        warning = "Внимание: значение меньше предыдущего (аномалия)"

    new_reading = models.Reading(**reading.model_dump(), status=status)
    db.add(new_reading)
    db.commit()
    db.refresh(new_reading)

    broker_status = broker.send_event({
        "action": "ADDED", "meter_id": new_reading.meter_id, "value": new_reading.value
    })
    return {"reading": new_reading, "warning": warning, "broker_status": broker_status}

@app.put("/readings/{reading_id}")
def update_reading(reading_id: str, update_data: schemas.ReadingUpdate, db: Session = Depends(get_db)):
    db_reading = db.query(models.Reading).filter(models.Reading.id == reading_id).first()
    if not db_reading:
        raise HTTPException(status_code=404, detail="Показание не найдено")

    if update_data.value <= 0:
        raise HTTPException(status_code=400, detail="Значение должно быть > 0")

    # Ищем предыдущее показание (не считая текущее исправляемое)
    prev_reading = db.query(models.Reading).filter(
        models.Reading.meter_id == db_reading.meter_id,
        models.Reading.reading_date < db_reading.reading_date,
        models.Reading.id != reading_id
    ).order_by(models.Reading.reading_date.desc()).first()

    # Если есть предыдущее и новое значение всё ещё меньше — отклоняем
    if prev_reading and update_data.value < prev_reading.value:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя исправить: {update_data.value} меньше предыдущего показания ({prev_reading.value}). Введите корректное значение."
        )

    db_reading.value = update_data.value
    db_reading.reading_date = update_data.reading_date
    db_reading.status = "CORRECTED"
    db.commit()
    db.refresh(db_reading)

    broker_status = broker.send_event({
        "action": "CORRECTED", "reading_id": db_reading.id, "new_value": db_reading.value
    })
    return {"message": "Показания исправлены", "reading": db_reading, "broker_status": broker_status}

@app.get("/readings/{meter_id}")
def get_readings(meter_id: str, db: Session = Depends(get_db)):
    return db.query(models.Reading).filter(models.Reading.meter_id == meter_id).all()
