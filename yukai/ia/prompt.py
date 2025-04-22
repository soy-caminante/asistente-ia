import  datetime

from    database.context      import  *
#--------------------------------------------------------------------------------------------------

class IndexerPrompt:
    def __init__(self, context):
        self._context   = context
    #----------------------------------------------------------------------------------------------

    def get_system_promt(self):
        return  "Eres un asistente médico que estructura información clínica. " + \
                "Analiza el siguiente texto clínico y organiza la información en las siguientes categorías, " + \
                "devolviendo los datos en formato JSON con campos:\n" + \
                "fecha: fecha consignada en el documento\n" + \
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
                "si alguna información no aparece o no se menciona, ni incluyas el campo ni lo indiques\n" + \
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
        self._age       = self.date_to_age(self._context.fecha_nacimiento)
    #----------------------------------------------------------------------------------------------

    def get_system_promt(self):
        return  "No sabes nada de medicina. A continuación tienes una serie de documentos clínicos seguido de una pregunta." + \
                "Debes responder únicamente basándote en el contenido del texto, no añadas ni infieras nada." + \
                "Formato del documento: cada campo se codifica como n.valor. Campos múltiples separados por |. Listas separadas por ;.Delimitadores internos reemplazados por ¬.Fin de documento ||. Mapeo:0:nombre documento,1=fecha documento,2=motivo,3=síntomas,4=estado físico,5=medicación,6=tratamiento,7=recomendaciones,8=ingresos,9=comentarios,19=diagnósticos,11=antecedentes familiares,12=factores riesgo cardiovascular,13=alergias,14=operaciones,15=implantes,16=otros\n" + \
                "Por cada información indica el documento del que procede." + \
                "Responde en formato markdown. No resumas al final.\n"
    
                
    #----------------------------------------------------------------------------------------------
    
    def get_user_prompt(self):

        context = f"||1.{self._age}|2.{self._context.sexo}||"

        for nombre, c in self._context.iadocs.items(): 
            context += f"documento:{nombre} " + c + "||"

        ret =  "Texto clínico:\n" +\
                "<<<" + \
                f"{context}"    + "\n" + \
                ">>>" + \
                "Pregunta:"     + "\n" + \
                f"{self._question}" + "\n" + \
                "Respuesta"    
        print(ret)
        return ret
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

