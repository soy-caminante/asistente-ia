import re
#--------------------------------------------------------------------------------------------------

def get_matches_case_no_sensitive(lista_cadenas, patron):
    return [(indice, cadena) for indice, cadena in enumerate(lista_cadenas) if re.search(patron, cadena, re.IGNORECASE)]
#--------------------------------------------------------------------------------------------------

def elapsed_time_to_str(elapsed_time):
    # Convertir a minutos y segundos
    minutos         = int(elapsed_time // 60)
    segundos        = int(elapsed_time % 60)
    milisegundos    = int((elapsed_time - int(elapsed_time)) * 1000)

    # Formatear a mm:ss:ms
    return f"{minutos:02}:{segundos:02}:{milisegundos:03}"
#--------------------------------------------------------------------------------------------------

