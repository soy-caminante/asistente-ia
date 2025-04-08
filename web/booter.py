import  flet                        as ft 
import  os 
import  sys

from    environment.environment     import  Environment
from    webapp.webapp               import  WebApp
#--------------------------------------------------------------------------------------------------

class Booter:
    def __init__(self):
        self._env: Environment  = None
        self._console           = False
    #----------------------------------------------------------------------------------------------

    def run(self):
        
        self._console = "console" in sys.argv

        if "huggingface" in sys.argv:
            self._env = Environment("huggingface")
        else:
            self._env = Environment("openai")
            
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
