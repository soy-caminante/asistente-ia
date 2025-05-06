import  flet                        as ft 
import  re
import  time

from    dataclasses                 import  dataclass
from    tools.factories             import  *
#--------------------------------------------------------------------------------------------------

@dataclass
class ColorPalette:
    theme:str   = "#54BAAD"
    grey:str    = ft.Colors.GREY_300
#--------------------------------------------------------------------------------------------------

class Factories:
    tf: TextFactory                             = None
    bf: CircularButtonFactory|IconButtonFactory = None
    lf: LogoFactory                             = None
    cp: ColorPalette                            = None
    #----------------------------------------------------------------------------------------------

    @classmethod
    def setup(cls, tf, bf, lf, cp):
        cls.tf      = tf
        cls.bf      = bf
        cls.lf      = lf
        cls.cp      = ColorPalette()
    #----------------------------------------------------------------------------------------------

    def __init__(self):
        pass
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class WarningControl(ft.Container, Factories):
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
        self.update()
    #----------------------------------------------------------------------------------------------

    def wait_answer(self):
        while self._answer is None:
            time.sleep(0.5)
            self.update()
        return self._answer
    #----------------------------------------------------------------------------------------------

    def set_accept(self, _): self._answer = True
    #----------------------------------------------------------------------------------------------

    def set_cancel(self, _): self._answer = False
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        self._msg           = self.tf.container_title("Mensaje")
        self._msg.text_align= ft.TextAlign.CENTER
        row = ft.Row \
        (
            [ 
                ft.Column \
                (
                    [   
                        ft.Container(expand=True),
                        ft.Card
                        (
                            ft.Container \
                            (
                                ft.Column \
                                (
                                    [
                                        ft.Container(self._msg, expand=True),
                                        ft.Row \
                                        (
                                            [
                                                ft.Container(ft.Text("    "), expand=True),
                                                self.bf.accept_button(on_click=self.set_accept, visible=True),
                                                self.bf.cancel_button(on_click=self.set_cancel, visible=True)
                                            ],
                                            alignment           = ft.MainAxisAlignment.END,
                                            vertical_alignment  = ft.CrossAxisAlignment.CENTER,
                                            expand              = True
                                        )
                                    ],
                                    expand              = True,
                                    horizontal_alignment= ft.CrossAxisAlignment.END
                                ),
                                padding = 10,
                                expand  = True
                            ),
                            elevation   = 2
                        ),
                        ft.Container(expand=True)
                    ],
                    alignment           = ft.MainAxisAlignment.CENTER,
                    horizontal_alignment= ft.CrossAxisAlignment.CENTER,
                )
            ],
            expand              = True,
            alignment           = ft.MainAxisAlignment.CENTER,
            vertical_alignment  = ft.MainAxisAlignment.CENTER
        )
        
        self.content    = row
        self.expand     = True
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class WaitCtrl(ft.Container, Factories):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def set_msg(self, msg): 
        lines           = ""
        if not isinstance(msg, list):
            msg = [ msg ]
        for m in msg:
            if lines != "": lines += "\n"
            lines += m
        self._msg.value = lines
        self.update()
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        self._msg               = self.tf.mosaic_title("Cargado nuevos pacientes")
        self._msg.width         = 300
        self._msg.text_align    = ft.TextAlign.CENTER
        
        row         = ft.Row \
        (
            [ 
                ft.Column \
                (
                    [
                        ft.Card
                        (
                            ft.Container \
                            (
                                ft.Row \
                                (
                                    [ ft.ProgressRing(width=20, height=20), self._msg ],
                                    alignment           = ft.MainAxisAlignment.CENTER,
                                    vertical_alignment  = ft.CrossAxisAlignment.CENTER
                                ),
                                padding= 10
                            ),
                            elevation   = 2,
                            opacity     = 1
                        )
                    ],
                    alignment           = ft.MainAxisAlignment.CENTER,
                    horizontal_alignment= ft.CrossAxisAlignment.CENTER
                )
            ],
            expand              = True,
            alignment           = ft.MainAxisAlignment.CENTER,
            vertical_alignment  = ft.MainAxisAlignment.CENTER
        )
        self.content    = row
        self.expand     = True
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class OverlayCtrl(ft.Container, Factories):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    #----------------------------------------------------------------------------------------------

    def show_warning(self, msg):
        self.visible                = True
        self._wait_ctrl.visible     = False
        self._warning_ctrl.visible  = True
        self._warning_ctrl.set_msg(msg)
        self.update()
        return self
    #----------------------------------------------------------------------------------------------
    
    def show_wait(self, msg):
        self.visible                = True
        self._wait_ctrl.visible     = True
        self._warning_ctrl.visible  = False
        self._wait_ctrl.set_msg(msg)
        self.update()
    #----------------------------------------------------------------------------------------------

    def hide(self):
        self.visible = False
        self.update()
    #----------------------------------------------------------------------------------------------

    def wait_answer(self): 
        ret             = self._warning_ctrl.wait_answer()
        self.visible    = False
        self.update()
        return ret
    #----------------------------------------------------------------------------------------------

    def update_wait_info(self, msg): self._wait_ctrl.set_msg(msg)
    #----------------------------------------------------------------------------------------------

    def build_ui(self):
        self._warning_ctrl  = WarningControl()
        self._wait_ctrl     = WaitCtrl()

        bg_ctrl = ft.Container \
        (
            bgcolor            = ft.colors.BLACK54,
            opacity            = 0.7,
            animate_opacity    = 300,
            expand             = True
        )
        self.content = ft.Stack \
        ([
            bg_ctrl,
            self._wait_ctrl,
            self._warning_ctrl
        ],
        expand=True)
        self.expand = True
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class OverlayCtrlWrapper:
    class WaitWrapper:
        def __init__(self, msg, ctrl: OverlayCtrl):
            self._ctrl  = ctrl
            self._msg   = msg
        #------------------------------------------------------------------------------------------

        def show(self):
            self._ctrl.show_wait(self._msg)
        #------------------------------------------------------------------------------------------

        def hide(self):
            self._ctrl.hide()
        #------------------------------------------------------------------------------------------

        def __enter__(self):
            self.show()
            return self
        #------------------------------------------------------------------------------------------

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.hide()
        #------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------

    def __init__(self, ctrl: OverlayCtrl):
        self._ctrl = ctrl
    #----------------------------------------------------------------------------------------------

    def wait(self, msg=None): return self.WaitWrapper(msg, self._ctrl)
    #----------------------------------------------------------------------------------------------

    def warning(self, msg=None): return self._ctrl.show_warning(msg).wait_answer()
    #----------------------------------------------------------------------------------------------

    def update(self, msg): self._ctrl.update_wait_info(msg)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

