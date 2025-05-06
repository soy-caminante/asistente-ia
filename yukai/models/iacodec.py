class IACodec:
    # Mapeo de campos con sus índices
    FIELD_MAP = \
    {
        "documento": 0,
        "fecha": 1,
        "motivo": 2,
        "síntomas": 3,
        "estado físico": 4,
        "medicación": 5,
        "tratamiento": 6,
        "recomendaciones": 7,
        "ingresos": 8,
        "comentarios": 9,
        "diagnósticos": 10,
        "antecedentes familiares": 11,
        "factores riesgo cardivascular": 12,
        "alergias": 13,
        "operaciones": 14,
        "implantes": 15,
        "otros": 16
    }
    #----------------------------------------------------------------------------------------------

    # Delimitadores
    FIELD_DELIM = "|"
    LIST_DELIM = ";"
    ESCAPE_CHAR = "¬"
    #----------------------------------------------------------------------------------------------

    # Campos que deben tratarse como listas
    LIST_FIELDS = \
    {
        "síntomas", 
        "estado físico", 
        "medicación", 
        "tratamiento",
        "recomendaciones", 
        "ingresos", 
        "comentarios", 
        "diagnósticos",
        "antecedentes familiares", 
        "factores riesgo cardivascular", 
        "alergias", 
        "operaciones", 
        "implantes", 
        "otros"
    }
    #----------------------------------------------------------------------------------------------

    def __init__(self):
        # Invertimos el FIELD_MAP para decodificación
        self._index_to_field = {v: k for k, v in self.FIELD_MAP.items()}
    #----------------------------------------------------------------------------------------------

    def _sanitize(self, text):
        if not isinstance(text, str):
            text = str(text)
        return text.replace(self.FIELD_DELIM, self.ESCAPE_CHAR).replace(self.LIST_DELIM, self.ESCAPE_CHAR)
    #----------------------------------------------------------------------------------------------

    def _desanitize(self, text):
        return text.replace(self.ESCAPE_CHAR, self.FIELD_DELIM).replace(self.ESCAPE_CHAR, self.LIST_DELIM)
    #----------------------------------------------------------------------------------------------

    def encode(self, data: dict, doc_id) -> str:
        data["documento"]   = doc_id
        parts               = [ ]
        for field, index in self.FIELD_MAP.items():
            if field in data:
                value = data[field]
                if value is None: continue
                if isinstance(value, list):
                    encoded = self.LIST_DELIM.join(self._sanitize(v) for v in value)
                else:
                    encoded = self._sanitize(value)
                if encoded != "":
                    parts.append(f"{index}.{encoded}")
        return self.FIELD_DELIM.join(parts)
    #----------------------------------------------------------------------------------------------

    def decode(self, encoded_str: str) -> dict:
        result = {}
        parts = encoded_str.split(self.FIELD_DELIM)
        for part in parts:
            if "." not in part:
                continue
            idx_str, value_str = part.split(".", 1)
            try:
                idx = int(idx_str)
            except ValueError:
                continue
            field = self._index_to_field.get(idx)
            if not field:
                continue
            if field in self.LIST_FIELDS:
                items = value_str.split(self.LIST_DELIM)
                result[field] = [item.replace(self.ESCAPE_CHAR, self.LIST_DELIM).replace(self.ESCAPE_CHAR, self.FIELD_DELIM) for item in items]
            else:
                result[field] = value_str.replace(self.ESCAPE_CHAR, self.FIELD_DELIM).replace(self.ESCAPE_CHAR, self.LIST_DELIM)
        return result
    #----------------------------------------------------------------------------------------------

    def get_alergias(self, json_obj: dict):
        return json_obj.get("alergias", [])
    #----------------------------------------------------------------------------------------------

    def get_riesgo_cardio(self, json_obj: dict):
        return json_obj.get("factores riesgo cardivascular", [])
    #----------------------------------------------------------------------------------------------

    def get_antecedentes(self, json_obj: dict):
        return json_obj.get("antecedentes familiares", [])
    #----------------------------------------------------------------------------------------------

    def get_ingresos(self, json_obj: dict):
        return json_obj.get("ingresos", [])
    #----------------------------------------------------------------------------------------------

    def get_visitas(self, json_obj: dict):
        if "fecha" in json_obj.keys(): return [ json_obj["fecha"] ]
        return [ ]
    #----------------------------------------------------------------------------------------------

    def get_medicacion(self, json_obj: dict):
        return json_obj.get("medicación", [])
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
