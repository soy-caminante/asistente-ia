import  json
import  os
import  statistics
import  threading
import  time

from    openai                      import AzureOpenAI
#--------------------------------------------------------------------------------------------------


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

def run_stress_test(num_clients: int):

    with open("/home/caminante/Documentos/proyectos/yukai-tests/clientes-data.json", encoding="utf-8") as f:
        clientes_data = json.load(f)

    num_clients = min(num_clients, len(clientes_data))

    print(f"🚀 Iniciando prueba de estrés con {num_clients} clientes simultáneos...")

    clients = [ChatClient(i+1) for i in range(num_clients)]
    threads = []

    # Arrancamos todos los clientes en paralelo
    for index, client in enumerate(clients):
        print(f"Cliente {index}")
        print(clientes_data[index]["expediente"][0:255])
        pass
        # t = threading.Thread(target=client.run_queries, args=(clientes_data[index]["expediente"], clientes_data[index]["preguntas"]))
        # t.start()
        # threads.append(t)

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