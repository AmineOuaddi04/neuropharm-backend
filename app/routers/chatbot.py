from fastapi import APIRouter, Depends, HTTPException, Body
from app.core.auth import get_current_user
from app.db.supabase import supabase
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Nueva forma de inicializar el cliente
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/chat")
def chat_with_ia(
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
        "Eres un asistente IA de salud farmacogenómica. "
        "No des diagnósticos ni medicaciones. Si la duda es clínica, sugiere consultar con su médico. "
        f"Perfil genético: {genetica}. Últimos informes: {informes}.\n"
        f"Paciente pregunta: {mensaje}\n"
        "Asistente responde:"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",   # O "gpt-4o" si tienes acceso
            messages=[
                {"role": "system", "content": "Eres un asistente IA de salud farmacogenómica."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
        )
        respuesta = completion.choices[0].message.content.strip()
        supabase.table("chat_histories").insert({
            "user_id": user_id,
            "mensaje": mensaje,
            "respuesta": respuesta
        }).execute()
        return {"respuesta": respuesta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error IA: {e}")
