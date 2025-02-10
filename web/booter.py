import  flet                        as ft 
import  os 
import  sys

from    environment.environment     import  Environment
from    webapp.webapp               import  WebApp
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._env       = Environment()
        self._console   = False
    #----------------------------------------------------------------------------------------------

    def run(self):
        if len(sys.argv) > 2:
            if sys.argv[2] == "console":
                self._console = True
        if self._console:
            ft.app(target=self.run_app, assets_dir="static")
        else:
            ft.app(target=self.run_app, assets_dir="static", view=ft.WEB_BROWSER, port=int(os.getenv("PORT", 8080)))
    #----------------------------------------------------------------------------------------------


    def run_app(self, page: ft.Page):
        self._env.set_page(page, self._console)
        WebApp(self._env)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
