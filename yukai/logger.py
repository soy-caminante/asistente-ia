import  inspect
import  logging
import  pathlib

from    logging.handlers    import RotatingFileHandler
#--------------------------------------------------------------------------------------------------

class Logger:
    @staticmethod
    def to_str(*args):
        text = ""
        for a in args[0]: 
            text += str(a)
        return text
    #----------------------------------------------------------------------------------------------

    class CallerInfoFilter(logging.Filter):
        def __init__(self, base_dir):
            self._base_dir = base_dir
        #------------------------------------------------------------------------------------------

        def get_relative_path(self, ruta: pathlib.Path):
            pieces = ruta.parts
            
            try:
                token_index     = pieces.index(self._base_dir)
                ruta_deseada    = pathlib.Path(*pieces[token_index + 1:])
                return ruta_deseada
            except ValueError:
                return ""
        #------------------------------------------------------------------------------------------

        def filter(self, record):
            frame           = inspect.stack()[7]
            record.filename = self.get_relative_path(pathlib.Path(frame.filename))
            record.lineno   = frame.lineno

            return True
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    class ShortPathFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None, subruta_clave='yukai'):
            super().__init__(fmt, datefmt)
            self.subruta_clave = subruta_clave
        #------------------------------------------------------------------------------------------

        def format(self, record):
            ruta = record.pathname
            idx = ruta.find(self.subruta_clave)
            if idx != -1:
                record.pathname = ruta[idx:]
            return super().format(record)
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    def __init__(self, enabled=True):
        self._base_dir  = ""
        self._handlers  = [ logging.StreamHandler() ]   
        self._enabled   = enabled
    #----------------------------------------------------------------------------------------------

    def setup(self, name: str, path: pathlib.Path, file_log_enabled=False, base_dir = "/"):
        if self._enabled:
            self._base_dir  = base_dir
            self._logger    = logging.getLogger(name)
            self._logger.setLevel(logging.INFO)
            
            if file_log_enabled:
                self._handlers.append(RotatingFileHandler(path/f"{name}.log",  maxBytes=10e6, backupCount=5))

            for h in self._handlers:
                formatter = Logger.ShortPathFormatter(fmt="%(asctime)s - %(pathname)s:%(lineno)d %(message)s")
                h.setFormatter(formatter)
                self._logger.addHandler(h)

            self._logger.addFilter(self.CallerInfoFilter(self._base_dir))

        return self
    #----------------------------------------------------------------------------------------------

    def remove_console_handler(self): self._logger.removeHandler(self._handlers[0])
    #----------------------------------------------------------------------------------------------

    def info(self, *args):
        if self._enabled:
            self._logger.info(self.to_str(args))
    #----------------------------------------------------------------------------------------------

    def multi_info(self, *args):
        if self._enabled:
            for a in args:
                self._logger.info(a)
    #----------------------------------------------------------------------------------------------

    def warning(self, *args):
        if self._enabled:
            self._logger.warning(self.to_str(args))
    #----------------------------------------------------------------------------------------------

    def critical(self, *args):
        if self._enabled:
            self._logger.critical(self.to_str(args))
    #----------------------------------------------------------------------------------------------

    def multi_warning(self, *args):
        if self._enabled:    
            first = True
            for a in args:
                if first:
                    first = False
                    self._logger.warning(a)
                else:
                    self._logger.info(a)
    #----------------------------------------------------------------------------------------------

    def error(self, *args):
        if self._enabled:
            self._logger.error(self.to_str(args))
    #----------------------------------------------------------------------------------------------

    def multi_error(self, *args):
        if self._enabled:
            first = True
            for a in args:
                if first:
                    first = False
                    self._logger.error(a)
                else:
                    self._logger.info(a)
    #----------------------------------------------------------------------------------------------

    def exception(self, args):
        if self._enabled:
            self._logger.exception(args)
    #----------------------------------------------------------------------------------------------

    def multi_exception(self, *args):
        if self._enabled:
            first = True
            for a in args:
                if first:
                    first = False
                    self._logger.exception(a)
                else:
                    self._logger.info(a)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
