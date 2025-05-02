import flet as ft 
#--------------------------------------------------------------------------------------------------

snackbar_mngr_obj: 'SnackBarManager' = None
#--------------------------------------------------------------------------------------------------

class SnackBarManager:
    def __init__(self, page: ft.Page):
        self.page       = page
        self.text       = ft.Text("")
        self.snackbar   = ft.SnackBar(content=self.text, bgcolor="blue", duration=2000)
        self.page.overlay.append(self.snackbar)
    #----------------------------------------------------------------------------------------------

    def show_snackbar(self, message, tout):
        """Muestra un SnackBar y añade un mensaje extra si se proporciona."""
        self.text.value         = message
        self.snackbar.duration  = tout
        self.snackbar.open      = True
        self.snackbar.bgcolor   = "blue"
        self.page.update()
    #----------------------------------------------------------------------------------------------

    def show_snackbar_error(self, message, tout):
        """Muestra un SnackBar y añade un mensaje extra si se proporciona."""
        self.text.value         = message
        self.snackbar.duration  = tout
        self.snackbar.open      = True
        self.snackbar.bgcolor   = "red"
        self.page.update()
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

def set_snackbar_mngr(page: ft.Page):
    global snackbar_mngr_obj 
    snackbar_mngr_obj = SnackBarManager(page)
#--------------------------------------------------------------------------------------------------

def show_snackbar(message, tout=2000):
    snackbar_mngr_obj.show_snackbar(message, tout)
#--------------------------------------------------------------------------------------------------

def show_snackbar_error(message, tout=5000):
    snackbar_mngr_obj.show_snackbar_error(message, tout)
#--------------------------------------------------------------------------------------------------
