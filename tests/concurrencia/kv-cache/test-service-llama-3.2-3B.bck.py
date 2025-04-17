import asyncio
import httpx
import argparse
import time
import subprocess
import random
import string
import tiktoken
from statistics import mean

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="http://localhost:8000", help="Host del servidor vLLM")
parser.add_argument("--max-clients", type=int, default=35, help="Número de clientes simultáneos")
args = parser.parse_args()

ENDPOINT = f"{args.host}/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}
MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"

ENCODER = tiktoken.get_encoding("cl100k_base")
QUESTION_TEMPLATE = "Consulta {i}: ¿Cuál es el análisis detallado de la situación actual del paciente?"

def generate_long_context(client_id, max_tokens=4000):
    random.seed(client_id)
    base = "Expediente clínico del paciente. "
    text = base
    while len(ENCODER.encode(text)) < max_tokens:
        block = base + ''.join(random.choices(string.ascii_lowercase + " ", k=200))
        text += block + "\n"
    return text.strip()

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

async def simulate_client(session, client_id, n_queries=10):
    context = generate_long_context(client_id)
    history = [
        {"role": "system", "content": "Eres un asistente médico experto en interpretación de historiales clínicos."},
        {"role": "user", "content": context}
    ]
    latencies = []

    for i in range(n_queries):
        question = QUESTION_TEMPLATE.format(i=i + 1)
        history.append({"role": "user", "content": question})

        payload = {
            "model": MODEL_NAME,
            "messages": history,
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }

        try:
            start = time.time()
            response = await session.post(ENDPOINT, headers=HEADERS, json=payload, timeout=300)
            duration = time.time() - start
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                history.append({"role": "assistant", "content": content})
                latencies.append(duration)
                print(f"[{client_id:02d}] Consulta {i+1} ✅ {duration:.2f}s")
            else:
                print(f"[{client_id:02d}] ❌ Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[{client_id:02d}] ❌ Exception: {e}")

    return latencies

async def main():
    print(f"🚀 Iniciando prueba de estrés con {args.max_clients} clientes simultáneos...")
    async with httpx.AsyncClient() as session:
        tasks = [simulate_client(session, i + 1) for i in range(args.max_clients)]
        results = await asyncio.gather(*tasks)

    all_latencies = [lat for client_latencies in results for lat in client_latencies]

    if all_latencies:
        avg_latency = mean(all_latencies)
        min_latency = min(all_latencies)
        max_latency = max(all_latencies)
        print("\n📊 Resultados:")
        print(f"   Total peticiones: {len(all_latencies)}")
        print(f"   Latencia promedio: {avg_latency:.2f}s")
        print(f"   Latencia mínima:   {min_latency:.2f}s")
        print(f"   Latencia máxima:   {max_latency:.2f}s")

    gpu_util, mem_used, mem_total = get_gpu_metrics()
    if gpu_util is not None:
        print(f"\n📈 GPU: {gpu_util}% | VRAM: {mem_used}/{mem_total} MB")

if __name__ == "__main__":
    asyncio.run(main())
