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
        def __init__(self):
            self._excluded_locations    = { __file__: None }
        #------------------------------------------------------------------------------------------

        def add_excluded_locations(self, file, locations):
            if locations is not None:
                if not isinstance(locations, list):
                    locations = [ locations ]

            if not file in self._excluded_locations.keys():
                self._excluded_locations[file] = locations
            else:
                self._excluded_locations[file] += locations
        #------------------------------------------------------------------------------------------

        def get_frame(self):
            stack = inspect.stack()
            for index in range(7, len(stack)):
                if stack[index].filename != __file__:
                    if not stack[index].filename in self._excluded_locations.keys():
                        return stack[index]
                    else:
                        locations = self._excluded_locations[stack[index].filename]
                        if not locations and not stack[index].function.startswith("log_"):
                            return stack[index]
                        elif locations:
                            if stack[index].function not in locations:
                                return stack[index]
            return None
        #------------------------------------------------------------------------------------------

        def filter(self, record):
            frame           = self.get_frame()

            if frame:
                record.filename = pathlib.Path(frame.filename)
                record.lineno   = frame.lineno
                record.funcName = frame.function

                return True
            return False
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    class ShortPathFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None, subruta_clave='yukai'):
            super().__init__(fmt, datefmt)
            self.subruta_clave = subruta_clave
        #------------------------------------------------------------------------------------------

        def format(self, record):
            ruta    = str(record.filename)
            idx     = ruta.find(self.subruta_clave)
            if idx != -1:
                record.pathname = ruta[idx+len(self.subruta_clave)+1:]
            return super().format(record)
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    def __init__(self, enabled=True):
        self._handlers  = [ logging.StreamHandler() ]   
        self._enabled   = enabled
        self._filter    = self.CallerInfoFilter()
    #----------------------------------------------------------------------------------------------

    def setup(self, name: str, path: pathlib.Path, file_log_enabled=False, base_dir = "/"):
        if self._enabled:
            self._base_dir  = base_dir
            self._logger    = logging.getLogger(name)
            self._logger.setLevel(logging.INFO)
            
            if file_log_enabled:
                self._handlers.append(RotatingFileHandler(path/f"{name}.log",  maxBytes=10e6, backupCount=5))

            for h in self._handlers:
                formatter = Logger.ShortPathFormatter(fmt="%(asctime)s - %(pathname)s:%(funcName)s:%(lineno)d %(message)s")
                h.setFormatter(formatter)
                self._logger.addHandler(h)

            self._logger.addFilter(self._filter)

        return self
    #----------------------------------------------------------------------------------------------

    def remove_console_handler(self): self._logger.removeHandler(self._handlers[0])
    #----------------------------------------------------------------------------------------------

    def add_excluded_locations(self, file, locations):
        self._filter.add_excluded_locations(file, locations)
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
