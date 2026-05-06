import json
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import cm

def generate_pdf():
    # 1. Read bloque_firmado.json
    try:
        with open("aspr_cebada/bloque_firmado.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: aspr_cebada/bloque_firmado.json no encontrado.")
        return

    bloque = data["bloque"]
    sha256_hash = data["hash_sha256"]
    signature = data["signature_ed25519"]
    fingerprint = data["public_key_fingerprint"]

    # 2. Setup PDF document
    filename = "aspr_cebada/certificado_cebada_001.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=22,
        alignment=1, # Center
        spaceAfter=20,
        textColor=colors.HexColor("#1B4F72")
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#2E86C1"),
        spaceBefore=15,
        spaceAfter=10
    )

    content_list = []

    # Title
    content_list.append(Paragraph("Certificado de Agricultura Regenerativa — Cebada Bonaerense", title_style))
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,
        spaceAfter=20,
        textColor=colors.HexColor("#5D6D7E")
    )
    content_list.append(Paragraph("Rotación verificada · Suelo cubierto · Trazabilidad de origen", subtitle_style))
    content_list.append(Spacer(1, 0.5*cm))

    # Producer Data Section
    content_list.append(Paragraph("Datos del Productor y Ubicación", section_style))
    producer_data = [
        ["Partido:", bloque.get("partido", "N/A")],
        ["Coordenadas:", f"Lat: {bloque['lat']}, Lon: {bloque['lon']}"],
        ["Campaña:", bloque["campana"]],
        ["Cultivo:", bloque["cultivo"]],
        ["Certificación:", bloque.get("certificacion_tipo", "Agricultura Regenerativa")]
    ]
    t1 = Table(producer_data, colWidths=[4*cm, 10*cm])
    t1.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    content_list.append(t1)

    # Satellite Indices Section
    content_list.append(Paragraph("Buenas Prácticas Agrícolas Verificadas", section_style))
    
    indices = bloque["indices"]
    verif = bloque["verificaciones"]
    
    # Table headers and data
    table_data = [
        ["Práctica / Indicador", "Valor", "Estado"],
        ["Rotación (NDVI)", f"{indices['NDVI']}", verif.get("rotacion_verificada", verif.get("cultivo_activo", "N/A"))],
        ["Cobertura (BSI)", f"{indices['BSI']}", verif["calidad_suelo"]],
        ["Hidratación (NDMI)", f"{indices['NDMI']}", verif["estres_hidrico"]]
    ]
    
    t2 = Table(table_data, colWidths=[6*cm, 4*cm, 4*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#D4E6F1")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    
    # Color coding the status
    for i in range(1, 4):
        status = table_data[i][2]
        if status == "PASS":
            t2.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.darkgreen)]))
        elif status == "ALERTA":
            t2.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.orange)]))
        elif status == "FAIL":
            t2.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.red)]))

    content_list.append(t2)
    
    # Market Value Section
    if "valor_mercado" in bloque:
        content_list.append(Paragraph("Valor de mercado", section_style))
        for item in bloque["valor_mercado"]:
            content_list.append(Paragraph(f"• {item}", styles['Normal']))
    
    content_list.append(Spacer(1, 1*cm))

    # Verification and Security Section
    content_list.append(Paragraph("Seguridad Digital y Verificación", section_style))
    security_data = [
        ["Hash SHA256:", Paragraph(sha256_hash, styles['Code'])],
        ["Fingerprint Clave Pública:", Paragraph(fingerprint, styles['Code'])],
        ["Firma Ed25519 (fragmento):", Paragraph(signature[:40] + "...", styles['Code'])],
        ["Timestamp UTC:", bloque["timestamp_utc"]]
    ]
    t3 = Table(security_data, colWidths=[5*cm, 10*cm])
    t3.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    content_list.append(t3)

    # 4. Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(sha256_hash)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_path = "aspr_cebada/qr_verification.png"
    qr_img.save(qr_path)

    # Add QR code and Footer
    content_list.append(Spacer(1, 1*cm))
    
    # Footer
    footer_text = "Compatible con programas: Heineken Brewing a Better World · AB InBev 100+ · Carlsberg Zero Carbon"
    content_list.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.grey)))
    
    img = Image(qr_path, 3*cm, 3*cm)
    img.hAlign = 'RIGHT'
    content_list.append(img)
    content_list.append(Paragraph("Escanee para verificar la integridad del bloque", ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, alignment=2)))


    # Build PDF
    doc.build(content_list)
    print(f"Certificado generado exitosamente: {filename}")

if __name__ == "__main__":
    generate_pdf()
