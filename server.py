from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt
import datetime

app = FastAPI()
Base = declarative_base()

class License(Base):
    __tablename__ = 'licenses'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    license_key = Column(String, nullable=False)
    expiration_date = Column(Date, nullable=True)
    machine_id = Column(String, default="")
    used = Column(Boolean, default=False)

DATABASE_URL = 'sqlite:///licenses.db'
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class VerifyRequest(BaseModel):
    username: str
    password: str
    license_key: str
    machine_id: str

class ResetRequest(BaseModel):
    admin_token: str
    username: str

@app.post("/verify")
async def verify_license(data: VerifyRequest):
    session = Session()
    lic = session.query(License).filter_by(username=data.username).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if not bcrypt.checkpw(data.password.encode(), lic.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    if lic.license_key != data.license_key:
        raise HTTPException(status_code=401, detail="Clave de licencia incorrecta.")
    if not lic.machine_id:
        lic.machine_id = data.machine_id
    elif lic.machine_id != data.machine_id:
        raise HTTPException(status_code=401, detail="La licencia no corresponde a esta máquina.")
    if lic.used:
        raise HTTPException(status_code=401, detail="La licencia ya fue utilizada.")
    if lic.expiration_date and datetime.datetime.now().date() > lic.expiration_date:
        raise HTTPException(status_code=401, detail="La licencia ha expirado.")
    lic.used = True
    session.commit()
    session.close()
    exp = lic.expiration_date.isoformat() if lic.expiration_date else None
    return {"success": True, "message": "Licencia válida.", "expiration_date": exp}

@app.post("/reset_license")
async def reset_license(data: ResetRequest):
    if data.admin_token != "TU_CLAVE_SECRETA_ADMIN":
        raise HTTPException(status_code=403, detail="No autorizado.")
    session = Session()
    lic = session.query(License).filter_by(username=data.username).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Licencia no encontrada.")
    lic.machine_id = ""
    lic.used = False
    session.commit()
    session.close()
    return {"success": True, "message": "Licencia reiniciada."}
