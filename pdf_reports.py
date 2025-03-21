import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import HRFlowable

class NumberedCanvas(canvas.Canvas):
    """Canvas that adds page numbers and footers to each page"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        # Draw footer
        self.setFont("Helvetica", 9)
        self.drawCentredString(
            300, 30,
            "Vehicle Management System | Care Services Consortium"
        )
        # Draw page numbers
        self.drawRightString(
            550, 30,
            f"Page {self._pageNumber} of {page_count}"
        )

def generate_vehicle_report(df, report_title, report_type="vehicle_type"):
    """
    Generate a PDF report for vehicles
    
    Parameters:
    - df: DataFrame containing vehicle data
    - report_title: Title for the report (e.g., vehicle type or usage category)
    - report_type: Type of report ('vehicle_type' or 'usage')
    
    Returns:
    - pdf_file: Path to the generated PDF file
    """
    # Create PDF file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_file = f"{report_type}_report_{timestamp}.pdf"
    
    # Create document
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Container for PDF elements
    elements = []

    # Add logo and title in a table
    logo_path = "logo.png"  # Make sure to have the logo file
    
    title_data = [[
        Paragraph(
            f'<font name="Helvetica-Bold" size="18" color="darkgreen">{report_title} Vehicles Report</font>',
            getSampleStyleSheet()['Normal']
        ),
        Image(logo_path, width=100, height=40) if os.path.exists(logo_path) else ''
    ]]
    
    title_table = Table(title_data, colWidths=[350, 100])
    title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 20))

    # Add timestamp in grey
    timestamp_text = f'Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}'
    elements.append(Paragraph(
        f'<font name="Helvetica" size="9" color="grey">{timestamp_text}</font>',
        getSampleStyleSheet()['Normal']
    ))
    elements.append(Spacer(1, 10))

    # Add total count
    total_vehicles = len(df)
    elements.append(Paragraph(
        f'<font name="Helvetica-Bold" size="12">Total Vehicles: {total_vehicles}</font>',
        getSampleStyleSheet()['Normal']
    ))
    elements.append(Spacer(1, 10))

    # Add green horizontal divider
    elements.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.darkgreen,
        spaceBefore=1,
        spaceAfter=15
    ))

    # Create table with enhanced styling
    if not df.empty:
        table_data = [df.columns.tolist()] + df.values.tolist()
        table = Table(table_data)
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Content styling
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            # Grid with light grey borders
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            # Alternating row colors
            *[('BACKGROUND', (0, i), (-1, i), colors.lightgrey if i % 2 == 0 else colors.white) 
              for i in range(1, len(table_data))]
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph(
            f'<font name="Helvetica-Italic" size="12">No vehicles found for this report.</font>',
            getSampleStyleSheet()['Normal']
        ))
    
    # Build PDF with page numbers and footer
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    return pdf_file
