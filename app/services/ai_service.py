from app.db.supabase import supabase
from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
from app.services.medicos_service import medico_tiene_paciente

def analyze_vcf_file(current_user, input):
    # 1. Comprueba si el médico está asignado al paciente
    if not medico_tiene_paciente(current_user["id"], input.paciente_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a este paciente")

    # 2. Busca el archivo genético en la tabla genetic_profiles
    profile_res = supabase.table("genetic_profiles") \
        .select("*") \
        .eq("id", input.genetic_profile_id) \
        .single() \
        .execute()
    profile = profile_res.data

    if not profile or profile["user_id"] != input.paciente_id:
        raise HTTPException(status_code=404, detail="Archivo genético no válido o no pertenece al paciente")

    # 3. Descarga el archivo VCF desde Supabase Storage
    try:
        file_res = supabase.storage.from_("vcf-files").download(profile["archivo_vcf"])
        vcf_content = file_res.decode("utf-8") if hasattr(file_res, "decode") else file_res.text
    except Exception as e:
        raise HTTPException(status_code=500, detail="No se pudo descargar el archivo VCF")

    # 4. Llama a OpenAI o IA (aquí simulado)
    # Aquí pones la llamada real a la IA usando openai.ChatCompletion.create(...)
    simulated_result = {
        "medicamentos_no_recomendados": ["ibuprofeno"],
        "riesgos": ["Riesgo aumentado de reacciones adversas con AINEs"],
        "comentario_ia": "El paciente tiene una variante CYP2C9 que reduce el metabolismo de ibuprofeno."
    }
    resultado_json = simulated_result

    # 5. Guarda la evaluación en la tabla evaluaciones_ia
    data = {
        "id": str(uuid4()),
        "user_id": input.paciente_id,
        "resultado_json": resultado_json,
        "fecha_evaluacion": datetime.utcnow().isoformat()
    }
    res = supabase.table("evaluaciones_ia").insert(data).execute()
    if hasattr(res, "error") and res.error:
        raise HTTPException(status_code=500, detail=f"Error al guardar la evaluación: {res.error}")

    # Devuelve el objeto insertado
    return res.data[0]

def get_mis_evaluaciones(user):
    res = supabase.table("evaluaciones_ia").select("*").eq("user_id", user["id"]).order("fecha_evaluacion", desc=True).execute()
    return res.data or []

def get_evaluaciones_paciente(current_user, paciente_id):
    if not medico_tiene_paciente(current_user["id"], paciente_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a este paciente")
    res = supabase.table("evaluaciones_ia").select("*").eq("user_id", paciente_id).order("fecha_evaluacion", desc=True).execute()
    return res.data or []
