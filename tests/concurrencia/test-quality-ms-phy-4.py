import asyncio
import httpx
import argparse
import time
import subprocess
import random
import string
import tiktoken

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="http://localhost:8000", help="Host del servidor vLLM")
parser.add_argument("--max-clients", type=int, default=1, help="Máximo de clientes a probar")
parser.add_argument("--delay", type=float, default=1.5, help="Segundos entre cada ronda de carga")
args = parser.parse_args()

ENDPOINT = f"{args.host}/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

# Pregunta compleja para generar salida larga (~500 tokens)
QUESTION = (
    "Basándote únicamente en el texto anterior, redacta un análisis exhaustivo con ejemplos, "
    "detalles, y conexiones históricas que justifiquen las ideas planteadas."
)

ENCODER = tiktoken.get_encoding("cl100k_base")  # Compatible con la mayoría

def generate_long_context(client_id, max_tokens=1000):
    random.seed(client_id)
    base = (
        "La historia de la humanidad está marcada por avances tecnológicos y filosóficos que han cambiado profundamente las estructuras sociales. "
    )
    text = ""
    while True:
        block = base + ''.join(random.choices(string.ascii_lowercase + " ", k=80))
        text += block
        token_count = len(ENCODER.encode(text))
        if token_count >= max_tokens:
            break
    return text

def get_gpu_metrics():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,nounits,noheader"],
            encoding="utf-8"
        )
        values = output.strip().split(", ")
        return int(values[0]), int(values[1]), int(values[2])
    except Exception as e:
        print(f"⚠️ Error leyendo GPU: {e}")
        return None, None, None

