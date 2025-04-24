import  flet                        as      ft
import  mimetypes
import  time
import  unicodedata

from    dataclasses                 import  dataclass
from    difflib                     import  SequenceMatcher
from    enum                        import  IntEnum
from    models.models               import  *
from    pmanager.backend.service    import  BackendService
from    pmanager.view.environment   import  Environment
from    pmanager.view.snackbar      import  show_snackbar
from    tools.tools                 import  *
from    tools.viewtools             import  *
#--------------------------------------------------------------------------------------------------

class Callbacks(IntEnum):
    INSPECT_SRC     = 0
    INSPECT_CON     = 1
    INSPECT_DOC     = 2
    CONSOLIDAT_DOC  = 3
    DELETE_DOC      = 4
#--------------------------------------------------------------------------------------------------

class ExpedienteViwer(ft.Container, Factories):
    class HeaderCtrl(ft.Row, Factories):
        def __init__(self,  data: DocumentoSrc | DocumentoCon,
                            on_consolidate,
                            on_inspect,
                            on_delete):
            super().__init__()
            self._data              = data
            self._on_consolidate    = on_consolidate
            self._on_inspect        = on_inspect
            self._on_delete         = on_delete
            self.expand             = True
            self.alignment          = ft.MainAxisAlignment.START

            if on_consolidate:
                self.controls = [ ft.Text(f"{data.nombre}"), 
                                  ft.Container(expand=True),           
                                  self.bf.custom_button(ft.Icons.PLAY_ARROW,  self.on_consolidate, "Consolidar"),
                                  self.bf.custom_button(ft.Icons.PAGEVIEW,    self.on_inspect, "Inspeccionar"),
                                  self.bf.delete_button(self.on_delete) ]
            else:
                self.controls = [ ft.Text(f"{data.nombre}"), 
                                  ft.Container(expand=True), 
                                  self.bf.custom_button(ft.Icons.PAGEVIEW, self.on_inspect, "Inspeccionar"),
                                  self.bf.delete_button(self.on_delete) ]
        #------------------------------------------------------------------------------------------
            
        def on_consolidate(self, _): self._on_consolidate(self._data)
        #------------------------------------------------------------------------------------------

        def on_inspect(self, _): self._on_inspect(self._data)
        #------------------------------------------------------------------------------------------

        def on_delete(self, _): self._on_delete(self._data)
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    def __init__(self,  backend: BackendService,
                        on_go_back: callable,
                        **kwargs):
        super().__init__(**kwargs)
        self._backend       = backend
        self._on_go_back    = on_go_back
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def populate(self, docs: ExpedienteSrc | ExpedienteCon):
        self._documents_ctrl.controls.clear()
        if docs:
            self._paciente.value    = f"{docs.apellidos}, {docs.nombre}"
            self._dni.value         = f"{docs.dni} / {docs.ref_id}"
            self._edad.value        = f"{docs.sexo} - {get_elapsed_years(docs.fecha_nacimiento)} años"
            
            if isinstance(docs, ExpedienteSrc):
                for d in  docs.documentos:
                    self._documents_ctrl.controls.append(ft.ListTile(   title   = self.HeaderCtrl(  data           = d,
                                                                                                    on_consolidate = self.consolidate,
                                                                                                    on_inspect     = self.inspect,
                                                                                                    on_delete      = self.delete),
                                                                        subtitle= ft.Text(f"{d.tipo}, {d.size}")))
            else:
                for d in  docs.documentos:
                    self._documents_ctrl.controls.append(ft.ListTile(   title   = self.HeaderCtrl(  data           = d,
                                                                                                    on_consolidate = None,
                                                                                                    on_inspect     = self.inspect,
                                                                                                    on_delete      = self.delete),
                                                                        subtitle= ft.Text(f"{d.tipo}, {d.size}, {d.tokens} tokens")))
    #----------------------------------------------------------------------------------------------

    def consolidate(self, data):
        self._backend
    #----------------------------------------------------------------------------------------------

    def inspect(self, data): self._callback_fcn(Callbacks. data)
    #----------------------------------------------------------------------------------------------

    def delete(self, data): self._callback_fcn(data)
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        self._paciente = ft.TextField \
        (
            label       = "Paciente", 
            value       = None, 
            expand      = True,
            read_only   = True,
            border      = "none"
        )

        self._dni = ft.TextField \
        (
            label       = "DNI / Ref", 
            value       = None, 
            expand      = True,
            read_only   = True,
            border      = "none"
        )

        self._edad = ft.TextField \
        (
            label       = "Sexo - Edad", 
            value       = None, 
            expand      = True,
            read_only   = True,
            border      = "none"
        )

        self._documents_ctrl    = ft.Column([], scroll=ft.ScrollMode.ALWAYS, alignment=ft.MainAxisAlignment.START, expand=True)
        left_column             = ft.Column \
        (
            [
                ft.Container(self._paciente),
                ft.Container(self._dni),
                ft.Container(self._edad)
            ],
            expand      = 1,
            alignment   = ft.MainAxisAlignment.START,
        )

        rigth_column = ft.Container(self._documents_ctrl, expand=3)
        layout = ft.Row \
        (
            [   
                ft.Container( self.bf.back_button(lambda _: self._on_go_back()), expand=1), 
                left_column, 
                rigth_column, 
                ft.Container(expand=1) 
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        self.alignment  = ft.alignment.top_center
        self.content    = layout
        self.expand     = True
    #----------------------------------------------------------------------------------------------
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

    class HeaderCtrl(ft.Row, Factories):
        def __init__(self,  data: 'PacienteList.Content',
                            on_consolidate,
                            on_inspect,
                            on_delete):
            super().__init__()
            self._data              = data
            self._on_consolidate    = on_consolidate
            self._on_inspect        = on_inspect
            self._on_delete         = on_delete
            self.expand             = True
            self.alignment          = ft.MainAxisAlignment.START
            self.controls           = [     ft.Text(f"{data.apellidos}, {data.nombre}"), 
                                            ft.Container(expand=True), 
                                            self.bf.custom_button(ft.Icons.PLAY_ARROW,  self.on_consolidate, "Consolidar"),
                                            self.bf.custom_button(ft.Icons.PAGEVIEW,    self.on_inspect, "Inspeccionar"),
                                            self.bf.delete_button(self.on_delete) ]
        #------------------------------------------------------------------------------------------
            
        def on_consolidate(self, _): self._on_consolidate(self._data)
        #------------------------------------------------------------------------------------------

        def on_inspect(self, _): self._on_inspect(self._data)
        #------------------------------------------------------------------------------------------

        def on_delete(self, _): self._on_delete(self._data)
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    def __init__(self,  title:              str,
                        reload_fcn:         callable,
                        consolidate_fcn:    callable,
                        duplicate_fcn:      callable,
                        delete_fcn:         callable,
                        inspect_fcn:        callable,
                        **kwargs):
        super().__init__(**kwargs)
        self._title                                     = title
        self._reload_fcn                                = reload_fcn
        self._consolidate_fcn                           = consolidate_fcn
        self._duplicate_fcn                             = duplicate_fcn
        self._delete_fcn                                = delete_fcn
        self._inspect_fcn                               = inspect_fcn
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
                                                        title= self.HeaderCtrl( data           = p,
                                                                                on_consolidate = self.consolidate_one,
                                                                                on_inspect     = self.inspect_one,
                                                                                on_delete      = self.delete_one),
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
                                                        title= self.HeaderCtrl( data           = p,
                                                                                on_consolidate = self.consolidate_one,
                                                                                on_inspect     = self.inspect_one,
                                                                                on_delete      = self.delete_one),
                                                        subtitle= ft.Text(f"DNI: {p.dni} - ID: {p.id_local}")))
        self.update()
    #----------------------------------------------------------------------------------------------
    
    def consolidate_one(self, ref: 'PacienteList.Content'):
        self._consolidate_fcn([ref.db_id])
    #----------------------------------------------------------------------------------------------

    def delete_one(self, ref: 'PacienteList.Content'):
        self._list_content.clear()
        self.set_values(self._delete_fcn([ref.db_id]))
    #----------------------------------------------------------------------------------------------

    def inspect_one(self, ref: 'PacienteList.Content'):
        self._inspect_fcn(ref.db_id)
    #----------------------------------------------------------------------------------------------

    def reload(self, _):
        self._list_content.clear() 
        self.set_values(self._reload_fcn())
    #----------------------------------------------------------------------------------------------
    
    def remove_selected(self, _):
        targets = []
        for p in self._list_content:
            if p.selected: targets.append(p.db_id)
        self._list_content.clear()
        self.set_values(self._delete_fcn(targets))
    #----------------------------------------------------------------------------------------------

    def consolidate(self, _):
        targets = []
        for p in self._list_content:
            if p.selected: targets.append(p.db_id)
        self._consolidate_fcn(targets)
    #----------------------------------------------------------------------------------------------
    
    def consolidate_all(self, _):
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
        self._backend       = backend
        self._src_list      = PacienteList( "Nuevos",
                                            self.reload_src_pacientes,
                                            self.consolidate_src_pacientes,
                                            self.check_src_duplicates,
                                            self.delete_src_pacientes,
                                            self.inspect_src_pacientes)
        
        self._con_list      = PacienteList( "Consolidados",
                                            None,
                                            None,
                                            self.check_consolidated_duplicates,
                                            self.delete_consolidated_pacientes,
                                            self.inspect_consolidated_pacientes)
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
            show_snackbar("Error en el borrado de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def delete_consolidated_pacientes(self, pacientes: list[str]):
        status = self._backend.delete_consolidated_pacientes(pacientes)

        if status:
            self._con_list.set_values(status.get())
        else:
            show_snackbar("Error en el borrado de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def inspect_src_pacientes(self, paciente: str):
        status = self._backend.inspect_src_pacientes(paciente)

        if status:
            self._main_layout.visible       = False
            self._expediente_viwer.visible  = True
            self._expediente_viwer.populate(status.get())
            self.update()
        else:
            show_snackbar("Error al leer el expediente del paciente")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def inspect_consolidated_pacientes(self, paciente: str):
        status = self._backend.inspect_consolidated_pacientes(paciente)

        if status:
            self._main_layout.visible       = False
            self._expediente_viwer.visible  = True
            self._expediente_viwer.populate(status.get())
            self.update()
        else:
            show_snackbar("Error al leer el expediente del paciente")
    #----------------------------------------------------------------------------------------------

    def come_back(self):
        self._main_layout.visible       = True
        self._expediente_viwer.visible  = False
        self.update()
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def build_ui(self):
        self._main_layout   = ft.Row \
        (
            controls    = [ self._con_list, self._src_list ],
            alignment   = ft.MainAxisAlignment.CENTER,
            expand      = True
        )

        self._expediente_viwer = ExpedienteViwer(self._backend, self.come_back)

        self.content    = ft.Stack \
        (
            [
                self._main_layout,
                self._expediente_viwer
            ],
            expand=True
        )
        self.expand     = True
        self._main_layout.visible       = True
        self._expediente_viwer.visible  = False
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class LandingView(ft.View, Factories):
    def __init__(self, page: ft.Page, route: str, env:Environment, overlay_ctrl: OverlayCtrl, backend:BackendService):
        super().__init__(route=route)
        self.page           = page
        self._env           = env
        self._backend       = backend
        self._overlay_ctrl  = overlay_ctrl
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    @property
    def overlay_ctrl(self): return self._overlay_ctrl
    #----------------------------------------------------------------------------------------------

    def populate(self, scr_list: list[PacienteShort], con_list: list[PacienteShort]):
        self._main_panel.populate(scr_list, con_list)
        self.update()
    #----------------------------------------------------------------------------------------------
    
    def callback(self, fcn, *args):
        pass
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        logo_container          = self.lf.buil_logo(self.page, "/imgs/logo.png")
        self._main_panel        = MainPanel(self._backend)

        header_row = ft.Container \
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
                self._overlay_ctrl
            ],
            expand=True)
        ]
        self.expand                 = True
        self._overlay_ctrl.visible  = False
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
