from app.backend.service    import *
from fastapi                import APIRouter, HTTPException, Depends
from pydantic               import BaseModel
#--------------------------------------------------------------------------------------------------

router = APIRouter()
#--------------------------------------------------------------------------------------------------

class ChatRequest(BaseModel):
    ref_id:     str
    question:   str
#--------------------------------------------------------------------------------------------------

@router.post("/")
def chat_with_ai(chat_request: ChatRequest, backend: BackendService = Depends(get_service_instance)):
    response, gen_time = backend.chat(chat_request.ref_id, chat_request.question)

    if response is None:
        return { "response": "El paciente no existe", "generation": gen_time }
    return { "response": response, "generation": gen_time }
#--------------------------------------------------------------------------------------------------
