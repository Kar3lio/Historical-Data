from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import bcrypt

Base = declarative_base()

class Device(Base):
    __tablename__ = "device"
    id_device = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)

class Hist(Base):
    __tablename__ = "hist"
    id_hist = Column(Integer, primary_key=True, index=True)
    id_device = Column(Integer, ForeignKey("device.id_device"))
    event_datetime = Column(DateTime, default=datetime.utcnow)
    value = Column(Float)

    device = relationship("Device", back_populates="hist")

Device.hist = relationship("Hist", back_populates="device")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Hash the password before storing it
    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Verify password
    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
