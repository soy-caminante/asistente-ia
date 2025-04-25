import  datetime
import  functools
import  os
import  mimetypes
import  pathlib
import  re
import  sys

from    dateutil                    import parser
from    typing                      import Callable, TypeVar, Generic, Any
#--------------------------------------------------------------------------------------------------

def get_matches_case_no_sensitive(lista_cadenas, patron):
    return [(indice, cadena) for indice, cadena in enumerate(lista_cadenas) if re.search(patron, cadena, re.IGNORECASE)]
#--------------------------------------------------------------------------------------------------

def elapsed_time_to_str(elapsed_time):
    # Convertir a minutos y segundos
    minutos         = int(elapsed_time // 60)
    segundos        = int(elapsed_time % 60)
    milisegundos    = int((elapsed_time - int(elapsed_time)) * 1000)

    # Formatear a mm:ss:ms
    return f"{minutos:02}:{segundos:02}:{milisegundos:03}"
#--------------------------------------------------------------------------------------------------

def get_assets_dir_path(assets_dir, relative_to_cwd=False):
    def get_current_script_dir():
        pathname = os.path.dirname(sys.argv[0])
        return os.path.abspath(pathname)

    if assets_dir:
        if not pathlib.Path(assets_dir).is_absolute():
            if "_MEI" in __file__:
                # support for "onefile" PyInstaller
                assets_dir = str(
                    pathlib.Path(__file__).parent.parent.joinpath(assets_dir).resolve()
                )
            else:
                assets_dir = str(
                    pathlib.Path(os.getcwd() if relative_to_cwd else get_current_script_dir())
                    .joinpath(assets_dir)
                    .resolve()
                )

    env_assets_dir = os.getenv("FLET_ASSETS_DIR")
    if env_assets_dir:
        assets_dir = env_assets_dir
    return assets_dir
#--------------------------------------------------------------------------------------------------

def get_elapsed_years(fecha_nacimiento):
    # Convertir la cadena de texto a un objeto datetime
    fecha_nacimiento = datetime.datetime.strptime(fecha_nacimiento, "%d-%m-%Y")
    
    # Obtener la fecha actual
    fecha_actual = datetime.datetime.now()
    
    # Calcular la edad en años
    edad = fecha_actual.year - fecha_nacimiento.year
    
    # Ajustar si la fecha de nacimiento aún no ha ocurrido este año
    if (fecha_actual.month, fecha_actual.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1

    return edad
#--------------------------------------------------------------------------------------------------

T = TypeVar('T')
class StatusInfo(Generic[T]):
    @classmethod
    def ok(cls, value: T=None):
        return cls(value)
    #----------------------------------------------------------------------------------------------
    @classmethod 
    def error(cls, info=None):
        return cls().set_error(info)
    #----------------------------------------------------------------------------------------------
    
    def __init__(self, value:T=None, info=None):
        self._value = value
        self._info  = info
    #----------------------------------------------------------------------------------------------

    def __bool__(self):
        return self._value is not None
    #----------------------------------------------------------------------------------------------
    
    def set_ok(self, value:T, info=None):
        self._value = value
        self._info  = info
        return self
    #----------------------------------------------------------------------------------------------

    def set_error(self, info=None):
        self._value = None
        self._info  = info 
        return self
    #----------------------------------------------------------------------------------------------

    def is_present(self):
        return self._value is not None
    #----------------------------------------------------------------------------------------------

    def get(self) -> T:
        return self._value
    #----------------------------------------------------------------------------------------------

    def or_else(self, default_value: T|None=None) -> T|None:
        return self._value if self._value is not None else default_value
    #----------------------------------------------------------------------------------------------

    def if_present(self, consumer):
        if self._value is not None:
            consumer(self._value)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

def try_catch(log_fcn: Callable, default: Any = None, catch: tuple = (Exception,)):
    def decorator(func: Callable[..., T]) -> Callable[..., T | Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except catch as e:
                log_fcn(e)
                return default
        return wrapper
    return decorator
#--------------------------------------------------------------------------------------------------

def void_try_catch(log_fcn: Callable, catch: tuple = (Exception,)):
    def decorator(func: Callable[..., T]) -> Callable[..., None]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except catch as e:
                log_fcn(e)
        return wrapper
    return decorator
#--------------------------------------------------------------------------------------------------

def file_size_to_str(bytes_int):
    if bytes_int < 1024:
        return f"{bytes_int} B"
    elif bytes_int < 1024**2:
        return f"{bytes_int / 1024:.2f} kB"
    else:
        return f"{bytes_int / (1024**2):.2f} MB"
#--------------------------------------------------------------------------------------------------

def is_plaintext_mime(mime_type: str) -> bool:
    if mime_type.startswith("text/"):
        return True
    if mime_type in {"application/json", "application/xml", "application/javascript"}:
        return True
    return False        
#--------------------------------------------------------------------------------------------------

def is_plaint_text_file(file_path: str|pathlib.Path):
    mime, _ = mimetypes.guess_type(str(file_path))
    return is_plaint_text_file(mime), mime
#--------------------------------------------------------------------------------------------------

def timestamp_str_to_datetime(ref):
    try:
        return parser.parse(ref)
    except (ValueError, TypeError) as e:
        print(f"Error al parsear la fecha: {e}")
        return None
#--------------------------------------------------------------------------------------------------
