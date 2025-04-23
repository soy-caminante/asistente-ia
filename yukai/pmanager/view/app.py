import  flet                            as      ft
import  sys

from    pmanager.backend.service        import  BackendService
from    pmanager.view.environment       import  Environment
from    pmanager.view.landing           import  LandingView
#--------------------------------------------------------------------------------------------------

class App:
    def __init__(self, page: ft.Page, env: Environment, backend: BackendService):
        self._env       = env
        self._backend   = backend
        self._view      = LandingView(page, "/", env, backend) 
        self.build_ui(page, env, backend)
    #----------------------------------------------------------------------------------------------

    def load_initial_data(self):
        self._view.show_wait_ctrl(True, "Cargando datos iniciales")
        con_list    = self._backend.load_all_consolidated_pacientes()
        src_list    = self._backend.load_all_src_pacientes()

        if not con_list:
            self._env.log.error("No se ha podido cargar la lista de pacientes consolidados")
        if not src_list:
            self._env.log.error("No se ha podido cargar la lista de pacientes por consolidar")

        if not con_list or not src_list:
            status = self._backend.check_db()

            if not status:
                option = self._view.show_warning_ctrl \
                ([
                    "La base de datos no está correctamente configurada",
                    "¿Desea continuar?"
                ])

                if not option:
                    self._view.page.window.destroy()
                    return
        
        self._view.populate(src_list.or_else([]), con_list.or_else([]))
        self._view.show_wait_ctrl(False)
    #----------------------------------------------------------------------------------------------

    def build_ui(self, page: ft.Page, env: Environment, backend: BackendService):
        page.title      = "Gestor de Pacientes"
        page.theme_mode = "light"
        page.session.clear()
        page.views.append(self._view)
        page.go("/")

        self.load_initial_data()        
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------