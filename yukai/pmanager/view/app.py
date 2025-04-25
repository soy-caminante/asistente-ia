import  flet                            as      ft

from    pmanager.backend.environment    import  Environment         as BackEnvironment
from    pmanager.backend.service        import  BackendService
from    pmanager.view.environment       import  Environment
from    pmanager.view.landing           import  LandingView
from    tools.viewtools                 import  OverlayCtrl, OverlayCtrlWrapper
#--------------------------------------------------------------------------------------------------

class App:
    def __init__(self, page: ft.Page, env: Environment):
        self._env       = env
        self._overlay   = OverlayCtrl()
        self._ov_wrap   = OverlayCtrlWrapper(self._overlay)
        self._backend   = BackendService(BackEnvironment(env.log, env.runtime), self._ov_wrap)
        self._view      = LandingView(page, "/", env, self._overlay, self._backend)

        self.build_ui(page)
    #----------------------------------------------------------------------------------------------

    def load_initial_data(self):
        con_list    = self._backend.load_all_consolidated_clientes()
        src_list    = self._backend.load_all_src_clientes()

        if not con_list:
            self._env.log.error("No se ha podido cargar la lista de pacientes consolidados")
        if not src_list:
            self._env.log.error("No se ha podido cargar la lista de pacientes por consolidar")

        if not con_list or not src_list:
            status = self._backend.check_db()

            if not status:
                option = self._overlay.show_warning \
                ([
                    "La base de datos no está correctamente configurada",
                    "¿Desea continuar?"
                ]).wait_answer()

                if not option:
                    self._view.page.window.destroy()
                    return
        self._view.populate(src_list.or_else([]), con_list.or_else([]))
    #----------------------------------------------------------------------------------------------

    def build_ui(self, page: ft.Page):
        page.title      = "Gestor de Pacientes"
        page.theme_mode = "light"
        page.session.clear()
        page.views.append(self._view)
        page.go("/")

        self.load_initial_data()        
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------