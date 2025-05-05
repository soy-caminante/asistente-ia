import  datetime
import  mimetypes
import  os
import  pathlib
import  tiktoken

from    bson                    import  ObjectId
from    dataclasses             import  dataclass
from    tools.tools             import  get_elapsed_years, file_size_to_str, is_plaintext_mime, timestamp_str_to_datetime
#--------------------------------------------------------------------------------------------------

@dataclass 
class DocumentoSrc:
    nombre          : str
    path            : str
    tipo            : str
    size            : int
#--------------------------------------------------------------------------------------------------

@dataclass
class ExpedienteSrc:
    db_id               : str
    dni                 : str
    ref_id              : str
    nombre              : str
    apellidos           : str
    fecha_nacimiento    : str
    sexo                : str
    documentos          : list[DocumentoSrc]
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        if isinstance(self.db_id, ObjectId):
            self.db_id = str(self.db_id)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

@dataclass 
class DocumentoCon:
    nombre          : str
    path            : str
    tipo            : str
    size            : int
    tokens          : int
#--------------------------------------------------------------------------------------------------

@dataclass
class ExpedienteCon:
    db_id               : str
    dni                 : str
    ref_id              : str
    nombre              : str
    apellidos           : str
    fecha_nacimiento    : str
    sexo                : str
    documentos          : list[DocumentoCon]
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        if isinstance(self.db_id, ObjectId):
            self.db_id = str(self.db_id)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------


@dataclass
class IncommingFileInfo:
    path:       pathlib.Path
    mime:       str
    size:       int
    tokens:     str
    ts:         datetime.datetime
    content:    str = None

    @property
    def name(self): return self.path.stem
    #----------------------------------------------------------------------------------------------

    @property
    def size_str(self): return file_size_to_str(self.size)
    #----------------------------------------------------------------------------------------------

    @property
    def is_plain_text(self): return is_plaintext_mime(self.mime)
    #----------------------------------------------------------------------------------------------
    
    @property
    def ts_str(self): return self.ts.strftime("%d-%m-%Y")
    #----------------------------------------------------------------------------------------------

    @staticmethod
    def build(path: pathlib.Path, ts: datetime.datetime, encoding_model="cl100k_base") -> 'IncommingFileInfo':
        # Tipo MIME
        mime, _ = mimetypes.guess_type(str(path))

        # Tamaño en bytes
        size_bytes = os.path.getsize(str(path))

        # Leer contenido para contar tokens
        if is_plaintext_mime(mime):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read()

                # Tokenización
                tokenizer   = tiktoken.get_encoding(encoding_model)
                num_tokens  = len(tokenizer.encode(contenido))
        else:
            with open(path, "rb") as f:
                contenido   = f.read()
                num_tokens  = 0      
    
        return IncommingFileInfo(path, mime, size_bytes, num_tokens, ts, contenido)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

@dataclass
class ClienteInfo:
    nombre:             str
    apellidos:          str
    fecha_nacimiento:   str|datetime.datetime
    sexo:               str
    dni:                str
    id_interno:         str
    db_id:              str|None = None
    #----------------------------------------------------------------------------------------------

    @property
    def edad(self): return get_elapsed_years(self.fecha_nacimiento)
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        if isinstance(self.fecha_nacimiento, str):
            self.fecha_nacimiento = timestamp_str_to_datetime(self.fecha_nacimiento)
        self.fecha_nacimiento.replace(tzinfo=datetime.timezone.utc)

        if isinstance(self.db_id, ObjectId):
            self.db_id = str(self.db_id)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

@dataclass
class IncommingCliente:
    db_id:          pathlib.Path
    personal_info:  ClienteInfo
    docs:           list[IncommingFileInfo]
#--------------------------------------------------------------------------------------------------

