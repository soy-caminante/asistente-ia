from    __future__                  import  annotations

import  base64
import  flet                        as      ft
import  unicodedata

from    dataclasses                 import  dataclass
from    difflib                     import  SequenceMatcher
from    enum                        import  IntEnum
from    models.models               import  *
from    pmanager.backend.service    import  BackendService
from    pmanager.view.environment   import  Environment
from    pmanager.view.filedialog    import  show_filesaver
from    pmanager.view.snackbar      import  show_snackbar, show_snackbar_error
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

class DocumentViewer(ft.Container, Factories):
    def __init__(self, go_back, **kwargs):
        super().__init__(**kwargs)
        self._on_go_back        = go_back
        self._content           = None
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def open_save_dialog(self):
        show_filesaver(self.save_file, self._name or "document", self._mime_type)
    #----------------------------------------------------------------------------------------------

    def save_file(self, e: ft.FilePickerResultEvent):
        if e.path:
            try:
                with open(e.path, "wb") as f:
                    f.write(self._content)
            except Exception as ex:
                show_snackbar_error(f"Error al guardar el documento {ex}")
    #----------------------------------------------------------------------------------------------

    def setup_single(self, cliente: str, dni_ref: str, edad: str, doc_name: str, doc_len: str, doc_tokens: int, doc_content: bytes, doc_mime_type: str):
        self._cliente.value     = cliente
        self._dni.value         = dni_ref
        self._edad.value        = edad
        self._documento.value   = doc_name
        self._doc_len.value     = doc_len
        self._tokens.value      = doc_tokens
        self._content           = doc_content

        if doc_mime_type.startswith("text/"):
            text_str = doc_content.decode("utf-8", errors="ignore")
            control = ft.Text(text_str, selectable=True, overflow="auto")

        elif doc_mime_type.startswith("image/"):
            b64_data = base64.b64encode(doc_content).decode("utf-8")
            control = ft.Image(src_base64=b64_data, fit=ft.ImageFit.CONTAIN)

        elif doc_mime_type == "application/pdf":
            b64_data = base64.b64encode(doc_content).decode("utf-8")
            data_url = f"data:application/pdf;base64,{b64_data}"
            control = ft.Iframe(src=data_url, width=600, height=800)
        else:
            control = ft.Text(f"Tipo MIME no soportado: {doc_mime_type}")
        self._doc_display.content = control
        self.update()
    #----------------------------------------------------------------------------------------------

    def setup_split(self,   cliente: str, 
                            dni_ref: str, 
                            edad: str, 
                            doc_name: str, 
                            doc_len: str, 
                            doc_tokens: int, 
                            src_doc_content: bytes, 
                            iadoc_content: bytes,
                            doc_mime_type: str):
        self._cliente.value     = cliente
        self._dni.value         = dni_ref
        self._edad.value        = edad
        self._documento.value   = doc_name
        self._doc_len.value     = doc_len
        self._tokens.value      = doc_tokens
        self._content           = src_doc_content

        src_text    = src_doc_content.decode("utf-8", errors="ignore")
        control_src = ft.Text(src_text, selectable=True, overflow="auto")

        iadoc_text  = iadoc_content.decode("utf-8", errors="ignore")
        control_src = ft.Text(control_src, selectable=True, overflow="auto")

        self._doc_display.content = ft.Row([ft.Container(src_text, expand=True), ft.VerticalDivider(), ft.Container(control_src, expand=True)])
        self.update()
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        self._cliente = ft.TextField \
        (
            label       = "Cliente", 
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

        self._documento = ft.TextField \
        (
            label       = "Documento", 
            value       = None, 
            expand      = True,
            read_only   = True,
            border      = "none"
        )

        self._doc_len = ft.TextField \
        (
            label       = "Tamaño", 
            value       = None, 
            expand      = True,
            read_only   = True,
            border      = "none"
        )

        self._tokens = ft.TextField \
        (
            label       = "Tokens", 
            value       = None, 
            expand      = True,
            read_only   = True,
            border      = "none"
        )

        first_row  = ft.Row \
        (
            [
                self._documento,
                ft.Container(expand=True),
                self.bf.back_button(lambda _: self._on_go_back()),
                self.bf.save_button(lambda _: self.open_save_dialog())
            ],
            expand=True
        )

        left_column             = ft.Column \
        (
            [
                ft.Container(first_row),
                ft.Container(self._doc_len),
                ft.Container(self._tokens),
                ft.Divider(),
                ft.Container(self._cliente),
                ft.Container(self._dni),
                ft.Container(self._edad)
            ],
            expand      = 1,
            alignment   = ft.MainAxisAlignment.START,
        )

        self._doc_display   = ft.Container(expand=3)
        layout                  = ft.Row \
        (
            [   
                ft.Container(expand=1), 
                left_column, 
                self._doc_display, 
                ft.Container(expand=1) 
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        )


        self.content    = layout
        self.expand     = True
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class ExpedienteViewer(ft.Container, Factories):
    @dataclass
    class ConsolidatedDoc:
        name:           str
        tokens:         int
        size_str:       str
        mime:           str
        ts:             datetime.datetime
        src_ref:        str
        iadoc_ref:      str
        biadoc_ref:     str

        @property
        def ts_str(self):  return self.ts.strftime("%d-%m-%Y")
    #----------------------------------------------------------------------------------------------

    class HeaderCtrl(ft.Row, Factories):
        def __init__(self,  data: IncommingFileInfo | ExpedienteViewer.ConsolidatedDoc,
                            on_consolidate      = None,
                            on_inspect_src      = None,
                            on_inspect_iadoc    = None,
                            on_delete           = None):
            super().__init__()
            self._data              = data
            self._on_consolidate    = on_consolidate
            self._on_inspect_src    = on_inspect_src
            self._on_inspect_iadoc  = on_inspect_iadoc
            self._on_delete         = on_delete
            self.expand             = True
            self.alignment          = ft.MainAxisAlignment.START

            if on_consolidate:
                self.controls = [ ft.Text(f"{data.name}"), 
                                  ft.Container(expand=True),           
                                  self.bf.custom_button(ft.Icons.PLAY_ARROW,  self.on_consolidate, "Consolidar"),
                                  self.bf.custom_button(ft.Icons.PAGEVIEW,    self.on_inspect_src, "Inspeccionar"),
                                  self.bf.delete_button(self.on_delete) ]
            else:
                if data.iadoc_ref:
                    self.controls = [ ft.Text(f"{data.name}"), 
                                    ft.Container(expand=True), 
                                    self.bf.custom_button(ft.Icons.PAGEVIEW,            self.on_inspect_src,    "Inspeccionar fuente"),
                                    self.bf.custom_button(ft.Icons.PAGEVIEW_OUTLINED,   self.on_inspect_iadoc,  "Inspeccionar iadoc"),
                                    self.bf.delete_button(self.on_delete) ]
                else:
                    self.controls = [ ft.Text(f"{data.name}"), 
                                    ft.Container(expand=True), 
                                    self.bf.custom_button(ft.Icons.PAGEVIEW, self.on_inspect_src, "Inspeccionar"),
                                    self.bf.delete_button(self.on_delete) ]
        #------------------------------------------------------------------------------------------
            
        def on_consolidate(self, _): self._on_consolidate(self._data)
        #------------------------------------------------------------------------------------------

        def on_inspect_src(self, _): self._on_inspect_src(self._data)
        #------------------------------------------------------------------------------------------

        def on_inspect_iadoc(self, _): self._on_inspect_iadoc(self._data)
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
        self._personal_info = None
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def populate(self, cliente: IncommingCliente | ClienteMetaInformation):
        self._info_layout.visible       = True
        self._document_viewer.visible   = False

        self._documents_ctrl.controls.clear()
        
        if cliente:
            if isinstance(cliente, IncommingCliente):
                self._personal_info     = cliente.personal_info
                self._tokens.visible    = False
                docs                    = sorted(cliente.docs, key=lambda x: x.ts, reverse=True)
                for d in  docs:
                    self._documents_ctrl.controls.append(ft.ListTile(   title   = self.HeaderCtrl(  data                = d,
                                                                                                    on_consolidate      = self.consolidate,
                                                                                                    on_inspect_src      = self.inspect_src,
                                                                                                    on_delete           = self.delete),
                                                                        subtitle= ft.Text(f"{d.mime}, {d.size_str}\n{d.ts_str}")))
            else:
                self._personal_info                         = cliente.personal_info
                tokens                                      = 0
                self._tokens.visible                        = True
                docs: list[ExpedienteViewer.ConsolidatedDoc] = [ ]
                src_in_biadocs                              = [ ]
                src_in_iadocs                               = [ ]
                src_in_bia_and_ia_docs                      = [ ]

                for src in cliente.src_docs:
                    bia_found   = None
                    ia_found    = None
                    for bia in cliente.biadocs:
                        if src.db_id == bia.source_ref:
                            bia_found = bia
                            break
                    for ia in cliente.iadocs:
                        if src.db_id == ia.source_ref:
                            ia_found = ia
                            break
                    if bia_found and ia_found:
                        src_in_bia_and_ia_docs.append((src, ia_found, bia_found))
                    elif bia_found:
                        src_in_biadocs.append((src, bia_found))
                    elif ia_found:
                        src_in_iadocs.append((src, ia_found))

                    if not ia_found and not bia_found:
                        docs.append(ExpedienteViewer.ConsolidatedDoc(src.name,
                                                                    0,
                                                                    src.size_str,
                                                                    src.mime,
                                                                    src.ts,
                                                                    src.db_id,
                                                                    None,
                                                                    None))
                for src, ia, bia in src_in_bia_and_ia_docs:
                    src:    SrcDocInfo
                    bia:    BIaDcoInfo
                    ia:     IaDcoInfo
                    docs.append(ExpedienteViewer.ConsolidatedDoc(src.name,
                                                                bia.tokens,
                                                                src.size_str,
                                                                src.mime,
                                                                src.ts,
                                                                src.db_id,
                                                                ia.db_id,
                                                                bia.db_id))
                for src, ia in src_in_iadocs:
                    src:    SrcDocInfo
                    ia:     IaDcoInfo
                    docs.append(ExpedienteViewer.ConsolidatedDoc(src.name,
                                                                ia.tokens,
                                                                src.size_str,
                                                                src.mime,
                                                                src.ts,
                                                                src.db_id,
                                                                ia.db_id,
                                                                None))

                for src, bia in src_in_biadocs:
                    src:    SrcDocInfo
                    bia:    BIaDcoInfo
                    docs.append(ExpedienteViewer.ConsolidatedDoc(src.name,
                                                                bia.tokens,
                                                                src.size_str,
                                                                src.mime,
                                                                src.ts,
                                                                src.db_id,
                                                                None,
                                                                bia.db_id))

                docs = sorted(docs, key=lambda x: x.ts, reverse=True)
                for d in  docs:
                    tokens += d.tokens
                    self._documents_ctrl.controls.append(ft.ListTile(   title   = self.HeaderCtrl(  data                = d,
                                                                                                    on_consolidate      = None,
                                                                                                    on_inspect_src      = self.inspect_src,
                                                                                                    on_inspect_iadoc    = self.inspect_iadoc,
                                                                                                    on_delete           = self.delete),
                                                                        subtitle= ft.Text(f"{d.mime}, {d.size_str}, {d.tokens if d.tokens else "-"} tokens\n{d.ts_str}")))
                self._tokens.value = str(tokens)

            self._paciente.value    = f"{self._personal_info.apellidos}, {self._personal_info.nombre}"
            self._dni.value         = f"{self._personal_info.dni} / {self._personal_info.id_interno}"
            self._edad.value        = f"{self._personal_info.sexo} - {get_elapsed_years(self._personal_info.fecha_nacimiento)} años"
    #----------------------------------------------------------------------------------------------

    def hide_document_viewer(self):
        self._info_layout.visible       = True
        self._document_viewer.visible   = False
        self.update()
    #----------------------------------------------------------------------------------------------

    def consolidate(self, data):
        pass
    #----------------------------------------------------------------------------------------------

    def inspect_src(self, data: IncommingFileInfo|ExpedienteViewer.ConsolidatedDoc):
        self._info_layout.visible       = False
        self._document_viewer.visible   = True

        if isinstance(data, IncommingFileInfo):
            content = self._backend.load_incomming_document(data.db_id)

            if content:
                self._document_viewer.setup_single( self._paciente.value,
                                                    self._dni.value,
                                                    self._edad.value,
                                                    data.name,
                                                    data.size_str,
                                                    "-",
                                                    content.get(),
                                                    data.mime)
            else:
                show_snackbar_error("No se ha podido cargar el documento")
        else:
            content_src     = self._backend.load_conslidated_src_document(data.src_ref)
            content_iadoc   = self._backend.load_conslidated_iadoc(data.iadoc_ref)

            if content_src and content_iadoc:
                self._document_viewer.setup_split(  self._paciente.value,
                                                    self._dni.value,
                                                    self._edad.value,
                                                    data.name,
                                                    data.size_str,
                                                    data.tokens,
                                                    content_src.get(),
                                                    content_iadoc.get(),
                                                    data.mime)
            else:
                show_snackbar_error("No se ha podido cargar el documento")

        self.update()
    #----------------------------------------------------------------------------------------------

    def inspect_iadoc(self, data:ExpedienteViewer.ConsolidatedDoc):
        self._info_layout.visible       = False
        self._document_viewer.visible   = True
        content                         = self._backend.load_conslidated_iadoc(data.iadoc_ref)

        if content:
            self._document_viewer.setup(self._paciente.value,
                                        self._dni.value,
                                        self._edad.value,
                                        data.name,
                                        data.size_str,
                                        data.tokens,
                                        content.get(),
                                        data.mime)
        else:
            show_snackbar_error("No se ha podido cargar el documento")

        self.update()
    #----------------------------------------------------------------------------------------------

    def delete(self, data):
        pass
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

        self._tokens = ft.TextField \
        (
            label       = "Tokens", 
            value       = None, 
            expand      = True,
            read_only   = True,
            border      = "none"
        )

        self._documents_ctrl    = ft.Column([], scroll=ft.ScrollMode.ALWAYS, alignment=ft.MainAxisAlignment.START, expand=True)

        first_row  = ft.Row \
        (
            [
                self._paciente,
                ft.Container(expand=True),
                self.bf.back_button(lambda _: self._on_go_back())
            ],
            expand=True
        )

        left_column             = ft.Column \
        (
            [
                ft.Container(first_row),
                ft.Container(self._dni),
                ft.Container(self._edad),
                ft.Container(self._tokens)
            ],
            expand      = 1,
            alignment   = ft.MainAxisAlignment.START,
        )

        rigth_column        = ft.Container(self._documents_ctrl, expand=3)
        self._info_layout   = ft.Row \
        (
            [   
                ft.Container(expand=1), 
                left_column, 
                rigth_column, 
                ft.Container(expand=1) 
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        )

        self._document_viewer   = DocumentViewer(self.hide_document_viewer)

        self.content    = ft.Stack \
        (
            [
                self._info_layout,
                self._document_viewer
            ],
            expand=True
        )

        self.alignment  = ft.alignment.top_center
        self.expand     = True

        self._info_layout.visible       = True
        self._document_viewer.visible   = False
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

    def set_values(self, clientes: list[IncommingCliente] | list[ClienteInfo]):
        self._list_content.clear()
        self._list_ctrl.controls.clear()
        
        if not len(clientes): return

        for p_obj in clientes:
            cliente: ClienteInfo
            if isinstance(p_obj, IncommingCliente):
                cliente         = p_obj.personal_info
                cliente.db_id   = p_obj.db_id
            else:
                cliente = p_obj

            self._list_content.append(self.Content( cliente.db_id,
                                                    cliente.dni,
                                                    cliente.id_interno,
                                                    cliente.apellidos,
                                                    cliente.nombre))
        self._list_content.sort(key=lambda c: c.apellidos.lower())

        for p in self._list_content:
            self._list_ctrl.controls.append(ft.ListTile(leading = ft.Checkbox(  value       = p.selected,
                                                                                on_change   = p.changed),
                                                        title= self.HeaderCtrl( data           = p,
                                                                                on_consolidate = self.consolidate_one,
                                                                                on_inspect     = self.inspect_one,
                                                                                on_delete      = self.delete_one),
                                                        subtitle= ft.Text(f"DNI: {p.dni} - ID: {p.id_local}")))
        self.update()
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
        self._delete_fcn([ref.db_id])
    #----------------------------------------------------------------------------------------------

    def inspect_one(self, ref: 'PacienteList.Content'):
        self._inspect_fcn(ref.db_id)
    #----------------------------------------------------------------------------------------------

    def reload(self, _):
        self._list_content.clear() 
        self._reload_fcn()
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
    def __init__(self, overlay_ctrl: OverlayCtrl, backend: BackendService, **kwargs):
        super().__init__(**kwargs)
        self._overlay_ctrl  = overlay_ctrl
        self._backend       = backend
        self._src_list      = PacienteList( "Nuevos",
                                            self.reload_src_clientes,
                                            self.consolidate_src_pacientes,
                                            self.check_src_duplicates,
                                            self.delete_src_pacientes,
                                            self.inspect_src_pacientes)
        
        self._con_list      = PacienteList( "Consolidados",
                                            self.reload_consolidated_clientes,
                                            None,
                                            self.check_consolidated_duplicates,
                                            self.delete_consolidated_pacientes,
                                            self.inspect_consolidated_pacientes)
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def show_cannot_undo_warning(self) -> bool:
        self._overlay_ctrl.show_warning(["Esta operación no se puede deshacer.\n¿Desea continuar?"])
        return self._overlay_ctrl.wait_answer()
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def populate(self, src_list: list[IncommingCliente], con_list: list[ClienteInfo]):
        self._src_list.set_values(src_list)
        self._con_list.set_values(con_list)
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def reload_src_clientes(self):
        status = self._backend.load_all_src_clientes()
        if status:
            self._src_list.set_values(status.get())
        else:
            show_snackbar_error("Error en la recarga de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def reload_consolidated_clientes(self):
        status = self._backend.load_all_consolidated_clientes()
        if status:
            self._con_list.set_values(status.get())
        else:
            show_snackbar_error("Error en la recarga de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def consolidate_src_pacientes(self, pacientes: list[str]):
        status = self._backend.consolidate_clientes(pacientes)

        if status:
            self.reload_consolidated_clientes()
            self.reload_src_clientes()
            show_snackbar("Consolidación finalizada")
        else:
            show_snackbar_error("Error en la consolidación de los pacientes")
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
        if self.show_cannot_undo_warning():
            status = self._backend.delete_src_clientes(pacientes)

            if status:
                self._src_list.set_values(status.get())
            else:
                show_snackbar_error("Error en el borrado de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def delete_consolidated_pacientes(self, pacientes: list[str]):
        if self.show_cannot_undo_warning():
            status = self._backend.delete_consolidated_clientes(pacientes)

            if status:
                self._con_list.set_values(status.get())
            else:
                show_snackbar_error("Error en el borrado de los pacientes")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def inspect_src_pacientes(self, paciente: str):
        status = self._backend.inspect_src_cliente(paciente)

        if status:
            self._main_layout.visible       = False
            self._expediente_viewer.visible  = True
            self._expediente_viewer.populate(status.get())
            self.update()
        else:
            show_snackbar_error("Error al leer el expediente del paciente")
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def inspect_consolidated_pacientes(self, paciente: str):
        status = self._backend.inspect_consolidated_cliente(paciente)

        if status:
            self._main_layout.visible       = False
            self._expediente_viewer.visible  = True
            self._expediente_viewer.populate(status.get())
            self.update()
        else:
            show_snackbar_error("Error al leer el expediente del paciente")
    #----------------------------------------------------------------------------------------------

    def come_back(self):
        con_list    = self._backend.load_all_consolidated_clientes()
        src_list    = self._backend.load_all_src_clientes()

        if not con_list or not src_list:
            status = self._backend.check_db()
        else:
            status = True

        self._main_layout.visible       = True
        self._expediente_viewer.visible  = False
        self.populate(src_list.or_else([]), con_list.or_else([]))
        self.update()

        if not status:
            show_snackbar_error("Error al cargar los pacientes")        
    #----------------------------------------------------------------------------------------------

    @void_try_catch(Environment.log_fcn)
    def build_ui(self):
        self._main_layout   = ft.Row \
        (
            controls    = [ self._con_list, ft.VerticalDivider(), self._src_list ],
            alignment   = ft.MainAxisAlignment.CENTER,
            expand      = True
        )

        self._expediente_viewer = ExpedienteViewer(self._backend, self.come_back)

        self.content    = ft.Stack \
        (
            [
                self._main_layout,
                self._expediente_viewer
            ],
            expand=True
        )
        self.expand     = True
        self._main_layout.visible       = True
        self._expediente_viewer.visible = False
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

    def populate(self, scr_list: list[IncommingCliente], con_list: list[ClienteInfo]):
        self._main_panel.populate(scr_list, con_list)
        self.update()
    #----------------------------------------------------------------------------------------------
    
    def callback(self, fcn, *args):
        pass
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        logo_container          = self.lf.buil_logo(self.page, "/imgs/logo.png")
        self._main_panel        = MainPanel(self._overlay_ctrl, self._backend)

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
