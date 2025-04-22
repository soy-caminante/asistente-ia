import  flet                            as      ft

from    pmanager.backend.service        import  BackendService
from    pmanager.view.environment       import  Environment
from    pmanager.view.landing           import  LandingView
#--------------------------------------------------------------------------------------------------

class App:
    def __init__(self, page: ft.Page, env: Environment, backend: BackendService):
        self.build_ui(page, env, backend)
    #----------------------------------------------------------------------------------------------

    def build_ui(self, page: ft.Page, env: Environment, backend: BackendService):
        page.title        = "Gestor de Pacientes"
        page.theme_mode   = "light"
        page.session.clear()
        page.views.append(LandingView(page, "/", env, backend))
        page.go("/")
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------