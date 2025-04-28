import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.orm import declarative_base, sessionmaker
import bcrypt
import datetime
import uvicorn

# ——————————————
# BASE_DIR y DATABASE_URL Correcto
# ——————————————
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'licenses.db')}"

# ——————————————
# Logging
# ——————————————
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ——————————————
# App y Base de datos
# ——————————————
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

engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# ——————————————
# Pydantic models
# ——————————————
class VerifyRequest(BaseModel):
    username: str
    password: str
    license_key: str
    machine_id: str

class ResetRequest(BaseModel):
    admin_token: str
    username: str

# ——————————————
# Endpoints
# ——————————————
@app.post("/verify")
async def verify_license(data: VerifyRequest):
    logger.info(f"Received /verify request: username={data.username!r}, machine_id={data.machine_id!r}")
    session = Session()
    lic = session.query(License).filter_by(username=data.username).first()
    if not lic:
        session.close()
        logger.warning(f"Usuario no encontrado: {data.username}")
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if not bcrypt.checkpw(data.password.encode(), lic.password_hash.encode()):
        session.close()
        logger.warning(f"Contraseña incorrecta para user: {data.username}")
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    if lic.license_key != data.license_key:
        session.close()
        logger.warning(f"Clave de licencia incorrecta para user: {data.username}")
        raise HTTPException(status_code=401, detail="Clave de licencia incorrecta.")
    if not lic.machine_id:
        lic.machine_id = data.machine_id
    elif lic.machine_id != data.machine_id:
        session.close()
        logger.warning(f"Machine ID no coincide para user: {data.username}")
        raise HTTPException(status_code=401, detail="La licencia no corresponde a esta máquina.")
    if lic.used:
        session.close()
        logger.warning(f"Licencia ya usada para user: {data.username}")
        raise HTTPException(status_code=401, detail="La licencia ya fue utilizada.")
    if lic.expiration_date and datetime.datetime.now().date() > lic.expiration_date:
        session.close()
        logger.warning(f"Licencia expirada para user: {data.username}")
        raise HTTPException(status_code=401, detail="La licencia ha expirado.")
    lic.used = True
    session.commit()
    exp = lic.expiration_date.isoformat() if lic.expiration_date else None
    session.close()
    logger.info(f"Licencia validada con éxito para user: {data.username}")
    return {"success": True, "message": "Licencia válida.", "expiration_date": exp}

@app.post("/reset_license")
async def reset_license(data: ResetRequest):
    logger.info(f"Received /reset_license request for user: {data.username}")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "TU_CLAVE_SECRETA_ADMIN")
    if data.admin_token != ADMIN_TOKEN:
        logger.warning("Intento de reset no autorizado")
        raise HTTPException(status_code=403, detail="No autorizado.")
    session = Session()
    lic = session.query(License).filter_by(username=data.username).first()
    if not lic:
        session.close()
        logger.warning(f"Licencia no encontrada para reset: {data.username}")
        raise HTTPException(status_code=404, detail="Licencia no encontrada.")
    lic.machine_id = ""
    lic.used = False
    session.commit()
    session.close()
    logger.info(f"Licencia reiniciada para user: {data.username}")
    return {"success": True, "message": "Licencia reiniciada."}

# ——————————————
# Lanzar Uvicorn
# ——————————————
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )
