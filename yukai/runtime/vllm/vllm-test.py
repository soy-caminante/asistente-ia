import requests
import time

VLLM_API_URL = "http://localhost:8081/v1/completions"

PROMPT_EXPLANATION = (
    "Eres un asistente médico que estructura información clínica en las siguientes categorías: "
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
    "tags: tags del texto."
)

DOCUMENT = (
    "**Consulta 2: Seguimiento a 1 semana**\n\n"
    "**INFORME MÉDICO**\n\n"
    "**Paciente:** Luis Ramírez López\n"
    "**Fecha de consulta:** 12 de enero de 2024\n"
    "**Motivo de consulta:** Seguimiento tras diagnóstico de cálculos renales.\n\n"
    "### **Evolución:**\n"
    "El paciente refiere disminución del dolor, aunque persisten molestias ocasionales.\n\n"
    "### **Examen Físico:**\n"
    "- **Presión arterial:** 138/85 mmHg\n"
    "- Dolor leve a la palpación lumbar.\n\n"
    "### **Plan:**\n"
    "- Continuar con analgésicos según necesidad.\n"
    "- Realizar tomografía abdominal programada.\n\n"
    "**Firma:**\n"
    "Dr. Mario Sánchez Pérez"
)

QUESTION = (
    "Retorna la información en un json. "
    "Si algún campo no está presente en el documento no lo incluyas en el json. "
    "Condensa la información lo más posible. Sé sucinto y conciso. "
    "Retorna únicamente el json. Añade al final el marcador <END>."
)

prompt = f"system: {PROMPT_EXPLANATION}\n\n{DOCUMENT}\n\nuser: {QUESTION}"

payload = {
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "prompt": prompt,
    "max_tokens": 1024,
    "temperature": 0.3,
    "stop": ["<END>"]
}

start = time.time()
response = requests.post(VLLM_API_URL, json=payload)
elapsed = time.time() - start

text = response.json()["choices"][0]["text"]
text = text.split("<END>")[0].strip()

print(f"\nTiempo de respuesta: {elapsed:.2f} segundos\n")
print("Respuesta:\n")
print(text)
