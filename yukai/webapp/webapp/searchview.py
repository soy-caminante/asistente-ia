import  flet                        as      ft

from    webapp.webapp.environment   import  Environment
from    webapp.models.models        import  *
from    webapp.webapp.factories     import  *
from    webapp.webapp.navmanger     import  *
#--------------------------------------------------------------------------------------------------

class SearchView(AppView):
    def __init__(self, page:ft.Page, route, env:Environment):
        super().__init__(page=page, route=route)
        self._env           = env
        self._backend       = env.backend
        self._is_mobile     = True
        self._build_ui()
    #----------------------------------------------------------------------------------------------

    def _search(self, e: ft.ControlEvent):
        self._results.controls.clear()
        pacientes   = self._backend.get_pacientes(self._search_box.value.lower())
        for p in pacientes:
            self._results.controls.append(self._get_result_item(p))
        self.page.update()
    #----------------------------------------------------------------------------------------------

    def _show_patitent_details(self, e: ft.ControlEvent):
        self._results.controls.clear()
        self._search_box.value = ""
        self._nav_ctlr.show_view("/patient", e.control.data)
    #----------------------------------------------------------------------------------------------

    def _get_result_item(self, paciente:Paciente):
        if self._is_mobile:
            return ft.Card \
            (
                content=ft.Container \
                (
                    content = ft.ElevatedButton(f"{paciente.apellidos} {paciente.nombre} - {paciente.ref_id}", on_click=self._show_patitent_details, data=paciente.ref_id),
                    padding = 10,
                ),
                elevation=2,
            )
        else:
            return ft.Card \
            (
                content=ft.Container \
                (
                    content=ft.Row \
                    (
                        [
                            ft.Text(f"{paciente.apellidos} {paciente.nombre} - {paciente.ref_id}", size=18),
                            ft.ElevatedButton("Ver", on_click=self._show_patitent_details, data=paciente.ref_id)
                        ], 
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=10,
                ),
                elevation=2,
            )
    #----------------------------------------------------------------------------------------------

    def _build_ui(self):
        self._is_mobile     = self.page.platform.name in [ ft.PagePlatform.ANDROID.name, ft.PagePlatform.IOS.name ]
        logo_container      = LogoFactory.buil_logo(self.page, "/imgs/logo.png")
        self._results       = ft.Column()
        self._search_box    = ft.TextField \
        (
            label       = "Buscar...", 
            on_change   = self._search, 
            autofocus   = True, 
            expand      = True
        )

        if self._is_mobile:
            search_column = ft.Column \
            (
                [
                    self._search_box,
                    ft.Divider(),
                    self._results
                ],
                alignment   = ft.MainAxisAlignment.START,
                expand      = True
            )
            main_layout = ft.Column \
            (
                [
                    logo_container,
                    search_column,
                ],
                spacing = 20,
                expand  = True,
                scroll  = ft.ScrollMode.AUTO
            )
        
        # Diseño para tabletas y escritorio (centra elementos)
        else:
            search_row = ft.Row \
            (
                [ 
                    ft.Container(expand=1, bgcolor="transparent"),
                    ft.Container \
                    (
                        ft.Column \
                        (
                            [
                                self._search_box,
                                ft.Divider(),
                                self._results
                            ]
                        ),
                        expand=2,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(expand=1, bgcolor="transparent"),
                ],
                alignment   = ft.MainAxisAlignment.CENTER,
                expand      = True
            )
            
            main_layout = ft.Column \
            (
                controls= \
                [
                    logo_container,
                    search_row,
                    ft.Container(expand=True)
                ],
                alignment               = ft.MainAxisAlignment.START,
                horizontal_alignment    = ft.CrossAxisAlignment.CENTER,
                spacing                 = 20,
            )

        self.controls = [ ft.Container(content=main_layout) ]
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
