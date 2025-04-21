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
MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"

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


class ChatClient:
    # Configuración de tu Azure OpenAI
    ENDPOINT         = "https://ai-yukaisevilla0557ai738788825307.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2025-01-01-preview"
    API_VERSION      = "2024-12-01-preview"
    SUBSCRIPTION_KEY = os.getenv("azure_api_key")
    DEPLOYMENT       = "gpt-4o-mini"
    #----------------------------------------------------------------------------------------------

    def __init__(self, client_id: int):
        self._client_id  = client_id
        self._client     = AzureOpenAI(
            api_version     = self.API_VERSION,
            azure_endpoint  = self.ENDPOINT,
            api_key         = self.SUBSCRIPTION_KEY
        )
        self._durations: list[float] = []
    #----------------------------------------------------------------------------------------------

    def run_queries(self, expediente, preguntas):
        if len(expediente) > 4000:
            expediente = expediente[0:4000]
        for i in range(1, len(preguntas)):
            start       = time.perf_counter()
            question    = preguntas[i]

            response    = self._client.chat.completions.create \
            (
                model   = self.DEPLOYMENT,
                messages= \
                [
                    {"role": "system", "content": f"Eres un asistente médico experto en interpretación de historiales clínicos. Responde a las preguntas sobre este historial: {expediente}"},
                    {"role": "user", "content": question}
                ],
                max_tokens  = 1000,
                temperature = 1.0,
                top_p       = 1.0
            )
            end         = time.perf_counter()
            latency     = end - start
            self._durations.append(latency)
            print(f"[Client {self._client_id}] Query {i:2d} → {latency:.3f}s")
            time.sleep(15)
        print(f"[Client {self._client_id}] terminó  sus {len(preguntas)} consultas.")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

def main(num_clients: int):

    with open("/home/caminante/Documentos/proyectos/yukai-tests/clientes-data.json", encoding="utf-8") as f:
        clientes_data = json.load(f)

    num_clients = min(num_clients, len(clientes_data))

    print(f"🚀 Iniciando prueba de estrés con {num_clients} clientes simultáneos...")

    clients = [ChatClient(i+1) for i in range(num_clients)]
    threads = []

    # Arrancamos todos los clientes en paralelo
    for index, client in enumerate(clients):
        t = threading.Thread(target=client.run_queries, args=(clientes_data[index]["expediente"], clientes_data[index]["preguntas"]))
        t.start()
        threads.append(t)

    # Esperamos a que todos terminen
    for t in threads:
        t.join()

    # Recolectamos todas las latencias
    all_latencies = [lat for client in clients for lat in client._durations]

    # Calculamos estadísticas
    minimo  = min(all_latencies)
    maximo  = max(all_latencies)
    mediana = statistics.median(all_latencies)
    media   = statistics.mean(all_latencies)
    mediana = statistics.median(all_latencies)
    desv    = statistics.stdev(all_latencies)

    print("\n=== Estadísticas de latencia (s) ===")
    print(f"Mínimo   : {minimo:.3f}")
    print(f"Máximo   : {maximo:.3f}")
    print(f"Mediana  : {mediana:.3f}")
    print(f"Media    : {media:.3f}")
    print(f"Mediana  : {mediana:.3f}")
    print(f"Desv. Típ.: {desv:.3f}")
#--------------------------------------------------------------------------------------------------

main()
