# notification-service/main.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_app import create_app

if __name__ == '__main__':
    # Configuración para desarrollo local
    os.environ['DATABASE_URL'] = 'postgresql://postgres:2007sA@localhost:5432/veterinary-appointment-system'
    os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
    os.environ['MAIL_PORT'] = '587'
    os.environ['MAIL_USERNAME'] = 'test@example.com'
    os.environ['MAIL_PASSWORD'] = 'test-password'

    app = create_app()
    app.run(host='127.0.0.1', port=5003, debug=True)