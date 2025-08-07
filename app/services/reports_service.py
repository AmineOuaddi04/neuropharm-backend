from fpdf import FPDF
from app.db.supabase import supabase
from datetime import datetime
from uuid import uuid4

def generate_report_pdf(paciente_id, evaluacion_id, medico):
    # 1. Traer datos del paciente
    paciente = supabase.table("users").select("*").eq("id", paciente_id).single().execute().data
    if not paciente:
        raise Exception("Paciente no encontrado")

    # 2. Traer la evaluación
    evaluacion = supabase.table("evaluaciones_ia").select("*").eq("id", evaluacion_id).single().execute().data
    if not evaluacion:
        raise Exception("Evaluación no encontrada")

    # 3. Construir el PDF (tú puedes customizarlo)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "INFORME GENÉTICO PERSONALIZADO", 0, 1, "C")

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Paciente: {paciente['nombre']}  |  Email: {paciente['email']}", 0, 1)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
    pdf.cell(0, 10, f"Elaborado por: Dr/a. {medico['nombre']} ({medico['email']})", 0, 1)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Resultados IA:", 0, 1)

    resultado = evaluacion["resultado_json"]
    pdf.set_font("Arial", "", 12)
    for key, value in resultado.items():
        if isinstance(value, list):
            value = ", ".join(value)
        pdf.cell(0, 10, f"{key}: {value}", 0, 1)

    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Este informe es confidencial y generado automáticamente.", 0, 1)

    # 4. Guardar temporal y subir a Supabase Storage
    pdf_file = pdf.output(dest="S").encode("latin1")
    filename = f"{paciente_id}/{uuid4()}.pdf"
    supabase.storage.from_("reportes").upload(filename, pdf_file)

    # 5. Guardar URL en tabla informes
    data = {
        "id": str(uuid4()),
        "user_id": paciente_id,
        "archivo_pdf": filename,
        "fecha_generado": datetime.utcnow().isoformat()
    }
    supabase.table("informes").insert(data).execute()
    return data
