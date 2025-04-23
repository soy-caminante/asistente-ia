import  flet                        as      ft
import  time
import  unicodedata

from    dataclasses                 import  dataclass
from    difflib                     import  SequenceMatcher
from    models.models               import  *
from    pmanager.backend.service    import  BackendService
from    pmanager.view.environment   import  Environment
from    pmanager.view.snackbar      import  show_snackbar
from    pmanager.view.factories     import  Factories
from    tools.tools                 import  *
#--------------------------------------------------------------------------------------------------


class PacienteList(ft.Container, Factories):
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
        self._title                                     = title
        self._reload_fcn                                = reload_fcn
        self._consolidate_fcn                           = consolidate_fcn
        self._duplicate_fcn                             = duplicate_fcn
        self._delete_fcn                                = delete_fcn
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
                self._list_content.append(self.Content( paciente.db_id,
                                                        paciente.dni,
                                                        paciente.ref_id,
                                                        paciente.apellidos,
                                                        paciente.nombre))
        self._list_content.sort(key=lambda c: c.apellidos.lower())

        for p in self._list_content:
            self._list_ctrl.controls.append(ft.ListTile(leading = ft.Checkbox(  value       = p.selected,
                                                                                on_change   = p.changed),
                                                        title   = ft.Text(f"{p.apellidos}, {p.nombre}"),
                                                        subtitle= ft.Text(f"DNI: {p.dni} - ID: {p.id_local}")))
    #----------------------------------------------------------------------------------------------

    def search(self, _):
        def normalize(text):
            return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8").lower()
        
        def search_pattern(pattern: str, content: PacienteList.Content):
            pattern             = normalize(pattern)
            nombre_apellidos    = normalize(f"{content.nombre} {content.apellidos}")
            apellidos_nombre    = normalize(f"{content.apellidos} {content.nombre}")

            def is_similar(pattern: str, target: str, threshold: float = 0.7):
                if len(pattern) < len(target):
                    target = target[0:len(pattern)]
                return SequenceMatcher(None, pattern, target).ratio() >= threshold

            return  pattern in content.dni.lower() or \
                    pattern in content.id_local.lower() or \
                    is_similar(pattern, nombre_apellidos) or \
                    is_similar(pattern, apellidos_nombre) or \
                    nombre_apellidos.startswith(pattern) or \
                    apellidos_nombre.startswith(pattern)

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
        self._list_ctrl     = ft.Column([], scroll=ft.ScrollMode.ALWAYS, alignment=ft.MainAxisAlignment.START, expand=True)
        self._search_text   = ft.TextField( hint_text   = "Buscar paciente...",
                                            on_change   = self.search,
                                            tooltip     = "Filtra la lista de pacientes",
                                            text_size   = 20,
                                            border      = ft.InputBorder.NONE)

        label_field         = self.tf.container_title(self._title)
        label_field.expand  = True
        header_row          = ft.Row \
        (
            controls= \
            [
                label_field,
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

                ft.IconButton(  ft.icons.DELETE, 
                                icon_color  = ft.colors.BLUE_900, 
                                tooltip     = "Eliminar paciente", 
                                on_click    = self.remove_selected,
                                visible     = self._delete_fcn is not None)                
            ],
            alignment           = ft.MainAxisAlignment.CENTER,
            vertical_alignment  = ft.CrossAxisAlignment.START
        )

        column = ft.Column \
        (
            [
                header_row,
                self._search_text,
                self._list_ctrl,
                ft.Container(expand=True)
            ],
            expand         = True,
            alignment      = ft.MainAxisAlignment.START
        )

        self.content    = column
        self.expand     = True
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class MainPanel(ft.Container, Factories):
    def __init__(self, backend: BackendService, **kwargs):
        super().__init__(**kwargs)
        self._backend   = backend
        self._src_list  = PacienteList( "Nuevos",
                                        self.reload_src_pacientes,
                                        self.consolidate_src_pacientes,
                                        self.check_src_duplicates,
                                        self.delete_src_pacientes)
        
        self._con_list  = PacienteList( "Consolidados",
                                        None,
                                        None,
                                        self.check_consolidated_duplicates,
                                        self.delete_consolidates_pacientes)
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def populate(self, src_list: list[PacienteShort], con_list: list[PacienteShort]):
        self._src_list.set_values(src_list)
        self._con_list.set_values(con_list)
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
        row = ft.Row \
        (
            controls    = [ self._con_list, self._src_list ],
            alignment   = ft.MainAxisAlignment.CENTER,
            expand      = True
        )
        self.content    = row
        self.expand     = True
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class WarningControl(ft.Row, Factories):
    def __init__(self, **kwargs):
        self._answer = None
        super().__init__(**kwargs)
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def set_msg(self, msg): 
        self._answer    = None
        lines           = ""
        for m in msg:
            if lines != "": lines += "\n"
            lines += m
        self._msg.value = lines
    #----------------------------------------------------------------------------------------------

    def wait_answer(self):
        print("esperando")
        while self._answer is None:
            time.sleep(0.5)
            self.update()
        print("espera finalizada")
        return self._answer
    #----------------------------------------------------------------------------------------------

    def set_accept(self, _): self._answer = True
    #----------------------------------------------------------------------------------------------

    def set_cancel(self, _): self._answer = False
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        self._msg = self.tf.mosaic_title("Mensaje")
        self.controls = \
        [
            ft.Container(expand=True),
            ft.Column \
            (
                [
                    self._msg,
                    ft.Row \
                    (
                        [
                            ft.Container(expand=True),
                            self.bf.accept_button(on_click=self.set_accept, visible=True),
                            self.bf.cancel_button(on_click=self.set_cancel, visible=True)
                        ]
                    ),
                    ft.Container(expand=True)
                ],
                alignment           = ft.MainAxisAlignment.CENTER,
                horizontal_alignment= ft.CrossAxisAlignment.CENTER
            ),
            ft.Container(expand=True)  
        ]
        self.expand              = True,
        self.visible             = True,
        self.alignment           = ft.MainAxisAlignment.CENTER,
        self.vertical_alignment= ft.CrossAxisAlignment.CENTER
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

    def show_warning_ctrl(self, msg: list[str]):
        self._warning_ctrl.set_msg(msg)
        self._warning_ctrl.visible  = True
        self._wait_sync.visible     = False
        self._overlay_bg.visible    = True
        self._main_layout.visible   = False
        self.update()

        return self._warning_ctrl.wait_answer()
    #----------------------------------------------------------------------------------------------

    def show_wait_ctrl(self, visible, msg=None):
        if visible:
            if msg:
                self._wait_msg.value = f"{msg}..."
            else:
                self._wait_msg.value = "Procesando..."

        self._warning_ctrl.visible  = False
        self._wait_sync.visible     = visible
        self._overlay_bg.visible    = visible
        self._main_layout.visible   = True
        self._main_layout.disabled  = visible
        self.update()
    #----------------------------------------------------------------------------------------------

    def populate(self, scr_list: list[PacienteShort], con_list: list[PacienteShort]):
        self._main_panel.populate(scr_list, con_list)
    #----------------------------------------------------------------------------------------------
    
    def build_ui(self):
        logo_container          = self.lf.buil_logo(self.page, "/imgs/logo.png")

        self._overlay_bg        = ft.Container(     bgcolor         = ft.colors.BLACK54,
                                                    expand          = True,
                                                    opacity         = 0.7,
                                                    animate_opacity = 300)
        self._main_panel        = MainPanel(self._backend)
        self._wait_msg          = self.tf.mosaic_title("Procesando...")
        self._wait_sync         = ft.Row \
        (   
            [
                ft.Container(expand=True),
                ft.Column \
                (
                    [
                        ft.ProgressRing(width=80, height=80),
                        self._wait_msg
                    ],
                    alignment           = ft.MainAxisAlignment.CENTER,
                    horizontal_alignment= ft.CrossAxisAlignment.CENTER
                ),
                ft.Container(expand=True)  
            ],
            expand              = True,
            visible             = True,
            alignment           = ft.MainAxisAlignment.CENTER,
            vertical_alignment= ft.CrossAxisAlignment.CENTER
        )

        self._warning_ctrl  = WarningControl()

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


        self._main_layout = ft.Column \
        (
            controls= \
            [
                header_row,  # Fila con Datos del Paciente + Logo
                self._main_panel
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.START
        )

        self.controls = \
        [ 
            ft.Stack \
            ([
                self._main_layout,
                self._wait_sync,
                self._overlay_bg,
                self._warning_ctrl
            ],
            expand=True)
        ]
        self.expand                 = True
        self._wait_sync.visible     = False
        self._overlay_bg.visible    = False
        self._warning_ctrl.visible  = False
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
