import  flet                            as      ft
import  sys
import  time

from    pmanager.backend.environment    import  Environment         as BackEnvironment
from    pmanager.backend.service        import  BackendService
from    pmanager.view.environment       import  Environment
from    pmanager.view.landing           import  LandingView
from    tools.viewtools                 import  OverlayCtrl, OverlayCtrlWrapper
#--------------------------------------------------------------------------------------------------

class App:
    def __init__(self, page: ft.Page, env: Environment):
        self._env       = env
        self._page      = page
        self._overlay   = OverlayCtrl()
        self._ov_wrap   = OverlayCtrlWrapper(self._overlay)
        self._backend   = BackendService(   BackEnvironment(env.log, 
                                                            env.runtime, 
                                                            env.model,
                                                            env.chat_endpoint,
                                                            env.db_port, 
                                                            env.gpu), 
                                            self._ov_wrap)
        self._view      = LandingView(page, "/", env, self._overlay, self._backend)

        self.build_ui(page)
    #----------------------------------------------------------------------------------------------

    def check_db_connection(self):
        with self._ov_wrap.wait("Compronando la conexión con el servidor de datos"):
            if not self._backend.check_db():
                self._ov_wrap.update("Servidor de datos no disponible")
                self._overlay.show_warning \
                ([
                    "La base de datos no está correctamente configurada",
                    "¿Desea continuar?"
                ])

                if self._overlay.wait_answer():
                    time.sleep(3)
                    self._page.window.destroy()
                    sys.exit(-1)
    #----------------------------------------------------------------------------------------------

    def load_initial_data(self):
        con_list            = self._backend.load_all_consolidated_clientes()
        src_list            = self._backend.load_all_src_clientes()
        pretrained_status   = self._backend.load_pretrained()
        
        if not con_list:
            self._env.log.error("No se ha podido cargar la lista de pacientes consolidados")
        if not src_list:
            self._env.log.error("No se ha podido cargar la lista de pacientes por consolidar")
        if not pretrained_status:
            self._env.log.error("No se han podido generar los contextos preentrenados")

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

        self.check_db_connection()
        self.load_initial_data()        
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------