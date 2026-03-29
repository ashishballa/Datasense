import os
import io
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from google import genai

CERT_STEPS = [
    {
        "id": "property",
        "title": "Property Information",
        "fields": [
            {"key": "address", "label": "Property Address", "type": "text"},
            {"key": "year_built", "label": "Year Built", "type": "number"},
            {"key": "square_feet", "label": "Square Footage", "type": "number"},
            {"key": "property_type", "label": "Property Type", "type": "select",
             "options": ["Single Family", "Condo", "Townhouse", "Multi-Family"]},
        ]
    },
    {
        "id": "coverage",
        "title": "Coverage Needs",
        "fields": [
            {"key": "dwelling_coverage", "label": "Dwelling Coverage ($)", "type": "number"},
            {"key": "personal_property", "label": "Personal Property Coverage ($)", "type": "number"},
            {"key": "liability", "label": "Liability Coverage ($)", "type": "number"},
            {"key": "deductible", "label": "Deductible ($)", "type": "select",
             "options": ["500", "1000", "2500", "5000"]},
        ]
    },
    {
        "id": "risk",
        "title": "Risk Assessment",
        "fields": [
            {"key": "roof_age", "label": "Roof Age (years)", "type": "number"},
            {"key": "security_system", "label": "Security System Installed?", "type": "boolean"},
            {"key": "smoke_detectors", "label": "Smoke Detectors?", "type": "boolean"},
            {"key": "flood_zone", "label": "In Flood Zone?", "type": "boolean"},
            {"key": "prior_claims", "label": "Prior Claims (last 5 years)", "type": "number"},
        ]
    },
    {
        "id": "owner",
        "title": "Owner Information",
        "fields": [
            {"key": "owner_name", "label": "Full Name", "type": "text"},
            {"key": "email", "label": "Email", "type": "email"},
            {"key": "phone", "label": "Phone", "type": "tel"},
            {"key": "occupancy", "label": "Occupancy", "type": "select",
             "options": ["Owner-Occupied", "Rental", "Seasonal/Vacation"]},
        ]
    },
]

def get_steps():
    return CERT_STEPS

def autofill_from_chat(chat_history: list[dict]) -> dict:
    """Use Gemini to extract form field values from chat conversation."""
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    fields = [f["key"] for step in CERT_STEPS for f in step["fields"]]
    conversation = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in chat_history
    )
    prompt = f"""Extract home insurance form data from this conversation.
Return a JSON object with only the fields you can confidently extract.
Fields: {fields}

Conversation:
{conversation}

Return only valid JSON, no explanation."""

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    import json, re
    text = resp.text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}

def generate_certificate(form_data: dict, username: str) -> bytes:
    """Generate a PDF certificate from completed form data."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], textColor=colors.HexColor("#1a3c5e"))
    elements = []

    elements.append(Paragraph("Home Insurance Certificate", title_style))
    elements.append(Paragraph(f"Issued to: {form_data.get('owner_name', username)}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {date.today().isoformat()}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    for step in CERT_STEPS:
        elements.append(Paragraph(step["title"], styles["Heading2"]))
        rows = []
        for field in step["fields"]:
            val = form_data.get(field["key"], "—")
            if isinstance(val, bool):
                val = "Yes" if val else "No"
            rows.append([field["label"], str(val)])
        table = Table(rows, colWidths=[250, 250])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    doc.build(elements)
    return buf.getvalue()
