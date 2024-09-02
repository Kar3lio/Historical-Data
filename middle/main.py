from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Device, Hist, Role
from datetime import datetime
from pydantic import BaseModel
import bcrypt
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Permite todos los encabezados
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DeviceTypesRequest(BaseModel):
    types: List[str]

class HistRequest(BaseModel):
    id_device: List[int]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class AuthRequest(BaseModel):
    role_name: str
    password: str

@app.post("/device/")
def create_device(db: Session = Depends(get_db)):
    device = Device()
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

@app.get("/device")
def get_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return devices

@app.get("/device-types")
def get_device_types(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    types = list(set(device.type for device in devices))
    return types

@app.post("/devices-by-type/")
def get_devices_by_type(request: DeviceTypesRequest, db: Session = Depends(get_db)):
    types = request.types
    print(types)
    if types:
        # Filtrar los dispositivos que tienen un tipo en la lista de tipos proporcionada
        devices = db.query(Device).filter(Device.type.in_(types)).all()
    else:
        # Obtener todos los dispositivos si no hay tipos especificados
        devices = db.query(Device).all()
    
    # Retornar solo los ids y nombres de los dispositivos
    return [{"id": device.id_device, "name": device.name} for device in devices]

@app.post("/hist/")
def read_hists(request: HistRequest, db: Session = Depends(get_db)):
    id_device = request.id_device
    start_date = request.start_date
    end_date = request.end_date
    query = db.query(Hist)

    if id_device: 
        query = query.filter(Hist.id_device.in_(id_device)).order_by(Hist.event_datetime.desc())

    if start_date:
        query = query.filter(Hist.event_datetime >= start_date).order_by(Hist.event_datetime.desc())
    if end_date:
        query = query.filter(Hist.event_datetime <= end_date).order_by(Hist.event_datetime.desc())
    
    hist = query.all()    
    return hist

@app.get("/recent-hist/")
def get_last_100_histories(db: Session = Depends(get_db)):
    histories = (db.query(Hist.id_hist, Hist.event_datetime, Hist.value, Device.name.label("device_name"))
                 .join(Device, Hist.id_device == Device.id_device)
                 .order_by(Hist.event_datetime.desc())
                 .limit(100)
                 .all())

    # Retorna las historias con el nombre del dispositivo
    return [{"date_time": hist.event_datetime, "value": hist.value, "device_name": hist.device_name} for hist in histories]

@app.post("/auth/")
async def authenticate(request: AuthRequest, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.role_name == request.role_name).first()
    
    if not role or not role.check_password(request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect role or password")
    
    return {"role": role.role_name, "message": "Authenticated successfully"}

@app.post("/create-role/")
async def create_role(role_name: str, password: str, db: Session = Depends(get_db)):
    # Verificar si el rol ya existe
    if db.query(Role).filter(Role.role_name == role_name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")
    
    # Crear nuevo rol
    new_role = Role(role_name=role_name)
    new_role.set_password(password)
    
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    return {"role": new_role.role_name, "message": "Role created successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
