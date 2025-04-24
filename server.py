from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib
import datetime

app = Flask(__name__)
CORS(app)

# Configuración de SQLAlchemy y definición del modelo de Licencia
Base = declarative_base()

class License(Base):
    __tablename__ = 'licenses'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    license_key = Column(String, nullable=False)
    expiration_date = Column(Date, nullable=False)
    machine_id = Column(String, default="")  # Se asigna en el primer uso
    used = Column(Boolean, default=False)

# Usaremos SQLite para persistir los datos
DATABASE_URL = 'sqlite:///licenses.db'
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def is_license_valid(username, password, license_key, machine_id):
    session = Session()
    lic = session.query(License).filter_by(username=username).first()
    if not lic:
        session.close()
        return False, "Usuario no encontrado."
    
    if lic.password_hash != hashlib.sha256(password.encode()).hexdigest():
        session.close()
        return False, "Contraseña incorrecta."
    
    if lic.license_key != license_key:
        session.close()
        return False, "Clave de licencia incorrecta."
    
    if not lic.machine_id:
        lic.machine_id = machine_id
    else:
        if lic.machine_id != machine_id:
            session.close()
            return False, "La licencia no es válida para esta máquina."
    
    if lic.used:
        session.close()
        return False, "La licencia ya fue utilizada."
    
    try:
        if datetime.datetime.now().date() > lic.expiration_date:
            session.close()
            return False, "La licencia ha expirado."
    except Exception as e:
        session.close()
        return False, f"Formato de fecha de expiración incorrecto: {e}"
    
    lic.used = True
    session.commit()
    session.close()
    return True, "Licencia válida."

@app.route("/verify", methods=["POST"])
def verify():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No se proporcionaron datos."}), 400

    username = data.get("username")
    password = data.get("password")
    license_key = data.get("license_key")
    machine_id = data.get("machine_id")

    if not all([username, password, license_key, machine_id]):
        return jsonify({"success": False, "message": "Faltan datos."}), 400

    valid, message = is_license_valid(username, password, license_key, machine_id)
    return jsonify({"success": valid, "message": message})

@app.route("/", methods=["GET"])
def home():
    return "Servidor de licencias para autoclaves en funcionamiento ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
