# console_app/utils.py
import json
import time
import requests
from typing import Dict, List, Any
from datetime import datetime, date


class APITester:
    """Clase para testing sistemático de APIs"""

    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url
        self.service_name = service_name
        self.results = []

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None,
                      expected_status: int = 200, headers: Dict = None) -> Dict:
        """Test un endpoint específico"""
        url = f"{self.base_url}{endpoint}"

        try:
            start_time = time.time()

            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")

            response_time = (time.time() - start_time) * 1000

            result = {
                'service': self.service_name,
                'method': method.upper(),
                'endpoint': endpoint,
                'url': url,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'response_time_ms': round(response_time, 2),
                'success': response.status_code == expected_status,
                'timestamp': datetime.now().isoformat(),
                'data_sent': data,
                'response_data': None,
                'error': None
            }

            try:
                result['response_data'] = response.json()
            except:
                result['response_data'] = response.text[:500]

            self.results.append(result)
            return result

        except requests.exceptions.Timeout:
            result = {
                'service': self.service_name,
                'method': method.upper(),
                'endpoint': endpoint,
                'url': url,
                'status_code': None,
                'expected_status': expected_status,
                'response_time_ms': None,
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'data_sent': data,
                'response_data': None,
                'error': 'Timeout'
            }
            self.results.append(result)
            return result

        except Exception as e:
            result = {
                'service': self.service_name,
                'method': method.upper(),
                'endpoint': endpoint,
                'url': url,
                'status_code': None,
                'expected_status': expected_status,
                'response_time_ms': None,
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'data_sent': data,
                'response_data': None,
                'error': str(e)
            }
            self.results.append(result)
            return result

    def get_summary(self) -> Dict:
        """Obtener resumen de tests"""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['success']])
        failed_tests = total_tests - successful_tests

        avg_response_time = 0
        if self.results:
            valid_times = [r['response_time_ms'] for r in self.results if r['response_time_ms']]
            if valid_times:
                avg_response_time = sum(valid_times) / len(valid_times)

        return {
            'service': self.service_name,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'avg_response_time_ms': round(avg_response_time, 2)
        }


class DataGenerator:
    """Generador de datos de prueba"""

    @staticmethod
    def generate_user_data(role: str = "client") -> Dict:
        """Generar datos de usuario"""
        timestamp = int(time.time())
        return {
            "email": f"test_{timestamp}@example.com",
            "password": "password123",
            "first_name": "Usuario",
            "last_name": "Prueba",
            "phone": f"+123456{timestamp % 10000}",
            "role": role
        }

    @staticmethod
    def generate_pet_data(owner_id: str) -> Dict:
        """Generar datos de mascota"""
        import random

        names = ["Luna", "Max", "Bella", "Rocky", "Coco", "Milo", "Nala", "Zeus"]
        species = ["Perro", "Gato"]
        breeds = {
            "Perro": ["Labrador", "Golden Retriever", "Bulldog", "Pastor Alemán", "Poodle"],
            "Gato": ["Persa", "Siamés", "Maine Coon", "Bengalí", "Ragdoll"]
        }

        selected_species = random.choice(species)
        selected_breed = random.choice(breeds[selected_species])

        return {
            "owner_id": owner_id,
            "name": random.choice(names),
            "species": selected_species,
            "breed": selected_breed,
            "birth_date": f"20{random.randint(18, 23):02d}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "weight": round(random.uniform(2.0, 30.0), 1),
            "gender": random.choice(["Macho", "Hembra"]),
            "allergies": random.choice(["Ninguna conocida", "Polen", "Ciertos alimentos"]),
            "vaccination_status": random.choice(["Al día", "Pendiente", "Incompleta"])
        }

    @staticmethod
    def generate_medication_data() -> Dict:
        """Generar datos de medicamento"""
        import random

        medications = [
            {
                "name": "Amoxicilina 500mg",
                "category": "Antibiótico",
                "description": "Antibiótico para infecciones bacterianas"
            },
            {
                "name": "Meloxicam 5mg",
                "category": "Antiinflamatorio",
                "description": "Antiinflamatorio no esteroideo"
            },
            {
                "name": "Prednisona 20mg",
                "category": "Corticoesteroide",
                "description": "Corticoesteroide antiinflamatorio"
            },
            {
                "name": "Tramadol 50mg",
                "category": "Analgésico",
                "description": "Analgésico para dolor moderado a severo"
            }
        ]

        med = random.choice(medications)
        expiry_days = random.randint(30, 365)
        expiry_date = date.today().replace(year=date.today().year + 1)

        return {
            "name": med["name"],
            "description": med["description"],
            "stock_quantity": random.randint(10, 100),
            "unit_price": round(random.uniform(500, 5000), 2),
            "expiration_date": expiry_date.isoformat(),
            "supplier": random.choice(["Laboratorios Vet SA", "Pharma Animal", "VetMed Corp"]),
            "minimum_stock_alert": random.randint(5, 20),
            "category": med["category"],
            "presentation": random.choice(["Comprimidos", "Cápsulas", "Jarabe", "Inyectable"]),
            "concentration": med["name"].split()[-1] if "mg" in med["name"] else "N/A"
        }

    @staticmethod
    def generate_appointment_data(pet_id: str, vet_id: str, client_id: str) -> Dict:
        """Generar datos de cita"""
        import random
        from datetime import timedelta

        # Fecha futura aleatoria (1-30 días)
        future_date = date.today() + timedelta(days=random.randint(1, 30))

        # Hora entre 8:00 y 17:00
        hours = [f"{h:02d}:00" for h in range(8, 18)] + [f"{h:02d}:30" for h in range(8, 17)]

        reasons = [
            "Consulta general",
            "Vacunación",
            "Control post-operatorio",
            "Revisión de rutina",
            "Problema dermatológico",
            "Consulta nutricional"
        ]

        return {
            "pet_id": pet_id,
            "veterinarian_id": vet_id,
            "client_id": client_id,
            "appointment_date": future_date.isoformat(),
            "appointment_time": random.choice(hours),
            "reason": random.choice(reasons)
        }


