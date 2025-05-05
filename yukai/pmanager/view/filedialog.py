from    __future__              import  annotations

import  flet as ft 
import  mimetypes
#--------------------------------------------------------------------------------------------------

file_saver_obj: FileSaver = None
#--------------------------------------------------------------------------------------------------

class FileSaver:
    def __init__(self, page: ft.Page):
        self.page       = page
        self.file_saver = ft.FilePicker()        
        self.page.overlay.append(self.file_saver)
    #----------------------------------------------------------------------------------------------

    def show_filesaver(self, callback, name, mime):
        suggested_name              = name or "document"
        ext                         = mimetypes.guess_extension(mime) or ""
        self.file_saver.on_result   = callback
        self.file_saver.save_file(suggested_name + ext)
        self.page.update()
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

def set_filesaver_mngr(page: ft.Page):
    global file_saver_obj 
    file_saver_obj = FileSaver(page)
#--------------------------------------------------------------------------------------------------

def show_filesaver(callback: callable, name=None, mime=""): file_saver_obj.show_filesaver(callback, name, mime)
#--------------------------------------------------------------------------------------------------
