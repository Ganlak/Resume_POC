"""
Export Service
Generate PDF and CSV reports for candidate analysis results
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import io
from datetime import datetime
from typing import List, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.utils.helpers import format_percentage
from app.config import settings


# ==========================================
# PDF Report Generator
# ==========================================

class PDFReportGenerator:
    """
    Generate professional PDF reports for candidate analysis
    """
    
    def __init__(self):
        """Initialize PDF generator with styles"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#555555'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Candidate name style
        self.styles.add(ParagraphStyle(
            name='CandidateName',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            fontName='Helvetica'
        ))
    
    def generate_report(
        self,
        job_info: Dict,
        candidates_data: List[Dict],
        output_path: str = None
    ) -> io.BytesIO:
        """
        Generate complete PDF report
        
        Args:
            job_info: Job information dictionary
            candidates_data: List of candidate data with analysis
            output_path: Optional file path to save PDF
            
        Returns:
            BytesIO buffer containing PDF
        """
        # Create buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        if output_path:
            doc = SimpleDocTemplate(output_path, pagesize=letter)
        else:
            doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Build story (content)
        story = []
        
        # Add title page
        story.extend(self._create_title_page(job_info, candidates_data))
        
        # Add summary page
        story.extend(self._create_summary_page(job_info, candidates_data))
        
        # Add candidate details
        story.extend(self._create_candidate_pages(candidates_data))
        
        # Build PDF
        doc.build(story)
        
        if not output_path:
            buffer.seek(0)
            return buffer
        
        return None
    
    def _create_title_page(self, job_info: Dict, candidates_data: List[Dict]) -> List:
        """Create title page"""
        elements = []
        
        # Add spacing from top
        elements.append(Spacer(1, 2*inch))
        
        # Title
        title = Paragraph(
            "Candidate Analysis Report",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Job title
        job_title = Paragraph(
            f"Position: {job_info['title']}",
            self.styles['CustomSubtitle']
        )
        elements.append(job_title)
        
        # Date and stats
        elements.append(Spacer(1, 0.5*inch))
        
        report_date = datetime.now().strftime("%B %d, %Y")
        candidate_count = len(candidates_data)
        avg_score = sum(c['analysis']['relevance_score'] for c in candidates_data) / candidate_count if candidate_count > 0 else 0
        
        info_text = f"""
        <para align=center>
        <b>Report Generated:</b> {report_date}<br/>
        <b>Total Candidates:</b> {candidate_count}<br/>
        <b>Average Relevance Score:</b> {avg_score:.1f}/100<br/>
        </para>
        """
        
        info_para = Paragraph(info_text, self.styles['CustomBody'])
        elements.append(info_para)
        
        # Footer
        elements.append(Spacer(1, 2*inch))
        footer_text = Paragraph(
            "Powered by Azure OpenAI GPT-4",
            self.styles['CustomBody']
        )
        elements.append(footer_text)
        
        # Page break
        elements.append(PageBreak())
        
        return elements
    
    def _create_summary_page(self, job_info: Dict, candidates_data: List[Dict]) -> List:
        """Create summary page with statistics"""
        elements = []
        
        # Section header
        header = Paragraph("Executive Summary", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 0.2*inch))
        
        # Job details
        job_header = Paragraph("Job Details", self.styles['CandidateName'])
        elements.append(job_header)
        
        job_desc = job_info['description'][:500] + "..." if len(job_info['description']) > 500 else job_info['description']
        job_para = Paragraph(job_desc, self.styles['CustomBody'])
        elements.append(job_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Statistics table
        stats_header = Paragraph("Analysis Statistics", self.styles['CandidateName'])
        elements.append(stats_header)
        elements.append(Spacer(1, 0.1*inch))
        
        candidate_count = len(candidates_data)
        avg_score = sum(c['analysis']['relevance_score'] for c in candidates_data) / candidate_count if candidate_count > 0 else 0
        
        high_score_count = sum(1 for c in candidates_data if c['analysis']['relevance_score'] >= 80)
        medium_score_count = sum(1 for c in candidates_data if 60 <= c['analysis']['relevance_score'] < 80)
        low_score_count = sum(1 for c in candidates_data if c['analysis']['relevance_score'] < 60)
        
        stats_data = [
            ['Metric', 'Value'],
            ['Total Candidates Analyzed', str(candidate_count)],
            ['Average Relevance Score', f'{avg_score:.1f}/100'],
            ['High Match (80-100)', str(high_score_count)],
            ['Medium Match (60-79)', str(medium_score_count)],
            ['Low Match (0-59)', str(low_score_count)],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Top candidates ranking
        ranking_header = Paragraph("Top Candidates Ranking", self.styles['CandidateName'])
        elements.append(ranking_header)
        elements.append(Spacer(1, 0.1*inch))
        
        # Sort candidates by score
        sorted_candidates = sorted(
            candidates_data,
            key=lambda x: x['analysis']['relevance_score'],
            reverse=True
        )
        
        ranking_data = [['Rank', 'Name', 'Email', 'Score']]
        
        for idx, candidate in enumerate(sorted_candidates[:10], 1):
            ranking_data.append([
                str(idx),
                candidate['name'],
                candidate.get('email', 'N/A'),
                f"{candidate['analysis']['relevance_score']:.1f}"
            ])
        
        ranking_table = Table(ranking_data, colWidths=[0.6*inch, 2*inch, 2.2*inch, 0.8*inch])
        ranking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(ranking_table)
        elements.append(PageBreak())
        
        return elements
    
    def _create_candidate_pages(self, candidates_data: List[Dict]) -> List:
        """Create detailed pages for each candidate"""
        elements = []
        
        # Sort candidates by score
        sorted_candidates = sorted(
            candidates_data,
            key=lambda x: x['analysis']['relevance_score'],
            reverse=True
        )
        
        for idx, candidate in enumerate(sorted_candidates, 1):
            analysis = candidate['analysis']
            
            # Candidate header
            header_text = f"Candidate #{idx}: {candidate['name']}"
            header = Paragraph(header_text, self.styles['SectionHeader'])
            elements.append(header)
            elements.append(Spacer(1, 0.1*inch))
            
            # Contact info
            contact_info = f"<b>Email:</b> {candidate.get('email', 'N/A')}"
            if candidate.get('phone'):
                contact_info += f" | <b>Phone:</b> {candidate.get('phone')}"
            
            contact_para = Paragraph(contact_info, self.styles['CustomBody'])
            elements.append(contact_para)
            elements.append(Spacer(1, 0.2*inch))
            
            # Score visualization
            score = analysis['relevance_score']
            score_color = self._get_score_color(score)
            
            score_text = f"""
            <para align=center>
            <font size=24 color={score_color}><b>{score:.1f}/100</b></font><br/>
            <font size=12>Relevance Score</font>
            </para>
            """
            score_para = Paragraph(score_text, self.styles['CustomBody'])
            elements.append(score_para)
            elements.append(Spacer(1, 0.2*inch))
            
            # Skills table
            skills_data = [
                ['Matched Skills', 'Missing Skills'],
                [
                    ', '.join(analysis['matched_skills']) if analysis['matched_skills'] else 'None',
                    ', '.join(analysis['missing_skills']) if analysis['missing_skills'] else 'None'
                ]
            ]
            
            skills_table = Table(skills_data, colWidths=[2.8*inch, 2.8*inch])
            skills_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('PADDING', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(skills_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Feedback section
            feedback_header = Paragraph("AI Analysis Feedback", self.styles['CandidateName'])
            elements.append(feedback_header)
            
            feedback_para = Paragraph(analysis['feedback'], self.styles['CustomBody'])
            elements.append(feedback_para)
            elements.append(Spacer(1, 0.2*inch))
            
            # Additional metrics
            if analysis.get('experience_match') or analysis.get('education_match'):
                metrics_header = Paragraph("Additional Metrics", self.styles['CandidateName'])
                elements.append(metrics_header)
                
                metrics_text = ""
                if analysis.get('experience_match'):
                    metrics_text += f"<b>Experience Match:</b> {analysis['experience_match']:.0f}%<br/>"
                if analysis.get('education_match'):
                    metrics_text += f"<b>Education Match:</b> {analysis['education_match']:.0f}%"
                
                metrics_para = Paragraph(metrics_text, self.styles['CustomBody'])
                elements.append(metrics_para)
            
            # Page break after each candidate (except last)
            if idx < len(sorted_candidates):
                elements.append(PageBreak())
        
        return elements
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on score"""
        if score >= 80:
            return '#28a745'  # Green
        elif score >= 60:
            return '#ffc107'  # Yellow
        else:
            return '#dc3545'  # Red


# ==========================================
# Export Functions
# ==========================================

def generate_pdf_report(
    job_info: Dict,
    candidates_data: List[Dict],
    output_path: str = None
) -> io.BytesIO:
    """
    Generate PDF report
    
    Args:
        job_info: Job information
        candidates_data: List of candidates with analysis
        output_path: Optional file path to save
        
    Returns:
        BytesIO buffer or None if saved to file
    """
    generator = PDFReportGenerator()
    return generator.generate_report(job_info, candidates_data, output_path)


# ==========================================
# Test Function
# ==========================================

if __name__ == "__main__":
    """Test PDF generation"""
    
    print("=" * 60)
    print("PDF Export Service Test")
    print("=" * 60)
    print("\nThis module is tested through the Streamlit UI.")
    print("Navigate to 'Export Data' page to test PDF generation.")
    print("=" * 60)