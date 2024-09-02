from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .database import get_db
from .models import Role

router = APIRouter()

# Configura el contexto para usar bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/auth/")
def authenticate_role(role_name: str, password: str, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.role_name == role_name).first()
    
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if not verify_password(password, role.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    return {"message": "Authentication successful"}

@router.post("/create-role/")
def create_role(role_name: str, password: str, db: Session = Depends(get_db)):
    hashed_password = hash_password(password)
    role = Role(role_name=role_name, password_hash=hashed_password)
    db.add(role)
    db.commit()
    return {"message": "Role created successfully"}
