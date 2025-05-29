# microservices/auth_service/main.py
import os
import sys
from app import create_app

# Agregar directorios al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from utils import create_health_endpoint
from utils import setup_logger


def main():
    app = create_app()

    # Configurar logging
    logger = setup_logger('auth_service')

    # Configurar health check
    from app.models import db
    create_health_endpoint(app, 'auth_service', db)

    logger.info("🚀 Auth Service iniciado en puerto 5001")

    return app


if __name__ == '__main__':
    app = main()
    app.run(host='0.0.0.0', port=5001, debug=True)