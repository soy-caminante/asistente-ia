from backend.service        import *
from fastapi                import APIRouter, Depends
from pydantic               import BaseModel
#--------------------------------------------------------------------------------------------------

router = APIRouter()
#--------------------------------------------------------------------------------------------------

class ChatRequest(BaseModel):
    ref_id:     str
    question:   str
#--------------------------------------------------------------------------------------------------

response = \
"""
# 📋 Diagnóstico Médico

## 🏥 **Información del Paciente**
- **Nombre:** Juan Pérez
- **Edad:** 45 años
- **Género:** Masculino
- **Peso:** 110 kg
- **Estatura:** 1.70 m
- **Índice de Masa Corporal (IMC):** 38.1 (Obesidad grado II)
- **Antecedentes Médicos:** Hipertensión, resistencia a la insulina.

---

## 🩺 **Diagnóstico**
### **🔹 Condición Principal: Obesidad Grado II (IMC 35 - 39.9)**
- **Clasificación:** Obesidad severa.
- **Riesgos Asociados:**
  - Diabetes tipo 2
  - Hipertensión arterial
  - Enfermedades cardiovasculares
  - Apnea del sueño
  - Problemas articulares
"""
@router.post("/")
def chat_with_ai(chat_request: ChatRequest, backend: BackendService = Depends(get_service_instance)):
    return { "response": response, "generation": "00:01:00.0" }
#--------------------------------------------------------------------------------------------------
