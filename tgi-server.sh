#!/bin/bash

# Nombre del modelo que deseas usar
MODEL_PATH="/home/caminante/Documentos/proyectos/iA/models/gpt2"

# Verifica si Docker está corriendo
if ! systemctl is-active --quiet docker; then
    echo "Docker no está corriendo. Iniciando Docker..."
    sudo systemctl start docker

    if systemctl is-active --quiet docker; then
        echo "Docker iniciado exitosamente."
    else
        echo "Error: No se pudo iniciar Docker. Por favor, verifica tu configuración."
        exit 1
    fi
else
    echo "Docker ya está corriendo."
fi

# Verifica si el modelo existe en la ruta especificada
if [ ! -d "$MODEL_PATH" ]; then
    echo "Error: El modelo no se encuentra en $MODEL_PATH"
    echo "Por favor, descarga el modelo usando:"
    echo "  git clone https://huggingface.co/gpt2 $MODEL_PATH"
    exit 1
fi

# Lanza el servidor TGI
echo "Lanzando el servidor TGI con el modelo $MODEL_PATH..."
docker run -p 8080:80 -v /home/caminante/Documentos/proyectos/iA/models/:/models ghcr.io/huggingface/text-generation-inference:latest --model-id /models/gpt2
