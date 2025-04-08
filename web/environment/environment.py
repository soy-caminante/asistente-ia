import  flet                        as      ft
import  pathlib

from    environment.logger          import  Logger
from    webapp.factories            import  text_factory
from    backend.service             import  BackendService, get_service_instance
#--------------------------------------------------------------------------------------------------

class Locations:
    def __init__(self):
        self._logo_path = None
    #----------------------------------------------------------------------------------------------

    @classmethod
    def load(cls, page: ft.Page):
        ret             = cls()
        ret._logo_path  = "/imgs/logo.png"
        return ret
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class Environment:
    def __init__(self, model):
        self._backend: BackendService   = get_service_instance(model)
        self._locations: Locations      = None
        self._page: ft.Page             = None
        self._console                   = False

        text_factory.set_container_size(24)
        text_factory.set_row_title_size(20)
        text_factory.set_row_text_size(20)

        Logger.setup(pathlib.Path(__file__).parent.parent / "data/logs/logger.log")
    #----------------------------------------------------------------------------------------------

    def set_page(self, page: ft.Page, console):
        self._console       = console
        self._page          = page
        self._locations     = Locations.load(page)

        Logger.info("Sistema funcionando")
    #----------------------------------------------------------------------------------------------        
#--------------------------------------------------------------------------------------------------
        