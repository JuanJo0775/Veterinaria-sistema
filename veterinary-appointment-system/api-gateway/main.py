# api-gateway/main.py
from flask import Flask, request, jsonify, make_response
import requests
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Configuración de servicios
SERVICES = {
    'auth': 'http://localhost:5001',
    'appointment': 'http://localhost:5002',
    'notification': 'http://localhost:5003'
}


# Proxy genérico para redirigir peticiones
@app.route('/api/<service>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(service, path):
    """
    Proxy general para redirigir peticiones a los microservicios
    """
    if service not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404

    # Construir URL del servicio destino
    service_url = f"{SERVICES[service]}/api/{path}"

    # Obtener headers de la petición original
    headers = {key: value for key, value in request.headers if key != 'Host'}

    # Reenviar la petición al servicio correspondiente
    try:
        if request.method == 'GET':
            response = requests.get(service_url, params=request.args, headers=headers)
        elif request.method == 'POST':
            response = requests.post(service_url, json=request.json, headers=headers)
        elif request.method == 'PUT':
            response = requests.put(service_url, json=request.json, headers=headers)
        elif request.method == 'DELETE':
            response = requests.delete(service_url, headers=headers)
        elif request.method == 'OPTIONS':
            # Manejar CORS preflight
            response = make_response('', 200)
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            return response

        # Crear respuesta con los mismos headers y contenido
        gateway_response = make_response(response.content, response.status_code)

        # Copiar headers de la respuesta del servicio
        for key, value in response.headers.items():
            if key.lower() not in ['content-encoding', 'content-length', 'transfer-encoding']:
                gateway_response.headers[key] = value

        return gateway_response

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Service error: {str(e)}'}), 500


# Ruta de salud del gateway
@app.route('/health')
def health():
    """Verificar el estado del API Gateway y sus servicios"""
    services_status = {}

    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            services_status[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'code': response.status_code
            }
        except:
            services_status[service_name] = {
                'status': 'unavailable',
                'code': 0
            }

    # El gateway está saludable si al menos un servicio está disponible
    gateway_healthy = any(status['status'] == 'healthy' for status in services_status.values())

    return jsonify({
        'gateway': 'healthy' if gateway_healthy else 'unhealthy',
        'services': services_status
    }), 200 if gateway_healthy else 503


# Ruta especial para el auth login (ejemplo de ruta específica)
@app.route('/login', methods=['POST'])
def login():
    """Proxy específico para login"""
    try:
        response = requests.post(
            f"{SERVICES['auth']}/api/auth/login",
            json=request.json
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


# Ruta especial para registrar usuarios
@app.route('/register', methods=['POST'])
def register():
    """Proxy específico para registro"""
    try:
        response = requests.post(
            f"{SERVICES['auth']}/api/auth/register",
            json=request.json
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


# Documentación básica de la API
@app.route('/')
def api_docs():
    """Documentación básica del API Gateway"""
    return jsonify({
        'name': 'Veterinary API Gateway',
        'version': '1.0.0',
        'services': {
            'auth': {
                'base_url': '/api/auth',
                'endpoints': [
                    'POST /api/auth/login',
                    'POST /api/auth/register',
                    'GET /api/auth/me',
                    'GET /api/auth/veterinarians'
                ]
            },
            'appointment': {
                'base_url': '/api/appointment',
                'endpoints': [
                    'GET /api/appointment/appointments',
                    'POST /api/appointment/appointments',
                    'PUT /api/appointment/appointments/{id}',
                    'DELETE /api/appointment/appointments/{id}',
                    'GET /api/appointment/pets/{owner_id}',
                    'POST /api/appointment/pets'
                ]
            },
            'notification': {
                'base_url': '/api/notification',
                'endpoints': [
                    'POST /api/notification/send-email',
                    'GET /api/notification/notifications/{user_id}',
                    'PUT /api/notification/notifications/{id}/mark-read'
                ]
            }
        },
        'health_check': '/health'
    })


if __name__ == '__main__':
    print("API Gateway running on http://localhost:8000")
    print("Services:")
    for service, url in SERVICES.items():
        print(f"  - {service}: {url}")

    app.run(host='127.0.0.1', port=8000, debug=True)