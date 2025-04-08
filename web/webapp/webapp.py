import  flet                        as      ft
from    environment.environment     import  Environment
from    webapp.factories            import  *
from    webapp.navmanger            import  *
from    webapp.patitienview         import  PatitentView
from    webapp.searchview           import  SearchView
#--------------------------------------------------------------------------------------------------

class WebApp:
    def __init__(self, env: Environment):
        self._env                       = env
        self._page                      = env._page
        self._nav_ctlr                  = NavController(env._page)
        self._nav_ctlr.add_view(SearchView("/", env)).add_view(PatitentView("/patient", env))
        self._build_ui()
    #----------------------------------------------------------------------------------------------

    def _build_ui(self):
        self._page.title        = "SOCIEDAD - AI"
        self._page.theme_mode   = "light"
        self._nav_ctlr.show_home_view()
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------