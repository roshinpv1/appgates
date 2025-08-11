#!/usr/bin/env python3
"""
Enhanced PDF Generator for CodeGates Reports
Generates summary PDF and individual gate PDFs with consistent styling
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab not available. Install with: pip install reportlab")


class EnhancedPDFGenerator:
    """Enhanced PDF generator with consistent styling and proper naming"""
    
    def __init__(self):
        self.styles = None
        self.custom_styles = {}
        if REPORTLAB_AVAILABLE:
            self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles matching HTML template"""
        self.styles = getSampleStyleSheet()
        
        # Custom styles matching HTML template colors and styling
        self.custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Title'],
                fontSize=24,
                spaceAfter=30,
                textColor=HexColor('#1f2937'),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'Subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=self.styles['Normal'],
                fontSize=16,
                spaceAfter=20,
                textColor=HexColor('#2563eb'),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'Heading1': ParagraphStyle(
                'CustomHeading1',
                parent=self.styles['Heading1'],
                fontSize=18,
                spaceAfter=15,
                spaceBefore=20,
                textColor=HexColor('#1f2937'),
                backColor=HexColor('#f9fafb'),
                borderPadding=10,
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=HexColor('#e5e7eb')
            ),
            'Heading2': ParagraphStyle(
                'CustomHeading2',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15,
                textColor=HexColor('#374151'),
                fontName='Helvetica-Bold'
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                textColor=HexColor('#1f2937'),
                fontName='Helvetica'
            ),
            'Code': ParagraphStyle(
                'CustomCode',
                parent=self.styles['Normal'],
                fontSize=9,
                fontName='Courier',
                backColor=HexColor('#f3f4f6'),
                borderPadding=6,
                leftIndent=12,
                rightIndent=12,
                textColor=HexColor('#1f2937')
            ),
            'Italic': ParagraphStyle(
                'CustomItalic',
                parent=self.styles['Normal'],
                fontSize=9,
                fontName='Helvetica-Oblique',
                textColor=HexColor('#6b7280'),
                spaceAfter=6
            )
        }
    
    def generate_pdfs(self, scan_results: Dict[str, Any], output_dir: str = "./reports") -> Dict[str, List[str]]:
        """
        Generate summary PDF and individual gate PDFs
        
        Args:
            scan_results: The complete scan results dictionary
            output_dir: Directory to save PDF files
            
        Returns:
            Dictionary with 'summary' and 'gates' lists of generated PDF file paths
        """
        if not REPORTLAB_AVAILABLE:
            print("❌ Cannot generate PDFs: ReportLab not installed")
            return {"summary": [], "gates": []}
        
        # Extract project name and scan ID
        project_name = self._extract_project_name(scan_results)
        scan_id = scan_results.get("scan_id", "unknown")
        
        # Create output directory
        pdf_dir = os.path.join(output_dir, "pdfs", scan_id)
        os.makedirs(pdf_dir, exist_ok=True)
        
        generated_files = {"summary": [], "gates": []}
        
        # Generate summary PDF
        try:
            summary_pdf = self._generate_summary_pdf(scan_results, project_name, scan_id, pdf_dir)
            if summary_pdf:
                generated_files["summary"].append(summary_pdf)
                print(f"✅ Generated summary PDF: {os.path.basename(summary_pdf)}")
        except Exception as e:
            print(f"❌ Failed to generate summary PDF: {e}")
        
        # Generate individual gate PDFs
        gate_results = scan_results.get("gate_results", [])
        if not gate_results:
            gate_results = scan_results.get("gates", [])
        
        if gate_results:
            print(f"📄 Generating individual PDFs for {len(gate_results)} gates...")
            
            for gate in gate_results:
                try:
                    gate_pdf = self._generate_gate_pdf(gate, scan_results, project_name, scan_id, pdf_dir)
                    if gate_pdf:
                        generated_files["gates"].append(gate_pdf)
                        print(f"   ✅ Generated: {os.path.basename(gate_pdf)}")
                except Exception as e:
                    print(f"   ❌ Failed to generate PDF for {gate.get('gate', 'unknown')}: {e}")
        
        print(f"📄 Generated {len(generated_files['summary'])} summary and {len(generated_files['gates'])} gate PDF files")
        return generated_files
    
    def _extract_project_name(self, scan_results: Dict[str, Any]) -> str:
        """Extract project name from scan results"""
        # Try to get from project_name field
        project_name = scan_results.get("project_name", "")
        if project_name:
            # Extract just the project part (before the first dash or space)
            match = re.search(r'^([^-]+)', project_name)
            if match:
                return match.group(1).strip()
        
        # Try to extract from repository URL
        repo_url = scan_results.get("repository_url", "")
        if repo_url:
            # Extract project name from URL
            match = re.search(r'/([^/]+?)(?:\.git)?$', repo_url)
            if match:
                return match.group(1)
        
        return "project"
    
    def _generate_summary_pdf(self, scan_results: Dict[str, Any], project_name: str, scan_id: str, output_dir: str) -> Optional[str]:
        """Generate summary PDF with naming: project-scanid-summary.pdf"""
        
        filename = f"{project_name}-{scan_id}-summary.pdf"
        filepath = os.path.join(output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title
        story.append(Paragraph("CodeGates Validation Report", self.custom_styles['Title']))
        story.append(Paragraph("Enterprise Security Gate Analysis", self.custom_styles['Subtitle']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.extend(self._build_executive_summary(scan_results))
        story.append(Spacer(1, 20))
        
        # Overall Statistics
        story.extend(self._build_overall_statistics(scan_results))
        story.append(Spacer(1, 20))
        
        # Gate Results Summary
        story.extend(self._build_gate_results_summary(scan_results))
        story.append(Spacer(1, 20))
        
        # Key Findings and Recommendations
        story.extend(self._build_key_findings(scan_results))
        story.append(Spacer(1, 20))
        
        # Scan Information
        story.extend(self._build_scan_information(scan_results))
        
        # Build PDF
        doc.build(story)
        return filepath
    
    def _generate_gate_pdf(self, gate: Dict[str, Any], scan_results: Dict[str, Any], project_name: str, scan_id: str, output_dir: str) -> Optional[str]:
        """Generate individual gate PDF with naming: project-scanid-<gate-name>.pdf"""
        
        gate_name = gate.get("gate", "unknown_gate")
        # Clean gate name for filename
        safe_gate_name = re.sub(r'[^a-zA-Z0-9_-]', '_', gate_name).lower()
        
        filename = f"{project_name}-{scan_id}-{safe_gate_name}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Header
        story.extend(self._build_gate_header(gate, scan_results))
        story.append(Spacer(1, 20))
        
        # Gate Overview
        story.extend(self._build_gate_overview(gate))
        story.append(Spacer(1, 15))
        
        # Status and Metrics
        story.extend(self._build_gate_status_section(gate))
        story.append(Spacer(1, 15))
        
        # Evidence and Findings
        story.extend(self._build_gate_evidence_section(gate))
        story.append(Spacer(1, 15))
        
        # Recommendations
        story.extend(self._build_gate_recommendations_section(gate))
        story.append(Spacer(1, 15))
        
        # Technical Details
        story.extend(self._build_gate_technical_details(gate))
        story.append(Spacer(1, 15))
        
        # Matches and Patterns
        story.extend(self._build_gate_matches_section(gate))
        
        # Build PDF
        doc.build(story)
        return filepath
    
    def _build_executive_summary(self, scan_results: Dict[str, Any]) -> List:
        """Build executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.custom_styles['Heading1']))
        
        overall_score = scan_results.get("overall_score", 0)
        status = "PASS" if overall_score >= 70 else "FAIL"
        
        # Get gate statistics
        gate_results = scan_results.get("gate_results", [])
        if not gate_results:
            gate_results = scan_results.get("gates", [])
        
        passed = len([g for g in gate_results if g.get("status") == "PASS"])
        failed = len([g for g in gate_results if g.get("status") == "FAIL"])
        warnings = len([g for g in gate_results if g.get("status") == "WARNING"])
        not_applicable = len([g for g in gate_results if g.get("status") == "NOT_APPLICABLE"])
        total_gates = len(gate_results)
        
        # Executive summary text
        summary_text = f"""
        This report presents the results of a comprehensive security gate validation analysis for the codebase. 
        The analysis evaluated {total_gates} enterprise security gates to assess compliance with industry best practices 
        and security standards.
        
        Overall Assessment: The codebase achieved an overall compliance score of {overall_score:.1f}%, 
        which is classified as {status}. This indicates {'strong security practices' if status == 'PASS' else 'areas requiring attention'} 
        in the implementation of security controls and monitoring capabilities.
        
        Key Metrics:
        • Total Gates Evaluated: {total_gates}
        • Gates Passed: {passed}
        • Gates Failed: {failed}
        • Gates with Warnings: {warnings}
        • Gates Not Applicable: {not_applicable}
        """
        
        elements.append(Paragraph(summary_text, self.custom_styles['Normal']))
        return elements
    
    def _build_overall_statistics(self, scan_results: Dict[str, Any]) -> List:
        """Build overall statistics section"""
        elements = []
        
        elements.append(Paragraph("Overall Statistics", self.custom_styles['Heading1']))
        
        overall_score = scan_results.get("overall_score", 0)
        status = "PASS" if overall_score >= 70 else "FAIL"
        
        # Get metadata
        metadata = scan_results.get("metadata", {})
        total_files = metadata.get("file_count", 0)
        total_lines = metadata.get("line_count", 0)
        
        # Statistics table
        stats_data = [
            ["Overall Score", f"{overall_score:.1f}%"],
            ["Overall Status", status],
            ["Total Files Analyzed", str(total_files)],
            ["Total Lines of Code", str(total_lines)],
            ["Scan Date", scan_results.get("scan_timestamp_formatted", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))],
            ["Repository", scan_results.get("repository_url", "Unknown")]
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 3.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (1, 1), (1, 1), self._get_status_color(status)),  # Status cell color
        ]))
        
        elements.append(stats_table)
        return elements
    
    def _build_gate_results_summary(self, scan_results: Dict[str, Any]) -> List:
        """Build gate results summary section"""
        elements = []
        
        elements.append(Paragraph("Gate Results Summary", self.custom_styles['Heading1']))
        
        gate_results = scan_results.get("gate_results", [])
        if not gate_results:
            gate_results = scan_results.get("gates", [])
        
        if not gate_results:
            elements.append(Paragraph("No gate results available.", self.custom_styles['Normal']))
            return elements
        
        # Create summary table
        summary_data = [["Gate Name", "Status", "Score", "Category", "Priority"]]
        
        for gate in gate_results:
            gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
            status = gate.get("status", "UNKNOWN")
            score = gate.get("score", 0)
            category = gate.get("category", "Unknown")
            priority = gate.get("priority", "Medium")
            
            summary_data.append([
                gate_name,
                status,
                f"{score:.1f}%",
                category,
                priority
            ])
        
        # Create table with proper styling
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 0.8*inch, 1.2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Status column center
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Score column center
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Priority column center
        ]))
        
        elements.append(summary_table)
        return elements
    
    def _build_key_findings(self, scan_results: Dict[str, Any]) -> List:
        """Build key findings and recommendations section"""
        elements = []
        
        elements.append(Paragraph("Key Findings and Recommendations", self.custom_styles['Heading1']))
        
        gate_results = scan_results.get("gate_results", [])
        if not gate_results:
            gate_results = scan_results.get("gates", [])
        
        failed_gates = [g for g in gate_results if g.get("status") == "FAIL"]
        warning_gates = [g for g in gate_results if g.get("status") == "WARNING"]
        
        # Key findings text
        findings_text = f"""
        Based on the analysis of {len(gate_results)} security gates, the following key findings were identified:
        
        Critical Issues ({len(failed_gates)} gates):
        """
        
        if failed_gates:
            for gate in failed_gates[:5]:  # Show first 5 failed gates
                gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
                findings_text += f"• {gate_name}: Requires immediate attention\n"
        else:
            findings_text += "• No critical issues identified\n"
        
        findings_text += f"""
        
        Areas for Improvement ({len(warning_gates)} gates):
        """
        
        if warning_gates:
            for gate in warning_gates[:5]:  # Show first 5 warning gates
                gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
                findings_text += f"• {gate_name}: Consider implementing improvements\n"
        else:
            findings_text += "• No areas for improvement identified\n"
        
        findings_text += """
        
        Recommendations:
        • Review and address all failed gates as a priority
        • Implement improvements for gates with warnings
        • Consider additional security measures for high-risk areas
        • Establish monitoring and alerting for critical security controls
        • Regular security assessments to maintain compliance
        """
        
        elements.append(Paragraph(findings_text, self.custom_styles['Normal']))
        return elements
    
    def _build_scan_information(self, scan_results: Dict[str, Any]) -> List:
        """Build scan information section"""
        elements = []
        
        elements.append(Paragraph("Scan Information", self.custom_styles['Heading2']))
        
        scan_info_data = [
            ["Scan ID", scan_results.get("scan_id", "Unknown")],
            ["Repository URL", scan_results.get("repository_url", "Unknown")],
            ["Branch", scan_results.get("branch", "Unknown")],
            ["Scan Timestamp", scan_results.get("scan_timestamp_formatted", "Unknown")],
            ["Threshold", f"{scan_results.get('threshold', 70)}%"],
            ["Report Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        scan_info_table = Table(scan_info_data, colWidths=[2*inch, 4*inch])
        scan_info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(scan_info_table)
        return elements
    
    def _build_gate_header(self, gate: Dict[str, Any], scan_results: Dict[str, Any]) -> List:
        """Build gate header section"""
        elements = []
        
        # Title
        gate_name = gate.get("display_name", gate.get("gate", "Unknown Gate"))
        status = gate.get("status", "UNKNOWN")
        
        title_text = f"Gate Analysis: {gate_name}"
        elements.append(Paragraph(title_text, self.custom_styles['Title']))
        
        # Status subtitle
        status_text = f"Status: {status}"
        elements.append(Paragraph(status_text, self.custom_styles['Subtitle']))
        
        # Scan information
        scan_info_data = [
            ["Scan ID", scan_results.get("scan_id", "unknown")],
            ["Repository", scan_results.get("repository_url", "unknown")],
            ["Branch", scan_results.get("branch", "unknown")],
            ["Scan Date", scan_results.get("scan_timestamp_formatted", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))],
            ["Gate Score", f"{gate.get('score', 0):.1f}%"],
            ["Overall Score", f"{scan_results.get('overall_score', 0):.1f}%"]
        ]
        
        scan_info_table = Table(scan_info_data, colWidths=[2*inch, 4*inch])
        scan_info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (1, 4), (1, 4), self._get_status_color(status)),  # Gate score cell color
        ]))
        
        elements.append(scan_info_table)
        return elements
    
    def _build_gate_overview(self, gate: Dict[str, Any]) -> List:
        """Build gate overview section"""
        elements = []
        
        elements.append(Paragraph("Gate Overview", self.custom_styles['Heading1']))
        
        # Gate information
        description = gate.get("description", "No description available")
        category = gate.get("category", "Unknown")
        priority = gate.get("priority", "Medium")
        
        overview_data = [
            ["Gate Name", gate.get("display_name", gate.get("gate", "Unknown"))],
            ["Category", category],
            ["Priority", priority],
            ["Description", description]
        ]
        
        overview_table = Table(overview_data, colWidths=[1.5*inch, 4.5*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(overview_table)
        return elements
    
    def _build_gate_status_section(self, gate: Dict[str, Any]) -> List:
        """Build gate status and metrics section"""
        elements = []
        
        elements.append(Paragraph("Status & Metrics", self.custom_styles['Heading1']))
        
        status = gate.get("status", "UNKNOWN")
        score = gate.get("score", 0.0)
        patterns_used = gate.get("patterns_used", 0)
        matches_found = gate.get("matches_found", 0)
        relevant_files = gate.get("relevant_files", 0)
        total_files = gate.get("total_files", 0)
        
        metrics_data = [
            ["Status", status],
            ["Score", f"{score:.1f}%"],
            ["Patterns Used", str(patterns_used)],
            ["Matches Found", str(matches_found)],
            ["Relevant Files", f"{relevant_files}/{total_files}"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (1, 0), (1, 0), self._get_status_color(status)),  # Status value color
        ]))
        
        elements.append(metrics_table)
        return elements
    
    def _build_gate_evidence_section(self, gate: Dict[str, Any]) -> List:
        """Build gate evidence section"""
        elements = []
        
        elements.append(Paragraph("Evidence & Findings", self.custom_styles['Heading1']))
        
        # Enhanced data
        enhanced_data = gate.get("enhanced_data", {})
        validation_sources = gate.get("validation_sources", {})
        
        if enhanced_data or validation_sources:
            evidence_text = "Evidence collected during gate validation:\n\n"
            
            if validation_sources:
                llm_patterns = validation_sources.get("llm_patterns", {})
                static_patterns = validation_sources.get("static_patterns", {})
                
                evidence_text += f"• LLM Patterns: {llm_patterns.get('count', 0)} patterns, {llm_patterns.get('matches', 0)} matches\n"
                evidence_text += f"• Static Patterns: {static_patterns.get('count', 0)} patterns, {static_patterns.get('matches', 0)} matches\n"
                evidence_text += f"• Combined Confidence: {validation_sources.get('combined_confidence', 'unknown')}\n\n"
            
            if enhanced_data:
                evidence_text += "Additional Analysis:\n"
                for key, value in enhanced_data.items():
                    if key in ['confidence_score', 'coverage_percentage', 'technology_detected', 'files_analyzed']:
                        field_display = key.replace('_', ' ').title()
                        evidence_text += f"• {field_display}: {value}\n"
            
            elements.append(Paragraph(evidence_text, self.custom_styles['Normal']))
        else:
            elements.append(Paragraph("No detailed evidence data available for this gate.", self.custom_styles['Normal']))
        
        return elements
    
    def _build_gate_recommendations_section(self, gate: Dict[str, Any]) -> List:
        """Build gate recommendations section"""
        elements = []
        
        # Import the recommendation formatter
        try:
            from utils.recommendation_formatter import recommendation_formatter
            formatted_recommendation = recommendation_formatter.format_recommendation_for_details(gate)
        except ImportError:
            formatted_recommendation = gate.get("llm_recommendation", "")
        
        if not formatted_recommendation:
            return elements
        
        # Different titles based on gate status
        status = gate.get("status", "")
        if status == "PASS":
            title = "AI Best Practice Insights"
        else:
            title = "AI Recommendations"
        
        elements.append(Paragraph(title, self.custom_styles['Heading1']))
        
        # Add the formatted recommendation content
        elements.append(Paragraph(formatted_recommendation, self.custom_styles['Normal']))
        elements.append(Paragraph("Generated by AI Assistant", self.custom_styles['Italic']))
        
        return elements
    
    def _build_gate_technical_details(self, gate: Dict[str, Any]) -> List:
        """Build gate technical details section"""
        elements = []
        
        elements.append(Paragraph("Technical Details", self.custom_styles['Heading1']))
        
        # Pattern information
        patterns = gate.get("patterns", [])
        if patterns:
            elements.append(Paragraph("Patterns Used:", self.custom_styles['Heading2']))
            for pattern in patterns[:10]:  # Limit to first 10 patterns
                elements.append(Paragraph(pattern, self.custom_styles['Code']))
            if len(patterns) > 10:
                elements.append(Paragraph(f"... and {len(patterns) - 10} more patterns", self.custom_styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Splunk reference
        splunk_reference = gate.get("splunk_reference", {})
        if splunk_reference and splunk_reference.get("influenced"):
            elements.append(Paragraph("Splunk Integration:", self.custom_styles['Heading2']))
            splunk_text = f"""
            Query: {splunk_reference.get('query', 'N/A')}
            Job ID: {splunk_reference.get('job_id', 'N/A')}
            Message: {splunk_reference.get('message', 'N/A')}
            """
            elements.append(Paragraph(splunk_text, self.custom_styles['Normal']))
        
        return elements
    
    def _build_gate_matches_section(self, gate: Dict[str, Any]) -> List:
        """Build gate matches section"""
        elements = []
        
        matches = gate.get("matches", [])
        matches_found = gate.get("matches_found", 0)
        
        if not matches or matches_found == 0:
            return elements
        
        elements.append(Paragraph("Sample Matches", self.custom_styles['Heading1']))
        
        # Show first 5 matches
        sample_matches = matches[:5]
        
        for match in sample_matches:
            if isinstance(match, dict):
                file_path = match.get("file", "Unknown")
                line_number = match.get("line", "Unknown")
                pattern_match = match.get("match", "Unknown")
                
                match_text = f"{file_path}:{line_number} → {pattern_match}"
                elements.append(Paragraph(f"• {match_text}", self.custom_styles['Code']))
        
        # Show count if more matches exist
        if matches_found > 5:
            elements.append(Paragraph(f"... and {matches_found - 5} more matches", self.custom_styles['Normal']))
        
        return elements
    
    def _get_status_color(self, status: str) -> HexColor:
        """Get color for gate status"""
        status_colors = {
            "PASS": HexColor('#10b981'),      # Green
            "FAIL": HexColor('#ef4444'),      # Red
            "WARNING": HexColor('#f59e0b'),   # Orange
            "NOT_APPLICABLE": HexColor('#6b7280')  # Gray
        }
        return status_colors.get(status, HexColor('#6b7280'))


def generate_pdfs_from_scan_id(scan_id: str, base_dir: str = "./reports") -> Dict[str, List[str]]:
    """
    Generate PDFs from a scan ID with proper naming convention
    
    Args:
        scan_id: The scan ID to generate PDFs for
        base_dir: Base directory where reports are stored
        
    Returns:
        Dictionary with 'summary' and 'gates' lists of generated PDF file paths
    """
    # Look for JSON report in the correct scan_id subdirectory
    json_path = os.path.join(base_dir, scan_id, f"codegates_report_{scan_id}.json")
    
    if not os.path.exists(json_path):
        print(f"❌ JSON report not found: {json_path}")
        return {"summary": [], "gates": []}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            scan_results = json.load(f)
        
        pdf_generator = EnhancedPDFGenerator()
        return pdf_generator.generate_pdfs(scan_results, base_dir)
        
    except Exception as e:
        print(f"❌ Failed to generate PDFs from scan {scan_id}: {e}")
        return {"summary": [], "gates": []}


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        scan_id = sys.argv[1]
        pdf_files = generate_pdfs_from_scan_id(scan_id)
        
        if pdf_files["summary"] or pdf_files["gates"]:
            print(f"\n✅ Generated PDF files:")
            if pdf_files["summary"]:
                print(f"   📄 Summary: {pdf_files['summary'][0]}")
            print(f"   📄 Individual Gates: {len(pdf_files['gates'])} files")
            for pdf_file in pdf_files["gates"]:
                print(f"      - {os.path.basename(pdf_file)}")
        else:
            print("❌ No PDF files generated")
    else:
        print("Usage: python pdf_generator.py <scan_id>") 