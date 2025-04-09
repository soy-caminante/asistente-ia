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

        def get_relative_path(self, ruta):
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

    def __init__(self):
        self._base_dir  = ""
        self._handlers  = [ logging.StreamHandler() ]   
    #----------------------------------------------------------------------------------------------

    def setup(self, name: str, path: pathlib.Path, file_log_enabled=False, base_dir = "/"):
        self._base_dir  = base_dir
        self._logger    = logging.getLogger(name)
        
        if file_log_enabled:
            self._handlers.append(RotatingFileHandler(path/f"{name}.log",  maxBytes=10e6, backupCount=5))

        for h in self._handlers:
            h.setFormatter(logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d %(message)s"))
            self._logger.addHandler(h)

        self._logger.addFilter(self.CallerInfoFilter(self._base_dir))

        return self
    #----------------------------------------------------------------------------------------------

    def remove_console_handler(self): self._logger.removeHandler(self._handlers[0])
    #----------------------------------------------------------------------------------------------

    def info(self, *args):
        self._logger.info(self.to_str(args))
    #----------------------------------------------------------------------------------------------

    def multi_info(self, *args):
        for a in args:
            self._logger.info(a)
    #----------------------------------------------------------------------------------------------

    def warning(self, *args):
        self._logger.warning(self.to_str(args))
    #----------------------------------------------------------------------------------------------

    def critical(self, *args):
        self._logger.critical(self.to_str(args))
    #----------------------------------------------------------------------------------------------

    def multi_warning(self, *args):
        first = True
        for a in args:
            if first:
                first = False
                self._logger.warning(a)
            else:
                self._logger.info(a)
    #----------------------------------------------------------------------------------------------

    def error(self, *args):
        self._logger.error(self.to_str(args))
    #----------------------------------------------------------------------------------------------

    def multi_error(self, *args):
        first = True
        for a in args:
            if first:
                first = False
                self._logger.error(a)
            else:
                self._logger.info(a)
    #----------------------------------------------------------------------------------------------

    def exception(self, args):
        self._logger.exception(args)
    #----------------------------------------------------------------------------------------------

    def multi_exception(self, *args):
        first = True
        for a in args:
            if first:
                first = False
                self._logger.exception(a)
            else:
                self._logger.info(a)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
