from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    nombre: Optional[str] = None  # ← HAZLO OPCIONAL
    email: EmailStr
    rol: Literal['paciente', 'medico', 'admin'] = 'paciente'

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: UUID
    created_at: Optional[datetime] = None  # ← HAZLO OPCIONAL

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    id: Optional[str] = None
    rol: Optional[str] = None

class GeneticProfileOut(BaseModel):
    id: str
    user_id: str
    archivo_vcf: str
    fecha_subida: datetime

class AssignInput(BaseModel):
    medico_id: str
    paciente_id: str

class AnalyzeInput(BaseModel):
    paciente_id: str
    genetic_profile_id: str

class EvaluacionOut(BaseModel):
    id: str
    user_id: str
    resultado_json: dict
    fecha_evaluacion: str

class AnalyzeInput(BaseModel):
    paciente_id: str
    genetic_profile_id: str

class EvaluacionOut(BaseModel):
    id: str
    user_id: str
    resultado_json: dict
    fecha_evaluacion: str

