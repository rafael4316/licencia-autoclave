import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.orm import declarative_base, sessionmaker
import bcrypt
import datetime
import uvicorn

# Configuración del logger
tlogging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Configuración de la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'licenses.db')}"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo de Licencia
class License(Base):
    __tablename__ = 'licenses'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    license_key = Column(String, nullable=False)
    expiration_date = Column(Date, nullable=True)
    machine_id = Column(String, default="")
    used = Column(Boolean, default=False)

# Crear tablas si no existen
Base.metadata.create_all(engine)

# Instancia de FastAPI
app = FastAPI()

# Modelos Pydantic
class VerifyRequest(BaseModel):
    username: str
    password: str
    license_key: str
    machine_id: str

class ResetRequest(BaseModel):
    admin_token: str
    username: str

class CreateLicenseRequest(BaseModel):
    admin_token: str
    username: str
    password: str
    license_key: str
    expiration_date: str  # Formato "YYYY-MM-DD"

# Endpoint de verificación de licencia
@app.post("/verify")
async def verify_license(data: VerifyRequest):
    session = Session()
    lic = session.query(License).filter_by(username=data.username).first()
    if not lic:
        session.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if not bcrypt.checkpw(data.password.encode(), lic.password_hash.encode()):
        session.close()
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    if lic.license_key != data.license_key:
        session.close()
        raise HTTPException(status_code=401, detail="Clave de licencia incorrecta.")
    if not lic.machine_id:
        lic.machine_id = data.machine_id
    elif lic.machine_id != data.machine_id:
        session.close()
        raise HTTPException(status_code=401, detail="La licencia no corresponde a esta máquina.")
    if lic.used:
        session.close()
        raise HTTPException(status_code=401, detail="La licencia ya fue utilizada.")
    if lic.expiration_date and datetime.datetime.now().date() > lic.expiration_date:
        session.close()
        raise HTTPException(status_code=401, detail="La licencia ha expirado.")
    lic.used = True
    session.commit()
    exp = lic.expiration_date.isoformat() if lic.expiration_date else None
    session.close()
    return {"success": True, "message": "Licencia válida.", "expiration_date": exp}

# Endpoint para resetear licencia
@app.post("/reset_license")
async def reset_license(data: ResetRequest):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "TU_CLAVE_SECRETA_ADMIN")
    if data.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado.")
    session = Session()
    lic = session.query(License).filter_by(username=data.username).first()
    if not lic:
        session.close()
        raise HTTPException(status_code=404, detail="Licencia no encontrada.")
    lic.machine_id = ""
    lic.used = False
    session.commit()
    session.close()
    return {"success": True, "message": "Licencia reiniciada."}

# Endpoint para crear licencias remotamente
@app.post("/create_license")
async def create_license(data: CreateLicenseRequest):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "TU_CLAVE_SECRETA_ADMIN")
    if data.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado.")
    session = Session()
    if session.query(License).filter_by(username=data.username).first():
        session.close()
        raise HTTPException(status_code=409, detail="Usuario ya existe.")
    try:
        expiration_date = datetime.datetime.fromisoformat(data.expiration_date).date()
    except ValueError:
        session.close()
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
    pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    new_license = License(
        username=data.username,
        password_hash=pw_hash,
        license_key=data.license_key,
        expiration_date=expiration_date,
        machine_id="",
        used=False
    )
    session.add(new_license)
    session.commit()
    session.close()
    return {"success": True, "message": "Licencia creada."}

# Endpoint raíz para comprobación rápida
@app.get("/")
async def root():
    return {"message": "API de licencias al aire ✔️"}

# Arranque de Uvicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
