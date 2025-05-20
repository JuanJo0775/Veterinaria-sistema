# appointment-service/main.py
import sys
import os


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Renombrar temporalmente el archivo de rutas con problemas
import shutil

routes_path = os.path.join(os.path.dirname(__file__), 'routes.py')
routes_backup = os.path.join(os.path.dirname(__file__), 'routes_original.py')
routes_fixed = os.path.join(os.path.dirname(__file__), 'routes_fixed.py')

# Hacer backup y usar rutas corregidas
if os.path.exists(routes_path) and os.path.exists(routes_fixed):
    if not os.path.exists(routes_backup):
        shutil.copy2(routes_path, routes_backup)
    shutil.copy2(routes_fixed, routes_path)

from create_app import create_app

if __name__ == '__main__':
    # Configuración para desarrollo local
    os.environ['DATABASE_URL'] = 'postgresql://postgres:bocato0731@localhost:5432/veterinary-appointment-system'
    os.environ['AUTH_SERVICE_URL'] = 'http://localhost:5001'

    app = create_app()
    app.run(host='127.0.0.1', port=5002, debug=True)