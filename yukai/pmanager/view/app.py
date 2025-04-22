import  flet                            as      ft
from    pmanager.environment            import  Environment
from    tools.factories                 import  *
from    webapp.webapp.navmanger         import  *
from    webapp.webapp.patitienview      import  PatitentView
from    webapp.webapp.searchview        import  SearchView
#--------------------------------------------------------------------------------------------------

class App:
    def __init__(self, page: ft.Page, env: Environment):
        self._env                       = env
        self._page                      = page
        self._nav_ctlr                  = NavController(page)
        self._nav_ctlr.add_view(SearchView(page, "/", env)).add_view(PatitentView(page, "/patient", env))
        self._build_ui()
    #----------------------------------------------------------------------------------------------

    def _build_ui(self):
        self._page.title        = "Gestor de Pacientes"
        self._page.theme_mode   = "light"
        
        new_view: AppView = self._views["/"]
        self._page.views.clear()
        self._page.views.append(new_view)
        self._page.session.clear()
        self._page.go(new_view.route)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------