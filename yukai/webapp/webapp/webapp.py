import  flet                            as      ft
from    webapp.webapp.environment       import  Environment
from    webapp.webapp.factories         import  *
from    webapp.webapp.navmanger         import  *
from    webapp.webapp.patitienview      import  PatitentView
from    webapp.webapp.searchview        import  SearchView
#--------------------------------------------------------------------------------------------------

class WebApp:
    def __init__(self, page: ft.Page, env: Environment):
        self._env                       = env
        self._page                      = page
        self._nav_ctlr                  = NavController(page)
        self._nav_ctlr.add_view(SearchView(page, "/", env)).add_view(PatitentView(page, "/patient", env))
        self._build_ui()
    #----------------------------------------------------------------------------------------------

    def _build_ui(self):
        self._page.title        = "SOCIEDAD - AI"
        self._page.theme_mode   = "light"
        self._nav_ctlr.show_home_view()
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------