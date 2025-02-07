import  flet                        as      ft

from    environment.environment     import  Environment
from    models.models               import  *
from    webapp.factories            import  *
from    webapp.navmanger            import  *
#--------------------------------------------------------------------------------------------------

class SearchView(AppView):
    def __init__(self, route, env:Environment):
        super().__init__(page=env._page, route=route)
        self._env           = env
        self._backend       = env._backend
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
        logo_container      = LogoFactory.buil_logo(self.page, self._env._locations._logo_path)
        self._results       = ft.Column()
        self._search_box    = ft.TextField \
        (
            label="Buscar...", 
            on_change=self._search, 
            autofocus=True, 
            expand=True
        )

        search_row          = ft.Row \
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
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )
        
        self.controls.append \
        (
            ft.Container \
            (
                content= ft.Column \
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
            )
        )
#--------------------------------------------------------------------------------------------------
