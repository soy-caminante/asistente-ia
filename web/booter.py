import  flet                        as ft 
import  sys

from    environment.environment     import  Environment
from    webapp.webapp               import  WebApp
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._env = Environment()
    #----------------------------------------------------------------------------------------------

    def run(self):
        run_console = False
        if len(sys.argv) > 2:
            if sys.argv[2] == "console":
                run_console = True
        if run_console:
            ft.app(target=self.run_app, assets_dir="static")
        else:
            ft.app(target=self.run_app, assets_dir="static", view=ft.WEB_BROWSER, port=8080)
    #----------------------------------------------------------------------------------------------


    def run_app(self, page: ft.Page):
        self._env.set_page(page)
        WebApp(self._env)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
