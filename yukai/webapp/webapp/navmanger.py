import  flet    as ft
#--------------------------------------------------------------------------------------------------

class AppView(ft.View):
    def __init__(self, page: ft.Page, route):
        super().__init__(route=route)
        self.page       = page
        self._nav_ctlr  = None
    #----------------------------------------------------------------------------------------------

    def set_nav_controller(self, nav_ctrl: 'NavController'):
        self._nav_ctlr = nav_ctrl
    #----------------------------------------------------------------------------------------------

    def show_view(self): pass
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class WaitControl(ft.Container):
    def __init__(self):
        super().__init__ \
        (
            alignment   = ft.alignment.center,  # Alineación centrada
            bgcolor     = ft.colors.with_opacity(0.5, ft.colors.BLACK),  # Fondo semi-transparente
            expand      = True,  # Ocupa toda la pantalla
            visible     = False  # Inicialmente oculto
        )

        # Elementos UI internos
        self.progress_ring  = ft.ProgressRing(width=80, height=80)  # Indicador de carga
        self.error_text     = ft.Text("", size=24, color=ft.colors.YELLOW, text_align="center")  # Mensaje de error
        self.accept_button  = ft.ElevatedButton \
        (
            content     = ft.Text("Aceptar", size=24, color=ft.colors.BLACK, text_align="center"),
            on_click    = self.hide, 
            width       = 200,
            height      = 50,
            visible     = False
        )

        # Contenedor del contenido
        self.content = ft.Column \
        (
            controls            = [ self.progress_ring, self.error_text, self.accept_button ],
            alignment           = ft.MainAxisAlignment.CENTER,
            horizontal_alignment= ft.CrossAxisAlignment.CENTER
        )

    #----------------------------------------------------------------------------------------------

    def show(self):  
        """Muestra el indicador de carga y oculta el error"""
        self.progress_ring.visible = True
        self.error_text.value = ""
        self.accept_button.visible = False
        self.visible = True
        self.update()
    #----------------------------------------------------------------------------------------------

    def hide(self, e=None):  
        """Oculta todo el control"""
        self.visible = False
        self.update()

    #----------------------------------------------------------------------------------------------

    def show_error(self, info: str):
        """Muestra un mensaje de error y oculta el indicador de carga"""
        self.progress_ring.visible = False
        self.error_text.value = info
        self.accept_button.visible = True
        self.visible = True
        self.update()
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class NavController:
    def __init__(self, page: ft.Page):
        self._page                          = page
        self._wait_control                  = WaitControl()
        self._views:  dict[str, AppView]    = { }

        self._page.overlay.append(self._wait_control)       
    #----------------------------------------------------------------------------------------------

    def show_wait_ctrl(self): self._wait_control.show()
    #----------------------------------------------------------------------------------------------

    def hide_wait_ctrl(self, e=None): self._wait_control.hide()
    #----------------------------------------------------------------------------------------------

    def show_error(self, info: str): self._wait_control.show_error(info)
    #----------------------------------------------------------------------------------------------

    def add_view(self, view: AppView):
        view.set_nav_controller(self)
        self._views[view.route] = view
        return self
    #----------------------------------------------------------------------------------------------

    def show_home_view(self):
        new_view: AppView = self._views["/"]
        self._page.views.clear()
        self._page.views.append(new_view)
        self._page.session.clear()
        self._page.go(new_view.route)
        new_view.show_view()
    #----------------------------------------------------------------------------------------------

    def show_view(self, route:str, data:None):
        new_view: AppView = self._views[route]
        self._page.views.append(new_view)
        self._page.session.set("paciente", data)
        self._page.go(new_view.route)
        new_view.show_view()
    #----------------------------------------------------------------------------------------------

    def go_back(self):
        self._page.views.pop(), 
        self._page.go(self._page.views[-1].route)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
