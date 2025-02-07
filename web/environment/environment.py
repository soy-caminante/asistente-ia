import  flet                        as      ft
import  pathlib

from    backend.service             import  BackendService, get_service_instance
#--------------------------------------------------------------------------------------------------

class Locations:
    def __init__(self):
        self._logo_path = None
    #----------------------------------------------------------------------------------------------

    @classmethod
    def load(cls, page: ft.Page):
        ret             = cls()
        print(f"Logo: ")
        ret._logo_path  = "/imgs/logo.png"
        print(ret._logo_path)
        return ret
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class Environment:
    def __init__(self):
        self._backend: BackendService   = get_service_instance()
        self._locations: Locations      = None
        self._page: ft.Page             = None
    #----------------------------------------------------------------------------------------------

    def set_page(self, page: ft.Page):
        self._page          = page
        self._locations     = Locations.load(page)
    #----------------------------------------------------------------------------------------------        
#--------------------------------------------------------------------------------------------------
        