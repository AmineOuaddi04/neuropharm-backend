# app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException, Body
from app.db.schemas import UserCreate, UserLogin, UserOut
from app.services import users_service
from app.core.auth import get_current_user, require_medico, require_admin
from app.db.supabase import supabase
import openai
import os
from datetime import datetime

# Asegúrate de tener OPENAI_API_KEY en tus variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()


# --------- Auth: Registro y Login ---------
@router.post("/register", response_model=UserOut)
def register(user: UserCreate):
    """
    Registra un nuevo usuario (paciente o admin por defecto).
    """
    return users_service.create_user(user)


@router.post("/login")
def login(login_data: UserLogin):
    """
    Autentica a un usuario y retorna un JWT.
    """
    user = users_service.authenticate_user(login_data)
    token = users_service.create_jwt_for_user(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], "rol": user["rol"]}
    }


# --------- Perfil propio ---------
@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    """
    Obtiene información del usuario autenticado.
    """
    return current_user


@router.patch("/me", response_model=UserOut, tags=["Profile"])
def update_my_profile(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Permite al usuario actualizar nombre, apellidos o email.
    """
    updates = {k: data[k] for k in ("nombre", "apellidos", "email") if k in data}
    if not updates:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    res = supabase.table("users") \
        .update(updates) \
        .eq("id", current_user["id"]) \
        .execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data[0]


@router.patch("/change_password")
def change_password(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Permite al usuario cambiar su contraseña, validando la antigua.
    """
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Faltan datos")
    # Verifica la contraseña antigua
    valid = users_service.authenticate_user(
        UserLogin(email=current_user["email"], password=old_password)
    )
    if not valid:
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
    users_service.update_password(current_user["id"], new_password)
    return {"detail": "Contraseña cambiada exitosamente"}


# --------- Usuarios médicos y pacientes ---------
@router.post("/create_medico", response_model=UserOut)
def create_medico(
    user: UserCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Admin crea un usuario con rol de médico.
    """
    user.rol = "medico"
    return users_service.create_user(user)


@router.get("/all", response_model=list[UserOut])
def get_all_patients(current_user: dict = Depends(require_medico)):
    """
    Lista todos los pacientes registrados (solo para médicos).
    """
    return users_service.get_all_patients()


@router.get("/mis_pacientes", response_model=list[UserOut])
def get_my_patients(current_user: dict = Depends(require_medico)):
    """
    Retorna los pacientes activos asignados al médico.
    """
    rels = supabase.table("medicos_pacientes") \
        .select("paciente_id") \
        .eq("medico_id", current_user["id"]) \
        .eq("status", "activo") \
        .execute().data
    if not rels:
        return []
    ids = [r["paciente_id"] for r in rels]
    return supabase.table("users") \
        .select("*") \
        .in_("id", ids) \
        .execute().data


@router.get("/mis_medicos", response_model=list[UserOut])
def get_my_doctors(current_user: dict = Depends(get_current_user)):
    """
    Retorna los médicos activos asignados al paciente.
    """
    if current_user["rol"] != "paciente":
        raise HTTPException(status_code=403, detail="Solo pacientes pueden consultar sus médicos.")
    rels = supabase.table("medicos_pacientes") \
        .select("medico_id") \
        .eq("paciente_id", current_user["id"]) \
        .eq("status", "activo") \
        .execute().data
    if not rels:
        return []
    ids = [r["medico_id"] for r in rels]
    return supabase.table("users") \
        .select("id", "email", "rol") \
        .in_("id", ids) \
        .execute().data


# --------- Actualizar usuario/paciente ---------
@router.patch("/users/{paciente_id}/update", response_model=UserOut)
def update_paciente(
    paciente_id: str,
    fields: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza datos de usuario/paciente.
    - Solo admin o médico asignado.
    - Si incluye 'geneticProfile', guarda perfil y lanza análisis IA.
    """
    # Verificar existencia
    paciente = supabase.table("users") \
        .select("*").eq("id", paciente_id).single().execute().data
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Permisos
    is_admin = current_user["rol"] == "admin"
    is_medico = current_user["rol"] == "medico"
    if is_medico:
        rel = supabase.table("medicos_pacientes") \
            .select("*") \
            .eq("medico_id", current_user["id"]) \
            .eq("paciente_id", paciente_id) \
            .eq("status", "activo") \
            .execute().data
        if not rel:
            raise HTTPException(status_code=403, detail="No autorizado")
    elif not is_admin:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Actualizar usuario
    res = supabase.table("users") \
        .update(fields) \
        .eq("id", paciente_id) \
        .execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    updated = res.data[0]

    # Si se actualiza perfil genético, guardarlo y analizar
    genetic = fields.get("geneticProfile")
    if genetic:
        supabase.table("genetic_profiles").upsert({
            "user_id": paciente_id,
            "profile": genetic,
            "updated_at": datetime.utcnow().isoformat()
        }).execute()

        # Analizar con IA
        prompt = (
            "Eres un experto en farmacogenómica clínica. "
            f"Analiza este perfil genético y sugiere riesgos o recomendaciones:\n{genetic}"
        )
        try:
            ia_resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Asistente IA farmacogenómico."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
            ).choices[0].message.content.strip()
        except Exception as e:
            ia_resp = f"Error IA: {e}"

        supabase.table("informes").insert({
            "user_id": paciente_id,
            "contenido": ia_resp,
            "tipo": "análisis automático",
            "fecha_generado": datetime.utcnow().isoformat()
        }).execute()

    return updated


# --------- Obtener usuario por ID ---------
@router.get("/users/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Recupera un usuario si es admin, él mismo, o médico asignado.
    """
    is_admin = current_user["rol"] == "admin"
    is_self = current_user["id"] == user_id
    if not (is_admin or is_self):
        if current_user["rol"] == "medico":
            rel = supabase.table("medicos_pacientes") \
                .select("*") \
                .eq("medico_id", current_user["id"]) \
                .eq("paciente_id", user_id) \
                .eq("status", "activo") \
                .execute().data
            if not rel:
                raise HTTPException(status_code=403, detail="No autorizado")
        else:
            raise HTTPException(status_code=403, detail="No autorizado")

    data = supabase.table("users") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute().data
    if not data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return data


# --------- Búsqueda de usuarios (solo Admin) ---------
@router.get("/users/search", response_model=list[UserOut])
def search_users(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Admin puede buscar usuarios globalmente por nombre.
    """
    if current_user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden buscar usuarios")
    return supabase.table("users") \
        .select("*") \
        .ilike("nombre", f"%{query}%") \
        .execute().data
