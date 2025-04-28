import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server import Base, License, DATABASE_URL
from datetime import datetime

# Configuración
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

def add_license(username, password, license_key, expiration_date_str):
    try:
        expiration_date = datetime.fromisoformat(expiration_date_str).date()
    except ValueError:
        print("Error: la fecha debe ser YYYY-MM-DD")
        return
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_license = License(
        username=username,
        password_hash=pw_hash,
        license_key=license_key,
        expiration_date=expiration_date,
        machine_id="",
        used=False
    )
    session.add(new_license)
    session.commit()
    print(f"Licencia creada para {username} con clave {license_key}, expira {expiration_date}")

if __name__ == "__main__":
    # Ejemplo: 
    add_license("juan", "MiPass123!", "JUAN-001-ABC", "2025-12-31")
    session.close()
