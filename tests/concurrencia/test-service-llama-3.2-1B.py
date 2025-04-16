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
parser.add_argument("--max-clients", type=int, default=50, help="Máximo de clientes a probar")
parser.add_argument("--delay", type=float, default=1.5, help="Segundos entre cada ronda de carga")
args = parser.parse_args()

# Codificador compatible con LLaMA/ChatGPT
ENCODER = tiktoken.get_encoding("cl100k_base")  # También puedes usar "gpt2" si falla

ENDPOINT = f"{args.host}/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

QUESTION = (
    "Ahora, basándote únicamente en el texto anterior, redacta un resumen extenso, "
    "analítico y detallado, con ejemplos, explicaciones, implicaciones y comparaciones históricas, "
    "y hazlo en un estilo narrativo académico, de al menos 1000 palabras."
)

# Simulamos ~5000 tokens (promedio 0.75 tokens por palabra → ~6500-7000 palabras)
def generate_long_context(client_id, max_tokens=4500):
    random.seed(client_id)
    base = (
        "La evolución del pensamiento filosófico occidental, desde los presocráticos hasta los posmodernos, "
        "ha influido en la manera en que las sociedades estructuran sus valores e instituciones. "
    )
    text = ""
    while True:
        # Añade bloques pseudo-random para asegurar diferencia entre clientes
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
    context = generate_long_context(client_id)
    full_prompt = context + "\n\n" + QUESTION
    payload = {
        "model": "meta-llama/Llama-3.2-1B-Instruct",
        "messages": [{"role": "user", "content": full_prompt}],
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.9
    }

    try:
        start = time.time()
        response = await session.post(ENDPOINT, headers=HEADERS, json=payload, timeout=300)
        duration = time.time() - start
        if response.status_code == 200:
            output = response.json()["choices"][0]["message"]["content"]
            print(f"[{client_id:02d}] ✅ ({duration:.2f}s) {output[:60]}...")
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
