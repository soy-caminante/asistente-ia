from    aimanager.docmanager                                    import LocalFAISS
from    huggingface_hub                                         import InferenceClient
from    huggingface_hub.inference._generated.types              import QuestionAnsweringOutputElement
#--------------------------------------------------------------------------------------------------

class InferenceModelClient:
    def __init__(self, api_key = "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"):
        self._client            = InferenceClient(api_key=api_key)
        self._db                = LocalFAISS()
        self._ia_model          = "Agnuxo/Agente-GPT-Qwen-2.5-7B-Spanish_16bit"
    #----------------------------------------------------------------------------------------------

    def is_ready(self): return self._db.load_db().is_ready()
    #----------------------------------------------------------------------------------------------

    def question_answering(self, question):
        target_pages    = self._db.retreive_relevant_pages(question)

        for page, context in target_pages.items():
            response: QuestionAnsweringOutputElement | list[QuestionAnsweringOutputElement]
            response = self._client.question_answering \
            (
            
                question                    = question,
                context                     = context,
                model                       = self._ia_model,
                align_to_words              = True,
                doc_stride                  = 100,
                handle_impossible_answer    = True,
                max_answer_len              = 128,
                top_k                       = 5
            )

            if not isinstance(response, list):
                response = [ response ]

            for r in response:
                print(r.answer)

        return response
    #----------------------------------------------------------------------------------------------

    def text_generation(self, question):
        target_pages    = self._db.retreive_relevant_pages(question)
        refined_context = ""

        for page, context in target_pages.items():
            prompt      = f"Si no encuentras la respuesta responde con Desconocido. Contexto: {context}\n\nPregunta: {question}\n\nRespuesta:"
            response    = self._client.text_generation \
            (
                prompt,
                model           = self._ia_model,
                max_new_tokens  = 100,
                temperature     = 0.7,
                top_p           = 0.9
            )

            refined_context += response + " "

            print(f"{page} - {response}\n{'-'*50}")

        prompt      = f"Si no encuentras la respuesta responde con Desconocido. Contexto: {refined_context}\n\nPregunta: {question}\n\nRespuesta:"
        response    = self._client.text_generation \
        (
            prompt,
            model           = self._ia_model,
            max_new_tokens  = 100,
            temperature     = 0.7,
            top_p           = 0.9
        )

        print(f"\n\n\n\nRespuesta refinada: { response}")
#--------------------------------------------------------------------------------------------------