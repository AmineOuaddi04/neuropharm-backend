from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

origins = [
    "http://localhost:8030",  # Vite
    # Agrega aquí dominios reales en producción si hace falta
]


def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
