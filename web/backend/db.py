import  re
import  transaction
import  unicodedata

from    models.models       import *
from    persistent.mapping  import PersistentMapping
from    ZODB                import DB, FileStorage
#--------------------------------------------------------------------------------------------------

class NoSQLDB:
    def __init__(self, path, log_callback):
        self._db            = DB(FileStorage.FileStorage(str(path)))
        self._connection    = self._db.open()
        self._root          = self._connection.root()
        self._log_callback  = log_callback

        if 'indice_por_letra' not in self._root:
            self._root['indice_por_letra'] = PersistentMapping()
            transaction.commit()
    #----------------------------------------------------------------------------------------------

    def add_to_index(self, paciente: Paciente):
        index   = self._root['indice_por_letra']
        letter  = paciente.apellidos[0].lower()
    
        if letter not in index:
            index[letter] = PersistentMapping()
    
        clave = f"{paciente.apellidos} {paciente.nombre}".lower()
    
        index[letter][clave] = paciente.ref_id
    #----------------------------------------------------------------------------------------------

    @property
    def root(self): return self._root
    #----------------------------------------------------------------------------------------------

    def log(self, fcn, info): 
        self._log_callback(fcn)
        self._log_callback(info)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class DbPacienteMngr:
    def __init__(self, db: NoSQLDB):
        self._db    = db
    #----------------------------------------------------------------------------------------------

    def check_paciente(self, ref_id:str): return ref_id in self._db.root
    #----------------------------------------------------------------------------------------------

    def get_paciente(self, ref_id:str) -> Paciente:
        if not self.check_paciente(ref_id): return None
        paciente    = self._db.root[ref_id]
        copy_obj    = paciente
        return copy_obj
    #----------------------------------------------------------------------------------------------

    def get_pacientes(self, pattern) -> list[Paciente]:
        def normalize(text):
            return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")

        ret = [ ]

        if pattern == "": return ret

        if pattern in self._db.root:
            paciente = self._db.root[pattern]
            ret.append(paciente)
        else:
            index   = self._db.root['indice_por_letra']
            patron  = re.compile(normalize(pattern), re.IGNORECASE)

            letter      = pattern[0].lower()
            subindex    = index.get(letter, { })

            if pattern == "pé":
                pass
            for key, ref_id in subindex.items():
                if patron.search(normalize(key)):
                    paciente = self._db.root.get(ref_id)
                    ret.append(paciente)

        return ret
    #----------------------------------------------------------------------------------------------
    
    def store_paciente(self, paciente: Paciente):
        try:
            self._db.root[paciente.ref_id] = paciente
            self._db.add_to_index(paciente)
            transaction.commit()
            return True
        except Exception as ex:
            self._db.log("Error en store_paciente", ex)
            transaction.abort()
            return False
    #----------------------------------------------------------------------------------------------

    def update_paciente(self, paciente: Paciente):
        try:
            self._db.root[paciente.ref_id] = paciente
            transaction.commit()
            return False
        except Exception as ex:
            self._db.log("Error en update_paciente", ex)
            transaction.abort()
            return True
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