class TestSuiteRunner:
    """Ejecutor de suites de tests"""

    def __init__(self, services: Dict[str, str]):
        self.services = services
        self.testers = {}
        self.sample_data = {}

        # Inicializar testers para cada servicio
        for service_name, service_url in services.items():
            self.testers[service_name] = APITester(service_url, service_name)

    def run_complete_test_suite(self) -> Dict:
        """Ejecutar suite completa de tests"""
        print("🧪 Ejecutando suite completa de tests...")

        # 1. Tests de conectividad
        self._test_connectivity()

        # 2. Test de autenticación y creación de usuarios
        self._test_auth_flow()

        # 3. Test de servicios médicos
        if self.sample_data.get('user_token'):
            self._test_medical_flow()

        # 4. Test de inventario
        self._test_inventory_flow()

        # 5. Test de citas
        if self.sample_data.get('pet_id') and self.sample_data.get('vet_id'):
            self._test_appointment_flow()

        # 6. Test de notificaciones
        self._test_notification_flow()

        return self._generate_final_report()

    def _test_connectivity(self):
        """Test de conectividad de todos los servicios"""
        print("🔍 Probando conectividad...")

        for service_name, tester in self.testers.items():
            tester.test_endpoint('GET', '/health')

    def _test_auth_flow(self):
        """Test del flujo de autenticación"""
        print("🔐 Probando flujo de autenticación...")

        auth_tester = self.testers.get('auth')
        if not auth_tester:
            return

        # Crear usuario cliente
        client_data = DataGenerator.generate_user_data("client")
        result = auth_tester.test_endpoint('POST', '/auth/register', client_data, 201)

        if result['success']:
            # Login
            login_data = {
                "email": client_data["email"],
                "password": client_data["password"]
            }
            login_result = auth_tester.test_endpoint('POST', '/auth/login', login_data, 200)

            if login_result['success']:
                token = login_result['response_data'].get('token')
                user_info = login_result['response_data'].get('user')

                self.sample_data['user_token'] = token
                self.sample_data['client_id'] = user_info.get('id')
                self.sample_data['client_email'] = user_info.get('email')

                # Test de verificación de token
                headers = {"Authorization": f"Bearer {token}"}
                auth_tester.test_endpoint('POST', '/auth/verify', None, 200, headers)

        # Crear veterinario
        vet_data = DataGenerator.generate_user_data("veterinarian")
        vet_result = auth_tester.test_endpoint('POST', '/auth/register', vet_data, 201)

        if vet_result['success']:
            # Login del veterinario para obtener ID
            vet_login = auth_tester.test_endpoint('POST', '/auth/login', {
                "email": vet_data["email"],
                "password": vet_data["password"]
            }, 200)

            if vet_login['success']:
                vet_info = vet_login['response_data'].get('user')
                self.sample_data['vet_id'] = vet_info.get('id')

    def _test_medical_flow(self):
        """Test del flujo médico"""
        print("🏥 Probando flujo médico...")

        medical_tester = self.testers.get('medical')
        if not medical_tester or not self.sample_data.get('client_id'):
            return

        # Crear mascota
        pet_data = DataGenerator.generate_pet_data(self.sample_data['client_id'])
        pet_result = medical_tester.test_endpoint('POST', '/medical/pets', pet_data, 201)

        if pet_result['success']:
            pet_id = pet_result['response_data']['pet']['id']
            self.sample_data['pet_id'] = pet_id

            # Buscar mascota
            medical_tester.test_endpoint('GET', f'/medical/pets/search?q={pet_data["name"]}')

            # Obtener mascota por ID
            medical_tester.test_endpoint('GET', f'/medical/pets/{pet_id}')

            # Crear historia clínica si tenemos veterinario
            if self.sample_data.get('vet_id'):
                record_data = {
                    "pet_id": pet_id,
                    "veterinarian_id": self.sample_data['vet_id'],
                    "symptoms_description": "Síntomas de prueba",
                    "physical_examination": "Examen físico normal",
                    "diagnosis": "Diagnóstico de prueba",
                    "treatment": "Tratamiento recomendado",
                    "weight_at_visit": 5.5,
                    "temperature": 38.5
                }

                record_result = medical_tester.test_endpoint('POST', '/medical/records', record_data, 201)

                if record_result['success']:
                    record_id = record_result['response_data']['medical_record']['id']
                    self.sample_data['medical_record_id'] = record_id

                    # Ver historia clínica
                    medical_tester.test_endpoint('GET', f'/medical/records/{record_id}')

                    # Ver historias de la mascota
                    medical_tester.test_endpoint('GET', f'/medical/records/pet/{pet_id}')

    def _test_inventory_flow(self):
        """Test del flujo de inventario"""
        print("💊 Probando flujo de inventario...")

        inventory_tester = self.testers.get('inventory')
        if not inventory_tester:
            return

        # Crear medicamento
        med_data = DataGenerator.generate_medication_data()
        med_result = inventory_tester.test_endpoint('POST', '/inventory/medications', med_data, 201)

        if med_result['success']:
            med_id = med_result['response_data']['medication']['id']
            self.sample_data['medication_id'] = med_id

            # Buscar medicamento
            inventory_tester.test_endpoint('GET', f'/inventory/medications/search?q={med_data["name"][:5]}')

            # Obtener medicamento por ID
            inventory_tester.test_endpoint('GET', f'/inventory/medications/{med_id}')

            # Movimiento de stock
            stock_data = {
                "medication_id": med_id,
                "quantity": 5,
                "reason": "Test de prescripción",
                "reference_id": self.sample_data.get('medical_record_id'),
                "user_id": self.sample_data.get('vet_id')
            }

            inventory_tester.test_endpoint('POST', '/inventory/reduce-stock', stock_data, 200)

            # Ver movimientos
            inventory_tester.test_endpoint('GET', f'/inventory/movements?medication_id={med_id}')

            # Resumen de inventario
            inventory_tester.test_endpoint('GET', '/inventory/summary')

    def _test_appointment_flow(self):
        """Test del flujo de citas"""
        print("📅 Probando flujo de citas...")

        appointment_tester = self.testers.get('appointment')
        if not appointment_tester or not all(k in self.sample_data for k in ['pet_id', 'vet_id', 'client_id']):
            return

        # Verificar slots disponibles
        from datetime import date, timedelta
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        appointment_tester.test_endpoint('GET',
                                         f'/appointments/available-slots?veterinarian_id={self.sample_data["vet_id"]}&date={tomorrow}')

        # Crear cita
        appointment_data = DataGenerator.generate_appointment_data(
            self.sample_data['pet_id'],
            self.sample_data['vet_id'],
            self.sample_data['client_id']
        )

        apt_result = appointment_tester.test_endpoint('POST', '/appointments/create', appointment_data, 201)

        if apt_result['success']:
            apt_id = apt_result['response_data']['appointment_id']
            self.sample_data['appointment_id'] = apt_id

            # Ver citas del veterinario
            appointment_tester.test_endpoint('GET', f'/appointments/by-veterinarian/{self.sample_data["vet_id"]}')

            # Ver citas del cliente
            appointment_tester.test_endpoint('GET', f'/appointments/by-client/{self.sample_data["client_id"]}')

            # Confirmar cita
            appointment_tester.test_endpoint('PUT', f'/appointments/confirm/{apt_id}')

    def _test_notification_flow(self):
        """Test del flujo de notificaciones"""
        print("📧 Probando flujo de notificaciones...")

        notification_tester = self.testers.get('notification')
        if not notification_tester:
            return

        # Test de email
        notification_tester.test_endpoint('POST', '/notifications/test-email',
                                          {"email": "test@example.com"}, 200)

        # Test de WhatsApp
        notification_tester.test_endpoint('POST', '/notifications/test-whatsapp',
                                          {"phone": "+1234567890"}, 200)

        # Recordatorio de cita
        if self.sample_data.get('client_id'):
            reminder_data = {
                "user_id": self.sample_data['client_id'],
                "email": self.sample_data.get('client_email'),
                "phone": "+1234567890",
                "appointment_details": {
                    "date": "2024-12-25",
                    "time": "10:00",
                    "veterinarian_name": "Dr. Prueba",
                    "pet_name": "Mascota Prueba",
                    "reason": "Consulta de prueba"
                }
            }

            notification_tester.test_endpoint('POST', '/notifications/send-reminder', reminder_data, 200)

    def _generate_final_report(self) -> Dict:
        """Generar reporte final"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "details": {},
            "sample_data_created": self.sample_data
        }

        for service_name, tester in self.testers.items():
            report["summary"][service_name] = tester.get_summary()
            report["details"][service_name] = tester.results

        return report


class ReportGenerator:
    """Generador de reportes"""

    @staticmethod
    def generate_html_report(report_data: Dict, filename: str = None):
        """Generar reporte en HTML"""
        if not filename:
            filename = f"test_report_{int(time.time())}.html"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reporte de Tests - Sistema Veterinario</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
                .service-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }}
                .success {{ border-left-color: #27ae60; }}
                .failure {{ border-left-color: #e74c3c; }}
                .details {{ margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .status-ok {{ color: #27ae60; }}
                .status-error {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🐾 Reporte de Tests - Sistema Veterinario</h1>
                <p>Generado el: {report_data['timestamp']}</p>
            </div>

            <div class="summary">
        """

        for service_name, summary in report_data['summary'].items():
            success_class = "success" if summary['success_rate'] > 80 else "failure"
            html_content += f"""
                <div class="service-card {success_class}">
                    <h3>{service_name.title()} Service</h3>
                    <p>Tests: {summary['total_tests']}</p>
                    <p>Éxito: {summary['successful_tests']}/{summary['total_tests']} ({summary['success_rate']:.1f}%)</p>
                    <p>Tiempo promedio: {summary['avg_response_time_ms']:.2f}ms</p>
                </div>
            """

        html_content += """
            </div>

            <div class="details">
                <h2>Detalles de Tests</h2>
        """

        for service_name, details in report_data['details'].items():
            html_content += f"""
                <h3>{service_name.title()} Service</h3>
                <table>
                    <tr>
                        <th>Endpoint</th>
                        <th>Método</th>
                        <th>Status</th>
                        <th>Tiempo (ms)</th>
                        <th>Resultado</th>
                    </tr>
            """

            for test in details:
                status_class = "status-ok" if test['success'] else "status-error"
                status_text = "✅" if test['success'] else "❌"

                html_content += f"""
                    <tr>
                        <td>{test['endpoint']}</td>
                        <td>{test['method']}</td>
                        <td>{test['status_code'] or 'N/A'}</td>
                        <td>{test['response_time_ms'] or 'N/A'}</td>
                        <td class="{status_class}">{status_text}</td>
                    </tr>
                """

            html_content += "</table>"

        html_content += """
            </div>
        </body>
        </html>
        """

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return filename