# auth-service/create_app.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from dotenv import load_dotenv
from db import db  # Importar la instancia singleton

load_dotenv()

jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    # Configuración
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    # Inicializar extensiones
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Configurar JWT callbacks
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please login again'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': 'Please provide a valid token'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization required',
            'message': 'Please provide an access token'
        }), 401

    # Ruta de salud
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'auth-service'}), 200

    with app.app_context():
        # Importar y registrar rutas
        from routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app