def format_markdown(markdown_text):
    """
    Función que procesa un texto markdown.
    Si encuentra una línea de lista, envuelve en negrita la parte del elemento
    hasta el primer punto (.) o dos puntos (:), dejándolo sin cambios el resto.
    """
    # Patrón para detectar líneas de lista:
    # - Puede iniciar con espacios en blanco.
    # - Luego puede tener un marcador de lista: "-", "*", "+" o un número seguido de un punto.
    # - Después de un espacio, el resto de la línea es el contenido del elemento.
    list_item_pattern = re.compile(r'^(\s*([-*+]|\d+\.)\s+)(.*)$')
    
    new_lines = []
    for line in markdown_text.splitlines():
        match = list_item_pattern.match(line)
        if match:
            # Separamos el marcador y el contenido de la lista
            marker = match.group(1)      # Por ejemplo, "  - " o "1. "
            item_text = match.group(3)     # El contenido del elemento
            
            # Buscamos el índice del primer "." o ":"
            dot_index = item_text.find('.')
            colon_index = item_text.find(':')
            
            # Si ninguno de los dos se encontró, consideramos que se debe formatear todo el texto
            if dot_index == -1 and colon_index == -1:
                index = len(item_text)
                punct = ''
            else:
                # Si uno de los dos no se encontró, tomamos el índice del que exista.
                if dot_index == -1:
                    index = colon_index
                    punct = item_text[colon_index]
                elif colon_index == -1:
                    index = dot_index
                    punct = item_text[dot_index]
                else:
                    # Ambos existen: se elige el que aparezca primero.
                    if dot_index < colon_index:
                        index = dot_index
                        punct = item_text[dot_index]
                    else:
                        index = colon_index
                        punct = item_text[colon_index]
            
            # Separamos el texto a poner en negrita y el resto
            # Es recomendable quitar espacios laterales en la parte que se bolda para que
            # el efecto se vea correcto en Markdown.
            bold_part = item_text[:index].strip()
            remainder = item_text[index:]
            
            # Reconstruimos la línea, dejando el marcador de lista intacto
            new_line = f"{marker}**{bold_part}**{remainder}"
            new_lines.append(new_line)
        else:
            # Si la línea no es un elemento de lista, se deja sin modificar
            new_lines.append(line)
    
    # Se retorna el texto modificado
    return "\n".join(new_lines)
#--------------------------------------------------------------------------------------------------



