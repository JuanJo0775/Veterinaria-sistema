# appointment-service/create_app.py (actualizado)
from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from db import db  # Importar la instancia singleton

load_dotenv()


def create_app():
    app = Flask(__name__)

    # Configuración
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['AUTH_SERVICE_URL'] = os.getenv('AUTH_SERVICE_URL')

    # Inicializar extensiones
    db.init_app(app)
    CORS(app)

    # Ruta de salud
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'appointment-service'}), 200

    with app.app_context():
        # Importar y registrar rutas
        from routes import appointment_bp
        app.register_blueprint(appointment_bp, url_prefix='/api/appointments')

        # Registrar rutas de horarios
        from schedule_routes import schedule_bp
        app.register_blueprint(schedule_bp, url_prefix='/api/schedules')

    return app