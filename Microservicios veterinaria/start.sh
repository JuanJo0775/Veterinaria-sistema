#!/bin/bash

# Script de inicio para el sistema de citas veterinarias

echo "🚀 Iniciando sistema de citas veterinarias..."

# Limpiar contenedores anteriores
docker-compose down

# Construir imágenes con paralelismo
echo "🔨 Construyendo imágenes Docker..."
docker-compose build --parallel

# Iniciar servicios
echo "🌟 Levantando servicios..."
docker-compose up -d

# Verificar estado
echo "✅ Verificando servicios..."
sleep 10
docker-compose ps

echo "📋 Logs de los servicios:"
docker-compose logs --tail=10

echo """
🎉 Sistema iniciado!

URLs disponibles:
- Frontend: http://localhost:5000
- Auth Service: http://localhost:5001/health
- Appointment Service: http://localhost:5002/health
- Notification Service: http://localhost:5003/health

Para ver los logs: docker-compose logs -f
Para detener: docker-compose down
"""