#!/usr/bin/env python3
"""
HTML to PDF Converter for CodeGates Reports
Pure Python implementation using ReportLab only
Generates PDFs that match the exact HTML theme, style, and data structure
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, white, red, green, orange, gray
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Frame, PageTemplate, HRFlowable
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib.units import cm
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab not available. Install with: pip install reportlab")


class HTMLToPDFConverter:
    """Convert HTML reports to PDFs with exact same theme, style, and data structure"""
    
    def __init__(self):
        self.styles = None
        self.custom_styles = {}
        
        if REPORTLAB_AVAILABLE:
            self._setup_reportlab_styles()
    
    def _setup_reportlab_styles(self):
        """Setup ReportLab styles to match HTML theme exactly"""
        self.styles = getSampleStyleSheet()
        
        # Custom styles matching HTML theme exactly
        self.custom_styles = {
            # Main title - matches HTML h1
            'MainTitle': ParagraphStyle(
                'MainTitle',
                parent=self.styles['Title'],
                fontSize=32,
                spaceAfter=30,
                textColor=HexColor('#1f2937'),
                alignment=TA_LEFT,
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderPadding=0,
                leftIndent=0
            ),
            
            # Report badge - matches HTML .report-badge
            'ReportBadge': ParagraphStyle(
                'ReportBadge',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=white,
                backColor=HexColor('#059669'),
                borderPadding=6,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                leftIndent=0,
                rightIndent=0
            ),
            
            # Subtitle - matches HTML subtitle
            'Subtitle': ParagraphStyle(
                'Subtitle',
                parent=self.styles['Normal'],
                fontSize=16,
                spaceAfter=20,
                textColor=HexColor('#2563eb'),
                alignment=TA_LEFT,
                fontName='Helvetica-Bold',
                leftIndent=0
            ),
            
            # Heading 2 - matches HTML h2
            'Heading2': ParagraphStyle(
                'Heading2',
                parent=self.styles['Heading2'],
                fontSize=24,
                spaceAfter=15,
                spaceBefore=40,
                textColor=HexColor('#1f2937'),
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderPadding=0,
                leftIndent=0
            ),
            
            # Heading 3 - matches HTML h3
            'Heading3': ParagraphStyle(
                'Heading3',
                parent=self.styles['Heading3'],
                fontSize=18,
                spaceAfter=10,
                spaceBefore=30,
                textColor=HexColor('#374151'),
                fontName='Helvetica-Bold',
                leftIndent=0
            ),
            
            # Category title - matches HTML .category-title
            'CategoryTitle': ParagraphStyle(
                'CategoryTitle',
                parent=self.styles['Heading3'],
                fontSize=20,
                spaceAfter=20,
                spaceBefore=25,
                textColor=HexColor('#1f2937'),
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderPadding=0,
                leftIndent=0
            ),
            
            # Normal text - matches HTML body
            'Normal': ParagraphStyle(
                'Normal',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                textColor=HexColor('#374151'),
                fontName='Helvetica',
                leftIndent=0
            ),
            
            # Compliance text - matches HTML compliance text
            'ComplianceText': ParagraphStyle(
                'ComplianceText',
                parent=self.styles['Normal'],
                fontSize=14,
                spaceAfter=5,
                textColor=HexColor('#1f2937'),
                fontName='Helvetica-Bold',
                leftIndent=0
            ),
            
            # Compliance explanation - matches HTML compliance explanation
            'ComplianceExplanation': ParagraphStyle(
                'ComplianceExplanation',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=20,
                textColor=HexColor('#6b7280'),
                fontName='Helvetica',
                leftIndent=0
            ),
            
            # Status styles - match HTML status classes exactly
            'StatusPass': ParagraphStyle(
                'StatusPass',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=HexColor('#059669'),
                backColor=HexColor('#ecfdf5'),
                borderPadding=4,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            ),
            'StatusFail': ParagraphStyle(
                'StatusFail',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=HexColor('#dc2626'),
                backColor=HexColor('#fef2f2'),
                borderPadding=4,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            ),
            'StatusWarning': ParagraphStyle(
                'StatusWarning',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=HexColor('#d97706'),
                backColor=HexColor('#fffbeb'),
                borderPadding=4,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            ),
            'StatusNotApplicable': ParagraphStyle(
                'StatusNotApplicable',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=HexColor('#6b7280'),
                backColor=HexColor('#f3f4f6'),
                borderPadding=4,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            ),
            
            # Footer - matches HTML footer
            'Footer': ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=0,
                textColor=HexColor('#6b7280'),
                fontName='Helvetica',
                alignment=TA_CENTER,
                leftIndent=0
            ),
            
            # Gate name - matches HTML gate names
            'GateName': ParagraphStyle(
                'GateName',
                parent=self.styles['Normal'],
                fontSize=12,
                spaceAfter=5,
                textColor=HexColor('#1f2937'),
                fontName='Helvetica-Bold',
                leftIndent=0
            ),
            
            # Evidence text - matches HTML evidence
            'EvidenceText': ParagraphStyle(
                'EvidenceText',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=5,
                textColor=HexColor('#374151'),
                fontName='Helvetica',
                leftIndent=0
            ),
            
            # Recommendation text - matches HTML recommendations
            'RecommendationText': ParagraphStyle(
                'RecommendationText',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=5,
                textColor=HexColor('#374151'),
                fontName='Helvetica',
                leftIndent=0
            ),
        }
    
    def generate_pdfs_from_html_reports(self, scan_results: Dict[str, Any], html_report_path: str, output_dir: str = "./reports") -> Dict[str, List[str]]:
        """
        Generate PDFs that match the exact HTML theme, style, and data structure
        
        Args:
            scan_results: The complete scan results dictionary
            html_report_path: Path to the generated HTML report
            output_dir: Directory to save PDF files
            
        Returns:
            Dictionary with 'summary' and 'gates' lists of generated PDF file paths
        """
        if not REPORTLAB_AVAILABLE:
            print("❌ Cannot generate PDFs: ReportLab not installed")
            return {"summary": [], "gates": []}
        
        # Create output directory
        pdf_dir = os.path.join(output_dir, "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        
        scan_id = scan_results.get("scan_id", "unknown")
        project_name = self._extract_project_name(scan_results.get("repository_url", ""))
        
        generated_pdfs = {"summary": [], "gates": []}
        
        # 1. Generate Summary PDF that matches HTML exactly
        if os.path.exists(html_report_path):
            summary_pdf_path = self._generate_summary_pdf_from_html(
                html_report_path, project_name, scan_id, pdf_dir, scan_results
            )
            if summary_pdf_path:
                generated_pdfs["summary"].append(summary_pdf_path)
                print(f"✅ Summary PDF generated from HTML: {os.path.basename(summary_pdf_path)}")
        
        # 2. Generate Individual Gate PDFs that match HTML theme
        gate_results = scan_results.get("gate_results", [])
        if not gate_results:
            gate_results = scan_results.get("gates", [])
        
        for gate in gate_results:
            gate_pdf_path = self._generate_gate_pdf_from_html(
                gate, scan_results, project_name, scan_id, pdf_dir
            )
            if gate_pdf_path:
                generated_pdfs["gates"].append(gate_pdf_path)
                gate_name = gate.get("gate", "unknown")
                print(f"✅ Gate PDF generated: {os.path.basename(gate_pdf_path)}")
        
        print(f"📄 Generated {len(generated_pdfs['summary'])} summary and {len(generated_pdfs['gates'])} individual gate PDFs")
        return generated_pdfs
    
    def _generate_summary_pdf_from_html(self, html_report_path: str, project_name: str, scan_id: str, output_dir: str, scan_results: Dict[str, Any]) -> Optional[str]:
        """Generate summary PDF that matches HTML theme and structure exactly"""
        
        filename = f"{project_name}-{scan_id}-summary.pdf"
        filepath = os.path.join(output_dir, filename)
        
        try:
            # Extract information from scan results (same as HTML)
            overall_score = scan_results.get("overall_score", 0.0)
            repository_url = scan_results.get("repository_url", "")
            branch = scan_results.get("branch", "")
            threshold = scan_results.get("threshold", 70)
            
            gate_results = scan_results.get("gate_results", [])
            if not gate_results:
                gate_results = scan_results.get("gates", [])
            
            # Calculate statistics (same as HTML)
            passed = len([g for g in gate_results if g.get("status") == "PASS"])
            failed = len([g for g in gate_results if g.get("status") == "FAIL"])
            warnings = len([g for g in gate_results if g.get("status") == "WARNING"])
            not_applicable = len([g for g in gate_results if g.get("status") == "NOT_APPLICABLE"])
            total_gates = len(gate_results)
            
            # Create PDF document with same layout as HTML
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # Title and Header (matches HTML exactly)
            app_id = self._extract_app_id(repository_url)
            project_display_name = f"{app_id} - {project_name} ({branch})"
            
            # Main title (matches HTML h1)
            story.append(Paragraph(project_display_name, self.custom_styles['MainTitle']))
            
            # Report badge (matches HTML .report-badge)
            story.append(Paragraph("Hybrid Validation Report", self.custom_styles['ReportBadge']))
            
            # Subtitle (matches HTML subtitle)
            story.append(Paragraph("Hard Gate Assessment Report", self.custom_styles['Subtitle']))
            story.append(Spacer(1, 20))
            
            # Executive Summary (matches HTML h2)
            story.append(Paragraph("Executive Summary", self.custom_styles['Heading2']))
            
            # Summary Statistics (matches HTML .summary-stats exactly)
            stats_data = [
                ['Total Gates Evaluated', str(total_gates)],
                ['Gates Met', str(passed)],
                ['Partially Met', str(warnings)],
                ['Not Met', str(failed)],
                ['Not Applicable', str(not_applicable)]
            ]
            
            # Create stats table with same styling as HTML
            stats_table = Table(stats_data, colWidths=[3*inch, 1*inch])
            stats_table.setStyle(TableStyle([
                # Background matches HTML .stat-card
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
                ('BACKGROUND', (1, 0), (1, -1), HexColor('#ffffff')),
                # Text colors match HTML
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
                ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#2563eb')),  # Numbers in blue like HTML
                # Alignment matches HTML
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                # Fonts match HTML
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, -1), 12),
                ('FONTSIZE', (1, 0), (1, -1), 16),  # Numbers larger like HTML
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                # Border matches HTML
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ]))
            
            story.append(stats_table)
            story.append(Spacer(1, 20))
            
            # Overall Compliance (matches HTML h3)
            story.append(Paragraph("Overall Compliance", self.custom_styles['Heading3']))
            
            # Compliance assessment (matches HTML exactly)
            if overall_score >= threshold:
                assessment = f"✅ PASS - Overall score of {overall_score:.1f}% meets threshold of {threshold}%"
            else:
                assessment = f"❌ FAIL - Overall score of {overall_score:.1f}% below threshold of {threshold}%"
            
            story.append(Paragraph(assessment, self.custom_styles['Normal']))
            story.append(Paragraph(f"{overall_score:.1f}% Hard Gates Compliance", self.custom_styles['ComplianceText']))
            story.append(Paragraph(f"Percentage calculated based on {total_gates} applicable gates (excluding {not_applicable} N/A gates)", self.custom_styles['ComplianceExplanation']))
            story.append(Spacer(1, 20))
            
            # Gate Applicability Summary (matches HTML)
            applicability_summary = scan_results.get("applicability_summary", {})
            if applicability_summary:
                story.append(Paragraph("Gate Applicability", self.custom_styles['Heading3']))
                
                applicable_gates = applicability_summary.get("applicable_gates", [])
                not_applicable_gates = applicability_summary.get("not_applicable_gates", [])
                
                if applicable_gates:
                    story.append(Paragraph(f"Applicable Gates ({len(applicable_gates)})", self.custom_styles['Heading3']))
                    for gate in applicable_gates:
                        gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
                        story.append(Paragraph(f"• {gate_name}", self.custom_styles['Normal']))
                    story.append(Spacer(1, 10))
                
                if not_applicable_gates:
                    story.append(Paragraph(f"Not Applicable Gates ({len(not_applicable_gates)})", self.custom_styles['Heading3']))
                    for gate in not_applicable_gates:
                        gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
                        story.append(Paragraph(f"• {gate_name}", self.custom_styles['Normal']))
                    story.append(Spacer(1, 10))
            
            # Hard Gates Analysis (matches HTML h2)
            story.append(Paragraph("Hard Gates Analysis", self.custom_styles['Heading2']))
            
            # Group gates by categories (matches HTML exactly)
            predefined_categories = {
                'Alerting': ['ALERTING_ACTIONABLE'],
                'Auditability': ['STRUCTURED_LOGS', 'AVOID_LOGGING_SECRETS', 'AUDIT_TRAIL', 'CORRELATION_ID', 'LOG_API_CALLS', 'LOG_APPLICATION_MESSAGES', 'UI_ERRORS'],
                'Availability': ['RETRY_LOGIC', 'TIMEOUTS', 'THROTTLING', 'CIRCUIT_BREAKERS', 'AUTO_SCALE'],
                'Error Handling': ['ERROR_LOGS', 'HTTP_CODES', 'UI_ERROR_TOOLS'],
                'Testing': ['AUTOMATED_TESTS']
            }
            
            # Generate category sections (matches HTML exactly)
            for category_name, gate_names in predefined_categories.items():
                category_gates = [g for g in gate_results if g.get("gate") in gate_names]
                
                if category_gates:
                    # Category title (matches HTML .category-title)
                    story.append(Paragraph(category_name, self.custom_styles['CategoryTitle']))
                    
                    # Create gates table (matches HTML table exactly)
                    gates_data = [['Gate #', 'Practice', 'Status', 'Evidence', 'Recommendation']]
                    
                    for gate in category_gates:
                        gate_name = gate.get("gate", "Unknown")
                        display_name = gate.get("display_name", gate_name)
                        status = gate.get("status", "UNKNOWN")
                        
                        # Get status info (matches HTML)
                        status_info = self._get_status_info_from_new_data(status, gate)
                        
                        # Format evidence (matches HTML)
                        evidence = self._format_evidence_from_new_data(gate)
                        
                        # Get recommendation (matches HTML)
                        recommendation = self._get_recommendation_from_new_data(gate)
                        
                        gates_data.append([
                            str(self._get_gate_number(gate_name)),
                            display_name,
                            status_info.get('display', status),
                            evidence,
                            recommendation
                        ])
                    
                    # Table styling matches HTML exactly
                    gates_table = Table(gates_data, colWidths=[0.5*inch, 2*inch, 1*inch, 1.5*inch, 1.5*inch])
                    gates_table.setStyle(TableStyle([
                        # Header styling matches HTML th
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2563eb')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        # Row styling matches HTML tr
                        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
                        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                    ]))
                    
                    story.append(gates_table)
                    story.append(Spacer(1, 15))
                    
                    # Add detailed gate analysis for each gate in this category
                    story.append(Paragraph("Detailed Gate Analysis", self.custom_styles['Heading3']))
                    
                    for gate in category_gates:
                        story.append(Spacer(1, 10))
                        
                        # Gate header with status
                        gate_name = gate.get("gate", "Unknown")
                        display_name = gate.get("display_name", gate_name)
                        status = gate.get("status", "UNKNOWN")
                        score = gate.get("score", 0.0)
                        
                        # Gate title with status badge
                        gate_title = f"🔒 {display_name}"
                        story.append(Paragraph(gate_title, self.custom_styles['GateName']))
                        
                        # Status and score
                        status_style = self._get_status_style_for_reportlab(status)
                        story.append(Paragraph(f"Status: {status} | Score: {score:.1f}%", status_style))
                        story.append(Spacer(1, 5))
                        
                        # Gate description
                        description = gate.get("description", "")
                        if description:
                            story.append(Paragraph("Description:", self.custom_styles['Normal']))
                            story.append(Paragraph(description, self.custom_styles['Normal']))
                            story.append(Spacer(1, 5))
                        
                        # Gate metrics table
                        gate_metrics_data = [
                            ['Category', gate.get("category", "")],
                            ['Priority', gate.get("priority", "")],
                            ['Patterns Used', str(gate.get("patterns_used", 0))],
                            ['Matches Found', str(gate.get("matches_found", 0))],
                            ['Relevant Files', str(gate.get("relevant_files", 0))]
                        ]
                        
                        gate_metrics_table = Table(gate_metrics_data, colWidths=[1.5*inch, 4.5*inch])
                        gate_metrics_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
                            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                        ]))
                        
                        story.append(gate_metrics_table)
                        story.append(Spacer(1, 5))
                        
                        # Evidence and matches
                        matches = gate.get("matches", [])
                        if matches:
                            story.append(Paragraph("Evidence & Matches:", self.custom_styles['Normal']))
                            
                            # Create matches table (limited to first 5 for summary)
                            matches_data = [['File', 'Line', 'Pattern', 'Context']]
                            
                            for match in matches[:5]:  # Limit to first 5 matches in summary
                                file_path = match.get("file_path", "")
                                line_number = match.get("line_number", "")
                                pattern = match.get("pattern", "")
                                context = match.get("context", "")
                                
                                # Truncate long paths and context
                                if len(file_path) > 30:
                                    file_path = "..." + file_path[-27:]
                                if len(context) > 40:
                                    context = context[:37] + "..."
                                
                                matches_data.append([file_path, line_number, pattern, context])
                            
                            if len(matches) > 5:
                                matches_data.append([f"... and {len(matches) - 5} more matches", "", "", ""])
                            
                            matches_table = Table(matches_data, colWidths=[1.2*inch, 0.4*inch, 1.2*inch, 2.2*inch])
                            matches_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#374151')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, -1), 7),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
                                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                            ]))
                            
                            story.append(matches_table)
                        else:
                            story.append(Paragraph("Evidence & Matches: No matches found for this gate.", self.custom_styles['Normal']))
                        
                        story.append(Spacer(1, 5))
                        
                        # Validation evidence
                        validation_sources = gate.get("validation_sources", {})
                        if validation_sources:
                            story.append(Paragraph("Validation Evidence:", self.custom_styles['Normal']))
                            
                            evidence_data = []
                            
                            # LLM Patterns
                            llm_patterns = validation_sources.get("llm_patterns", {})
                            if llm_patterns:
                                evidence_data.append(['LLM Patterns', f"{llm_patterns.get('count', 0)} patterns, {llm_patterns.get('matches', 0)} matches"])
                            
                            # Static Patterns
                            static_patterns = validation_sources.get("static_patterns", {})
                            if static_patterns:
                                evidence_data.append(['Static Patterns', f"{static_patterns.get('count', 0)} patterns, {static_patterns.get('matches', 0)} matches"])
                            
                            # Enhanced Data
                            enhanced_data = gate.get("enhanced_data", {})
                            if enhanced_data:
                                confidence = enhanced_data.get("confidence_score", 0)
                                coverage = enhanced_data.get("coverage_percentage", 0)
                                technologies = enhanced_data.get("technology_detected", [])
                                evidence_data.append(['Enhanced Analysis', f"Confidence: {confidence:.2f}, Coverage: {coverage:.1f}%, Tech: {', '.join(technologies)}"])
                            
                            if evidence_data:
                                evidence_table = Table(evidence_data, colWidths=[1.5*inch, 4.5*inch])
                                evidence_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
                                    ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                                ]))
                                
                                story.append(evidence_table)
                        
                        story.append(Spacer(1, 5))
                        
                        # AI Recommendations
                        recommendation = gate.get("llm_recommendation", "")
                        if recommendation:
                            story.append(Paragraph("AI Recommendations:", self.custom_styles['Normal']))
                            # Truncate long recommendations for summary
                            if len(recommendation) > 200:
                                recommendation = recommendation[:197] + "..."
                            story.append(Paragraph(recommendation, self.custom_styles['RecommendationText']))
                        
                        story.append(Spacer(1, 10))
                        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e5e7eb'), spaceAfter=10))
                    
                else:
                    # Empty category (matches HTML)
                    story.append(Paragraph(category_name, self.custom_styles['CategoryTitle']))
                    story.append(Paragraph("No gates in this category were evaluated for this codebase.", self.custom_styles['Normal']))
                    story.append(Spacer(1, 15))
            
            # Footer (matches HTML footer exactly)
            story.append(Spacer(1, 30))
            story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb'), spaceAfter=20))
            story.append(Paragraph(f"Hard Gate Assessment Hybrid Validation Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.custom_styles['Footer']))
            
            # Build PDF
            doc.build(story)
            return filepath
            
        except Exception as e:
            print(f"❌ Failed to generate summary PDF from HTML: {e}")
            return None
    
    def _generate_gate_pdf_from_html(self, gate: Dict[str, Any], scan_results: Dict[str, Any], 
                                   project_name: str, scan_id: str, output_dir: str) -> Optional[str]:
        """Generate individual gate PDF that matches HTML theme exactly"""
        
        gate_name = gate.get("gate", "unknown_gate")
        # Clean gate name for filename
        safe_gate_name = re.sub(r'[^a-zA-Z0-9_-]', '_', gate_name).lower()
        
        filename = f"{project_name}-{scan_id}-{safe_gate_name}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        try:
            # Generate individual gate PDF content using same theme as HTML
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # Gate header (matches HTML theme)
            display_name = gate.get("display_name", gate_name)
            status = gate.get("status", "UNKNOWN")
            score = gate.get("score", 0.0)
            
            # Title (matches HTML theme)
            story.append(Paragraph(f"🔒 {display_name}", self.custom_styles['MainTitle']))
            story.append(Paragraph("CodeGates Security Gate Analysis", self.custom_styles['Subtitle']))
            story.append(Spacer(1, 20))
            
            # Scan Information (matches HTML theme)
            story.append(Paragraph("Scan Information", self.custom_styles['Heading3']))
            
            scan_id = scan_results.get("scan_id", "unknown")
            repository_url = scan_results.get("repository_url", "")
            branch = scan_results.get("branch", "")
            overall_score = scan_results.get("overall_score", 0.0)
            
            scan_info_data = [
                ['Project', project_name],
                ['Repository', repository_url],
                ['Branch', branch],
                ['Scan ID', scan_id],
                ['Overall Score', f"{overall_score:.1f}%"],
                ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            ]
            
            # Table styling matches HTML theme
            scan_info_table = Table(scan_info_data, colWidths=[1.5*inch, 4.5*inch])
            scan_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                ('ROUNDEDCORNERS', [8, 8, 8, 8]),
            ]))
            
            story.append(scan_info_table)
            story.append(Spacer(1, 20))
            
            # Gate Overview (matches HTML theme)
            story.append(Paragraph("Gate Overview", self.custom_styles['Heading2']))
            
            # Status with color coding (matches HTML status styles)
            status_style = self._get_status_style_for_reportlab(status)
            story.append(Paragraph(f"Status: {status}", status_style))
            story.append(Spacer(1, 15))
            
            # Create gate info table (matches HTML theme)
            gate_data = [
                ['Gate Name', display_name],
                ['Status', status],
                ['Score', f"{score:.1f}%"],
                ['Category', gate.get("category", "")],
                ['Priority', gate.get("priority", "")],
                ['Patterns Used', str(gate.get("patterns_used", 0))],
                ['Matches Found', str(gate.get("matches_found", 0))],
                ['Relevant Files', str(gate.get("relevant_files", 0))]
            ]
            
            # Table styling matches HTML theme
            gate_table = Table(gate_data, colWidths=[2*inch, 4*inch])
            gate_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                ('ROUNDEDCORNERS', [8, 8, 8, 8]),
            ]))
            
            story.append(gate_table)
            story.append(Spacer(1, 20))
            
            # Description (matches HTML theme)
            description = gate.get("description", "")
            if description:
                story.append(Paragraph("Description", self.custom_styles['Heading3']))
                story.append(Paragraph(description, self.custom_styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Evidence and matches (matches HTML theme)
            matches = gate.get("matches", [])
            if matches:
                story.append(Paragraph("Evidence & Matches", self.custom_styles['Heading3']))
                
                # Create matches table (matches HTML theme)
                matches_data = [['File', 'Line', 'Pattern', 'Context']]
                
                for match in matches[:10]:  # Limit to first 10 matches
                    file_path = match.get("file_path", "")
                    line_number = match.get("line_number", "")
                    pattern = match.get("pattern", "")
                    context = match.get("context", "")
                    
                    # Truncate long paths and context
                    if len(file_path) > 40:
                        file_path = "..." + file_path[-37:]
                    if len(context) > 60:
                        context = context[:57] + "..."
                    
                    matches_data.append([file_path, line_number, pattern, context])
                
                # Table styling matches HTML theme
                matches_table = Table(matches_data, colWidths=[1.5*inch, 0.5*inch, 1.5*inch, 2.5*inch])
                matches_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#374151')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                    ('ROUNDEDCORNERS', [8, 8, 8, 8]),
                ]))
                
                story.append(matches_table)
            else:
                story.append(Paragraph("Evidence & Matches", self.custom_styles['Heading3']))
                story.append(Paragraph("No matches found for this gate.", self.custom_styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Validation Evidence (matches HTML theme)
            validation_sources = gate.get("validation_sources", {})
            if validation_sources:
                story.append(Paragraph("Validation Evidence", self.custom_styles['Heading3']))
                
                evidence_data = []
                
                # LLM Patterns
                llm_patterns = validation_sources.get("llm_patterns", {})
                if llm_patterns:
                    evidence_data.append(['LLM Patterns', f"{llm_patterns.get('count', 0)} patterns, {llm_patterns.get('matches', 0)} matches"])
                
                # Static Patterns
                static_patterns = validation_sources.get("static_patterns", {})
                if static_patterns:
                    evidence_data.append(['Static Patterns', f"{static_patterns.get('count', 0)} patterns, {static_patterns.get('matches', 0)} matches"])
                
                # Enhanced Data
                enhanced_data = gate.get("enhanced_data", {})
                if enhanced_data:
                    confidence = enhanced_data.get("confidence_score", 0)
                    coverage = enhanced_data.get("coverage_percentage", 0)
                    technologies = enhanced_data.get("technology_detected", [])
                    evidence_data.append(['Enhanced Analysis', f"Confidence: {confidence:.2f}, Coverage: {coverage:.1f}%, Tech: {', '.join(technologies)}"])
                
                if evidence_data:
                    # Table styling matches HTML theme
                    evidence_table = Table(evidence_data, colWidths=[2*inch, 4*inch])
                    evidence_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
                        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
                    ]))
                    
                    story.append(evidence_table)
                    story.append(Spacer(1, 15))
            
            # Recommendations (matches HTML theme)
            recommendation = gate.get("llm_recommendation", "")
            if recommendation:
                story.append(Paragraph("AI Recommendations", self.custom_styles['Heading3']))
                story.append(Paragraph(recommendation, self.custom_styles['RecommendationText']))
                story.append(Spacer(1, 15))
            
            # Footer (matches HTML theme)
            story.append(Spacer(1, 30))
            story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb'), spaceAfter=20))
            story.append(Paragraph("Generated by CodeGates Security Analysis Platform", self.custom_styles['Footer']))
            story.append(Paragraph("This PDF was generated using pure Python ReportLab", self.custom_styles['Footer']))
            
            # Build PDF
            doc.build(story)
            return filepath
            
        except Exception as e:
            print(f"❌ Failed to generate gate PDF for {gate_name}: {e}")
            return None
    
    def _get_status_style_for_reportlab(self, status: str) -> ParagraphStyle:
        """Get ReportLab paragraph style for gate status (matches HTML exactly)"""
        if status == "PASS":
            return self.custom_styles['StatusPass']
        elif status == "FAIL":
            return self.custom_styles['StatusFail']
        elif status == "WARNING":
            return self.custom_styles['StatusWarning']
        elif status == "NOT_APPLICABLE":
            return self.custom_styles['StatusNotApplicable']
        else:
            return self.custom_styles['Normal']
    
    def _get_status_info_from_new_data(self, status: str, gate: Dict[str, Any] = None) -> Dict[str, str]:
        """Get status info matching HTML structure exactly"""
        status_map = {
            "PASS": {"display": "PASS", "description": "Gate requirements met"},
            "FAIL": {"display": "FAIL", "description": "Gate requirements not met"},
            "WARNING": {"display": "WARNING", "description": "Partial implementation detected"},
            "NOT_APPLICABLE": {"display": "N/A", "description": "Not applicable to this project type"}
        }
        return status_map.get(status, {"display": status, "description": "Unknown status"})
    
    def _format_evidence_from_new_data(self, gate: Dict[str, Any]) -> str:
        """Format evidence matching HTML structure exactly"""
        if gate.get("status") == 'NOT_APPLICABLE':
            return 'Not applicable to this project type'
        
        matches_found = gate.get("matches_found", 0)
        score = gate.get("score", 0)
        
        if matches_found > 0:
            return f"Found {matches_found} implementations with {score:.1f}% coverage"
        else:
            return 'No relevant patterns found in codebase'
    
    def _get_recommendation_from_new_data(self, gate: Dict[str, Any]) -> str:
        """Get recommendation matching HTML structure exactly"""
        recommendation = gate.get("llm_recommendation", "")
        if recommendation:
            # Truncate long recommendations
            if len(recommendation) > 100:
                return recommendation[:97] + "..."
            return recommendation
        else:
            return "No specific recommendations available"
    
    def _get_gate_number(self, gate_name: str) -> int:
        """Get gate number matching HTML structure exactly"""
        gate_numbers = {
            "ALERTING_ACTIONABLE": 1,
            "STRUCTURED_LOGS": 2,
            "AVOID_LOGGING_SECRETS": 3,
            "AUDIT_TRAIL": 4,
            "CORRELATION_ID": 5,
            "LOG_API_CALLS": 6,
            "LOG_APPLICATION_MESSAGES": 7,
            "UI_ERRORS": 8,
            "RETRY_LOGIC": 9,
            "TIMEOUTS": 10,
            "THROTTLING": 11,
            "CIRCUIT_BREAKERS": 12,
            "AUTO_SCALE": 13,
            "ERROR_LOGS": 14,
            "HTTP_CODES": 15,
            "UI_ERROR_TOOLS": 16,
            "AUTOMATED_TESTS": 17
        }
        return gate_numbers.get(gate_name, 0)
    
    def _extract_project_name(self, repository_url: str) -> str:
        """Extract project name from repository URL (matches HTML)"""
        if not repository_url:
            return "unknown"
        
        # Extract from GitHub URL
        if "github.com" in repository_url:
            parts = repository_url.rstrip("/").split("/")
            if len(parts) >= 2:
                return parts[-1].replace(".git", "")
        
        # Extract from other URLs
        parts = repository_url.rstrip("/").split("/")
        if parts:
            return parts[-1].replace(".git", "")
        
        return "unknown"
    
    def _extract_app_id(self, repository_url: str) -> str:
        """Extract App Id from repository URL using /app-XYZ/ pattern (matches HTML)"""
        import re
        try:
            # Remove .git if present
            if repository_url.endswith('.git'):
                repository_url = repository_url[:-4]
            # Find /app-XYZ or /app-XYZ/ in the path
            match = re.search(r"/app-([A-Za-z0-9_-]+)(/|$)", repository_url)
            if match:
                return match.group(1)
            else:
                return "APP ID"
        except Exception:
            return "APP ID"


def generate_pdfs_from_html_reports(scan_results: Dict[str, Any], html_report_path: str, output_dir: str = "./reports") -> Dict[str, List[str]]:
    """
    Convenience function to generate PDFs from HTML reports with exact theme matching
    
    Args:
        scan_results: The complete scan results dictionary
        html_report_path: Path to the generated HTML report
        output_dir: Directory to save PDF files
        
    Returns:
        Dictionary with 'summary' and 'gates' lists of generated PDF file paths
    """
    converter = HTMLToPDFConverter()
    return converter.generate_pdfs_from_html_reports(scan_results, html_report_path, output_dir) 