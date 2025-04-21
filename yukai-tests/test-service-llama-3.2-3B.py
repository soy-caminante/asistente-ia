import  argparse
import  httpx
import  json
import  statistics
import  sys
import  threading
import  time

from    pathlib import Path
#--------------------------------------------------------------------------------------------------

class ChatClient:
    # Configuración del endpoint
    ENDPOINT    = None
    HEADERS     = None
    MODEL_NAME  = None
    #----------------------------------------------------------------------------------------------

    def __init__(self, client_id: int):
        self._client_id  = client_id
        self._client     = httpx.Client()
        self._durations: list[float] = []
    #----------------------------------------------------------------------------------------------

    def run_queries(self, expediente, preguntas):
        if len(expediente) > 4000:
            expediente_info = expediente[0:4000]
        else:
            expediente_info = expediente

        for i in range(1, len(preguntas)):
            start       = time.perf_counter()
            question    = preguntas[i]
            history     = \
            [
                {"role": "system", "content": f"Eres un asistente médico experto en interpretación de historiales clínicos. Responde a las preguntas sobre este historial: {expediente_info}"},
                {"role": "user", "content": question}
            ]

            payload = \
            {
                "model":        self.MODEL_NAME,
                "messages":     history,
                "max_tokens":   1000,
                "temperature":  0.7,
                "top_p":        0.9,
                "stream":       False
            }

            try:
                response = self._client.post(self.ENDPOINT, headers=self.HEADERS, json=payload, timeout=300)
                if response.status_code == 200:
                    end         = time.perf_counter()
                    latency     = end - start
                    self._durations.append(latency)
                    print(f"[Client {self._client_id}] Query {i:2d} → {latency:.3f}s")
                else:
                    print(f"[{self._client_id:02d}] ❌ Error {response.status_code}: {response.text}")
            except Exception as ex:
                print(f"[{self._client_id:02d}] ❌ Exception: {ex}")

            time.sleep(15)
        print(f"[Client {self._client_id}] terminó  sus {len(preguntas)} consultas.")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

def load():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="http://localhost:8000", help="Host del servidor vLLM")
    parser.add_argument("--data", type=str, default="clientes-data.json", help="Ruta al archivo JSON con expedientes y preguntas")
    args = parser.parse_args()

    ChatClient.ENDPOINT = f"{args.host}/v1/chat/completions"
    ChatClient.HEADERS = {"Content-Type": "application/json"}
    ChatClient.MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"

    data_path = Path.cwd() / Path(args.data)

    if not data_path.exists():
        print("Fichero de datos no encontrado")
        return sys.exit(-1)
    
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)
#--------------------------------------------------------------------------------------------------

def main():
    clientes_data   = load()
    num_clients     = len(clientes_data)

    print(f"🚀 Iniciando prueba de estrés con {num_clients} clientes simultáneos...")

    clients = [ ChatClient(i+1) for i in range(num_clients) ]
    threads = [ ]

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