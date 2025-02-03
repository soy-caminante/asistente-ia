import  datetime

from    ..backend.service      import *
from    fastapi                import APIRouter, HTTPException, Query, Depends
#--------------------------------------------------------------------------------------------------

router = APIRouter()
#--------------------------------------------------------------------------------------------------

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
#--------------------------------------------------------------------------------------------------

def clean_list(src_list, sort=False):
    ret = [ ]

    for d in src_list:
        if "no encuentro la respuesta" in d.lower(): continue
        if d in ret: continue
        ret.append(d)

    if sort: ret.sort()
    return ret
#--------------------------------------------------------------------------------------------------

@router.get("/search")
def search_patient(pattern:str, backend: BackendService = Depends(get_service_instance)):
    pacientes: list[Paciente]   = backend.get_pacientes(pattern)
    ret                         = [ ]

    for p in pacientes:
        ret.append({ "dni": p.ref_id, "nombre": p.nombre, "apellidos": p.apellidos })

    return {"results": ret}
#--------------------------------------------------------------------------------------------------

@router.get("/patient_data")
def get_patient_details(ref_id: str, backend: BackendService = Depends(get_service_instance)):
    paciente = backend.get_paciente_info(ref_id)

    if paciente is not None:
        ret = \
        {
            "nombre":       paciente.nombre,
            "apellidos":    paciente.apellidos,
            "dni":          paciente.ref_id,
            "edad":         get_patient_age(paciente.fecha_nacimiento),
            "sexo":         paciente.sexo,
            "visitas":      clean_list(paciente.visitas, True),
            "antecedentes": clean_list(paciente.antecedentes),
            "riesgo":       clean_list(paciente.factores_riesgo),
            "medicacion":   clean_list(paciente.medicacion, True),
            "alergias":     clean_list(paciente.alergias),
            "ingresos":     clean_list(paciente.ingresos, True)
        }

        return ret
        
    raise HTTPException(status_code=404, detail="Paciente no encontrado.")
#--------------------------------------------------------------------------------------------------
