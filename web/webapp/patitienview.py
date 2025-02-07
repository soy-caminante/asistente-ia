import  datetime
import  flet                        as      ft

from    environment.environment     import  Environment
from    fuzzywuzzy import           fuzz
from    models.models               import  *
from    webapp.factories            import  *
from    webapp.navmanger            import  *
#--------------------------------------------------------------------------------------------------

class PatitentView(AppView):
    class DatosPaciente:
        def __init__(self, tf: TextFactory): 
            self._tf        = tf
            self._nombre    = tf.row_title("")
            self._edad      = tf.row_text("")
            self._sexo      = tf.row_text("")
            self._id        = tf.row_text("")
        #------------------------------------------------------------------------------------------

        def clear(self):
            self._nombre    = self._tf.row_title("")
            self._edad      = self._tf.row_text("")
            self._sexo      = self._tf.row_text("")
            self._id        = self._tf.row_text("")
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

        def set_nombre(self, value): self._nombre = self._tf.row_title(value)
        #------------------------------------------------------------------------------------------

        def set_edad(self, value):  self._edad = self._tf.row_text(value)
        #------------------------------------------------------------------------------------------

        def set_sexo(self, value):  self._sexo = self._tf.row_text(value)
        #------------------------------------------------------------------------------------------

        def set_id(self, value):  self._id = self._tf.row_text(value)
        #------------------------------------------------------------------------------------------

        def get_controls(self): return [ self._nombre, self._edad, self._sexo, self._id ]
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    class DatosLista:
        def __init__(self, tf: TextFactory):
            self._tf    = tf
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
                self._rows.append(ft.ListTile(title=self._tf.row_text(m.lstrip("!@#$%^&*()-+=<>?,.;:'\" "))))

            if len(self._rows) == 0:
                self._rows.append(ft.ListTile(title=self._tf.row_text("No hay registros")))

            return self._rows
        #------------------------------------------------------------------------------------------

        def add(self, info):
            self._rows.append(ft.ListTile(title=self._tf.row_text(info)))
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    def __init__(self, route, env:Environment):
        super().__init__(page=env._page, route=route)
        self._env                   = env
        self._backend               = env._backend
        self._button_factory        = ButtonFactory(ft.colors.BLUE)
        self._ctrl_paciente         = self.DatosPaciente(get_text_factory())
        self._ctrl_medicacion       = self.DatosLista(get_text_factory())
        self._ctrl_alergias         = self.DatosLista(get_text_factory())
        self._ctrl_cardiovascular   = self.DatosLista(get_text_factory())
        self._ctrl_visitas          = self.DatosLista(get_text_factory())
        self._ctrl_ingresos         = self.DatosLista(get_text_factory())
        self._build_ui()
    #----------------------------------------------------------------------------------------------

    def show_view(self):

        patitent_id = self.page.session.get("paciente")

        if patitent_id is not None:
            paciente: Paciente = self._backend.get_paciente_info(patitent_id)

            if paciente is not None:
                self._datos_paciente.controls           = self._ctrl_paciente.update(paciente)
                self._medicacion.controls               = self._ctrl_medicacion.update(paciente.medicacion)
                self._alergias.controls                 = self._ctrl_alergias.update(paciente.alergias)
                self._riesgo_cardiovascular.controls    = self._ctrl_cardiovascular.update(paciente.factores_riesgo)
                self._ultimas_visitas.controls          = self._ctrl_visitas.update(paciente.visitas)
                self._ingresos.controls                 = self._ctrl_ingresos.update(paciente.ingresos)
                self.page.update()

            else:
                self._nav_ctlr.show_error("No se puede recuperar la información del paciente")
                self._nav_ctlr.show_home_view()
        else:
            self._nav_ctlr.show_error("Paciente no definido")
            self._nav_ctlr.show_home_view()
    #----------------------------------------------------------------------------------------------

    def send_chat_question(self, e: ft.ControlEvent):
        msg = self._input_chat_field.value.strip()
        if msg:
            reversed_msg = msg[::-1]  # Invierte el mensaje

            # 🟢 MENSAJE DEL USUARIO (66% del ancho, fondo gris)
            user_message = ft.Container(
                content=ft.Text(msg, size=16, color="black"),
                bgcolor=ft.colors.GREY_300,
                padding=10,
                border_radius=10,
                width=self.page.width * 0.66,  # Ocupa el 66% del ancho del chat
                alignment=ft.alignment.center_right
            )

            # 🔵 RESPUESTA INVERTIDA DEL BOT (100% del ancho)
            bot_message = ft.Container(
                content=ft.Text(f"Bot: {reversed_msg}", size=16, color="black"),
                bgcolor=ft.colors.BLUE_100,
                padding=10,
                border_radius=10,
                width=self.page.width * 0.66,  # Ocupa el 66% del ancho del chat
                alignment=ft.alignment.center_left
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

    def _build_ui(self):
        text_factory                = get_text_factory()
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

        self._medicacion            = ft.ExpansionTile \
        (
            title                   = text_factory.container_title("Medicación pautada"),
            affinity                = ft.TileAffinity.PLATFORM,
            maintain_state          = True,
            controls                = self._ctrl_medicacion._rows,
        )

        self._riesgo_cardiovascular = ft.ExpansionTile \
        (
            title                   = text_factory.container_title("Factores de riesgo cardiovascular"),
            affinity                = ft.TileAffinity.PLATFORM,
            maintain_state          = True,
            controls                = self._ctrl_cardiovascular._rows
        )

        self._alergias              = ft.ExpansionTile \
        (
            title                   = text_factory.container_title("Alergias"),
            affinity                = ft.TileAffinity.PLATFORM,
            maintain_state          = True,
            controls                = self._ctrl_alergias._rows
        )

        self._ultimas_visitas       = ft.ExpansionTile \
        (
            title                   = text_factory.container_title("Últimas visitas"),
            affinity                = ft.TileAffinity.PLATFORM,
            maintain_state          = True,
            controls                = self._ctrl_visitas._rows
        )

        self._ingresos              = ft.ExpansionTile \
        (
            title                   = text_factory.container_title("Historial de ingresos"),
            affinity                = ft.TileAffinity.PLATFORM,
            maintain_state          = True,
            controls                = self._ctrl_ingresos._rows
        )

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
                    ft.Container(expand=True)
                ],
                expand = True,
                spacing= 10
            ),
            expand          = 1,
            padding         = 10,
            border          = ft.border.all(1, ft.colors.GREY_300),
            border_radius   = 10
        )

        self._chat_list = ft.ListView \
        (
            expand      = True,
            spacing     = 10,
            auto_scroll = True,  # Desplaza automáticamente cuando hay nuevos mensajes
            reverse     = True  # Rellena la lista de abajo hacia arriba
        )

        # Campo de entrada
        self._input_chat_field = ft.TextField \
        (
            hint_text   = "Escribe un mensaje...",
            expand      = True,
            on_submit   = self.send_chat_question  # Permite enviar con "Enter"
        )

        # Botón de enviar
        send_button = ft.IconButton \
        (
            icon        = ft.icons.SEND,
            tooltip     = "Enviar",
            on_click    = self.send_chat_question
        )

        # Contenedor inferior con campo de entrada + botón
        input_row = ft.Row([ self._input_chat_field, send_button ])

        chat_container = ft.Container \
        (
            ft.Column \
            (
                controls = \
                [
                    self._chat_list,
                    input_row  # Input siempre abajo
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
