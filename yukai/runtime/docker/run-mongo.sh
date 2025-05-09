#!/bin/bash

#--------------------------------------
# Configuración
MONGO_USER="yukai"
MONGO_PASS="YukaiSecureP@ss"
KEYFILE_NAME="mongo-keyfile"
COMPOSE_FILE="docker-compose.yml"
CONTAINER_NAME="mongodb"
#--------------------------------------

echo "✅ 1. Generando keyfile..."
openssl rand -base64 756 > $KEYFILE_NAME
chmod 400 $KEYFILE_NAME
sudo chown 999:999 $KEYFILE_NAME

echo "✅ 2. Escribiendo docker-compose.yml..."
cat > $COMPOSE_FILE <<EOF
version: '3.8'

services:
  mongo:
    image: mongo:7
    container_name: $CONTAINER_NAME
    ports:
      - "27017:27017"
    command: ["--replSet", "rs0", "--bind_ip_all", "--keyFile", "/etc/mongo-keyfile"]
    environment:
      MONGO_INITDB_ROOT_USERNAME: $MONGO_USER
      MONGO_INITDB_ROOT_PASSWORD: $MONGO_PASS
    volumes:
      - mongodb_data:/data/db
      - ./mongo-keyfile:/etc/mongo-keyfile:ro
    restart: unless-stopped

volumes:
  mongodb_data:
EOF

echo "🧹 3. Eliminando contenedores y volúmenes anteriores (si existen)..."
docker compose down -v

echo "🚀 4. Iniciando MongoDB con replicaset..."
docker compose up -d

echo "⏳ 5. Esperando a que MongoDB esté listo..."
sleep 15

echo "🧠 6. Inicializando el replicaset..."
docker exec -i $CONTAINER_NAME mongosh -u "$MONGO_USER" -p "$MONGO_PASS" --authenticationDatabase admin <<EOF
rs.initiate()
EOF

echo "🔧 7. Reconfigurando host del replicaset a localhost:27017..."
docker exec -i $CONTAINER_NAME mongosh -u "$MONGO_USER" -p "$MONGO_PASS" --authenticationDatabase admin <<EOF
cfg = rs.conf()
cfg.members[0].host = "localhost:27017"
rs.reconfig(cfg, {force: true})
EOF

echo "🎉 MongoDB con replicaset, autenticación y host correcto está listo en localhost:27017"