async def query_model(session, client_id):
    full_prompt = "A continuación tienes una serie de documentos clínicos seguido de una pregunta. " \
                "Debes responder únicamente basándote en el contenido del texto " \
                "Formato del documento: cada campo se codifica como n.valor. Campos múltiples separados por |. " \
                "Listas separadas por ;. Delimitadores internos reemplazados por ¬. Fin de documento ||. " \
                "Mapeo: 0:nombre documento, 1=fecha documento, 2=motivo, 3=síntomas, 4=estado físico, 5=medicación, " \
                "6=tratamiento, 7=recomendaciones, 8=ingresos, 9=comentarios, 10=diagnósticos, 11=antecedentes familiares, " \
                "12=factores riesgo cardiovascular, 13=alergias, 14=operaciones, 15=implantes, 16=otros.\n" \
                "Por cada información indica el documento del que procede. Responde en formato markdown. No resumas al final.\n\n" \
                "Texto clínico:\n<<<||1.58|2.hombre||documento:0001-2 0.0001-2|1.3 de febrero de 2025|2.Revisión del tratamiento y evaluación de síntomas|3.Episodios de disnea, palpitaciones ocasionales y fatiga leve|4.Mejoría parcial en la presión arterial y los síntomas de disnea|5.Enalapril 10 mg y metoprolol 50 mg|6.Continuar con enalapril 10 mg y metoprolol 50 mg, iniciar Holter de 24 horas para evaluar las palpitaciones y reforzar recomendaciones sobre dieta y actividad física|7.Reforzar recomendaciones sobre dieta y actividad física|9.Se evidencia una mejora parcial en la presión arterial y los síntomas de disnea. Se indica un estudio complementario para un mejor manejo de las palpitaciones||documento:0001-3 0.0001-3|1.3 de marzo de 2025|2.Revisión de los resultados del Holter|3.Presencia de episodios aislados de arritmia ventricular|4.Presión arterial: 138/85 mmHg¬ Frecuencia cardíaca: 86 latidos por minuto¬ Peso: 82 kg¬ IMC: 27.4|5.Amiodarona 200 mg diarios|6.Iniciar amiodarona 200 mg diarios para el control de las arritmias¬ Continuar con el resto de la medicación actual¬ Programar una ecocardiografía de control|7.Ajustar el tratamiento para controlar las arritmias|9.Se identificaron episodios de arritmia leve|10.Episodios de arritmia ventricular leve||documento:0001-4 0.0001-4|1.3 de abril de 2025|2.Revisión de los resultados de la ecocardiografía|4.La función cardíaca se encuentra estable|5.Amiodarona;Enalapril;Metoprolol|6.Mantener el tratamiento actual y planificar un control trimestral|7.Reforzar el control de los niveles de colesterol y triglicéridos|9.Dr. Alejandro Rodríguez López|10.Hipertrofia ventricular izquierda|12.55% de fracción de eyección||documento:0001-5 0.0001-5|1.3 de julio de 2025|2.Revisión y control trimestral|3.No presenta síntomas|4.Buen control de los factores de riesgo cardiovascular|5.Tratamiento actual|6.Continuar con el tratamiento actual|7.Reforzar las medidas preventivas de estilo de vida|8.No|9.El paciente muestra una evolución favorable|10.No|11.No|12.Buen control de los factores de riesgo cardiovascular|13.No|14.No|15.No|16.Programar un control en 6 meses||documento:0001-1 0.0001-1|1.3 de enero de 2025|2.Dolor torácico y disnea progresiva|3.Dolor torácico opresivo en el centro del pecho, irradiado hacia el brazo izquierdo, acompañado de sudoración y disnea.;Episodios de palpitaciones y fatiga generalizada.|4.Hipertrofia ventricular izquierda con fracción de eyección del 50%.|5.Metoprolol 50 mg cada 12 horas;Enalapril 10 mg cada 12 horas;Atorvastatina 40 mg en la noche;Aspirina 100 mg diaria|6.Tratamiento farmacológico;Modificación de hábitos de vida;Realizar ejercicio físico moderado (caminar 30 minutos diarios, 5 veces por semana);Dieta baja en sodio, grasas saturadas y azúcares;Pérdida de peso gradual con objetivo de alcanzar un IMC inferior a 25;Abandono del tabaquismo (si aplica)|7.Revisión en un mes para evaluar la respuesta al tratamiento;Realización de un Holter de 24 horas si persisten las palpitaciones|10.Cardiopatía isquémica;Hipertrofia ventricular izquierda;Hipertensión arterial no controlada;Dislipidemia|11.Padre fallecido por infarto agudo de miocardio a los 60 años|12.Hipertensión arterial;Dislipidemia;Sobrepeso (IMC: 28.5);Sedentarismo||\n>>>Pregunta:\nmedicación\nRespuesta>>>Pregunta:\nmedicación\nRespuesta:"


    payload = {
        "model": "microsoft/Phi-4-mini-instruct",
        "prompt": full_prompt,
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    try:
        start = time.time()
        response = await session.post(f"{args.host}/v1/completions", headers=HEADERS, json=payload, timeout=180)
        duration = time.time() - start
        if response.status_code == 200:
            output = response.json()["choices"][0]["text"]
            print(f"[{client_id:02d}] ✅ ({duration:.2f}s) {output}")
            return True
        else:
            print(f"[{client_id:02d}] ❌ Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[{client_id:02d}] ❌ Exception: {e}")
        return False

async def run_round(n_clients):
    print(f"\n🔄 Probing with {n_clients} concurrent users...")
    async with httpx.AsyncClient() as session:
        tasks = [query_model(session, i + 1) for i in range(n_clients)]
        results = await asyncio.gather(*tasks)

    gpu_util, mem_used, mem_total = get_gpu_metrics()
    if gpu_util is not None:
        print(f"📊 GPU: {gpu_util}% | VRAM: {mem_used}/{mem_total} MB")

    return all(results)

async def main():
    for users in range(1, args.max_clients + 1):
        success = await run_round(users)
        if not success:
            print(f"\n🛑 Capacidad máxima alcanzada con {users - 1} usuarios.")
            break
        await asyncio.sleep(args.delay)

if __name__ == "__main__":
    asyncio.run(main())
