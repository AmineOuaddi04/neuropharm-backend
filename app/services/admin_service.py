from app.db.supabase import supabase

def assign_patient_to_medico(medico_id: str, paciente_id: str):
    # Comprueba si ya existe la asignación para evitar duplicados (opcional)
    exists = supabase.table("medicos_pacientes") \
        .select("id") \
        .eq("medico_id", medico_id) \
        .eq("paciente_id", paciente_id) \
        .execute()
    if exists.data and len(exists.data) > 0:
        return {"message": "El paciente ya está asignado a este médico"}

    res = supabase.table("medicos_pacientes").insert({
        "medico_id": medico_id,
        "paciente_id": paciente_id,
    }).execute()
    if hasattr(res, "error") and res.error:
        raise Exception(res.error)
    return {"message": "Paciente asignado correctamente"}

def assign_patient_to_medico(medico_id: str, paciente_id: str):
    # Comprueba si ya existe la asignación para evitar duplicados (opcional)
    exists = supabase.table("medicos_pacientes") \
        .select("id") \
        .eq("medico_id", medico_id) \
        .eq("paciente_id", paciente_id) \
        .execute()
    if exists.data and len(exists.data) > 0:
        return {"message": "El paciente ya está asignado a este médico"}

    res = supabase.table("medicos_pacientes").insert({
        "medico_id": medico_id,
        "paciente_id": paciente_id,
    }).execute()
    if hasattr(res, "error") and res.error:
        raise Exception(res.error)
    return {"message": "Paciente asignado correctamente"}
