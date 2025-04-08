import  cmd2
import  json
import  os
import  pathlib

from    ia.client                       import  *
from    ia.prompt                       import  *
from    indexer.environment             import  Environment
from    indexer.search_engine           import  *
#--------------------------------------------------------------------------------------------------

class CtrlConsole(cmd2.Cmd):
    prompt      = "(indexer) "  # Personaliza el prompt
    #----------------------------------------------------------------------------------------------

    def __init__(self,  env: Environment):
        super().__init__()

        self._env                   = env
        self._search_engine         = PatientSearchEngine(None) # Eliiminar None para cargar el modelo si vas a usar FAISS
        self._ia: InferenceContext  = None
    #----------------------------------------------------------------------------------------------

    def do_list(self, args_obj: cmd2.Statement):
        base_dir    = None
        the_args    = args_obj.arg_list

        if len(the_args) == 0:
            base_dir = self._env.income_dir
        elif the_args[0] == "income":
            base_dir = self._env.income_dir
        elif the_args[0] == "consolidated":
            base_dir = self._env.consolidated_dir

        if base_dir:
            subdirs = [d for d in base_dir.iterdir() if d.is_dir()]
            for sub in subdirs: print(sub.name)
        else:
            print(f"Valores permitidos <income|consolidated>")
    #----------------------------------------------------------------------------------------------

    def do_index(self, args_obj: cmd2.Statement):
        the_args    = args_obj.arg_list

        if len(the_args) > 0:
            target_dir: pathlib.Path = self._env.income_dir / the_args[0]

            if target_dir.exists():
                print(f"Indexando el paciente {the_args[0]}")

                dest_dir: pathlib.Path  = self._env.consolidated_dir / the_args[0]
                out_dir                 = self._env.indexes_dir
                corpus                  = PatientCorpus(target_dir)
                self._search_engine.build_index_for_patient(corpus, out_dir)
                target_dir.rename(dest_dir)

                print("Paciente indexado")
            else:
                print("El cliente especificado no existe")    
        else:
            print("Debes especificar el directorio de entrada del paciente")
    #----------------------------------------------------------------------------------------------

    def do_bestindex(self, args_obj: cmd2.Statement):
        the_args    = args_obj.arg_list

        if len(the_args) > 0:
            input = ""
            for a in the_args:
                if input == "": input = a
                else:
                    input += " " + a
            tokens = input.split(":")

            if len(tokens) == 2:
                user        = tokens[0].strip()
                question    = tokens[1].strip()

                print(f"Examinando el paciente {user}")
                self._search_engine.load_index(user, self._env.indexes_dir)
                results = self._search_engine.query_patient(user, question)

                print(f"📄 Resultados para paciente {user}:\n")
                for result in results:
                    print(f"✅ Documento: {result['path']} | Score: {result['score']:.4f}")                

            else:
                print("Formato del comando incorrecto")
        else:
            print("Debes especificar el paciente y la pregunta: chat <paciente>:<pregunta>")
    #----------------------------------------------------------------------------------------------

    def do_list_ia(self, _):
        print("1: ChatGPT 4oMini")
        print("2: Llama-3.1-8B-Instruct")
        print("3: Llama-3.2-1B-Instruct")
    #----------------------------------------------------------------------------------------------

    def do_setupia(self, args_obj: cmd2.Statement):
        the_args    = args_obj.arg_list

        if len(the_args) > 0:
            if the_args[0]      == "1":
                self._ia        = InferenceContext.openai(os.getenv('oai_api_key'))
                self._ia.model  = "gpt-4o-mini"
            elif the_args[0]    == "2":
                self._ia        = InferenceContext.huggingface(os.getenv('hf_api_key'))
                self._ia.model  = "meta-llama/Llama-3.1-8B-Instruct"
            elif the_args[0]    == "3":
                self._ia        = InferenceContext.huggingface(os.getenv('hf_api_key'))
                self._ia.model  = "meta-llama/Llama-3.2-3B-Instruct"
            else:
                print("Modelo no válido")
        else:
            print("Debes especificar el modelo de IA")
    #----------------------------------------------------------------------------------------------

    def do_preprocess(self, args_obj: cmd2.Statement):
        def load_text_from_file(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                    return text
            except Exception as e:
                print(f"Error procesando {filepath}: {e}")
                return ""
            
        def clean_and_minify_json(data):
            def remove_nulls(obj):
                if isinstance(obj, dict):
                    return {k: remove_nulls(v) for k, v in obj.items() if v is not None}
                elif isinstance(obj, list):
                    return [remove_nulls(item) for item in obj if item is not None]
                else:
                    return obj

            cleaned = remove_nulls(data)
            return json.dumps(cleaned, separators=(',', ':'))

        the_args    = args_obj.arg_list
        encoder     = CompactEncoder()

        if len(the_args) > 0:
            target_dir: pathlib.Path = self._env.income_dir / the_args[0]

            if target_dir.exists():
                for target_file in target_dir.iterdir():
                    if target_file.is_file() and target_file.suffix == ".txt":
                        print(f"Indexando el paciente {the_args[0]} {target_file.name}")

                        text    = load_text_from_file(target_file)
                        if text != "":
                            prompt      = Prompt(context=text)
                            response    = self._ia.chat_indexer(prompt)

                            try:
                                cleaned     = response.strip().removeprefix("```json").removesuffix("```").strip()
                                parsed_json = json.loads(cleaned)
                                cleaned     = clean_and_minify_json(parsed_json)
                                comapct     = encoder.encode(parsed_json)
                                print(json.dumps(parsed_json, indent=2, ensure_ascii=False))
                                print(comapct)

                                print(f"Eficiencia {len(cleaned)} {len(comapct)} ({int(100 * len(comapct) / len(cleaned))})")
                            except Exception as e:
                                print("Error al parsear JSON:", e)
                                
                print("Paciente indexado")
            else:
                print("El cliente especificado no existe")    
        else:
            print("Debes especificar el directorio de entrada del paciente")

    def do_exit(self, _):
        return True
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------