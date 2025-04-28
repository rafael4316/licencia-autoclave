import requests

url = "https://licencia-autoclave.onrender.com/create_license"

payload = {
    "admin_token": "TU_CLAVE_SECRETA_ADMIN",
    "username": "nuevo_usuari1",
    "password": "ddsdsad",
    "license_key": "AGB-123-XYZ",
    "expiration_date": "2025-12-31"
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    print("✅ Licencia creada correctamente.")
else:
    print(f"❌ Error: {response.status_code} - {response.text}")
