from app.db.supabase import supabase

def medico_tiene_paciente(medico_id: str, paciente_id: str) -> bool:
    res = supabase.table("medicos_pacientes").select("id").eq("medico_id", medico_id).eq("paciente_id", paciente_id).execute()
    return bool(res.data)
