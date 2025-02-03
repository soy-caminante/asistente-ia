from backend.service        import *
from frontend.routers       import patients, chat
from fastapi                import FastAPI, Request, Depends
from fastapi.responses      import RedirectResponse
from fastapi.staticfiles    import StaticFiles
from fastapi.templating     import Jinja2Templates
#--------------------------------------------------------------------------------------------------

app = FastAPI()
#--------------------------------------------------------------------------------------------------

# Routers
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(chat.router,     prefix="/api/chat",     tags=["chat"])
#--------------------------------------------------------------------------------------------------

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
#--------------------------------------------------------------------------------------------------

# Configurar plantillas
templates = Jinja2Templates(directory="templates")
#--------------------------------------------------------------------------------------------------

@app.get("/")
def home(request: Request, backend: BackendService = Depends(get_service_instance)):
    return templates.TemplateResponse("index.html", {"request": request})
#--------------------------------------------------------------------------------------------------

@app.get("/patient/{id}")
def patient_detail(request: Request, id: int,  backend: BackendService = Depends(get_service_instance)):
    return templates.TemplateResponse("patient.html", {"request": request, "patient_id": id})
#--------------------------------------------------------------------------------------------------

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
#--------------------------------------------------------------------------------------------------

# Redirigir favicon.ico a evitar errores
@app.get("/favicon.ico")
def favicon():
    return RedirectResponse(url="/static/images/favicon.ico")
#--------------------------------------------------------------------------------------------------



