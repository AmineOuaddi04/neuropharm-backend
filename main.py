from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, genetics, admin, ai, reports, chatbot, chatbotmedico

from app.core.cors import setup_cors
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="NeuroPharm-AI Backend")

origins = [
    "http://localhost:8030",  # Vite frontend
    # Añade aquí dominios de prod si hace falta
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # O ["*"] en dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Rutas y routers ----

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(genetics.router, prefix="/genetics", tags=["Genetics"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(ai.router, prefix="/ai", tags=["AI"])
app.include_router(reports.router, prefix="/reports")  # <-- <---
app.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(chatbotmedico.router, prefix="/chatbotmedico", tags=["chatbotmedico"])
app.include_router(reports.router, prefix="/informes", tags=["Informes"])

@app.get("/")
def read_root():
    return {"message": "¡NeuroPharm-AI Backend listo!"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="NeuroPharm-AI Backend",
        version="0.1.0",
        description="API de NeuroPharm-AI",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema




app.openapi = custom_openapi
