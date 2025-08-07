from fastapi import APIRouter, Depends
from app.core.auth import require_medico, get_current_user
from app.services.ai_service import analyze_vcf_file, get_mis_evaluaciones, get_evaluaciones_paciente
from app.db.schemas import AnalyzeInput, EvaluacionOut
from app.db.supabase import supabase
import os
import openai
from pydantic import BaseModel

router = APIRouter()

@router.post("/analyze", response_model=EvaluacionOut)
def analyze(
    input: AnalyzeInput,
    current_user: dict = Depends(require_medico)
):
    return analyze_vcf_file(current_user, input)

@router.get("/mine", response_model=list[EvaluacionOut])
def get_my_evaluations(current_user: dict = Depends(get_current_user)):
    return get_mis_evaluaciones(current_user)

@router.get("/patient/{paciente_id}", response_model=list[EvaluacionOut])
def get_patient_evaluations(
    paciente_id: str,
    current_user: dict = Depends(require_medico)
):
    return get_evaluaciones_paciente(current_user, paciente_id)

from pydantic import BaseModel
from fastapi import APIRouter, Depends
import os
import openai
from app.core.auth import get_current_user
from app.db.supabase import supabase

router = APIRouter()

# 1. Define el modelo para el body
class IAContextualInput(BaseModel):
    paciente_id: str
    pregunta: str

# 2. Cambia la función para aceptar el modelo como parámetro
@router.post("/ai/contextual")
def ia_contextual(input: IAContextualInput, user=Depends(get_current_user)):
    paciente_id = input.paciente_id
    pregunta = input.pregunta

    # Busca el informe genético más reciente de este paciente
    perfil = supabase.table("genetic_profiles")\
        .select("*").eq("user_id", paciente_id)\
        .order("fecha_subida", desc=True).limit(1).execute().data
    resumen_ia = ""
    if perfil:
        informe = supabase.table("informes")\
            .select("*").eq("user_id", paciente_id)\
            .order("fecha_generado", desc=True).limit(1).execute().data
        if informe:
            resumen_ia = informe[0].get("contenido", "")

    contexto = (
        f"Paciente ID: {paciente_id}\n"
        f"Resumen IA genética: {resumen_ia if resumen_ia else 'Sin informe genético disponible.'}"
    )

    prompt = (
        f"{contexto}\n\n"
        f"Pregunta clínica: {pregunta}\n\n"
        "INSTRUCCIONES IMPORTANTES PARA LA IA:\n"
        "- Responde SOLO para médicos especialistas, nunca para pacientes.\n"
        "- NO digas nunca 'consulta a un médico' ni 'acude a un especialista', ya eres el experto.\n"
        "- Sé preciso, técnico y basado en la evidencia farmacogenómica.\n"
        "- Relaciona variantes genéticas, SNPs o genes del paciente con guías farmacogenómicas (CPIC, FDA, etc) cuando sea posible.\n"
        "- Si falta información clínica/genética relevante, dilo pero orienta profesionalmente según lo disponible.\n"
        "- Sé breve, conciso y directo."
    )

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.chat.completions.create(
        model="gpt-4o",  # Usa gpt-4o (si tu cuenta lo permite)
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres una IA clínica de soporte experto en farmacogenómica, solo para médicos. "
                    "Nunca respondas que consulten a otro médico. Da respuestas precisas, técnicas, útiles y basadas en guías farmacogenómicas. "
                    "Si falta información, explica qué datos serían necesarios, pero orienta con lo disponible."
                )
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.2
    )

    return {"respuesta": response.choices[0].message.content.strip()}
