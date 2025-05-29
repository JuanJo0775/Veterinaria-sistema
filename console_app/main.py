# console_app/main.py
import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import uuid


class Colors:
    """Colores para la consola"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class VeterinaryConsoleApp:
    def __init__(self):
        self.services = {
            'auth': 'http://localhost:5001',
            'appointment': 'http://localhost:5002',
            'notification': 'http://localhost:5003',
            'medical': 'http://localhost:5004',
            'inventory': 'http://localhost:5005'
        }

        # Estado de la aplicación
        self.current_user = None
        self.access_token = None
        self.sample_data = {}

        # Verificar si los servicios están corriendo
        self.services_status = {}

    def print_header(self, title: str):
        """Imprimir header con formato"""
        print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{title.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")

    def print_success(self, message: str):
        """Imprimir mensaje de éxito"""
        print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

    def print_error(self, message: str):
        """Imprimir mensaje de error"""
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

    def print_warning(self, message: str):
        """Imprimir mensaje de advertencia"""
        print(f"{Colors.WARNING}⚠️ {message}{Colors.ENDC}")

    def print_info(self, message: str):
        """Imprimir mensaje informativo"""
        print(f"{Colors.OKBLUE}ℹ️ {message}{Colors.ENDC}")

    def check_docker_services(self):
        """Verificar si Docker y los servicios están corriendo"""
        self.print_header("VERIFICANDO SERVICIOS")

        # Verificar Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.print_success("Docker está instalado")
            else:
                self.print_error("Docker no está disponible")
                return False
        except FileNotFoundError:
            self.print_error("Docker no está instalado")
            return False

        # Verificar servicios
        all_healthy = True
        for service_name, service_url in self.services.items():
            try:
                response = requests.get(f"{service_url}/health", timeout=5)
                if response.status_code == 200:
                    self.print_success(f"{service_name.title()} Service - {service_url}")
                    self.services_status[service_name] = True
                else:
                    self.print_error(f"{service_name.title()} Service - {service_url} (HTTP {response.status_code})")
                    self.services_status[service_name] = False
                    all_healthy = False
            except requests.exceptions.RequestException:
                self.print_error(f"{service_name.title()} Service - {service_url} (No disponible)")
                self.services_status[service_name] = False
                all_healthy = False

        return all_healthy

    def start_services(self):
        """Iniciar todos los servicios con Docker Compose"""
        self.print_header("INICIANDO SERVICIOS")

        try:
            self.print_info("Ejecutando: make dev-up")
            result = subprocess.run(['make', 'dev-up'],
                                    capture_output=True, text=True, cwd='..')

            if result.returncode == 0:
                self.print_success("Servicios iniciados correctamente")
                self.print_info("Esperando 15 segundos para que los servicios estén listos...")
                time.sleep(15)
                return True
            else:
                self.print_error(f"Error iniciando servicios: {result.stderr}")
                return False

        except FileNotFoundError:
            self.print_error("Make no encontrado. Intentando con docker-compose...")
            try:
                result = subprocess.run([
                    'docker-compose', '-f', '../docker-compose.dev.yml', 'up', '-d'
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    self.print_success("Servicios iniciados con docker-compose")
                    time.sleep(15)
                    return True
                else:
                    self.print_error(f"Error con docker-compose: {result.stderr}")
                    return False
            except FileNotFoundError:
                self.print_error("Docker-compose no encontrado")
                return False

    def stop_services(self):
        """Detener todos los servicios"""
        self.print_header("DETENIENDO SERVICIOS")

        try:
            result = subprocess.run(['make', 'dev-down'],
                                    capture_output=True, text=True, cwd='..')
            if result.returncode == 0:
                self.print_success("Servicios detenidos correctamente")
            else:
                self.print_error(f"Error deteniendo servicios: {result.stderr}")
        except FileNotFoundError:
            try:
                result = subprocess.run([
                    'docker-compose', '-f', '../docker-compose.dev.yml', 'down'
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    self.print_success("Servicios detenidos con docker-compose")
                else:
                    self.print_error(f"Error: {result.stderr}")
            except FileNotFoundError:
                self.print_error("No se pudieron detener los servicios")

    # =============== AUTH SERVICE TESTS ===============

    def test_auth_service(self):
        """Test completo del servicio de autenticación"""
        self.print_header("TESTING AUTH SERVICE")

        if not self.services_status.get('auth'):
            self.print_error("Auth Service no está disponible")
            return

        # Test 1: Health Check
        self.print_info("1. Probando Health Check...")
        try:
            response = requests.get(f"{self.services['auth']}/health")
            if response.status_code == 200:
                self.print_success("Health Check OK")
                print(f"   Response: {response.json()}")
            else:
                self.print_error(f"Health Check falló: {response.status_code}")
        except Exception as e:
            self.print_error(f"Error en Health Check: {e}")

        # Test 2: Registro de usuario
        self.print_info("2. Registrando usuario de prueba...")
        test_user_data = {
            "email": f"test_{int(time.time())}@test.com",
            "password": "password123",
            "first_name": "Usuario",
            "last_name": "Prueba",
            "phone": "+1234567890",
            "role": "client"
        }

        try:
            response = requests.post(
                f"{self.services['auth']}/auth/register",
                json=test_user_data
            )
            if response.status_code == 201:
                self.print_success("Usuario registrado exitosamente")
                result = response.json()
                print(f"   User ID: {result.get('user_id')}")
                self.sample_data['test_user'] = test_user_data
            else:
                self.print_error(f"Error en registro: {response.json()}")
        except Exception as e:
            self.print_error(f"Error registrando usuario: {e}")

        # Test 3: Login
        self.print_info("3. Probando login...")
        try:
            login_data = {
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
            response = requests.post(
                f"{self.services['auth']}/auth/login",
                json=login_data
            )
            if response.status_code == 200:
                result = response.json()
                self.print_success("Login exitoso")
                self.access_token = result.get('token')
                self.current_user = result.get('user')
                print(f"   Token: {self.access_token[:50]}...")
                print(f"   User: {self.current_user}")
            else:
                self.print_error(f"Error en login: {response.json()}")
        except Exception as e:
            self.print_error(f"Error en login: {e}")

        # Test 4: Verificar token
        if self.access_token:
            self.print_info("4. Verificando token...")
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.post(
                    f"{self.services['auth']}/auth/verify",
                    headers=headers
                )
                if response.status_code == 200:
                    self.print_success("Token válido")
                    print(f"   Verificación: {response.json()}")
                else:
                    self.print_error(f"Token inválido: {response.json()}")
            except Exception as e:
                self.print_error(f"Error verificando token: {e}")

    def create_sample_veterinarian(self):
        """Crear veterinario de ejemplo"""
        vet_data = {
            "email": "vet@veterinariaclinic.com",
            "password": "vet123",
            "first_name": "Dr. Juan",
            "last_name": "Pérez",
            "phone": "+1234567891",
            "role": "veterinarian"
        }

        try:
            response = requests.post(
                f"{self.services['auth']}/auth/register",
                json=vet_data
            )
            if response.status_code == 201:
                self.print_success("Veterinario creado")
                self.sample_data['veterinarian'] = vet_data

                # Login del veterinario para obtener su ID
                login_response = requests.post(
                    f"{self.services['auth']}/auth/login",
                    json={"email": vet_data["email"], "password": vet_data["password"]}
                )
                if login_response.status_code == 200:
                    vet_info = login_response.json()
                    self.sample_data['veterinarian_id'] = vet_info['user']['id']
                    print(f"   Veterinarian ID: {self.sample_data['veterinarian_id']}")

            else:
                self.print_warning("Veterinario ya existe o error en creación")
        except Exception as e:
            self.print_error(f"Error creando veterinario: {e}")

    # =============== MEDICAL SERVICE TESTS ===============

    def test_medical_service(self):
        """Test completo del servicio médico"""
        self.print_header("TESTING MEDICAL SERVICE")

        if not self.services_status.get('medical'):
            self.print_error("Medical Service no está disponible")
            return

        # Test 1: Health Check
        self.print_info("1. Health Check...")
        try:
            response = requests.get(f"{self.services['medical']}/health")
            if response.status_code == 200:
                self.print_success("Health Check OK")
            else:
                self.print_error(f"Health Check falló: {response.status_code}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 2: Crear mascota
        self.print_info("2. Creando mascota de prueba...")
        pet_data = {
            "owner_id": self.current_user['id'] if self.current_user else str(uuid.uuid4()),
            "name": "Luna",
            "species": "Gato",
            "breed": "Persa",
            "birth_date": "2020-03-15",
            "weight": 4.5,
            "gender": "Hembra",
            "allergies": "Ninguna conocida",
            "vaccination_status": "Al día"
        }

        try:
            response = requests.post(
                f"{self.services['medical']}/medical/pets",
                json=pet_data
            )
            if response.status_code == 201:
                result = response.json()
                pet_id = result['pet']['id']
                self.sample_data['pet_id'] = pet_id
                self.print_success(f"Mascota creada - ID: {pet_id}")
                print(f"   Nombre: {result['pet']['name']}")
            else:
                self.print_error(f"Error creando mascota: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 3: Buscar mascotas
        self.print_info("3. Buscando mascotas...")
        try:
            response = requests.get(f"{self.services['medical']}/medical/pets/search?q=Luna")
            if response.status_code == 200:
                result = response.json()
                self.print_success(f"Búsqueda exitosa - {len(result['pets'])} resultados")
                for pet in result['pets']:
                    print(f"   - {pet['name']} ({pet['species']})")
            else:
                self.print_error(f"Error en búsqueda: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 4: Crear historia clínica
        if 'pet_id' in self.sample_data and 'veterinarian_id' in self.sample_data:
            self.print_info("4. Creando historia clínica...")
            record_data = {
                "pet_id": self.sample_data['pet_id'],
                "veterinarian_id": self.sample_data['veterinarian_id'],
                "symptoms_description": "Pérdida de apetito y letargo",
                "physical_examination": "Temperatura normal, ganglios sin alteraciones",
                "diagnosis": "Infección gastrointestinal leve",
                "treatment": "Dieta blanda y medicación",
                "weight_at_visit": 4.3,
                "temperature": 38.5
            }

            try:
                response = requests.post(
                    f"{self.services['medical']}/medical/records",
                    json=record_data
                )
                if response.status_code == 201:
                    result = response.json()
                    record_id = result['medical_record']['id']
                    self.sample_data['medical_record_id'] = record_id
                    self.print_success(f"Historia clínica creada - ID: {record_id}")
                else:
                    self.print_error(f"Error: {response.json()}")
            except Exception as e:
                self.print_error(f"Error: {e}")

    # =============== INVENTORY SERVICE TESTS ===============

    def test_inventory_service(self):
        """Test completo del servicio de inventario"""
        self.print_header("TESTING INVENTORY SERVICE")

        if not self.services_status.get('inventory'):
            self.print_error("Inventory Service no está disponible")
            return

        # Test 1: Health Check
        self.print_info("1. Health Check...")
        try:
            response = requests.get(f"{self.services['inventory']}/health")
            if response.status_code == 200:
                self.print_success("Health Check OK")
            else:
                self.print_error(f"Health Check falló: {response.status_code}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 2: Crear medicamento
        self.print_info("2. Creando medicamento...")
        med_data = {
            "name": "Ibuprofeno 400mg",
            "description": "Antiinflamatorio no esteroideo",
            "stock_quantity": 50,
            "unit_price": 1200,
            "expiration_date": (date.today() + timedelta(days=365)).isoformat(),
            "supplier": "Laboratorios Farmacéuticos SA",
            "minimum_stock_alert": 15,
            "category": "Analgésico",
            "presentation": "Comprimidos",
            "concentration": "400mg"
        }

        try:
            response = requests.post(
                f"{self.services['inventory']}/inventory/medications",
                json=med_data
            )
            if response.status_code == 201:
                result = response.json()
                med_id = result['medication']['id']
                self.sample_data['medication_id'] = med_id
                self.print_success(f"Medicamento creado - ID: {med_id}")
                print(f"   Nombre: {result['medication']['name']}")
                print(f"   Stock: {result['medication']['stock_quantity']}")
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 3: Buscar medicamentos
        self.print_info("3. Buscando medicamentos...")
        try:
            response = requests.get(f"{self.services['inventory']}/inventory/medications/search?q=Ibuprofeno")
            if response.status_code == 200:
                result = response.json()
                self.print_success(f"Búsqueda exitosa - {len(result['medications'])} resultados")
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 4: Movimiento de stock
        if 'medication_id' in self.sample_data:
            self.print_info("4. Reduciendo stock...")
            try:
                stock_data = {
                    "medication_id": self.sample_data['medication_id'],
                    "quantity": 5,
                    "reason": "Prescripción médica",
                    "reference_id": self.sample_data.get('medical_record_id'),
                    "user_id": self.sample_data.get('veterinarian_id')
                }

                response = requests.post(
                    f"{self.services['inventory']}/inventory/reduce-stock",
                    json=stock_data
                )
                if response.status_code == 200:
                    result = response.json()
                    self.print_success("Stock reducido exitosamente")
                    print(f"   Stock anterior: {result['result']['previous_stock']}")
                    print(f"   Stock nuevo: {result['result']['new_stock']}")
                else:
                    self.print_error(f"Error: {response.json()}")
            except Exception as e:
                self.print_error(f"Error: {e}")

    # =============== APPOINTMENT SERVICE TESTS ===============

    def test_appointment_service(self):
        """Test completo del servicio de citas"""
        self.print_header("TESTING APPOINTMENT SERVICE")

        if not self.services_status.get('appointment'):
            self.print_error("Appointment Service no está disponible")
            return

        # Test 1: Health Check
        self.print_info("1. Health Check...")
        try:
            response = requests.get(f"{self.services['appointment']}/health")
            if response.status_code == 200:
                self.print_success("Health Check OK")
            else:
                self.print_error(f"Health Check falló: {response.status_code}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 2: Verificar slots disponibles
        if 'veterinarian_id' in self.sample_data:
            self.print_info("2. Verificando slots disponibles...")
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            try:
                response = requests.get(
                    f"{self.services['appointment']}/appointments/available-slots"
                    f"?veterinarian_id={self.sample_data['veterinarian_id']}&date={tomorrow}"
                )
                if response.status_code == 200:
                    result = response.json()
                    self.print_success(f"Slots disponibles: {len(result['available_slots'])}")
                    if result['available_slots']:
                        print(f"   Slots: {', '.join(result['available_slots'][:5])}")
                else:
                    self.print_error(f"Error: {response.json()}")
            except Exception as e:
                self.print_error(f"Error: {e}")

        # Test 3: Crear cita
        if all(key in self.sample_data for key in ['pet_id', 'veterinarian_id']) and self.current_user:
            self.print_info("3. Creando cita...")
            appointment_data = {
                "pet_id": self.sample_data['pet_id'],
                "veterinarian_id": self.sample_data['veterinarian_id'],
                "client_id": self.current_user['id'],
                "appointment_date": (date.today() + timedelta(days=1)).isoformat(),
                "appointment_time": "10:00",
                "reason": "Consulta general"
            }

            try:
                response = requests.post(
                    f"{self.services['appointment']}/appointments/create",
                    json=appointment_data
                )
                if response.status_code == 201:
                    result = response.json()
                    appointment_id = result['appointment_id']
                    self.sample_data['appointment_id'] = appointment_id
                    self.print_success(f"Cita creada - ID: {appointment_id}")
                    print(f"   Fecha: {result['appointment']['appointment_date']}")
                    print(f"   Hora: {result['appointment']['appointment_time']}")
                else:
                    self.print_error(f"Error: {response.json()}")
            except Exception as e:
                self.print_error(f"Error: {e}")

    # =============== NOTIFICATION SERVICE TESTS ===============

    def test_notification_service(self):
        """Test completo del servicio de notificaciones"""
        self.print_header("TESTING NOTIFICATION SERVICE")

        if not self.services_status.get('notification'):
            self.print_error("Notification Service no está disponible")
            return

        # Test 1: Health Check
        self.print_info("1. Health Check...")
        try:
            response = requests.get(f"{self.services['notification']}/health")
            if response.status_code == 200:
                self.print_success("Health Check OK")
            else:
                self.print_error(f"Health Check falló: {response.status_code}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 2: Enviar email de prueba
        self.print_info("2. Enviando email de prueba...")
        try:
            response = requests.post(
                f"{self.services['notification']}/notifications/test-email",
                json={"email": "test@example.com"}
            )
            if response.status_code == 200:
                result = response.json()
                self.print_success(f"Email de prueba enviado: {result['email_sent']}")
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

        # Test 3: Enviar recordatorio de cita
        if self.current_user and 'appointment_id' in self.sample_data:
            self.print_info("3. Enviando recordatorio de cita...")
            reminder_data = {
                "user_id": self.current_user['id'],
                "email": self.current_user.get('email'),
                "phone": "+1234567890",
                "appointment_details": {
                    "date": (date.today() + timedelta(days=1)).isoformat(),
                    "time": "10:00",
                    "veterinarian_name": "Juan Pérez",
                    "pet_name": "Luna",
                    "reason": "Consulta general"
                }
            }

            try:
                response = requests.post(
                    f"{self.services['notification']}/notifications/send-reminder",
                    json=reminder_data
                )
                if response.status_code == 200:
                    result = response.json()
                    self.print_success("Recordatorio enviado")
                    print(f"   Email: {result['email_sent']}")
                    print(f"   WhatsApp: {result['whatsapp_sent']}")
                else:
                    self.print_error(f"Error: {response.json()}")
            except Exception as e:
                self.print_error(f"Error: {e}")

    # =============== MENÚS Y NAVEGACIÓN ===============

    def show_main_menu(self):
        """Mostrar menú principal"""
        while True:
            self.print_header("SISTEMA DE GESTIÓN VETERINARIA - CONSOLA")
            print(f"{Colors.OKBLUE}Estado de servicios:{Colors.ENDC}")
            for service, status in self.services_status.items():
                status_icon = "🟢" if status else "🔴"
                print(f"  {status_icon} {service.title()} Service")

            if self.current_user:
                print(
                    f"\n{Colors.OKGREEN}Usuario actual: {self.current_user['email']} ({self.current_user['role']}){Colors.ENDC}")

            print(f"\n{Colors.BOLD}OPCIONES DISPONIBLES:{Colors.ENDC}")
            print("1. 🚀 Iniciar servicios")
            print("2. 🔍 Verificar servicios")
            print("3. 🧪 Ejecutar tests completos")
            print("4. 👤 Tests de autenticación")
            print("5. 🏥 Tests de servicio médico")
            print("6. 💊 Tests de inventario")
            print("7. 📅 Tests de citas")
            print("8. 📧 Tests de notificaciones")
            print("9. 📊 Crear datos de ejemplo")
            print("10. 📈 Ver resumen del sistema")
            print("11. 🛑 Detener servicios")
            print("0. ❌ Salir")

            try:
                choice = input(f"\n{Colors.OKCYAN}Selecciona una opción: {Colors.ENDC}")

                if choice == "1":
                    self.start_services()
                    self.check_docker_services()
                elif choice == "2":
                    self.check_docker_services()
                elif choice == "3":
                    self.run_complete_tests()
                elif choice == "4":
                    self.test_auth_service()
                elif choice == "5":
                    self.test_medical_service()
                elif choice == "6":
                    self.test_inventory_service()
                elif choice == "7":
                    self.test_appointment_service()
                elif choice == "8":
                    self.test_notification_service()
                elif choice == "9":
                    self.create_sample_data()
                elif choice == "10":
                    self.show_system_summary()
                elif choice == "11":
                    self.stop_services()
                elif choice == "0":
                    break
                else:
                    self.print_warning("Opción no válida")

                input(f"\n{Colors.OKCYAN}Presiona Enter para continuar...{Colors.ENDC}")

            except KeyboardInterrupt:
                print(f"\n{Colors.WARNING}Operación cancelada{Colors.ENDC}")
                break
            except Exception as e:
                self.print_error(f"Error: {e}")

    def run_complete_tests(self):
        """Ejecutar todos los tests en secuencia"""
        self.print_header("EJECUTANDO TESTS COMPLETOS")

        if not all(self.services_status.values()):
            self.print_warning("No todos los servicios están disponibles")
            self.check_docker_services()

        # Ejecutar tests en orden
        self.test_auth_service()
        time.sleep(2)

        if self.current_user:
            self.create_sample_veterinarian()
            time.sleep(1)

            self.test_medical_service()
            time.sleep(2)

            self.test_inventory_service()
            time.sleep(2)

            self.test_appointment_service()
            time.sleep(2)

            self.test_notification_service()

        self.print_header("TESTS COMPLETADOS")
        self.print_success("Todos los tests han sido ejecutados")

    def create_sample_data(self):
        """Crear datos de ejemplo completos"""
        self.print_header("CREANDO DATOS DE EJEMPLO")

        # Crear usuarios
        self.print_info("Creando usuarios de ejemplo...")
        self.create_sample_veterinarian()

        # Crear cliente si no existe
        if not self.current_user:
            self.test_auth_service()

        # Crear más datos
        self.print_info("Creando datos médicos...")
        self.test_medical_service()

        self.print_info("Creando inventario...")
        self.test_inventory_service()

        self.print_info("Creando citas...")
        self.test_appointment_service()

        self.print_success("Datos de ejemplo creados exitosamente")

    def show_system_summary(self):
        """Mostrar resumen completo del sistema"""
        self.print_header("RESUMEN DEL SISTEMA")

        # Resumen de servicios
        print(f"{Colors.BOLD}Estado de Microservicios:{Colors.ENDC}")
        for service, status in self.services_status.items():
            status_text = f"{Colors.OKGREEN}ACTIVO{Colors.ENDC}" if status else f"{Colors.FAIL}INACTIVO{Colors.ENDC}"
            print(f"  • {service.title()}: {status_text}")

        # Resumen de datos
        print(f"\n{Colors.BOLD}Datos de Prueba Creados:{Colors.ENDC}")
        for key, value in self.sample_data.items():
            print(f"  • {key}: {str(value)[:50]}...")

        # Usuario actual
        if self.current_user:
            print(f"\n{Colors.BOLD}Usuario Actual:{Colors.ENDC}")
            print(f"  • Email: {self.current_user['email']}")
            print(f"  • Rol: {self.current_user['role']}")
            print(f"  • ID: {self.current_user['id']}")

        # Obtener estadísticas de cada servicio
        self.get_service_statistics()

    def get_service_statistics(self):
        """Obtener estadísticas de cada servicio"""
        print(f"\n{Colors.BOLD}Estadísticas del Sistema:{Colors.ENDC}")

        # Inventario
        if self.services_status.get('inventory'):
            try:
                response = requests.get(f"{self.services['inventory']}/inventory/summary")
                if response.status_code == 200:
                    data = response.json()['summary']
                    print(f"  📦 Inventario:")
                    print(f"    - Total medicamentos: {data.get('total_medications', 0)}")
                    print(f"    - Valor total: ${data.get('total_inventory_value', 0):,.2f}")
                    print(f"    - Stock bajo: {data.get('low_stock_count', 0)}")
            except:
                print(f"  📦 Inventario: No disponible")

        # Citas del día
        if self.services_status.get('appointment'):
            try:
                response = requests.get(f"{self.services['appointment']}/appointments/today")
                if response.status_code == 200:
                    data = response.json()
                    print(f"  📅 Citas hoy: {len(data.get('appointments', []))}")
            except:
                print(f"  📅 Citas: No disponible")

    def interactive_testing_menu(self):
        """Menú interactivo para testing específico"""
        while True:
            self.print_header("TESTING INTERACTIVO")
            print("1. 🧪 Test específico de Auth")
            print("2. 🧪 Test específico de Medical")
            print("3. 🧪 Test específico de Inventory")
            print("4. 🧪 Test específico de Appointments")
            print("5. 🧪 Test específico de Notifications")
            print("6. 🔍 Inspeccionar datos")
            print("7. 🛠 Herramientas avanzadas")
            print("0. ⬅ Volver al menú principal")

            choice = input(f"\n{Colors.OKCYAN}Selecciona una opción: {Colors.ENDC}")

            if choice == "1":
                self.interactive_auth_test()
            elif choice == "2":
                self.interactive_medical_test()
            elif choice == "3":
                self.interactive_inventory_test()
            elif choice == "4":
                self.interactive_appointment_test()
            elif choice == "5":
                self.interactive_notification_test()
            elif choice == "6":
                self.inspect_data()
            elif choice == "7":
                self.advanced_tools()
            elif choice == "0":
                break

    def interactive_auth_test(self):
        """Test interactivo de autenticación"""
        self.print_header("TEST INTERACTIVO - AUTH SERVICE")

        print("1. Registrar nuevo usuario")
        print("2. Login con usuario existente")
        print("3. Verificar token actual")
        print("4. Cambiar contraseña")
        print("5. Ver perfil actual")

        choice = input(f"\n{Colors.OKCYAN}Selecciona una opción: {Colors.ENDC}")

        if choice == "1":
            self.register_interactive_user()
        elif choice == "2":
            self.login_interactive()
        elif choice == "3":
            self.verify_current_token()
        elif choice == "4":
            self.change_password_interactive()
        elif choice == "5":
            self.show_current_profile()

    def register_interactive_user(self):
        """Registro interactivo de usuario"""
        print(f"\n{Colors.BOLD}REGISTRO DE NUEVO USUARIO{Colors.ENDC}")

        email = input("Email: ")
        password = input("Contraseña: ")
        first_name = input("Nombre: ")
        last_name = input("Apellido: ")
        phone = input("Teléfono (opcional): ")

        print("Roles disponibles:")
        roles = ["client", "veterinarian", "receptionist", "auxiliary", "admin"]
        for i, role in enumerate(roles, 1):
            print(f"{i}. {role}")

        role_choice = input("Selecciona rol (1-5): ")
        role = roles[int(role_choice) - 1] if role_choice.isdigit() and 1 <= int(role_choice) <= 5 else "client"

        user_data = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "role": role
        }

        try:
            response = requests.post(f"{self.services['auth']}/auth/register", json=user_data)
            if response.status_code == 201:
                self.print_success("Usuario registrado exitosamente")
                print(json.dumps(response.json(), indent=2))
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def login_interactive(self):
        """Login interactivo"""
        print(f"\n{Colors.BOLD}LOGIN{Colors.ENDC}")

        email = input("Email: ")
        password = input("Contraseña: ")

        try:
            response = requests.post(
                f"{self.services['auth']}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                result = response.json()
                self.current_user = result['user']
                self.access_token = result['token']
                self.print_success("Login exitoso")
                print(f"Usuario: {self.current_user['email']} ({self.current_user['role']})")
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def interactive_medical_test(self):
        """Test interactivo del servicio médico"""
        self.print_header("TEST INTERACTIVO - MEDICAL SERVICE")

        print("1. Crear nueva mascota")
        print("2. Buscar mascotas")
        print("3. Ver mascota por ID")
        print("4. Crear historia clínica")
        print("5. Ver historias clínicas de mascota")
        print("6. Agregar prescripción")
        print("7. Subir resultado de examen")

        choice = input(f"\n{Colors.OKCYAN}Selecciona una opción: {Colors.ENDC}")

        if choice == "1":
            self.create_pet_interactive()
        elif choice == "2":
            self.search_pets_interactive()
        elif choice == "3":
            self.get_pet_by_id_interactive()
        elif choice == "4":
            self.create_medical_record_interactive()
        elif choice == "5":
            self.get_medical_records_interactive()
        elif choice == "6":
            self.add_prescription_interactive()

    def create_pet_interactive(self):
        """Crear mascota interactivamente"""
        print(f"\n{Colors.BOLD}CREAR NUEVA MASCOTA{Colors.ENDC}")

        if not self.current_user:
            self.print_error("Debes estar logueado")
            return

        name = input("Nombre de la mascota: ")
        species = input("Especie (Perro/Gato/etc): ")
        breed = input("Raza (opcional): ")
        birth_date = input("Fecha de nacimiento (YYYY-MM-DD, opcional): ")
        weight = input("Peso en kg (opcional): ")
        gender = input("Género (Macho/Hembra, opcional): ")
        allergies = input("Alergias conocidas (opcional): ")
        vaccination_status = input("Estado de vacunación (opcional): ")

        pet_data = {
            "owner_id": self.current_user['id'],
            "name": name,
            "species": species,
            "breed": breed if breed else None,
            "birth_date": birth_date if birth_date else None,
            "weight": float(weight) if weight else None,
            "gender": gender if gender else None,
            "allergies": allergies if allergies else None,
            "vaccination_status": vaccination_status if vaccination_status else None
        }

        # Limpiar valores None
        pet_data = {k: v for k, v in pet_data.items() if v is not None}

        try:
            response = requests.post(f"{self.services['medical']}/medical/pets", json=pet_data)
            if response.status_code == 201:
                result = response.json()
                self.print_success(f"Mascota creada - ID: {result['pet']['id']}")
                print(json.dumps(result['pet'], indent=2))
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def search_pets_interactive(self):
        """Buscar mascotas interactivamente"""
        search_term = input("Término de búsqueda: ")

        try:
            response = requests.get(f"{self.services['medical']}/medical/pets/search?q={search_term}")
            if response.status_code == 200:
                result = response.json()
                self.print_success(f"Encontradas {len(result['pets'])} mascotas")
                for pet in result['pets']:
                    print(f"  • {pet['name']} - {pet['species']} - ID: {pet['id']}")
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def interactive_inventory_test(self):
        """Test interactivo del servicio de inventario"""
        self.print_header("TEST INTERACTIVO - INVENTORY SERVICE")

        print("1. Crear nuevo medicamento")
        print("2. Buscar medicamentos")
        print("3. Ver medicamento por ID")
        print("4. Agregar stock")
        print("5. Reducir stock")
        print("6. Ver movimientos de stock")
        print("7. Ver alertas de stock bajo")
        print("8. Ver medicamentos por vencer")
        print("9. Resumen de inventario")

        choice = input(f"\n{Colors.OKCYAN}Selecciona una opción: {Colors.ENDC}")

        if choice == "1":
            self.create_medication_interactive()
        elif choice == "2":
            self.search_medications_interactive()
        elif choice == "3":
            self.get_medication_by_id_interactive()
        elif choice == "4":
            self.add_stock_interactive()
        elif choice == "5":
            self.reduce_stock_interactive()
        elif choice == "6":
            self.view_stock_movements()
        elif choice == "7":
            self.view_low_stock_alerts()
        elif choice == "8":
            self.view_expiring_medications()
        elif choice == "9":
            self.view_inventory_summary()

    def create_medication_interactive(self):
        """Crear medicamento interactivamente"""
        print(f"\n{Colors.BOLD}CREAR NUEVO MEDICAMENTO{Colors.ENDC}")

        name = input("Nombre del medicamento: ")
        description = input("Descripción (opcional): ")
        stock_quantity = input("Cantidad inicial en stock: ")
        unit_price = input("Precio unitario: ")
        expiration_date = input("Fecha de vencimiento (YYYY-MM-DD, opcional): ")
        supplier = input("Proveedor (opcional): ")
        minimum_stock_alert = input("Alerta de stock mínimo (default 10): ")
        category = input("Categoría (opcional): ")

        med_data = {
            "name": name,
            "description": description if description else None,
            "stock_quantity": int(stock_quantity) if stock_quantity.isdigit() else 0,
            "unit_price": float(unit_price) if unit_price else 0,
            "expiration_date": expiration_date if expiration_date else None,
            "supplier": supplier if supplier else None,
            "minimum_stock_alert": int(minimum_stock_alert) if minimum_stock_alert.isdigit() else 10,
            "category": category if category else None
        }

        # Limpiar valores None
        med_data = {k: v for k, v in med_data.items() if v is not None}

        try:
            response = requests.post(f"{self.services['inventory']}/inventory/medications", json=med_data)
            if response.status_code == 201:
                result = response.json()
                self.print_success(f"Medicamento creado - ID: {result['medication']['id']}")
                print(json.dumps(result['medication'], indent=2))
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def search_medications_interactive(self):
        """Buscar medicamentos interactivamente"""
        search_term = input("Término de búsqueda: ")

        try:
            response = requests.get(f"{self.services['inventory']}/inventory/medications/search?q={search_term}")
            if response.status_code == 200:
                result = response.json()
                self.print_success(f"Encontrados {len(result['medications'])} medicamentos")
                for med in result['medications']:
                    print(f"  • {med['name']} - Stock: {med['stock_quantity']} - ID: {med['id']}")
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def view_inventory_summary(self):
        """Ver resumen de inventario"""
        try:
            response = requests.get(f"{self.services['inventory']}/inventory/summary")
            if response.status_code == 200:
                result = response.json()
                summary = result['summary']

                print(f"\n{Colors.BOLD}RESUMEN DE INVENTARIO:{Colors.ENDC}")
                print(f"  📦 Total medicamentos: {summary['total_medications']}")
                print(f"  💰 Valor total: ${summary['total_inventory_value']:,.2f}")
                print(f"  ⚠️ Stock bajo: {summary['low_stock_count']}")
                print(f"  🚫 Sin stock: {summary['out_of_stock_count']}")
                print(f"  ⏰ Por vencer: {summary['expiring_soon_count']}")
            else:
                self.print_error(f"Error: {response.json()}")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def inspect_data(self):
        """Inspeccionar datos del sistema"""
        self.print_header("INSPECCIÓN DE DATOS")

        print("Datos almacenados en la sesión:")
        if self.sample_data:
            for key, value in self.sample_data.items():
                print(f"  • {key}: {value}")
        else:
            print("  No hay datos de muestra")

        print(f"\nUsuario actual:")
        if self.current_user:
            print(json.dumps(self.current_user, indent=2))
        else:
            print("  No hay usuario logueado")

    def advanced_tools(self):
        """Herramientas avanzadas"""
        self.print_header("HERRAMIENTAS AVANZADAS")

        print("1. 🔄 Reiniciar servicios")
        print("2. 🧹 Limpiar datos de prueba")
        print("3. 📊 Generar reporte completo")
        print("4. 🔍 Test de conectividad")
        print("5. 📈 Benchmark de servicios")
        print("6. 🛠 Configurar entorno")

        choice = input(f"\n{Colors.OKCYAN}Selecciona una opción: {Colors.ENDC}")

        if choice == "1":
            self.restart_services()
        elif choice == "2":
            self.clear_test_data()
        elif choice == "3":
            self.generate_complete_report()
        elif choice == "4":
            self.connectivity_test()
        elif choice == "5":
            self.benchmark_services()
        elif choice == "6":
            self.configure_environment()

    def restart_services(self):
        """Reiniciar todos los servicios"""
        self.print_info("Reiniciando servicios...")
        self.stop_services()
        time.sleep(5)
        self.start_services()
        self.check_docker_services()

    def clear_test_data(self):
        """Limpiar datos de prueba"""
        confirm = input("¿Estás seguro de que quieres limpiar todos los datos? (yes/no): ")
        if confirm.lower() == 'yes':
            self.print_info("Limpiando datos...")
            try:
                result = subprocess.run(['make', 'clean'], capture_output=True, text=True, cwd='..')
                if result.returncode == 0:
                    self.print_success("Datos limpiados")
                    self.sample_data.clear()
                    self.current_user = None
                    self.access_token = None
                else:
                    self.print_error("Error limpiando datos")
            except Exception as e:
                self.print_error(f"Error: {e}")

    def generate_complete_report(self):
        """Generar reporte completo del sistema"""
        self.print_header("REPORTE COMPLETO DEL SISTEMA")

        timestamp = datetime.now().isoformat()
        print(f"Generado el: {timestamp}")

        # Estado de servicios
        print(f"\n{Colors.BOLD}ESTADO DE SERVICIOS:{Colors.ENDC}")
        for service, status in self.services_status.items():
            print(f"  {service}: {'✅' if status else '❌'}")

        # Estadísticas detalladas
        self.get_detailed_statistics()

        # Guardar reporte
        report_data = {
            "timestamp": timestamp,
            "services_status": self.services_status,
            "current_user": self.current_user,
            "sample_data_keys": list(self.sample_data.keys())
        }

        try:
            with open(f"report_{int(time.time())}.json", "w") as f:
                json.dump(report_data, f, indent=2)
            self.print_success("Reporte guardado")
        except Exception as e:
            self.print_error(f"Error guardando reporte: {e}")

    def get_detailed_statistics(self):
        """Obtener estadísticas detalladas"""
        print(f"\n{Colors.BOLD}ESTADÍSTICAS DETALLADAS:{Colors.ENDC}")

        for service_name, service_url in self.services.items():
            if self.services_status.get(service_name):
                print(f"\n📊 {service_name.title()} Service:")
                try:
                    response = requests.get(f"{service_url}/health", timeout=5)
                    if response.status_code == 200:
                        health_data = response.json()
                        print(f"  - Status: {health_data.get('status', 'unknown')}")
                        print(f"  - Uptime: {health_data.get('uptime', 0):.2f}s")
                        print(f"  - Memory: {health_data.get('memory_usage', {}).get('percent', 0):.1f}%")
                        print(f"  - CPU: {health_data.get('cpu_usage', 0):.1f}%")
                except Exception as e:
                    print(f"  - Error obteniendo estadísticas: {e}")

    def connectivity_test(self):
        """Test de conectividad detallado"""
        self.print_header("TEST DE CONECTIVIDAD")

        for service_name, service_url in self.services.items():
            print(f"\n🔍 Probando {service_name}...")

            # Test de ping básico
            try:
                start_time = time.time()
                response = requests.get(f"{service_url}/health", timeout=10)
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    self.print_success(f"Conectividad OK - {response_time:.2f}ms")
                else:
                    self.print_error(f"HTTP {response.status_code} - {response_time:.2f}ms")
            except requests.exceptions.Timeout:
                self.print_error("Timeout (>10s)")
            except requests.exceptions.ConnectionError:
                self.print_error("No se puede conectar")
            except Exception as e:
                self.print_error(f"Error: {e}")

    def benchmark_services(self):
        """Benchmark de rendimiento de servicios"""
        self.print_header("BENCHMARK DE SERVICIOS")

        iterations = 10
        self.print_info(f"Ejecutando {iterations} requests por servicio...")

        for service_name, service_url in self.services.items():
            if not self.services_status.get(service_name):
                continue

            print(f"\n⚡ Benchmark {service_name}:")
            times = []

            for i in range(iterations):
                try:
                    start_time = time.time()
                    response = requests.get(f"{service_url}/health", timeout=5)
                    end_time = time.time()

                    if response.status_code == 200:
                        times.append((end_time - start_time) * 1000)

                except Exception:
                    pass

            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)

                print(f"  - Promedio: {avg_time:.2f}ms")
                print(f"  - Mínimo: {min_time:.2f}ms")
                print(f"  - Máximo: {max_time:.2f}ms")
                print(f"  - Requests exitosos: {len(times)}/{iterations}")
            else:
                print(f"  - No se pudieron completar requests")


def main():
    """Función principal"""
    app = VeterinaryConsoleApp()

    try:
        # Verificar servicios al inicio
        app.check_docker_services()

        # Mostrar menú principal
        app.show_main_menu()

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Aplicación terminada por el usuario{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}Error fatal: {e}{Colors.ENDC}")
    finally:
        print(f"\n{Colors.OKBLUE}¡Gracias por usar el sistema de testing!{Colors.ENDC}")


if __name__ == "__main__":
    main()