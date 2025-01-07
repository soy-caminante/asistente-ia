import  json
import  os
import  pathlib
import  re

from    app.backend.db                  import *
from    app.backend.ia.inferenceclient  import *
from    app.backend.ia.prompt           import *
#--------------------------------------------------------------------------------------------------

STORAGE_PATH = (pathlib.Path(__file__).parent / "../../data").resolve()
#--------------------------------------------------------------------------------------------------

class DocPopulator:
    def __init__(self, storage_path=STORAGE_PATH):
        self._docs_path         = storage_path / "src-docs"
        self._oai_context       = InferenceContext.openai(os.getenv('oai_api_key'))
        self._oai_context.model = "gpt-4o-mini"
        self._db                = NoSQLDB(storage_path / "dbs/documents.fs", self.log_callback)
        self._db_paciente       = DbPacienteMngr(self._db)
    #----------------------------------------------------------------------------------------------

    def log_callback(self, info): print(info)
    #----------------------------------------------------------------------------------------------

    def run(self, path=None):
        def clean_string(texto):
            return re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', texto)

        if path is not None:
            self._docs_path = pathlib.Path(path)

        for dir in self._docs_path.iterdir():
            id_file = dir/"id.json"
            if id_file.exists():
                paciente        = Paciente()
                ref_id          = dir.name
                paciente_data   = { }
                with open(id_file, "r") as f:
                    paciente_data = json.load(f)

                    if len(paciente_data) == 0: continue

                print(f"Paciente: {ref_id}")
                
                paciente.ref_id             = ref_id
                paciente.nombre             = paciente_data["nombre"]
                paciente.apellidos          = paciente_data["apellidos"]
                paciente.fecha_nacimiento   = paciente_data["fecha-nacimiento"]
                paciente.sexo               = paciente_data["sexo"]

                medicacion      = ""
                antecedentes    = ""
                alergias        = ""
                riesgo          = ""
                visitas         = ""
                ingresos        = ""

                for doc in pathlib.Path(dir).glob('*.txt'):
                    tag_set         = set()
                    keyword_set     = set()

                    with open(doc) as f:
                        self._oai_context.full_context  = f.read()
                        self._oai_context.update_chunks()

                        tag_prompts             = [ ]
                        kw_prompts              = [ ]
                        medicacion_prompts      = [ ]
                        antecedentes_prompts    = [ ]
                        alergias_prompts        = [ ]
                        riesgo_prompts          = [ ]
                        visitas_prompts         = [ ]
                        ingresos_promts         = [ ]

                        for chunk in self._oai_context.chunks:
                            tag_prompts.append(Prompt(chunk, "Dame una lista exhaustiva de tags que sirvan para clasificar este documento"))
                            kw_prompts.append(Prompt(chunk, "Dame una lista exhaustiva de keywords que sirvan para clasificar este documento"))
                            medicacion_prompts.append(Prompt(chunk, "Qúe medicación tiene pautada este paciente. En texto plano, sin usar markdown. Por cada medicamento una línea con formato Fecha (dd-mm-YYYY) Medicamento. Si no hay nada o no encuentras la respuesta dímo DATOS NO ENCONTRADOS"))
                            antecedentes_prompts.append(Prompt(chunk, "Qúe antecedentes médicos de interés tiene este paciente. En texto plano, sin usar markdown. Un antecedente por línea. Si no hay nada o no encuentras la respuesta dímo DATOS NO ENCONTRADOS"))
                            alergias_prompts.append(Prompt(chunk, "Qúe alergias tiene este paciente. Una alergia por línea. En texto plano, sin usar markdown. Una alergia por lína. Si no hay nada o no encuentras la respuesta dímo DATOS NO ENCONTRADOS"))
                            riesgo_prompts.append(Prompt(chunk, "Qúe factores de riesgo cardiovascular tiene este paciente. En texto plano, sin usar markdown. Un factor de riesgo por línea. Si no hay nada o no encuentras la respuesta dímo DATOS NO ENCONTRADOS"))
                            visitas_prompts.append(Prompt(chunk, "Lista de fechas de las visitas del paciente. En texto plano, sin usar markdown. Por cada visita una línea con formato Fecha (dd-mm-YYYY) y el motivo de la visita. Si no hay nada o no encuentras la respuesta dímo DATOS NO ENCONTRADOS"))
                            ingresos_promts.append(Prompt(chunk, "Lista de fechas de los ingresos del paciente. En texto plano, sin usar markdown. Por cada ingreso una línea con formato Fecha (dd-mm-YYYY) y el motivo de la visita. Si no hay nada o no encuentras la respuesta dímo DATOS NO ENCONTRADOS"))

                        tags             = self._oai_context.chat(tag_prompts)
                        keywords         = self._oai_context.chat(kw_prompts)
                        medicacion_c     = self._oai_context.chat(medicacion_prompts)
                        antecedentes_c   = self._oai_context.chat(antecedentes_prompts)
                        alergias_c       = self._oai_context.chat(alergias_prompts)
                        riesgo_c         = self._oai_context.chat(riesgo_prompts)
                        visitas_c        = self._oai_context.chat(visitas_prompts)
                        ingresos_c       = self._oai_context.chat(ingresos_promts)

                        if not "datos no encontrados" in medicacion_c.lower():
                            if medicacion != "": medicacion += "\n"
                            medicacion      += medicacion_c
                        if not "datos no encontrados" in antecedentes_c.lower():
                            if antecedentes != "": antecedentes += "\n"
                            antecedentes    += antecedentes_c
                        if not "datos no encontrados" in alergias_c.lower():
                            if alergias != "": alergias += "\n"
                            alergias        += alergias_c
                        if not "datos no encontrados" in riesgo_c.lower():
                            if riesgo != "": riesgo += "\n"
                            riesgo          += riesgo_c
                        if not "datos no encontrados" in visitas_c.lower():
                            if visitas != "": visitas += "\n"
                            visitas         += visitas_c
                        if not "datos no encontrados" in ingresos_c.lower():
                            if ingresos != "": ingresos += "\n"
                            ingresos        += ingresos_c

                        for token in tags.split("\n"):
                            tag_set.add(clean_string(token))
                        for token in keywords.split("\n"):
                            keyword_set.add(clean_string(token))

                        document_data = \
                        {
                            "contenido":    self._oai_context.full_context,
                            "tags":         list(tag_set),
                            "keywords":     list(keyword_set)
                        }

                        paciente.documentos.append(document_data)

                tokens = medicacion.split("\n")
                paciente.medicacion         = [ token for token in tokens]
                tokens = antecedentes.split("\n")
                paciente.antecedentes       = [ token for token in tokens]
                tokens = alergias.split("\n")
                paciente.alergias           = [ token for token in tokens]
                tokens = riesgo.split("\n")
                paciente.factores_riesgo    = [ token for token in tokens]
                tokens = visitas.split("\n")
                paciente.visitas            = [ token for token in tokens]
                tokens = ingresos.split("\n")
                paciente.ingresos           = [ token for token in tokens]

                self._db_paciente.store_paciente(paciente)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------