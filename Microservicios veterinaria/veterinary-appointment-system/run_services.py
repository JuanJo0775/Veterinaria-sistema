# run_services.py
import subprocess
import sys
import time
import os
import signal


# Colores para la consola
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Servicios a ejecutar
SERVICES = {
    'auth': {
        'path': 'auth-service',
        'file': 'main_fixed.py',
        'port': 5001,
        'name': 'Auth Service'
    },
    'appointment': {
        'path': 'appointment-service',
        'file': 'main.py',
        'port': 5002,
        'name': 'Appointment Service'
    },
    'notification': {
        'path': 'notification-service',
        'file': 'main.py',
        'port': 5003,
        'name': 'Notification Service'
    },
    'frontend': {
        'path': 'frontend',
        'file': 'main.py',
        'port': 5000,
        'name': 'Frontend'
    },
    'gateway': {
        'path': 'api-gateway',
        'file': 'main.py',
        'port': 8000,
        'name': 'API Gateway'
    }
}

processes = []


def run_service(service_info):
    """Ejecutar un servicio individual"""
    service_path = service_info['path']
    service_file = service_info['file']
    service_name = service_info['name']
    port = service_info['port']

    print(f"{Colors.OKBLUE}Starting {service_name} on port {port}...{Colors.ENDC}")

    # Cambiar al directorio del servicio
    current_dir = os.getcwd()
    full_path = os.path.join(current_dir, service_path)

    print(f"Checking: {full_path}")

    if not os.path.exists(full_path):
        print(f"{Colors.FAIL}✗ Error: Directory does not exist: {full_path}{Colors.ENDC}")
        return None

    file_path = os.path.join(full_path, service_file)
    if not os.path.exists(file_path):
        print(f"{Colors.FAIL}✗ Error: File does not exist: {file_path}{Colors.ENDC}")
        return None

    # Comando para ejecutar el servicio
    cmd = [sys.executable, service_file]

    try:
        # Crear un nuevo entorno
        env = os.environ.copy()
        env['PYTHONPATH'] = full_path + os.pathsep + env.get('PYTHONPATH', '')

        # Establecer variables de entorno específicas para cada servicio
        if 'auth' in service_name.lower():
            env['DATABASE_URL'] = 'postgresql://postgres:bocato0731@localhost:5432/veterinary-appointment-system'
            env['JWT_SECRET_KEY'] = 'dev-secret-key-for-local-development'
        elif 'appointment' in service_name.lower():
            env['DATABASE_URL'] = 'postgresql://postgres:bocato0731@localhost:5432/veterinary-appointment-system'
            env['AUTH_SERVICE_URL'] = 'http://localhost:5001'
        elif 'notification' in service_name.lower():
            env['DATABASE_URL'] = 'postgresql://postgres:bocato0731@localhost:5432/veterinary-appointment-system'
            env['MAIL_SERVER'] = 'smtp.gmail.com'
            env['MAIL_PORT'] = '587'
            env['MAIL_USERNAME'] = 'test@example.com'
            env['MAIL_PASSWORD'] = 'test-password'

        # Ejecutar el servicio
        process = subprocess.Popen(
            cmd,
            cwd=full_path,
            env=env
        )

        print(f"{Colors.OKGREEN}✓ {service_name} started successfully on port {port}{Colors.ENDC}")
        return process
    except Exception as e:
        print(f"{Colors.FAIL}✗ Error starting {service_name}: {e}{Colors.ENDC}")
        return None


def main():
    """Función principal"""
    print(f"{Colors.HEADER}{Colors.BOLD}=== Veterinary System Development Server ==={Colors.ENDC}")
    print(f"{Colors.OKCYAN}Starting all microservices...{Colors.ENDC}\n")

    # Iniciar cada servicio con un retraso entre ellos
    for service_id, service_info in SERVICES.items():
        process = run_service(service_info)
        if process:
            processes.append(process)
        time.sleep(3)  # Esperar 3 segundos entre servicios

    print(f"\n{Colors.OKGREEN}{Colors.BOLD}All services started!{Colors.ENDC}")
    print(f"\n{Colors.HEADER}Available URLs:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  • Frontend: http://localhost:5000{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  • API Gateway: http://localhost:8000{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  • Auth Service: http://localhost:5001{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  • Appointment Service: http://localhost:5002{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  • Notification Service: http://localhost:5003{Colors.ENDC}")

    print(f"\n{Colors.WARNING}Press Ctrl+C to stop all services{Colors.ENDC}")

    try:
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
            # Verificar si algún proceso ha terminado
            for i, process in enumerate(processes):
                if process and process.poll() is not None:
                    service_name = list(SERVICES.values())[i]['name']
                    print(f"{Colors.FAIL}✗ {service_name} has stopped unexpectedly{Colors.ENDC}")
    except KeyboardInterrupt:
        pass
    finally:
        # Detener todos los procesos
        for process in processes:
            if process and process.poll() is None:
                process.terminate()
                time.sleep(0.5)
                if process.poll() is None:
                    process.kill()
        print(f"{Colors.OKGREEN}All services stopped{Colors.ENDC}")


if __name__ == "__main__":
    main()