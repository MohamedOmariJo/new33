"""
=============================================================================
📄 مولد PDF احترافي - بدون اعتماد على خطوط عربية
=============================================================================
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import List, Dict, Optional
import io
from datetime import datetime

from config.settings import Config
from utils.logger import logger


# ──────────────────────────────────────────────────────────────────
#  ألوان الكرات حسب النطاق
# ──────────────────────────────────────────────────────────────────
def _ball_color(num: int) -> colors.HexColor:
    if num <= 8:   return colors.HexColor('#ef4444')   # أحمر
    if num <= 16:  return colors.HexColor('#f97316')   # برتقالي
    if num <= 24:  return colors.HexColor('#3b82f6')   # أزرق
    return         colors.HexColor('#8b5cf6')           # بنفسجي


class PDFGenerator:
    """مولد PDF احترافي"""

    @staticmethod
    def create_ticket_pdf(
        tickets: List[List[int]],
        metadata: Optional[Dict] = None,
        design: str = 'professional'
    ) -> io.BytesIO:
        op_id = logger.start_operation('pdf_generation', {'tickets_count': len(tickets)})
        try:
            buffer = io.BytesIO()
            PDFGenerator._build_pdf(buffer, tickets, metadata)
            logger.end_operation(op_id, 'completed', {'pdf_size': buffer.getbuffer().nbytes})
            return buffer
        except Exception as e:
            logger.end_operation(op_id, 'failed', {'error': str(e)})
            raise

    @staticmethod
    def _build_pdf(buffer: io.BytesIO, tickets: List[List[int]], metadata: Optional[Dict]):
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm,   bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()

        # ── أنماط نصية (بالإنجليزية لضمان العرض الصحيح)
        s_title = ParagraphStyle('T', parent=styles['Title'],
            fontSize=22, textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER, spaceAfter=6)

        s_sub = ParagraphStyle('S', parent=styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER, spaceAfter=20)

        s_ticket_hdr = ParagraphStyle('TH', parent=styles['Normal'],
            fontSize=12, textColor=colors.HexColor('#1e40af'),
            spaceAfter=6, spaceBefore=14)

        s_info = ParagraphStyle('I', parent=styles['Normal'],
            fontSize=9, textColor=colors.HexColor('#374151'),
            spaceAfter=4)

        s_footer = ParagraphStyle('F', parent=styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#9ca3af'),
            alignment=TA_CENTER, spaceBefore=30)

        story = []

        # ── رأس الصفحة
        story.append(Paragraph("Jordan Lottery AI Pro", s_title))
        strategy = (metadata or {}).get('strategy', 'Smart Generation')
        story.append(Paragraph(
            f"Date: {datetime.now().strftime('%Y-%m-%d  %H:%M')}  |  "
            f"Tickets: {len(tickets)}  |  Strategy: {strategy}  |  "
            f"Version: {Config.APP_VERSION}",
            s_sub
        ))

        # ── خط فاصل
        story.append(Table([['']], colWidths=[17*cm],
            style=[('LINEABOVE', (0,0), (-1,-1), 1.5, colors.HexColor('#3b82f6'))]))
        story.append(Spacer(1, 0.4*cm))

        # ── التذاكر
        for idx, ticket in enumerate(tickets, 1):
            nums = sorted(ticket)
            ticket_sum   = sum(nums)
            odd_count    = sum(1 for n in nums if n % 2 != 0)
            even_count   = len(nums) - odd_count
            consec_count = sum(1 for i in range(len(nums)-1) if nums[i+1]-nums[i]==1)

            # عنوان التذكرة
            story.append(Paragraph(f"Ticket #{idx}", s_ticket_hdr))

            # ── كرات الأرقام
            balls = []
            ball_styles = []
            for j, num in enumerate(nums):
                p = Paragraph(
                    f"<font size='13' color='white'><b>{num}</b></font>",
                    ParagraphStyle(f'B{idx}{j}', parent=styles['Normal'], alignment=TA_CENTER)
                )
                balls.append(p)
                ball_styles.append(('BACKGROUND', (j,0), (j,0), _ball_color(num)))
                ball_styles.append(('ROUNDEDCORNERS', [4], (j,0), (j,0)))

            ball_table = Table([balls], colWidths=[1.8*cm]*len(balls))
            ball_table.setStyle(TableStyle([
                ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white]),
            ] + ball_styles))

            story.append(ball_table)
            story.append(Spacer(1, 0.2*cm))

            # ── بيانات التذكرة
            info_rows = [
                ['Sum', str(ticket_sum),
                 'Odd / Even', f'{odd_count} / {even_count}',
                 'Consecutive', str(consec_count)]
            ]
            info_table = Table(info_rows,
                colWidths=[2.5*cm, 2*cm, 2.5*cm, 2*cm, 2.8*cm, 2*cm])
            info_table.setStyle(TableStyle([
                ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
                ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTNAME',   (2,0), (2,-1), 'Helvetica-Bold'),
                ('FONTNAME',   (4,0), (4,-1), 'Helvetica-Bold'),
                ('TEXTCOLOR',  (0,0), (0,-1), colors.HexColor('#6b7280')),
                ('TEXTCOLOR',  (2,0), (2,-1), colors.HexColor('#6b7280')),
                ('TEXTCOLOR',  (4,0), (4,-1), colors.HexColor('#6b7280')),
                ('TEXTCOLOR',  (1,0), (1,-1), colors.HexColor('#1e40af')),
                ('TEXTCOLOR',  (3,0), (3,-1), colors.HexColor('#1e40af')),
                ('TEXTCOLOR',  (5,0), (5,-1), colors.HexColor('#1e40af')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor('#e5e7eb')),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.6*cm))

            # فاصل صفحة كل 6 تذاكر
            if idx % 6 == 0 and idx < len(tickets):
                story.append(PageBreak())

        # ── تذييل
        story.append(Table([['']], colWidths=[17*cm],
            style=[('LINEABOVE', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb'))]))
        story.append(Paragraph(
            "Generated by Jordan Lottery AI Pro v8.0  |  For entertainment purposes only  |  (c) 2026",
            s_footer
        ))

        doc.build(story)
        buffer.seek(0)

    # ── متوافق مع النداءات القديمة
    @staticmethod
    def _create_professional_pdf(buffer, tickets, metadata):
        PDFGenerator._build_pdf(buffer, tickets, metadata)
        return buffer

    @staticmethod
    def _create_minimal_pdf(buffer, tickets, metadata):
        PDFGenerator._build_pdf(buffer, tickets, metadata)
        return buffer

    @staticmethod
    def _create_colorful_pdf(buffer, tickets, metadata):
        PDFGenerator._build_pdf(buffer, tickets, metadata)
        return buffer

    @staticmethod
    def _get_number_color(num: int) -> colors.HexColor:
        return _ball_color(num)
