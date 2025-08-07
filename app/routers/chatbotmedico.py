from fastapi import APIRouter, Depends, HTTPException, Body
from app.core.auth import get_current_user
from app.db.supabase import supabase
import openai
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
openai.api_key = os.getenv("OPENAI_API_KEY")

@router.post("/chat")
def chat_with_ia_medico(
    mensaje: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]

    genetica = (
        supabase.table("genetic_profiles")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    informes = (
        supabase.table("informes")
        .select("*")
        .eq("user_id", user_id)
        .order("fecha_generado", desc=True)
        .limit(3)
        .execute()
        .data
    )

    prompt = (
        "Eres un asistente IA especializado en farmacogenómica clínica dirigido a profesionales de la salud. "
        "Responde con detalle técnico, citas de evidencia científica y posibles interpretaciones genéticas. "
        "Nunca hagas diagnósticos ni prescribas tratamientos, solo proporciona apoyo informativo y sugerencias basadas en la literatura. "
        f"Datos genéticos del paciente: {genetica}. Informes previos: {informes}.\n"
        f"Consulta del médico: {mensaje}\n"
        "Respuesta del asistente:"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente IA experto en farmacogenómica clínica para médicos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
        )
        respuesta = response.choices[0].message.content.strip()
        supabase.table("chat_histories").insert({
            "user_id": user_id,
            "mensaje": mensaje,
            "respuesta": respuesta
        }).execute()
        return {"respuesta": respuesta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error IA: {e}")

@router.post("/chat_paciente")
def chat_ia_paciente(
    paciente_id: str = Body(..., embed=True),
    mensaje: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    # 1. Cargar datos básicos del usuario/paciente
    user_res = supabase.table("users").select("*").eq("id", paciente_id).single().execute()
    datos_usuario = user_res.data if user_res.data else {}

    # 2. Perfiles genéticos
    perfiles_gen = (
        supabase.table("genetic_profiles")
        .select("*")
        .eq("user_id", paciente_id)
        .execute()
        .data
    ) or []

    # 3. Informes
    informes = (
        supabase.table("informes")
        .select("*")
        .eq("user_id", paciente_id)
        .order("fecha_generado", desc=True)
        .limit(3)
        .execute()
        .data
    ) or []

    # 4. Prompt con todo junto
    prompt = (
        f"Eres un asistente IA clínico para médicos. "
        f"Datos del paciente: {datos_usuario}. "
        f"Perfiles genéticos: {perfiles_gen}. "
        f"Últimos informes: {informes}. "
        f"Consulta del médico: {mensaje}\n"
        "Respuesta del asistente:"
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente IA clínico experto en farmacogenómica para médicos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
        )
        respuesta = response.choices[0].message.content.strip()
        supabase.table("chat_histories").insert({
            "user_id": current_user["id"],
            "paciente_id": paciente_id,
            "mensaje": mensaje,
            "respuesta": respuesta
        }).execute()
        return {"respuesta": respuesta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error IA: {e}")
