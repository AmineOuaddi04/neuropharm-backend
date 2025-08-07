from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import require_admin
from app.services.admin_service import assign_patient_to_medico
from app.db.schemas import AssignInput

router = APIRouter()

@router.post("/assign_patient", tags=["Admin"])
def assign_patient(
    input: AssignInput,
    current_user: dict = Depends(require_admin)
):
    return assign_patient_to_medico(input.medico_id, input.paciente_id)
