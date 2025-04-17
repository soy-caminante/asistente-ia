import asyncio
import httpx
import argparse
import time
import subprocess
import json
from statistics import mean
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="http://localhost:8000", help="Host del servidor vLLM")
parser.add_argument("--data", type=str, default="/home/pepe/ia/asistente-ia/runtime/clientes-data.json", help="Ruta al archivo JSON con expedientes y preguntas")
args = parser.parse_args()

ENDPOINT = f"{args.host}/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}
MODEL_NAME = "microsoft/Phi-4-mini-instruct"

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

async def simulate_client(session, client_id, expediente, preguntas):
    history = [
        {"role": "system", "content": "Eres un asistente médico experto en interpretación de historiales clínicos."},
        {"role": "user", "content": expediente}
    ]
    latencies = []

    for i, question in enumerate(preguntas):
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
    data_path = Path(args.data)
    with open(data_path, encoding="utf-8") as f:
        clientes_data = json.load(f)

    print(f"🚀 Iniciando prueba de estrés con {len(clientes_data)} clientes simultáneos...")
    async with httpx.AsyncClient() as session:
        tasks = [
            simulate_client(session, cliente["client_id"], cliente["expediente"], cliente["preguntas"])
            for cliente in clientes_data
        ]
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