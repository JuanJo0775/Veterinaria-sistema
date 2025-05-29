# console_app/config.py
import os
from typing import Dict


class ConsoleConfig:
    """Configuración para la aplicación de consola"""

    # URLs de servicios (pueden ser sobrescritas por variables de entorno)
    SERVICES = {
        'auth': os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5001'),
        'appointment': os.environ.get('APPOINTMENT_SERVICE_URL', 'http://localhost:5002'),
        'notification': os.environ.get('NOTIFICATION_SERVICE_URL', 'http://localhost:5003'),
        'medical': os.environ.get('MEDICAL_SERVICE_URL', 'http://localhost:5004'),
        'inventory': os.environ.get('INVENTORY_SERVICE_URL', 'http://localhost:5005')
    }

    # Configuración de timeouts
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '10'))

    # Configuración de Docker
    DOCKER_COMPOSE_FILE = os.environ.get('DOCKER_COMPOSE_FILE', '../docker-compose.dev.yml')

    # Configuración de reportes
    REPORTS_DIR = os.environ.get('REPORTS_DIR', './reports')

    # Configuración de testing
    DEFAULT_TEST_ITERATIONS = int(os.environ.get('TEST_ITERATIONS', '5'))

    # Configuración de datos de ejemplo
    SAMPLE_DATA_CONFIG = {
        'create_multiple_users': True,
        'create_multiple_pets': True,
        'create_sample_medications': True,
        'create_sample_appointments': True,
        'user_roles': ['client', 'veterinarian', 'receptionist', 'admin']
    }

    # Comandos de Docker
    DOCKER_COMMANDS = {
        'start': ['make', 'dev-up'],
        'stop': ['make', 'dev-down'],
        'clean': ['make', 'clean'],
        'logs': ['make', 'dev-logs'],
        'health': ['make', 'health']
    }

    # Fallback a docker-compose si make no está disponible
    DOCKER_COMPOSE_COMMANDS = {
        'start': ['docker-compose', '-f', DOCKER_COMPOSE_FILE, 'up', '-d'],
        'stop': ['docker-compose', '-f', DOCKER_COMPOSE_FILE, 'down'],
        'clean': ['docker-compose', '-f', DOCKER_COMPOSE_FILE, 'down', '-v'],
        'logs': ['docker-compose', '-f', DOCKER_COMPOSE_FILE, 'logs', '-f']
    }

    @classmethod
    def get_service_url(cls, service_name: str) -> str:
        """Obtener URL de un servicio"""
        return cls.SERVICES.get(service_name, f'http://localhost:500{len(cls.SERVICES)}')

    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validar configuración"""
        validation = {
            'docker_compose_file_exists': os.path.exists(cls.DOCKER_COMPOSE_FILE),
            'reports_dir_writable': True,
            'all_services_configured': len(cls.SERVICES) >= 5
        }

        # Verificar que el directorio de reportes se pueda crear
        try:
            os.makedirs(cls.REPORTS_DIR, exist_ok=True)
        except Exception:
            validation['reports_dir_writable'] = False

        return validation


# Configuración específica para diferentes entornos
class DevelopmentConfig(ConsoleConfig):
    """Configuración para desarrollo"""
    DEBUG = True
    VERBOSE_LOGGING = True
    AUTO_RETRY_FAILED_TESTS = True


class ProductionConfig(ConsoleConfig):
    """Configuración para producción"""
    DEBUG = False
    VERBOSE_LOGGING = False
    AUTO_RETRY_FAILED_TESTS = False

    # URLs de producción (si son diferentes)
    SERVICES = {
        'auth': os.environ.get('AUTH_SERVICE_URL', 'http://auth-service:5001'),
        'appointment': os.environ.get('APPOINTMENT_SERVICE_URL', 'http://appointment-service:5002'),
        'notification': os.environ.get('NOTIFICATION_SERVICE_URL', 'http://notification-service:5003'),
        'medical': os.environ.get('MEDICAL_SERVICE_URL', 'http://medical-service:5004'),
        'inventory': os.environ.get('INVENTORY_SERVICE_URL', 'http://inventory-service:5005')
    }


# Seleccionar configuración basada en variable de entorno
ENV = os.environ.get('FLASK_ENV', 'development')

if ENV == 'production':
    config = ProductionConfig
else:
    config = DevelopmentConfig