@dataclass
class SrcDocInfo:
    db_id:              str
    owner:              str
    filename:           str
    path:               str
    mime:               str
    created_at:         datetime.datetime
    source_created_at:  datetime.datetime
    size_bytes:         int
    content:            str|None = None
    #----------------------------------------------------------------------------------------------

    @property
    def ts(self): return self.source_created_at
    #----------------------------------------------------------------------------------------------

    @property
    def ts_str(self): return self.source_created_at.strftime("%d-%m-%Y")
    #----------------------------------------------------------------------------------------------

    @property
    def name(self): return self.filename
    #----------------------------------------------------------------------------------------------

    @property
    def size_str(self): return file_size_to_str(self.size_bytes)
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        self.created_at.replace(tzinfo=datetime.timezone.utc)
        self.source_created_at.replace(tzinfo=datetime.timezone.utc)
        if isinstance(self.db_id, ObjectId):
            self.db_id = str(self.db_id)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

@dataclass
class IaDcoInfo:
    db_id:              str
    owner:              str
    filename:           str
    path:               str
    source_ref:         str
    source_mime:        str
    source_created_at:  datetime.datetime
    created_at:         datetime.datetime
    size_bytes:         int
    tokens:             int
    content:            str|None = None
    #----------------------------------------------------------------------------------------------

    @property
    def ts(self): return self.source_created_at
    #----------------------------------------------------------------------------------------------

    @property
    def ts_str(self): return self.source_created_at.strftime("%d-%m-%Y")
    #----------------------------------------------------------------------------------------------

    @property
    def name(self): return self.source_ref
    #----------------------------------------------------------------------------------------------

    @property
    def size_str(self): return file_size_to_str(self.size_bytes)
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        self.created_at.replace(tzinfo=datetime.timezone.utc)
        self.source_created_at.replace(tzinfo=datetime.timezone.utc)
        if isinstance(self.db_id, ObjectId):
            self.db_id = str(self.db_id)
        if isinstance(self.source_ref, ObjectId):
            self.source_ref = str(self.source_ref)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

@dataclass
class BIaDcoInfo:
    db_id:              str
    owner:              str
    filename:           str
    path:               str
    source_ref:         str
    iadoc_ref:          str
    source_mime:        str
    source_created_at:  datetime.datetime
    created_at:         datetime.datetime
    size_bytes:         int
    tokens:             int
    content:            bytes|None = None
    #----------------------------------------------------------------------------------------------

    @property
    def name(self): return self.source_ref
    #----------------------------------------------------------------------------------------------

    @property
    def ts(self): return self.source_created_at
    #----------------------------------------------------------------------------------------------

    @property
    def ts_str(self): return self.source_created_at.strftime("%d-%m-%Y")
    #----------------------------------------------------------------------------------------------

    @property
    def size_str(self): return file_size_to_str(self.size_bytes)
    #----------------------------------------------------------------------------------------------

    def __post_init__(self):
        self.created_at.replace(tzinfo=datetime.timezone.utc)
        self.source_created_at.replace(tzinfo=datetime.timezone.utc)
        if isinstance(self.db_id, ObjectId):
            self.db_id = str(self.db_id)
        if isinstance(self.source_ref, ObjectId):
            self.source_ref = str(self.source_ref)
        if isinstance(self.iadoc_ref, ObjectId):
            self.iadoc_ref = str(self.iadoc_ref)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

@dataclass
class ClienteMetaInformation:
    personal_info:  ClienteInfo
    src_docs:       list[SrcDocInfo]
    iadocs:         list[IaDcoInfo]
    biadocs:        list[BIaDcoInfo]
#--------------------------------------------------------------------------------------------------

@dataclass
class StructuredExpediente:
    content: str
#--------------------------------------------------------------------------------------------------

@dataclass
class ExpedienteBasicInfo:
    antecedentes_familiares:        str
    factores_riesgo_cardiovascular: str
    medicacion:                     str
    alergias:                       str
    ingresos:                       str
    ultimas_visitas:                str
#--------------------------------------------------------------------------------------------------
