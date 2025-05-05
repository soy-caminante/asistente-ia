#!/bin/bash

set -e

SERVICES=()
NO_CACHE=false

# Parsear argumentos
for arg in "$@"; do
  case $arg in
    --no-cache)
      NO_CACHE=true
      ;;
    ia-server|pmanager|webapp|ia-server-local)
      SERVICES+=("$arg")
      ;;
    all)
      SERVICES=("ia-server" "pmanager" "webapp")
      ;;
    *)
      echo "❌ Argumento no reconocido: $arg"
      echo "Uso: ./run.sh [ia-server|pmanager|webapp|ia-server-local|all] [--no-cache]"
      exit 1
      ;;
  esac
done

if [ ${#SERVICES[@]} -eq 0 ]; then
  echo "⚠️ No se especificó ningún servicio. Usa [ia-server|pmanager|webapp|ia-server-local|all]"
  exit 1
fi

# Comprobar si Mongo está corriendo
if docker ps --format '{{.Names}}' | grep -q '^mongodb$'; then
  echo "✅ MongoDB ya está corriendo."
else
  echo "🔌 MongoDB no está corriendo. Iniciando..."
  docker-compose up -d mongo
fi

# Asegurarse de que Mongo está en la red 'yukai-net'
if ! docker network inspect yukai-net | grep -q '"Name": "mongodb"'; then
  echo "🔗 Conectando 'mongodb' a la red 'yukai-net'..."
  docker network connect yukai-net mongodb || true
fi

# Esperar a que Mongo esté disponible
echo "⏳ Esperando a que MongoDB esté accesible..."
until docker exec mongodb mongosh --eval "db.runCommand({ ping: 1 })" >/dev/null 2>&1; do
  sleep 1
done

# Verificar si el replica set está inicializado
echo "🔍 Verificando estado del replicaset..."
RS_STATUS=$(docker exec mongodb mongosh --quiet --eval "rs.status()" 2>&1 || true)

if echo "$RS_STATUS" | grep -q "no replset config has been received"; then
  echo "⚙️ Replica set no inicializado. Ejecutando rs.initiate()..."
  docker exec mongodb mongosh --eval "rs.initiate({ _id: 'rs0', members: [{ _id: 0, host: 'mongo:27017' }] })"
  echo "✅ Replica set inicializado correctamente."
elif echo "$RS_STATUS" | grep -q '"ok" : 1'; then
  echo "✅ Replica set ya está activo."
else
  echo "❌ Error al verificar el estado del replicaset:"
  echo "$RS_STATUS"
  exit 1
fi

# Asignación de Dockerfile y tag correcto para cada servicio
for SERVICE in "${SERVICES[@]}"; do
  echo "🔨 Preparando build para $SERVICE..."

  case "$SERVICE" in
    ia-server)
      DOCKERFILE="Dockerfile.ia"
      IMAGENAME="yukai/ia-server"
      ;;
    ia-server-local)
      DOCKERFILE="Dockerfile.local.ia"
      IMAGENAME="yukai/ia-server-local"
      ;;
    pmanager)
      DOCKERFILE="Dockerfile.pmanager"
      IMAGENAME="yukai/pmanager"
      ;;
    webapp)
      DOCKERFILE="Dockerfile.webapp"
      IMAGENAME="yukai/webapp"
      ;;
    *)
      echo "❌ Servicio desconocido: $SERVICE"
      exit 1
      ;;
  esac

  # Construcción controlada
  if [ "$NO_CACHE" = true ]; then
    docker build -f $DOCKERFILE -t $IMAGENAME . --no-cache
  else
    docker build -f $DOCKERFILE -t $IMAGENAME .
  fi

  echo "🚀 Lanzando contenedor $SERVICE..."
  docker compose up -d $SERVICE
done

echo "✅ Todos los servicios solicitados están en marcha con Mongo en modo replicaset."
