# auth-service/main_fixed.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import jsonify
from create_app import create_app

if __name__ == '__main__':
    # Configuración para desarrollo local
    os.environ['DATABASE_URL'] = 'postgresql://postgres:bocato0731@localhost:5432/veterinary-appointment-system'
    os.environ['JWT_SECRET_KEY'] = 'dev-secret-key-for-local-development'

    app = create_app()


    # Reemplazar la ruta raíz que intenta renderizar index.html
    @app.route('/')
    def auth_root():
        return jsonify({
            'service': 'Auth Service',
            'status': 'running',
            'endpoints': [
                '/api/auth/login',
                '/api/auth/register',
                '/api/auth/me',
                '/api/auth/verify-token'
            ]
        })


    app.run(host='127.0.0.1', port=5001, debug=True)