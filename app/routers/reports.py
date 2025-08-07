from fastapi import APIRouter, Depends, HTTPException, Response
from app.core.auth import require_medico, get_current_user
from app.services.reports_service import generate_report_pdf
from app.db.supabase import supabase
import os
from fastapi.responses import FileResponse, StreamingResponse
import io


router = APIRouter()

@router.get("/generate", tags=["Reports"])
def generate_report(paciente_id: str, evaluacion_id: str, current_user: dict = Depends(require_medico)):
    try:
        data = generate_report_pdf(paciente_id, evaluacion_id, current_user)
        return {"detail": "Informe generado correctamente", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/mine")
def get_my_reports(current_user: dict = Depends(get_current_user)):
    # Busca informes donde user_id == id del usuario autenticado
    res = supabase.table("informes").select("*").eq("user_id", current_user["id"]).order("fecha_generado", desc=True).execute()
    return res.data or []


@router.get("/download/{id}")
def download_report(id: str, current_user: dict = Depends(get_current_user)):
    # 1. Busca el informe por ID
    res = supabase.table("informes").select("*").eq("id", id).single().execute()
    report = res.data

    if not report:
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    # 2. Permitir acceso al propio paciente O a un médico asignado
    es_paciente = str(report["user_id"]).strip() == str(current_user["id"]).strip()
    es_medico = current_user.get("rol") == "medico"

    autorizado = es_paciente

    # Si es médico, comprobar relación médico-paciente
    if es_medico and not autorizado:
        relaciones = supabase.table("medicos_pacientes") \
            .select("*") \
            .eq("medico_id", current_user["id"]) \
            .eq("paciente_id", report["user_id"]) \
            .eq("status", "activo") \
            .execute().data
        autorizado = bool(relaciones)

    if not autorizado:
        raise HTTPException(status_code=403, detail="No tienes permiso para este informe")

    # 3. Descarga el archivo PDF del bucket Supabase
    ruta_pdf = report.get("archivo_pdf")
    if not ruta_pdf:
        raise HTTPException(status_code=404, detail="El informe no tiene PDF generado")

    try:
        file_data = supabase.storage.from_("reportes").download(ruta_pdf)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"No se pudo descargar: {str(e)}")

    filename = os.path.basename(ruta_pdf)
    from fastapi.responses import StreamingResponse
    import io

    return StreamingResponse(
        io.BytesIO(file_data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
    
@router.get("/paciente/{paciente_id}")
def get_informes_paciente(paciente_id: str, current_user: dict = Depends(get_current_user)):
    """
    Devuelve todos los informes IA de un paciente, accesible por médicos asignados, el propio paciente y admin.
    """
    is_admin = current_user["rol"] == "admin"
    is_self = current_user["id"] == paciente_id
    if not (is_admin or is_self):
        if current_user["rol"] == "medico":
            # Verifica relación médico-paciente
            rel = supabase.table("medicos_pacientes") \
                .select("*") \
                .eq("medico_id", current_user["id"]) \
                .eq("paciente_id", paciente_id) \
                .eq("status", "activo") \
                .execute().data
            if not rel:
                raise HTTPException(status_code=403, detail="No autorizado")
        else:
            raise HTTPException(status_code=403, detail="No autorizado")
    informes = supabase.table("informes").select("*").eq("user_id", paciente_id).order("fecha_generado", desc=True).execute()
    if hasattr(informes, "data"):
        return informes.data or []
    return []