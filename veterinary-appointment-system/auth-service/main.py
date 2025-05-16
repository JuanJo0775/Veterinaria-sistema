# auth-service/main_fixed.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import jsonify, Flask, render_template
from create_app import create_app

if __name__ == '__main__':
    # Configuración para desarrollo local
    os.environ['DATABASE_URL'] = 'postgresql://postgres:bocato0731@localhost:5432/veterinary-appointment-system'
    os.environ['JWT_SECRET_KEY'] = 'dev-secret-key-for-local-development'

    app = create_app()


    # Reemplazar la ruta raíz que intenta renderizar index.html
    @app.route('/')
    def index():
        return jsonify({
            'service': 'Auth Service',
            'status': 'running',
            'endpoints': [
                '/api/auth/login',
                '/api/auth/register',
                '/api/auth/me',
                '/api/auth/verify-token',
                '/api/auth/veterinarians'
            ]
        })


    # Ruta para diagnóstico
    @app.route('/debug')
    def debug():
        # Listar todas las rutas registradas
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })

        # Ver variables de entorno
        env_vars = {
            'DATABASE_URL': os.environ.get('DATABASE_URL', 'No definido'),
            'JWT_SECRET_KEY': 'Exists' if os.environ.get('JWT_SECRET_KEY') else 'No definido'
        }

        return jsonify({
            'service': 'Auth Service',
            'status': 'running',
            'routes': routes,
            'environment': env_vars
        })


    # Iniciar el servidor
    app.run(host='127.0.0.1', port=5001, debug=True)