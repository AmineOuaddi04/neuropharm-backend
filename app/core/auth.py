from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token
from app.db.supabase import supabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("id")
    try:
        user = supabase.table("users").select("*").eq("id", user_id).single().execute().data
    except Exception:
        raise HTTPException(status_code=500, detail="Error consultando usuario en Supabase")
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# ---- Roles ----

def require_medico(current_user: dict = Depends(get_current_user)):
    if current_user["rol"] != "medico":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para médicos",
        )
    return current_user

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["rol"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para administrador",
        )
    return current_user

def require_paciente(current_user: dict = Depends(get_current_user)):
    if current_user["rol"] != "paciente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para pacientes",
        )
    return current_user
