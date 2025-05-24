# create_admin.py
# Coloca este archivo en la carpeta auth-service y ejecútalo

import sys
import os
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Añadir directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar conexión a la base de datos
DATABASE_URL = os.getenv('DATABASE_URL',
                         'postgresql://postgres:2007sA@localhost:5432/veterinary-appointment-system')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Importar modelo de usuario
from models import User

# Verificar si ya existe un admin
admin = session.query(User).filter_by(email='admin@veterinary.com').first()

if admin:
    print("El usuario administrador ya existe.")
    print("¿Deseas resetear su contraseña? (s/n)")
    reset = input().lower()

    if reset == 's':
        new_password = "admin123"
        # Generar hash de contraseña
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Actualizar contraseña
        admin.password = password_hash
        session.commit()
        print(f"Contraseña actualizada. Credenciales: admin@veterinary.com / {new_password}")
    else:
        print("No se ha modificado el usuario administrador.")
else:
    # Crear nuevo administrador
    password = "admin123"
    # Generar hash de contraseña
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Crear usuario administrador
    new_admin = User(
        email='admin@veterinary.com',
        password=password_hash,
        first_name='Admin',
        last_name='Sistema',
        phone='555-ADMIN',
        role='admin',
        is_active=True
    )

    # Guardar en la base de datos
    session.add(new_admin)
    session.commit()

    print(f"Usuario administrador creado con éxito. Credenciales: admin@veterinary.com / {password}")