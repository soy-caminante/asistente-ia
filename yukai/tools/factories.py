import flet         as ft
import pathlib
#--------------------------------------------------------------------------------------------------

class CircularButton(ft.Container):
    def __init__(self, icon, tooltip, on_click, visible, style_color):
        super().__init__\
        (
            content         = ft.IconButton(icon=icon, tooltip=tooltip, on_click=on_click),
            padding         = 5,
            visible         = visible,
            border          = ft.border.all(2, style_color),
            border_radius   = ft.border_radius.all(30),
        )
    #----------------------------------------------------------------------------------------------

    def set_on_click(self, on_click):
        button          = ft.IconButton(self.content)
        button.on_click = on_click
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class ButtonFactory:
    def __init__(self, style_color="#DAA520"):
        self._style_color = style_color
    #----------------------------------------------------------------------------------------------
    
    def move_up_button(self, on_click, visible):
        return CircularButton(ft.icons.ARROW_UPWARD, "Mover arriba", on_click, visible, self._style_color)
    #----------------------------------------------------------------------------------------------

    def move_down_button(self, on_click, visible):
        return CircularButton(ft.icons.ARROW_DOWNWARD, "Mover abajo", on_click, visible, self._style_color)
    #----------------------------------------------------------------------------------------------

    def delete_button(self, on_click, visible):
        return CircularButton(ft.icons.DELETE, "Eliminar el elemento seleccionado", on_click, visible, self._style_color)
    #----------------------------------------------------------------------------------------------

    def save_button(self, on_click, visible):
        return CircularButton(ft.icons.SAVE, "Guardar los cambios", on_click, visible, self._style_color)
    #----------------------------------------------------------------------------------------------

    def add_button(self, on_click, visible):
        return CircularButton(ft.icons.ADD, "Agregar un nuevo elemento", on_click, visible, self._style_color)
    #----------------------------------------------------------------------------------------------

    def back_button(self, on_click, visible):
        return CircularButton(ft.icons.ARROW_BACK, "Volver al inicio", on_click, visible, self._style_color)
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class TextFactory:
    def __init__(self,  style_color     = "#54BAAD",
                        page_size       = 64,
                        container_size  = 32,
                        mosaic_size     = 24,
                        row_title_size  = 16,
                        row_text_size   = 16):
        self._style_color       = style_color
        self._page_size         = page_size
        self._container_size    = container_size
        self._mosaic_size       = mosaic_size
        self._row_title_size    = row_title_size
        self._row_text_size     = row_text_size
    #----------------------------------------------------------------------------------------------

    def page_title(self, text):
        return ft.Text(text, weight=ft.FontWeight.BOLD, color=self._style_color, size=self._page_size)
    #----------------------------------------------------------------------------------------------

    def mosaic_title(self, text):
        return ft.Text(text, weight=ft.FontWeight.BOLD, color=self._style_color, size=self._mosaic_size)
    #----------------------------------------------------------------------------------------------

    def container_title(self, text):
        return ft.Text(text, weight=ft.FontWeight.BOLD, color=self._style_color, size=self._container_size)
    #----------------------------------------------------------------------------------------------

    def row_title(self, text):
        return ft.Text(text, weight=ft.FontWeight.BOLD, size=self._row_title_size)
    #----------------------------------------------------------------------------------------------

    def row_text(self, text):
        return ft.Text(text, size=self._row_text_size)
    #----------------------------------------------------------------------------------------------

    def set_style_color(self, color): self._style_color = color
    #----------------------------------------------------------------------------------------------
    
    def set_container_size(self, size): self._container_size = size
    #----------------------------------------------------------------------------------------------

    def set_mosaic_size(self, size): self._mosaic_size = size
    #----------------------------------------------------------------------------------------------

    def set_row_title_size(self, size): self._row_title_size = size
    #----------------------------------------------------------------------------------------------

    def set_row_text_size(self, size): self._row_text_size = size
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

text_factory = TextFactory()
#--------------------------------------------------------------------------------------------------

def set_text_factory(factory: TextFactory):
    global text_factory
    text_factory = factory
#--------------------------------------------------------------------------------------------------

def get_text_factory() -> TextFactory: return text_factory
#--------------------------------------------------------------------------------------------------

class IconFactory:
    @staticmethod
    def green_check_mark(text):
        return ft.Row \
        (
            controls=[text_factory.row_text(text), ft.Icon(ft.Icons.CHECK, size=20, color=ft.Colors.GREEN) ]
        )
    #----------------------------------------------------------------------------------------------

    @staticmethod
    def red_cross(text):
        return ft.Row \
        (
            controls=[text_factory.row_text(text), ft.Icon(ft.Icons.CLOSE, size=20, color=ft.Colors.RED) ]
        )
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class LogoFactory:
    @staticmethod
    def buil_logo(page: ft.Page, logo_path: pathlib.Path):
        screen_height       = page.height
        logo_height         = screen_height * 0.3 # Máximo 20% de la pantalla
        logo                = ft.Image \
        (
            src     = logo_path,
            width   = logo_height * (839 / 397),  # Manteniendo la proporción
            height  = logo_height,
            fit     = ft.ImageFit.CONTAIN
        )

        logo_container = ft.Container \
        (
            content         = logo,
            padding         = 10,  # Espacio interno
        )

        return logo_container
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
