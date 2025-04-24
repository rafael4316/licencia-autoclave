<<<<<<< HEAD
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server import Base, License, DATABASE_URL
import hashlib
from datetime import datetime

# Configuración de la base de datos
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

def add_license(username, password, license_key, expiration_date_str):
    try:
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d").date()
    except ValueError:
        print("Error: La fecha debe estar en formato YYYY-MM-DD")
        return
    
    new_license = License(
        username=username,
        password_hash=hashlib.sha256(password.encode()).hexdigest(),
        license_key=license_key,
        expiration_date=expiration_date,
        machine_id="",  # Se asignará en el primer uso
        used=False
    )
    session.add(new_license)
    session.commit()
    print(f"Licencia para '{username}' agregada correctamente.")

# agregar una licencia nueva
if __name__ == "__main__":
    # Modifica estos valores según sea necesario: 
    add_license("marianne_mariños", "carsol12345@", "KYY-777-XZV", "2025-12-31")
    session.close()
=======
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server import Base, License, DATABASE_URL
import hashlib
from datetime import datetime

# Configuración de la base de datos
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

def add_license(username, password, license_key, expiration_date_str):
    try:
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d").date()
    except ValueError:
        print("Error: La fecha debe estar en formato YYYY-MM-DD")
        return
    
    new_license = License(
        username=username,
        password_hash=hashlib.sha256(password.encode()).hexdigest(),
        license_key=license_key,
        expiration_date=expiration_date,
        machine_id="",  # Se asignará en el primer uso
        used=False
    )
    session.add(new_license)
    session.commit()
    print(f"Licencia para '{username}' agregada correctamente.")

# agregar una licencia nueva
if __name__ == "__main__":
    # Modifica estos valores según sea necesario: 
    add_license("marianne_mariños", "carsol12345@", "KYY-777-XZV", "2025-12-31")
    session.close()
>>>>>>> 37ed595605f5e49dfbb4ba4f8f32897fdb752a7c
