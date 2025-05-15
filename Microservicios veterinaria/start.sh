#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Sistema de Citas Veterinarias...${NC}"

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado. Por favor instala Docker primero.${NC}"
    exit 1
fi

# Verificar si Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está instalado. Por favor instala Docker Compose primero.${NC}"
    exit 1
fi

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creando archivo .env...${NC}"
    cat > .env << EOL
# Database Configuration
DB_USER=postgres
DB_PASSWORD=bocato0731
DB_NAME=veterinary-appointment-system

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this

# Email Configuration (opcional para desarrollo)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Service URLs
AUTH_SERVICE_URL=http://auth-service:5001
APPOINTMENT_SERVICE_URL=http://appointment-service:5002
NOTIFICATION_SERVICE_URL=http://notification-service:5003
EOL
fi

# Detener servicios anteriores si existen
echo -e "${YELLOW}🛑 Deteniendo servicios anteriores...${NC}"
docker-compose down

# Limpiar volúmenes si se especifica
if [ "$1" == "--clean" ]; then
    echo -e "${YELLOW}🧹 Limpiando volúmenes...${NC}"
    docker-compose down -v
fi

# Construir imágenes
echo -e "${GREEN}🔨 Construyendo imágenes...${NC}"
docker-compose build

# Levantar servicios
echo -e "${GREEN}🚀 Levantando servicios...${NC}"
docker-compose up -d

# Esperar a que los servicios estén listos
echo -e "${YELLOW}⏳ Esperando a que los servicios estén listos...${NC}"
sleep 15

# Verificar estado de los servicios
echo -e "${GREEN}✅ Verificando servicios...${NC}"
docker-compose ps

# Verificar salud de cada servicio
echo -e "${GREEN}🔍 Verificando salud de los servicios...${NC}"

# Check database
DB_STATUS=$(docker-compose exec -T db pg_isready 2>&1)
if [[ $DB_STATUS == *"accepting connections"* ]]; then
    echo -e "${GREEN}✅ Base de datos: OK${NC}"
else
    echo -e "${RED}❌ Base de datos: Error${NC}"
fi

# Check auth service
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health)
if [ $AUTH_STATUS -eq 200 ]; then
    echo -e "${GREEN}✅ Auth Service: OK${NC}"
else
    echo -e "${RED}❌ Auth Service: Error (HTTP $AUTH_STATUS)${NC}"
fi

# Check appointment service
APPOINTMENT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5002/health)
if [ $APPOINTMENT_STATUS -eq 200 ]; then
    echo -e "${GREEN}✅ Appointment Service: OK${NC}"
else
    echo -e "${RED}❌ Appointment Service: Error (HTTP $APPOINTMENT_STATUS)${NC}"
fi

# Check notification service
NOTIFICATION_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5003/health)
if [ $NOTIFICATION_STATUS -eq 200 ]; then
    echo -e "${GREEN}✅ Notification Service: OK${NC}"
else
    echo -e "${RED}❌ Notification Service: Error (HTTP $NOTIFICATION_STATUS)${NC}"
fi

# Check frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
if [ $FRONTEND_STATUS -eq 200 ]; then
    echo -e "${GREEN}✅ Frontend: OK${NC}"
else
    echo -e "${RED}❌ Frontend: Error (HTTP $FRONTEND_STATUS)${NC}"
fi

echo -e "${GREEN}✅ Sistema listo!${NC}"
echo -e "${GREEN}🌐 Frontend: http://localhost:5000${NC}"
echo -e "${GREEN}🔐 Auth Service: http://localhost:5001/health${NC}"
echo -e "${GREEN}📅 Appointment Service: http://localhost:5002/health${NC}"
echo -e "${GREEN}📧 Notification Service: http://localhost:5003/health${NC}"
echo ""
echo -e "${YELLOW}Para ver los logs: docker-compose logs -f${NC}"
echo -e "${YELLOW}Para detener: docker-compose down${NC}"
echo -e "${YELLOW}Para ver logs de un servicio específico: docker-compose logs -f [nombre-servicio]${NC}"