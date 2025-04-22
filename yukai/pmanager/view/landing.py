import  flet                        as      ft

from    dataclasses                 import  dataclass
from    difflib                     import  SequenceMatcher
from    models.models               import  *
from    pmanager.backend.service    import  BackendService
from    pmanager.view.environment   import  Environment
from    pmanager.view.snackbar      import  show_snackbar
from    pmanager.view.factories     import  Factories
from    tools.tools                 import  *
#--------------------------------------------------------------------------------------------------


class PacienteList(ft.Column, Factories):
    @dataclass
    class Content:
        db_id:      str
        dni:        str
        id_local:   str
        apellidos:  str
        nombre:     str
        selected:   bool    = False

        def changed(self, _): self.selected = not self.selected
    #----------------------------------------------------------------------------------------------

    def __init__(self,  title:              str,
                        reload_fcn:         callable,
                        consolidate_fcn:    callable,
                        duplicate_fcn:      callable,
                        delete_fcn:         callable,
                        **kwargs):
        super().__init__(**kwargs)
        self._title             = title
        self._reload_fcn        = reload_fcn
        self._consolidate_fcn   = consolidate_fcn
        self._duplicate_fcn     = duplicate_fcn
        self._delete_fcn        = delete_fcn
        self._list_content: list[PacienteList.Content]  = [ ]
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def set_values(self, pacientes: PacienteShort|list[PacienteShort]):
        self._list_content.clear()
        self._list_ctrl.controls.clear()
        
        if isinstance(pacientes, Paciente):
            pacientes = [ pacientes ]
        for paciente in pacientes:
            paciente: PacienteShort
            found = False
            for p in self._list_content:
                if p.dni == paciente.dni and p.id_local == paciente.ref_id:
                    found = True
                    break
            if not found:
                self._list_content.append(self.Content( paciente.dni,
                                                        paciente.ref_id,
                                                        paciente.apellidos,
                                                        paciente.nombre))
        self._list_content.sort(key=lambda c: c.apellidos.lower())

        for p in self._list_content:
            ft.Checkbox.on_change
            self._list_ctrl.controls.append(ft.ListTile(leading = ft.Checkbox(  value       = p.selected,
                                                                                on_change   = p.changed),
                                                        title   = ft.Text(f"{p.apellidos}, {p.nombre}"),
                                                        subtitle= ft.Text(f"DNI: {p.dni} - ID: {p.id_local}")))
    #----------------------------------------------------------------------------------------------

    def search(self):
        def search_pattern(pattern: str, content: PacienteList.Content):
            pattern = pattern.lower()

            def is_similar(a: str, b: str, threshold: float = 0.7):
                return SequenceMatcher(None, a, b).ratio() >= threshold

            return  (pattern in content.dni.lower() or
                    pattern in content.id_local.lower() or
                    is_similar(pattern, f"{content.nombre.lower()} {content.apellidos.lower()}") or
                    is_similar(pattern, f"{content.apellidos.lower()} {content.nombre.lower()}"))

        search_text         = self._search_text.value.strip().lower()
        filtered_content    = filter(lambda c: search_pattern(search_text, c), self._list_content)

        self._list_ctrl.controls.clear()
        for p in filtered_content:
            self._list_ctrl.controls.append(ft.ListTile(leading = ft.Checkbox(  value       = p.selected,
                                                                                on_change   = p.changed),
                                                        title   = ft.Text(f"{p.apellidos}, {p.nombre}"),
                                                        subtitle= ft.Text(f"DNI: {p.dni} - ID: {p.id_local}")))
        self.update()
    #----------------------------------------------------------------------------------------------
    
    def reload(self):
        self._list_content.clear() 
        self.set_values(self._reload_fcn())
    #----------------------------------------------------------------------------------------------
    
    def remove_selected(self):
        targets = []
        for p in self._list_content:
            if p.selected: targets.append(p.db_id)
        self._list_content.clear()
        self.set_values(self._delete_fcn(targets))
    #----------------------------------------------------------------------------------------------

    def consolidate(self):
        targets = []
        for p in self._list_content:
            if p.selected: targets.append(p.db_id)
        self._consolidate_fcn(targets)
    #----------------------------------------------------------------------------------------------
    
    def consolidate_all(self):
        targets = []
        for p in self._list_content:
            targets.append(p.db_id)
        self._consolidate_fcn(targets)
    #----------------------------------------------------------------------------------------------

    def search_duplicated(self):
        pass
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        self._list_ctrl     = ft.Column([])
        self._search_text   = ft.TextField( hint_text   = "Buscar paciente...",
                                            on_change   = self.search,
                                            tooltip     = "Filtra la lista de pacientes",
                                            expand      = True,
                                            text_size   = 20,
                                            border      = ft.InputBorder.NONE)

        self.controls   = \
        [
            self.tf.container_title(self._title),
            ft.Row \
            (
                [
                    self._search_text,
                    ft.Container(expand=True),

                    ft.IconButton(  ft.icons.REPLAY, 
                                    icon_color  = ft.colors.BLUE_900, 
                                    tooltip     = "Recargar lista de pacientes", 
                                    on_click    = self.reload,
                                    visible     = self._reload_fcn is not None),

                    ft.IconButton(  ft.icons.PLAY_ARROW, 
                                    icon_color  = ft.colors.BLUE_900, 
                                    tooltip     = "Consolidar seleccionados", 
                                    on_click    = self.consolidate,
                                    visible     = self._consolidate_fcn is not None),
                    
                    ft.IconButton(  ft.icons.PLAY_CIRCLE, 
                                    icon_color  = ft.colors.BLUE_900, 
                                    tooltip     = "Consolidar todos", 
                                    on_click    = self.consolidate_all,
                                    visible     = self._consolidate_fcn is not None),

                    ft.IconButton(  ft.icons.FIND_IN_PAGE, 
                                    icon_color  = ft.colors.BLUE_900, 
                                    tooltip     = "Buscar repetidos", 
                                    on_click    = self.search_duplicated,
                                    visible     = self._duplicate_fcn is not None),

                    ft.IconButton(  ft.icons.REMOVE, 
                                    icon_color  = ft.colors.BLUE_900, 
                                    tooltip     = "Eliminar paciente", 
                                    on_click    = self.remove_selected,
                                    visible     = self._delete_fcn is not None)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            self._list_ctrl
        ]
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class MainPanel(ft.Column, Factories):
    def __init__(self, backend: BackendService, **kwargs):
        super().__init__(**kwargs)
        self._backend   = backend
        self._src_list  = PacienteList( "Pacientes",
                                        self.reload_src_pacientes,
                                        self.consolidate_src_pacientes,
                                        self.check_src_duplicates,
                                        self.delete_src_pacientes)
        
        self._con_list  = PacienteList( "Pacientes Consolidados",
                                        None,
                                        None,
                                        self.check_consolidated_duplicates,
                                        self.delete_consolidates_pacientes)
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def reload_src_pacientes(self):
        status = self._backend.load_all_src_pacientes()
        if status:
            self._src_list.set_values(status.get())
        else:
            show_snackbar("Error en la recarga de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def consolidate_src_pacientes(self, pacientes: list[str]):
        status = self._backend.consolidate_pacientes(pacientes)

        if status:
            self._con_list.set_values(status.get())
        else:
            show_snackbar("Error en la consolidación de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def check_src_duplicates(self):
        pass
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def check_consolidated_duplicates(self):
        pass
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def delete_src_pacientes(self, pacientes: list[str]):
        status = self._backend.delete_src_pacientes(pacientes)

        if status:
            self._src_list.set_values(status.get())
        else:
            show_snackbar("Error en la consolidación de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def delete_consolidates_pacientes(self, pacientes: list[str]):
        status = self._backend.delete_consolidated_pacientes(pacientes)

        if status:
            self._con_list.set_values(status.get())
        else:
            show_snackbar("Error en la consolidación de los pacientes")        
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def build_ui(self):
        self.controls   = ft.Row(controls   = [ self._src_list, self._con_list],
                                 expand     = True,
                                 alignment  = ft.MainAxisAlignment.CENTER)
        self.expand     = True
        self.alignment  = ft.MainAxisAlignment.START
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class LandingView(ft.View, Factories):
    def __init__(self, page: ft.Page, route: str, env:Environment, backend:BackendService):
        super().__init__(route=route)
        self.page           = page
        self._env           = env
        self._backend       = backend
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        logo_container          = self.lf.buil_logo(self.page, "/imgs/logo.png")

        self._overlay_bg        = ft.Container(     bgcolor=ft.colors.BLACK54,
                                                    expand=True,
                                                    opacity=0.7,
                                                    animate_opacity=300,
                                                    visible=False)
        self._main_panel        = MainPanel(self._backend)
        self._sync_info         = self.tf.mosaic_title("Procesando...")
        self._wait_sync         = ft.Row \
        (   
            [
                ft.Container(expand=True),
                ft.Column \
                (
                    [
                        ft.ProgressRing(width=80, height=80),
                        self._sync_info
                    ],
                    alignment   = ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(expand=True)  
            ],
            expand              = True,
            visible             = True,
            alignment           = ft.MainAxisAlignment.CENTER,
            vertical_alignment= ft.CrossAxisAlignment.CENTER
        )

        header_row          = ft.Container \
        (
            ft.Row \
            (
                [
                    self.tf.page_title("Gestor de Pacientes"),
                    ft.Container(expand=True),
                    logo_container,

                ],
                expand      = True,
                alignment   = ft.MainAxisAlignment.START
            ),
            border          = ft.border.only(bottom=ft.BorderSide(2, self.cp.grey)),  
            padding         = 10
        )


        main_layout = ft.Column \
        (
            controls= \
            [
                header_row,  # Fila con Datos del Paciente + Logo
                ft.Stack \
                (
                    [
                        self._main_panel,   # Dos columnas abajo (Formulario y Chat)
                        self._overlay_bg,
                        self._wait_sync
                    ],
                    expand=True
                )

            ],
            expand=True,
            alignment=ft.MainAxisAlignment.START
        )

        self.controls = [ ft.Container(content=main_layout) ]
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
