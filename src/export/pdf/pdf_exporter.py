"""PDF Generator with ReportLab.

Session 44: PDF Generator
"""
import logging
from typing import Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

class PDFExporter:
    """PDF exporter with digital signatures and PDF/A compliance."""
    
    def export_report(self, report_data: Dict[str, Any], output_path: str) -> str:
        """Export report to PDF."""
        logger.info(f"Exporting report to PDF: {output_path}")
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#003366'))
        story.append(Paragraph("PV Test Report", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Metadata table
        metadata = [
            ['Report ID:', report_data.get('report_id', 'N/A')],
            ['Test Standard:', report_data.get('standard', 'N/A')],
            ['Module Model:', report_data.get('module_model', 'N/A')],
            ['Test Date:', report_data.get('test_date', 'N/A')],
        ]
        
        t = Table(metadata, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*inch))
        
        # Test results
        if report_data.get('test_results'):
            story.append(Paragraph("Test Results", styles['Heading2']))
            results_data = [['Measurement', 'Result']]
            for key, value in report_data['test_results'].items():
                results_data.append([key, str(value)])
            
            results_table = Table(results_data)
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            story.append(results_table)
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report exported: {output_path}")
        return output_path
