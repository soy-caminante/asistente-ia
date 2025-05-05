#!/bin/bash

set -e

CONTAINER_NAME="mongodb"
REPLICA_SET_NAME="rs0"

echo "🔄 Levantando MongoDB con docker-compose..."
docker compose up -d

echo "⏳ Esperando que Mongo esté listo..."
until docker exec "$CONTAINER_NAME" mongosh --eval "db.runCommand({ ping: 1 })" >/dev/null 2>&1; do
  sleep 1
done

echo "✅ Mongo está accesible. Verificando estado del replicaset..."

STATUS=$(docker exec "$CONTAINER_NAME" mongosh --quiet --eval "rs.status()" 2>&1 || true)

if echo "$STATUS" | grep -q "no replset config has been received"; then
  echo "🚀 Replica set no inicializado. Ejecutando rs.initiate()..."
  docker exec "$CONTAINER_NAME" mongosh --eval "rs.initiate({ _id: '$REPLICA_SET_NAME', members: [{ _id: 0, host: 'localhost:27017' }] })"
  echo "✅ Replica set inicializado."
elif echo "$STATUS" | grep -q '"ok" : 1'; then
  echo "✅ Replica set ya está inicializado."
else
  echo "⚠️ Error al verificar el estado del replicaset:"
  echo "$STATUS"
  exit 1
fi
