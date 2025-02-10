import  inspect
import  logging
import  pathlib

from    logging.handlers    import RotatingFileHandler
#--------------------------------------------------------------------------------------------------

class Logger:
    BASE_DIR = ""
    #----------------------------------------------------------------------------------------------

    def to_str(*args):
        text = ""
        for a in args[0]: 
            text += str(a)
        return text
    #----------------------------------------------------------------------------------------------

    class CallerInfoFilter(logging.Filter):
        @classmethod
        def get_relative_path(cls, ruta):
            pieces = ruta.parts
            
            try:
                token_index     = pieces.index(Logger.BASE_DIR)
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
    
    @classmethod
    def setup(cls, path: pathlib.Path, file_log_enabled=False, base_dir = "/"):
        cls.BASE_DIR    = base_dir
        handlers        = [ logging.StreamHandler() ]
        
        if file_log_enabled:
            handlers.append(RotatingFileHandler(path,  maxBytes=10e6, backupCount=5))

        logging.basicConfig(handlers    =   handlers,
                                            format      = "%(asctime)s - %(filename)s:%(lineno)d %(message)s", 
                                            datefmt     = "%d-%m-%y %H:%M:%S",
                                            level       = logging.INFO)
        
        logger = logging.getLogger()
        logger.addFilter(cls.CallerInfoFilter())
    #----------------------------------------------------------------------------------------------

    @classmethod
    def info(cls, *args):
        logging.info(cls.to_str(args))
    #----------------------------------------------------------------------------------------------

    @classmethod
    def multi_info(cls, *args):
        for a in args:
            logging.info(a)
    #----------------------------------------------------------------------------------------------

    @classmethod
    def warning(cls, *args):
        logging.warning(cls.to_str(args))
    #----------------------------------------------------------------------------------------------

    @classmethod
    def critical(cls, *args):
        logging.critical(cls.to_str(args))
    #----------------------------------------------------------------------------------------------

    @classmethod
    def multi_warning(cls, *args):
        first = True
        for a in args:
            if first:
                first = False
                logging.warning(a)
            else:
                logging.info(a)
    #----------------------------------------------------------------------------------------------

    @classmethod
    def error(cls, *args):
        logging.error(cls.to_str(args))
    #----------------------------------------------------------------------------------------------

    @classmethod
    def multi_error(cls, *args):
        first = True
        for a in args:
            if first:
                first = False
                logging.error(a)
            else:
                logging.info(a)
    #----------------------------------------------------------------------------------------------

    @classmethod
    def exception(cls, args):
        logging.exception(args)
    #----------------------------------------------------------------------------------------------

    @classmethod
    def multi_exception(cls, *args):
        first = True
        for a in args:
            if first:
                first = False
                logging.exception(a)
            else:
                logging.info(a)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
