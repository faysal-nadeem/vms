import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
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
        self.setFont("Calibri", 7)
        self.drawCentredString(
            letter[0]/2, 15,
            "Vehicle Management System | Care Services Consortium"
        )
        # Draw page numbers
        self.drawRightString(
            letter[0]-72, 15,
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
    
    # Use landscape orientation for more width
    page_size = landscape(letter)
    
    # Create document with consistent margins
    margin = 72  # 1 inch margin
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=page_size,
        rightMargin=margin,
        leftMargin=margin,
        topMargin=24,    # 1/3 inch margin
        bottomMargin=24  # 1/3 inch margin
    )

    # Container for PDF elements
    elements = []

    # Add logo and title in a table - with full width
    logo_path = "/static/care_logo.png"  # Make sure to have the logo file
    
    # Calculate available width (page width minus margins)
    available_width = page_size[0] - (2 * margin)
    
    title_data = [[
        Paragraph(
            f'<font name="Helvetica-Bold" size="16" color="darkgreen">{report_title} Vehicles Report</font>',
            getSampleStyleSheet()['Normal']
        ),
        Image(logo_path, width=60, height=24) if os.path.exists(logo_path) else ''
    ]]
    
    # Use full available width for title table
    title_table = Table(title_data, colWidths=[available_width * 0.85, available_width * 0.15])
    title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 2))  # Minimal spacing

    # Add timestamp in grey
    timestamp_text = f'Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}'
    elements.append(Paragraph(
        f'<font name="Helvetica" size="7" color="grey">{timestamp_text}</font>',
        getSampleStyleSheet()['Normal']
    ))
    elements.append(Spacer(1, 2))  # Minimal spacing

    # Add total count - aligned left
    total_vehicles = len(df)
    elements.append(Paragraph(
        f'<font name="Helvetica-Bold" size="10">Total Vehicles: {total_vehicles}</font>',
        getSampleStyleSheet()['Normal']
    ))
    elements.append(Spacer(1, 2))  # Minimal spacing

    # Add green horizontal divider - full width
    elements.append(HRFlowable(
        width=available_width,  # Explicitly set to available width
        thickness=1,
        color=colors.darkgreen,
        spaceBefore=1,
        spaceAfter=5  # Minimal spacing
    ))

    # Create table with enhanced styling and calculate column widths
    if not df.empty:
        # Remove p_key column if it exists
        if 'p_key' in df.columns:
            df = df.drop(columns=['p_key'])
        
        # Add SR. column (serial number)
        df.insert(0, 'SR.', range(1, len(df) + 1))
        
        # Calculate appropriate column widths based on content and actual content length
        col_widths = []
        
        # Get max content length for each column to determine width
        max_lengths = {}
        for col in df.columns:
            if col == 'SR.':
                max_lengths[col] = 3  # SR. is always short
            else:
                # Convert all values to string and get the max length
                max_lengths[col] = max(
                    len(str(col)),  # Header length
                    df[col].astype(str).str.len().max() if len(df) > 0 else 0  # Max content length
                )
        
        # Total characters to distribute width
        total_chars = sum(max_lengths.values())
        
        # Calculate proportional widths - ensuring they sum to available_width
        total_width = 0
        for col in df.columns:
            if col == 'SR.':
                width = available_width * 0.05  # Fixed small width for SR.
            else:
                # Proportional width based on content length, with some minimum
                proportion = max(0.06, max_lengths[col] / total_chars)
                width = available_width * proportion
            
            col_widths.append(width)
            total_width += width
        
        # Adjust widths to exactly match available_width
        if total_width != available_width:
            scale_factor = available_width / total_width
            col_widths = [w * scale_factor for w in col_widths]
        
        # Create table with calculated widths - ensuring it's exactly available_width
        table_data = [df.columns.tolist()] + df.values.tolist()
        table = Table(table_data, colWidths=col_widths)
        
        # Apply table styling
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),  # Header font size
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),  # Header padding
            ('TOPPADDING', (0, 0), (-1, 0), 4),  # Header padding
            # Content styling
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),  # Content font size
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2),  # Minimal padding
            ('TOPPADDING', (0, 1), (-1, -1), 2),  # Minimal padding
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Center align SR. column
            ('ALIGN', (1, 0), (-1, 0), 'CENTER'),  # Center align headers
            # Different alignment based on column content
            *[('ALIGN', (i, 1), (i, -1), 'LEFT' if df.columns[i] in ['MAKE', 'MODEL', 'OWNER', 'USED_FOR', 'VEHICLE_TYPE'] else 'CENTER') 
              for i in range(1, len(df.columns))],
            # Grid with light grey borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),  # Thinner grid lines
            # Alternating row colors
            *[('BACKGROUND', (0, i), (-1, i), colors.lightgrey if i % 2 == 0 else colors.white) 
              for i in range(1, len(table_data))]
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph(
            f'<font name="Helvetica-Italic" size="8">No vehicles found for this report.</font>',
            getSampleStyleSheet()['Normal']
        ))
    
    # Build PDF with page numbers and footer
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    return pdf_file
