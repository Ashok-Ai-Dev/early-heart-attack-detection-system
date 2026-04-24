import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem

def generate_risk_report_pdf(data: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50, leftMargin=50,
        topMargin=50, bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=20,
        alignment=1 # Center
    )
    
    heading_style = ParagraphStyle(
        name='HeadingStyle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#374151'),
        spaceBefore=20,
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 8
    
    elements = []
    
    # 1. Header
    elements.append(Paragraph("CardioCare AI - Heart Risk Report", title_style))
    current_time = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    elements.append(Paragraph(f"<b>Date & Time:</b> {current_time}", normal_style))
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", color=colors.HexColor('#d1d5db'), thickness=1, spaceAfter=20))
    
    # 2. Patient Details
    elements.append(Paragraph("Patient Details", heading_style))
    
    patient_info = [
        f"<b>Name:</b> {data.get('name', 'Unknown')}",
        f"<b>Age:</b> {data.get('age', 'N/A')}",
        f"<b>Gender:</b> {'Male' if str(data.get('gender')) == '1' else 'Female'}",
        f"<b>Email:</b> {data.get('email', 'N/A')}"
    ]
    
    for info in patient_info:
        elements.append(Paragraph(info, normal_style))
        
    elements.append(Spacer(1, 15))
    
    # 3. Risk Analysis
    elements.append(Paragraph("Risk Analysis", heading_style))
    
    risk_level = data.get('risk_level', 'LOW')
    risk_prob = data.get('risk_percentage', 0)
    
    # Color coding based on risk level
    if risk_level == "HIGH":
        risk_color = colors.HexColor('#ef4444') # Red
    elif risk_level == "MEDIUM":
        risk_color = colors.HexColor('#f59e0b') # Yellow
    else:
        risk_color = colors.HexColor('#10b981') # Green
        
    risk_prob_style = ParagraphStyle(
        name='RiskProb',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=5
    )
    
    risk_level_style = ParagraphStyle(
        name='RiskLevel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=risk_color,
        spaceAfter=15
    )
    
    elements.append(Paragraph(f"<b>Risk Percentage:</b> {risk_prob}%", risk_prob_style))
    elements.append(Paragraph(f"<b>Risk Level:</b> {risk_level}", risk_level_style))
    
    # 4. Health Suggestions
    elements.append(Paragraph("Health Suggestions", heading_style))
    
    suggestions = data.get('suggestions', [])
    if not suggestions:
        suggestions = ["Maintain a healthy lifestyle."]
        
    list_items = []
    for sug in suggestions:
        list_items.append(ListItem(Paragraph(sug, normal_style)))
        
    elements.append(ListFlowable(
        list_items,
        bulletType='bullet',
        start='bulletchar',
        bulletFontName='Helvetica',
        bulletFontSize=11,
        leftIndent=20
    ))
    
    elements.append(Spacer(1, 40))
    elements.append(HRFlowable(width="100%", color=colors.HexColor('#d1d5db'), thickness=1, spaceAfter=20))
    
    # 5. Footer (Disclaimer)
    disclaimer_style = ParagraphStyle(
        name='Disclaimer',
        parent=styles['Italic'],
        fontSize=10,
        textColor=colors.HexColor('#6b7280'),
        alignment=1 # Center
    )
    elements.append(Paragraph("Disclaimer: This report is AI-generated and not a medical diagnosis. Please consult a healthcare professional for accurate medical advice.", disclaimer_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
