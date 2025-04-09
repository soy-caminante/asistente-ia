import  datetime

from    ia.context      import  *
#--------------------------------------------------------------------------------------------------

class IndexerPrompt:
    def __init__(self, context):
        self._context = context
    #----------------------------------------------------------------------------------------------

    def get_system_promt(self):
        return  "Eres un asistente médico que estructura información clínica. " + \
                "Analiza el siguiente texto clínico y organiza la información en las siguientes categorías, " + \
                "devolviendo los datos en formato JSON con campos:\n" + \
                "edad: edad del paciente\n" + \
                "sexo: sexo del paciente\n" + \
                "motivo: motivo de la visista\n" + \
                "síntomas: sintomatología referida por el paciente\n" + \
                "esatdo físico: estado físico del paciente\n" + \
                "medicación: medicación pautada o referida\n" + \
                "tratamiento: tratamiento recomendado\n" + \
                "recomendaciones: instrucciones dadas al paciente\n" + \
                "ingresos: ingresos hospitalarios\n" + \
                "comentarios: comentatios recogidos en el documento\n"  + \
                "diagnósticos: diagnóstico efectuado\n" + \
                "antecedentes familiares: antecedentes familiares\n" + \
                "factores riesgo cardivascular: factores de riesgo cardiovascular del paciente\n" + \
                "alergias: alergias del paciente\n" + \
                "operaciones: operaciones sufridas por el paciente\n" + \
                "implantes: implantes que tiene el paciente\n" + \
                "otros: cualquier cosa no recogida en los campos anteriores\n" + \
                "keywords: keywords del texto\n" + \
                "tags: tags del texto\n" + \
                "si algún campo no está presente no lo incluyas\n" + \
                "condensa la información lo más posible. se sucinto y conciso\n" + \
                "retorna únicamente el json"
    #----------------------------------------------------------------------------------------------

    def get_user_prompt(self):
        return  "Texto clínico\n:" + \
                f"{self._context}" + "\n" + \
                "Devuelve la información estructurada como JSON por categoría."
    #----------------------------------------------------------------------------------------------
 #-------------------------------------------------------------------------------------------------

class DoctorPrompt:
    @staticmethod
    def date_to_age(birth_date_str):
        formats   = [ '%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y' ]
        hoy       = datetime.datetime.today()

        for format in formats:
            try:
                db  = datetime.datetime.strptime(birth_date_str, format)
                age = hoy.year - db.year - (
                    (hoy.month, hoy.day) < (db.month, db.day)
                )
                return age
            except ValueError:
                continue
        return 30
    #----------------------------------------------------------------------------------------------

    def __init__(self, context: PatientContext, question: str):
        self._context   = context
        self._question  = question
        self._age       = self.date_to_age(self._context.birth_date)
    #----------------------------------------------------------------------------------------------

    def get_system_promt(self):
        return  "Eres un asistente médico experto en comprensión de documentos clínicos."
    #----------------------------------------------------------------------------------------------
    
    def get_user_prompt(self):

        context = f"||1.{self._age}|2.{self._context.sex}||"

        for _, c in self._context.iadocs.items(): 
            context += c + "||"

        return  "Eres un asistente médico. A continuación tienes una serie de documentos clínicos seguido de una pregunta." + \
                "Formato del documento: cada campo se codifica como n.valor. Campos múltiples separados por |. Listas separadas por ;.Delimitadores internos reemplazados por ¬.Fin de documento ||. Mapeo:0:nombre documento,1=edad,2=sexo,3=fecha documento,4=motivo,5=síntomas,6=estado físico,7=medicación,8=tratamiento,9=recomendaciones,10=ingresos,11=comentarios,12=diagnósticos,13=antecedentes familiares,14=factores riesgo cardiovascular,15=alergias,16=operaciones,17=implantes,18=otros,19=keywords,20=tags\n" + \
                "Debes responder únicamente basándote en el contenido del texto" + \
                "Responde en formato markdown. No resumas al final.\n" + \
                "Texto clínico:\n" +\
                "<<<" + \
                f"{context}"    + "\n" + \
                ">>>" + \
                "Pregunta:"     + "\n" + \
                f"{self._question}" + "\n" + \
                "Respuesta"    
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

