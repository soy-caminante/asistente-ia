import  datetime
import  flet                        as      ft

from    environment.environment     import  Environment
from    environment.logger          import  Logger
from    fuzzywuzzy import           fuzz
from    models.models               import  *
from    webapp.factories            import  *
from    webapp.navmanger            import  *
#--------------------------------------------------------------------------------------------------

class PatitentView(AppView):
    class DatosPaciente:
        def __init__(self): 
            self._nombre    = text_factory.row_title("")
            self._edad      = text_factory.row_text("")
            self._sexo      = text_factory.row_text("")
            self._id        = text_factory.row_text("")
        #------------------------------------------------------------------------------------------

        def clear(self):
            self._nombre    = text_factory.row_title("")
            self._edad      = text_factory.row_text("")
            self._sexo      = text_factory.row_text("")
            self._id        = text_factory.row_text("")
        #------------------------------------------------------------------------------------------

        def update(self, paciente: Paciente):
            def get_patient_age(fecha_nacimiento):
                # Convertir la cadena de texto a un objeto datetime
                fecha_nacimiento = datetime.datetime.strptime(fecha_nacimiento, "%d-%m-%Y")
                
                # Obtener la fecha actual
                fecha_actual = datetime.datetime.now()
                
                # Calcular la edad en años
                edad = fecha_actual.year - fecha_nacimiento.year
                
                # Ajustar si la fecha de nacimiento aún no ha ocurrido este año
                if (fecha_actual.month, fecha_actual.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
                    edad -= 1

                return edad
            #--------------------------------------------------------------------------------------

            self.set_nombre(f"{paciente.apellidos}, {paciente.nombre}")
            self.set_edad(f"Edad: {get_patient_age(paciente.fecha_nacimiento)}")
            self.set_sexo(f"Sexo: {paciente.sexo}")
            self.set_id(f"DNI: {paciente.ref_id}")

            return self.get_controls()
        #------------------------------------------------------------------------------------------

        def set_nombre(self, value): self._nombre = text_factory.row_title(value)
        #------------------------------------------------------------------------------------------

        def set_edad(self, value):  self._edad = text_factory.row_text(value)
        #------------------------------------------------------------------------------------------

        def set_sexo(self, value):  self._sexo = text_factory.row_text(value)
        #------------------------------------------------------------------------------------------

        def set_id(self, value):  self._id = text_factory.row_text(value)
        #------------------------------------------------------------------------------------------

        def get_controls(self): return [ self._nombre, self._edad, self._sexo, self._id ]
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    class DatosLista:
        def __init__(self):
            self._rows  = [ ]
        #------------------------------------------------------------------------------------------

        def clear(self): self._rows = [ ]
        #------------------------------------------------------------------------------------------

        def update(self, info_list: list[str]):
            def remove_duplicates(lista, umbral=70):
                resultado = []
                for cadena in lista:
                    if not any(fuzz.ratio(cadena, existente) > umbral for existente in resultado):
                        resultado.append(cadena)
                return resultado

            self._rows  = [ ]
            info_list   = remove_duplicates(info_list)

            for m in info_list:
                if "no encuentro la respuesta" in m.lower(): continue
                self._rows.append(ft.ListTile(title=text_factory.row_text(m.lstrip("!@#$%^&*()-+=<>?,.;:'\" "))))

            if len(self._rows) == 0:
                self._rows.append(ft.ListTile(title=text_factory.row_text("No hay registros")))

            return self._rows
        #------------------------------------------------------------------------------------------

        def add(self, info):
            self._rows.append(ft.ListTile(title=text_factory.row_text(info)))
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    class SideCard(ft.Card):
        def __init__(self, title):
            super().__init__()
            ft.Theme()
            self._data_ctrl         = PatitentView.DatosLista()
            self._expansion_tile    = ft.ExpansionTile \
            (
                title               = text_factory.container_title(title),
                affinity            = ft.TileAffinity.PLATFORM,
                maintain_state      = True,
                controls            = self._data_ctrl._rows
            )

            self.content = ft.Container \
            (
                content = self._expansion_tile,
                padding=ft.padding.all(10),
                border=None,
                animate_size=300  # Duración de la animación en milisegundos
            )
        #------------------------------------------------------------------------------------------

        def update_data(self, data:list[str]): self._expansion_tile.controls = self._data_ctrl.update(data)
    #----------------------------------------------------------------------------------------------

    def __init__(self, route, env:Environment):
        super().__init__(page=env._page, route=route)
        self._env                                   = env
        self._backend                               = env._backend
        self._button_factory                        = ButtonFactory(ft.colors.BLUE)
        self._ctrl_paciente                         = self.DatosPaciente()
        self._build_ui_2()
    #----------------------------------------------------------------------------------------------

    def show_view(self):
        patitent_id = self.page.session.get("paciente")

        if patitent_id is not None:
            paciente: Paciente = self._backend.get_paciente_info(patitent_id)

            if paciente is not None:
                self._chat_list.controls.clear()
                self._datos_paciente.controls = self._ctrl_paciente.update(paciente)
                self._medicacion.update_data(paciente.medicacion)
                self._alergias.update_data(paciente.alergias)
                self._riesgo_cardiovascular.update_data(paciente.factores_riesgo)
                self._ultimas_visitas.update_data(paciente.visitas)
                self._ingresos.update_data(paciente.ingresos)
                self.page.update()

            else:
                self._nav_ctlr.show_error("No se puede recuperar la información del paciente")
                self._nav_ctlr.show_home_view()
        else:
            self._nav_ctlr.show_error("Paciente no definido")
            self._nav_ctlr.show_home_view()
    #----------------------------------------------------------------------------------------------

    def send_chat_question(self, e: ft.ControlEvent):
        patitent_id = self.page.session.get("paciente")

        if patitent_id is None:
            self._nav_ctlr.show_error("Paciente no definido")
            self._nav_ctlr.show_home_view()
        
        Logger.info(f"Paciente {patitent_id}")

        msg = self._input_chat_field.value.strip()

        if msg:
            user_message = ft.Row \
            (
                controls= \
                [
                    ft.Container(expand=1),  # Espacio vacío (1 parte)
                    ft.Container \
                    (
                        content= ft.Container
                        (  # 🔹 Contenedor interno para que el fondo solo enmarque el texto
                            content         = ft.Text(msg, size=20, color="black", no_wrap=False),
                            bgcolor         = ft.colors.GREY_300,  # Fondo gris solo en el texto
                            padding         = 10,  # Margen interno
                            border_radius   = 10,  # Bordes redondeados
                        ),
                        alignment   = ft.alignment.center_right,
                        expand      = 3,  # El contenedor del mensaje ocupa 2 partes
                    )
                ],
                expand=True  # Hace que la fila ocupe todo el espacio disponible            
            )

            self._nav_ctlr.show_wait_ctrl()

            bot_msg, gen_time = self._backend.chat(patitent_id, msg)

            self._nav_ctlr.hide_wait_ctrl()

            md_style = ft.MarkdownStyleSheet \
            (
                p_text_style        = ft.TextStyle(size=20, color="grey"),
                strong_text_style   = ft.TextStyle(size=22, color="black")
            )
            
            bot_message = ft.Container \
            (
                content         = ft.Column \
                (
                    [
                        ft.Markdown(f"{bot_msg}", md_style_sheet=md_style),
                        ft.Text \
                        (
                            gen_time,
                            size=12,
                            color=ft.colors.GREY_600,
                            text_align=ft.TextAlign.LEFT
                        )
                    ],
                    spacing=0,  # Elimina el espacio entre los elementos
                    tight=True   # Reduce aún más la separación
                ),
                padding         = 10,
                alignment       = ft.alignment.center_left
            )

            # Agregar mensajes a la lista de chat
            self._chat_list.controls.insert(0, user_message)
            self._chat_list.controls.insert(0, bot_message)

            # Limpiar campo de entrada y actualizar UI
            self._input_chat_field.value = ""
            self.page.update()
    #----------------------------------------------------------------------------------------------

    def _go_back(self, e:ft.ControlEvent):
        self._nav_ctlr.show_home_view()
    #----------------------------------------------------------------------------------------------

    def _build_ui_2(self):
        """Construye la UI de manera adaptable según el tipo de dispositivo."""

        # 🔹 DETECTAR DISPOSITIVO
        is_mobile   = self.page.platform in ["ios", "android"]
        is_tablet   = self.page.window.width < 1024 and is_mobile
        is_desktop  = not is_mobile and not is_tablet

        # 🔹 LOGO Y HEADER
        logo_container              = LogoFactory.buil_logo(self.page, self._env._locations._logo_path)
        logo_container.alignment    = ft.alignment.top_right
        logo_container.expand       = False

        back_button = self._button_factory.back_button(self._go_back, True)

        self._datos_paciente = ft.Column(
            controls=[
                self._ctrl_paciente._nombre,
                self._ctrl_paciente._edad,
                self._ctrl_paciente._sexo,
                self._ctrl_paciente._id,
            ],
            spacing=5
        )

        datos_personales_container = ft.Container(
            content=self._datos_paciente,
            padding=10,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=10,
            expand=True
        )

        header = ft.Row(
            controls=[datos_personales_container, logo_container],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            expand=1
        )

        # 🔹 SECCIONES DE INFORMACIÓN
        self._medicacion = self.SideCard("Medicación pautada")
        self._riesgo_cardiovascular = self.SideCard("Factores de riesgo cardiovascular")
        self._alergias = self.SideCard("Alergias")
        self._ultimas_visitas = self.SideCard("Últimas visitas")
        self._ingresos = self.SideCard("Historial de ingresos")

        datos_paciente_container = ft.Container(
            content=ft.Column(
                controls=[
                    back_button,
                    self._medicacion,
                    self._riesgo_cardiovascular,
                    self._alergias,
                    self._ultimas_visitas,
                    self._ingresos,
                ],
                spacing=10,
                expand=True,
                scroll=ft.ScrollMode.AUTO
            ),
            expand=1,
            padding=10,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=10,
            alignment=ft.alignment.top_left
        )

        # 🔹 CHAT
        self._chat_list = ft.ListView(
            expand=True,
            spacing=10,
            reverse=True  # Para que los mensajes nuevos aparezcan abajo
        )

        self._input_chat_field = ft.TextField(
            hint_text="Escribe un mensaje...",
            expand=True,
            multiline=True,
            text_size=20,
            border=ft.InputBorder.NONE,
            on_submit=self.send_chat_question
        )

        send_button = ft.IconButton(
            icon=ft.icons.ARROW_UPWARD,
            tooltip="Enviar",
            on_click=self.send_chat_question
        )

        input_container = ft.Card(
            ft.Container(
                content=ft.Column(
                    [
                        self._input_chat_field,
                        ft.Row(
                            controls=[send_button],
                            alignment=ft.MainAxisAlignment.END
                        )
                    ]
                ),
                padding=10,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=10
            ),
            elevation=2
        )

        chat_container = ft.Container(
            ft.Column(
                controls=[
                    self._chat_list,
                    input_container  # Input siempre abajo
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            expand=2,
            padding=10,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=10
        )

        # 🔹 DISEÑO RESPONSIVO
        if is_mobile:
            layout = ft.Column(
                controls=[
                    header,  # Datos personales y logo en una sola fila
                    datos_paciente_container,  # Info personal arriba
                    chat_container  # Chat abajo
                ],
                expand=True
            )
        else:  # Escritorio o Tablet
            layout = ft.Column(
                controls=[
                    header,
                    ft.Row([datos_paciente_container, chat_container], expand=4)  # Dos columnas
                ],
                expand=True
            )

        self.controls = [layout]
        self.page.update()

    def _build_ui(self):
        logo_container              = LogoFactory.buil_logo(self.page, self._env._locations._logo_path)
        logo_container.alignment    = ft.alignment.top_right
        logo_container.expand       = False
        back_button                 = self._button_factory.back_button(self._go_back, True)
        self._datos_paciente        = ft.Column \
        (
            controls= \
            [
                self._ctrl_paciente._nombre,
                self._ctrl_paciente._edad,
                self._ctrl_paciente._sexo,
                self._ctrl_paciente._id,
            ],
            spacing=5
        )

        datos_personales_container = ft.Container \
        (
            content         = self._datos_paciente,
            padding         = 10,
            border          = ft.border.all(1, ft.colors.GREY_300),
            border_radius   = 10,
            expand          = True
        )

        header = ft.Row \
        (
            controls    = [ datos_personales_container, logo_container ],  # Coloca datos a la izquierda, logo a la derecha
            alignment   = ft.MainAxisAlignment.SPACE_BETWEEN,  # Separa los elementos
            expand      = 1
        )

        self._medicacion            = self.SideCard("Medicación pautada")
        self._riesgo_cardiovascular = self.SideCard("Factores de riesgo cardiovascular")
        self._alergias              = self.SideCard("Alergias")
        self._ultimas_visitas       = self.SideCard("Últimas visitas")
        self._ingresos              = self.SideCard("Historial de ingresos")

        datos_paciente_container = ft.Container \
        (
            content= ft.Column \
            (
                controls= \
                [
                    back_button,
                    self._medicacion,
                    self._riesgo_cardiovascular,
                    self._alergias,
                    self._ultimas_visitas,
                    self._ingresos,
                ],
                spacing = 10,
                expand  = True,
                scroll  = ft.ScrollMode.AUTO
            ),
            expand          = 1,
            padding         = 10,
            border          = ft.border.all(1, ft.colors.GREY_300),
            border_radius   = 10,
            alignment       = ft.alignment.top_left  
        )

        self._chat_list = ft.ListView \
        (
            expand      = True,
            spacing     = 10,
            reverse     = True  # Rellena la lista de abajo hacia arriba
        )

        # Campo de entrada
        self._input_chat_field = ft.TextField \
        (
            hint_text   = "Escribe un mensaje...",
            expand      = True,
            multiline   = True,
            text_size   = 20,
            border      = ft.InputBorder.NONE,
            on_submit   = self.send_chat_question  # Permite enviar con "Enter"
        )

        # Botón de enviar
        send_button = ft.IconButton \
        (
            icon        = ft.icons.ARROW_UPWARD,
            tooltip     = "Enviar",
            on_click    = self.send_chat_question
        )

        # Contenedor inferior con campo de entrada + botón
        input_conatiner = ft.Card \
        (
            ft.Container \
            (
                content = ft.Column \
                (
                    [
                        self._input_chat_field,
                        ft.Row \
                        (
                            controls    = [ send_button ],
                            alignment   = ft.MainAxisAlignment.END
                        )
                    ]
                ),
                padding         = 10,
                border          = ft.border.all(1, ft.colors.GREY_300),
                border_radius   = 10
            ),
            elevation=2
        )

        chat_container = ft.Container \
        (
            ft.Column \
            (
                controls = \
                [
                    self._chat_list,
                    input_conatiner  # Input siempre abajo
                ],
                expand      = True,
                alignment   = ft.MainAxisAlignment.SPACE_BETWEEN  # Mantiene el input abajo
            ),
            expand          = 2,  # Ocupará 2 partes del espacio total (doble que la izquierda)
            padding         = 10,
            border          = ft.border.all(1, ft.colors.GREY_300),
            border_radius   = 10
        )

        layout = ft.Column \
        (
            controls= \
            [
                header,  # Fila con Datos del Paciente + Logo
                ft.Row([datos_paciente_container, chat_container], expand=4)   # Dos columnas abajo (Formulario y Chat)
            ],
            expand=True
        )
        self.controls.append(layout)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
