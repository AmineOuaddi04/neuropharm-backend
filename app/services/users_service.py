from app.db.supabase import supabase
from app.core.security import hash_password, verify_password, create_access_token
from app.db.schemas import UserCreate, UserLogin
from fastapi import HTTPException, status

def create_user(user: UserCreate):
    # Check if email exists
    exists = supabase.table("users").select("id").eq("email", user.email).execute().data
    if exists:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    # Hash password
    hashed = hash_password(user.password)
    # Insert user
    new_user = {
        "nombre": user.nombre,
        "email": user.email,
        "password_hash": hashed,
        "rol": user.rol
    }
    res = supabase.table("users").insert(new_user).execute()
    # El cambio es aquí:
    if res.data is None or len(res.data) == 0:
        raise HTTPException(status_code=500, detail="Error creando usuario")
    return res.data[0]

def authenticate_user(login: UserLogin):
    user = supabase.table("users").select("*").eq("email", login.email).single().execute().data
    if not user or not verify_password(login.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o password incorrectos")
    return user

def create_jwt_for_user(user):
    token = create_access_token({"id": user["id"], "rol": user["rol"]})
    return token

def get_all_patients():
    res = supabase.table("users").select("id, nombre, email, rol, created_at").eq("rol", "paciente").execute()
    return res.data or []
