import time
import requests

prompt = (
            "Eres un asistente médico que estructura información clínica en las siguientes categorías. "
            "fecha: fecha consignada en el documento. "
            "motivo: motivo de la visita. "
            "síntomas: sintomatología referida por el paciente. "
            "estado físico: estado físico del paciente. "
            "medicación: medicación pautada o referida. "
            "tratamiento: tratamiento recomendado. "
            "recomendaciones: instrucciones dadas al paciente. "
            "ingresos: ingresos hospitalarios. "
            "comentarios: comentarios recogidos en el documento. "
            "diagnósticos: diagnóstico efectuado. "
            "antecedentes familiares: antecedentes familiares. "
            "factores riesgo cardiovascular: factores de riesgo cardiovascular del paciente. "
            "alergias: alergias del paciente. "
            "operaciones: operaciones sufridas por el paciente. "
            "implantes: implantes que tiene el paciente. "
            "otros: cualquier cosa no recogida en los campos anteriores. "
            "keywords: keywords del texto. "
            "tags: tags del texto. "

            "**Consulta 2: Seguimiento a 1 semana**\n\n**INFORME MÉDICO**\n\n"
            "**Paciente:** Luis Ramírez López\n**Fecha de consulta:** 12 de enero de 2024\n"
            "**Motivo de consulta:** Seguimiento tras diagnóstico de cálculos renales.\n\n"
            "### **Evolución:**\nEl paciente refiere disminución del dolor, aunque persisten molestias ocasionales.\n\n"
            "### **Examen Físico:**\n- **Presión arterial:** 138/85 mmHg\n- Dolor leve a la palpación lumbar.\n\n"
            "### **Plan:**\n- Continuar con analgésicos según necesidad.\n- Realizar tomografía abdominal programada.\n\n"
            "**Firma:**\nDr. Mario Sánchez Pérez"

            "Retorna la información en un json. "
            "No uses saltos de línea ni formato Markdown. "
            "No incluyas campos que no estén presentes en el documento. "
            "No pongas campos con valor null o similares. "
            "Condensa la información lo máximo posible. "
            "Retorna únicamente el json. Añade al final el marcador <ÑÑÑ>."
)

payload = {
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "prompt": prompt,
    "temperature": 0.3,
    "max_tokens": 512
}

start = time.time()
response = requests.post("http://localhost:8000/v1/completions", json=payload)
elapsed = time.time() - start

print("Tiempo de respuesta:", elapsed, "segundos")
print("Respuesta:\n", response.json()["choices"][0]["text"])
