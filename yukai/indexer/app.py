import  cmd2
import  json
import  os
import  pathlib
import  re

from    database.context                import  *
from    ia.iaclient.client              import  *
from    indexer.environment             import  Environment
from    indexer.gptstress               import  run_stress_test
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
        self._context_factory       = PacienteContextFactory(self.log_fcn)

        self._env.logger.remove_console_handler()
    #----------------------------------------------------------------------------------------------

    def log_fcn(self, err):
        if isinstance(err, Exception):
            self._env.logger.exception(err)
        else:
            self._env.logger.info(err)
    #----------------------------------------------------------------------------------------------

    def precmd(self, statement: cmd2.Statement):
        if "-" in statement.command:
            alt_statement = statement.to_dict()
            alt_statement["command"] = alt_statement["command"].replace("-", "_")
            return super().precmd(cmd2.Statement.from_dict(alt_statement))
        else:
            return super().precmd(statement)
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
        print("1: GPT-4o-mini")
        print("2: Llama-3.1-8B-Instruct")
        print("3: Llama-3.2-1B-Instruct")
    #----------------------------------------------------------------------------------------------

    def do_setup_ia(self, args_obj: cmd2.Statement):
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
            elif the_args[0]    == "4":
                self._ia        = InferenceContext.huggingface(os.getenv('hf_api_key'))
                self._ia.model  = the_args[1]
            else:
                print("Modelo no válido")
                return
            print(f"Modelo: {self._ia.model}")

        else:
            print("Debes especificar el modelo de IA")
    #----------------------------------------------------------------------------------------------

    def do_compact(self, args_obj: cmd2.Statement):
        def clean_text(text: str) -> str:
            # Quitar espacios al inicio y al final
            text = text.strip()
            # Reemplazar múltiples espacios por uno solo
            return re.sub(r'\s+', ' ', text)
                
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
            target_dir: pathlib.Path    = self._env.income_dir / the_args[0]
            patient_info, src_docs      = self._context_factory.load_src_paciente(target_dir)

            if patient_info:
                patient_context         = PacienteContext(patient_info)
                context_location        = self._env.consolidated_dir / the_args[0]

                for doc_name, doc_text in src_docs.items():
                    doc_text = clean_text(doc_text)

                    print(f"Procesando {doc_name}")
                    if doc_text != "":
                        prompt      = IndexerPrompt(doc_text)
                        response    = self._ia.chat_indexer(prompt)

                        try:
                            cleaned     = response.strip().removeprefix("```json").removesuffix("```").strip()
                            parsed_json = json.loads(cleaned)
                            cleaned     = clean_and_minify_json(parsed_json)
                            comapct     = encoder.encode(parsed_json, doc_name)
                            print(comapct)
                            print(f"Eficiencia {len(doc_text)} {len(comapct)} ({100 - int(100 * len(comapct) / len(doc_text))})")

                            patient_context.add_ia_doc(doc_name, comapct)
                            patient_context.add_src_doc(doc_name, doc_text)
                        except Exception as e:
                            self._env.logger.exception(e)
                            print(e)
                    else:
                        print("Dcoumento vacío")
                self._context_factory.consolidate_context(patient_context, context_location)
                print(f"Paciente indexado: {self._ia.calc_tokens(patient_context.get_context())} tokens")
            else:
                print("El cliente especificado no existe")    
        else:
            print("Debes especificar el directorio de entrada del paciente")
    #----------------------------------------------------------------------------------------------

    def do_exit(self, _):
        return True
    #----------------------------------------------------------------------------------------------

    def do_chat(self, args_obj: cmd2.Statement):
        the_args    = args_obj.arg_list

        if len(the_args) > 1:
            target_dir: pathlib.Path    = self._env.consolidated_dir / the_args[0]
            patient_context             = self._context_factory.load_consolidated_paciente(target_dir)

            if patient_context:
                question = ""
                for i in range(1, len(the_args)):
                    if question == "": question += the_args[i]
                    else:
                        question += " " + the_args[i]
                prompt      = DoctorPrompt(patient_context, question)
                response    = self._ia.chat_doctor(prompt)
                print(response)
            else:
                print("El cliente especificado no existe")    
        else:
            print("Debes especificar el directorio de entrada del paciente")
    #----------------------------------------------------------------------------------------------

    def do_test_gpt(self, args_obj: cmd2.Statement):
        the_args    = args_obj.arg_list

        if len(the_args) > 0:
            num_clients = int(the_args[0])
        else:
            num_clients = 35
        run_stress_test(num_clients)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------