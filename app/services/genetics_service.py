from app.db.supabase import supabase
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
import openai
import os
from fpdf import FPDF
import tempfile

# Configurar la API key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_vcf_with_ia(vcf_content: bytes) -> str:
    prompt = (
        "Eres un asistente IA clínico experto en farmacogenómica. Analiza este archivo VCF de perfil genético "
        "de un paciente y genera un informe clínico breve para el médico: "
        "\n---\n"
        f"{vcf_content.decode(errors='ignore')[:5000]}\n---\n"
        "Resume las variantes principales y posibles relevancias clínicas en menos de 350 palabras."
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # Usa gpt-4o si tienes acceso, si no pon "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "Eres un asistente IA experto en farmacogenómica clínica."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error al analizar archivo VCF con IA: {e}"

def _generar_pdf_informe_ia(texto, filename_pdf="informe_temp.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, texto)
    # Guardar temporalmente el PDF
    temp_pdf_path = os.path.join(tempfile.gettempdir(), filename_pdf)
    pdf.output(temp_pdf_path)
    with open(temp_pdf_path, "rb") as f:
        pdf_bytes = f.read()
    os.remove(temp_pdf_path)
    return pdf_bytes

def upload_genetic_file(file, paciente_id):
    content = file.file.read()
    filename = f"{paciente_id}/{uuid4()}.vcf"
    # Subir archivo VCF a Supabase Storage
    res = supabase.storage.from_("vcf-files").upload(filename, content)
    if hasattr(res, "error") and res.error:
        raise Exception(res.error)
    # Guardar perfil genético
    data = {
        "user_id": paciente_id,
        "archivo_vcf": filename,
        "fecha_subida": datetime.utcnow().isoformat()
    }
    result = supabase.table("genetic_profiles").insert(data).execute()
    profile = result.data[0]
    # Analizar automáticamente y crear informe en la tabla informes
    ia_report = analyze_vcf_with_ia(content)

    # ----------- GENERAR PDF CON FPDF -----------------
    filename_pdf = f"{paciente_id}/{uuid4()}.pdf"
    pdf_bytes = _generar_pdf_informe_ia(ia_report, "informe_temp.pdf")
    # Subir PDF a Supabase Storage (bucket: reportes)
    res_pdf = supabase.storage.from_("reportes").upload(filename_pdf, pdf_bytes)
    if hasattr(res_pdf, "error") and res_pdf.error:
        archivo_pdf = None
    else:
        archivo_pdf = filename_pdf

    # --------------------------------------------------
    supabase.table("informes").insert({
        "user_id": paciente_id,
        "descripcion": "Informe automático generado por IA tras subida de perfil genético.",
        "status": "completado",
        "created_at": datetime.utcnow().isoformat(),
        "fecha_generado": datetime.utcnow().isoformat(),
        "archivo_pdf": archivo_pdf,   # <- GUARDAMOS LA RUTA DEL PDF
        "contenido": ia_report
    }).execute()
    return profile

def get_my_genetic_files(user):
    res = supabase.table("genetic_profiles").select("*").eq("user_id", user["id"]).order("fecha_subida", desc=True).execute()
    return res.data or []

def get_genetic_file_detail(id, user):
    res = supabase.table("genetic_profiles").select("*").eq("id", id).single().execute()
    file = res.data
    if not file or (file["user_id"] != user["id"] and user["rol"] != "medico"):
        raise HTTPException(status_code=403, detail="Sin acceso a este archivo")
    return file
