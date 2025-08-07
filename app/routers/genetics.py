from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from app.core.auth import require_medico, get_current_user
from app.services import genetics_service
from app.db.schemas import GeneticProfileOut
from app.services.medicos_service import medico_tiene_paciente

router = APIRouter()

@router.post("/upload", response_model=GeneticProfileOut)
def upload_genetic_file(
    file: UploadFile = File(...),
    paciente_id: str = Form(...),
    current_user: dict = Depends(require_medico)
):
    # Solo médicos con ese paciente pueden subir
    if not medico_tiene_paciente(current_user["id"], paciente_id):
        raise HTTPException(status_code=403, detail="No puedes subir archivos para este paciente")
    return genetics_service.upload_genetic_file(file, paciente_id)

@router.get("/mine", response_model=list[GeneticProfileOut])
def get_my_genetic_files(current_user: dict = Depends(get_current_user)):
    return genetics_service.get_my_genetic_files(current_user)

@router.get("/{id}", response_model=GeneticProfileOut)
def get_genetic_file_detail(id: str, current_user: dict = Depends(get_current_user)):
    return genetics_service.get_genetic_file_detail(id, current_user)
