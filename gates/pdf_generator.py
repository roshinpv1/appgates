#!/usr/bin/env python3
"""
PDF Generator for CodeGates Reports
Generates individual PDF documents for each gate that can be uploaded to JIRA
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, white, red, green, orange, gray
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab not available. Install with: pip install reportlab")


class CodeGatesPDFGenerator:
    """Generate individual PDF documents for each gate result"""
    
    def __init__(self):
        self.styles = None
        self.custom_styles = {}
        if REPORTLAB_AVAILABLE:
            self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles for PDF generation"""
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Title'],
                fontSize=18,
                spaceAfter=30,
                textColor=HexColor('#1f2937'),
                alignment=TA_CENTER
            ),
            'Heading1': ParagraphStyle(
                'CustomHeading1',
                parent=self.styles['Heading1'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=12,
                textColor=HexColor('#374151'),
                backColor=HexColor('#f9fafb'),
                borderPadding=8
            ),
            'Heading2': ParagraphStyle(
                'CustomHeading2',
                parent=self.styles['Heading2'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=8,
                textColor=HexColor('#4b5563')
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                textColor=HexColor('#1f2937')
            ),
            'Code': ParagraphStyle(
                'CustomCode',
                parent=self.styles['Normal'],
                fontSize=9,
                fontName='Courier',
                backColor=HexColor('#f3f4f6'),
                borderPadding=4,
                leftIndent=10,
                rightIndent=10
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
    
    def generate_individual_gate_pdfs(self, scan_results: Dict[str, Any], output_dir: str = "./reports/pdfs") -> List[str]:
        """
        Generate individual PDF documents for each gate
        
        Args:
            scan_results: The complete scan results dictionary
            output_dir: Directory to save PDF files
            
        Returns:
            List of generated PDF file paths
        """
        if not REPORTLAB_AVAILABLE:
            print("❌ Cannot generate PDFs: ReportLab not installed")
            return []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Handle both gate_results (UI format) and gates (JSON report format)
        gate_results = scan_results.get("gate_results", [])
        if not gate_results:
            # Try to get from gates array (JSON report format)
            gate_results = scan_results.get("gates", [])
        
        if not gate_results:
            print("❌ No gate results found in scan data")
            return []
        
        generated_files = []
        scan_id = scan_results.get("scan_id", "unknown")
        
        print(f"📄 Generating individual PDFs for {len(gate_results)} gates...")
        
        for i, gate in enumerate(gate_results):
            try:
                gate_name = gate.get("gate", "unknown_gate")
                gate_display_name = gate.get("display_name", gate_name)
                status = gate.get("status", "UNKNOWN")
                
                # Create filename with gate number, name, and scan ID
                # Format: Gate_{number}_{gate_name}_{scan_id}.pdf
                gate_number = i + 1
                safe_gate_name = gate_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
                filename = f"Gate_{gate_number:02d}_{safe_gate_name}_{scan_id}.pdf"
                filepath = os.path.join(output_dir, filename)
                
                # Generate PDF for this gate
                self._generate_single_gate_pdf(gate, scan_results, filepath)
                generated_files.append(filepath)
                
                print(f"   ✅ Generated: {filename}")
                
            except Exception as e:
                print(f"   ❌ Failed to generate PDF for {gate.get('gate', 'unknown')}: {e}")
        
        print(f"📄 Generated {len(generated_files)} individual gate PDF files in {output_dir}")
        return generated_files
    
    def _generate_single_gate_pdf(self, gate: Dict[str, Any], scan_results: Dict[str, Any], filepath: str):
        """Generate a single PDF document for one gate with exact same data as HTML report"""
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build content
        story = []
        
        # Header with scan information
        story.extend(self._build_header(gate, scan_results))
        story.append(Spacer(1, 20))
        
        # Gate overview
        story.extend(self._build_gate_overview(gate))
        story.append(Spacer(1, 15))
        
        # Status and metrics
        story.extend(self._build_status_section(gate))
        story.append(Spacer(1, 15))
        
        # Sample matches section (like HTML report)
        story.extend(self._build_sample_matches_section(gate))
        story.append(Spacer(1, 10))
        
        # Splunk reference section (like HTML report)
        story.extend(self._build_splunk_reference_section(gate))
        story.append(Spacer(1, 10))
        
        # Full matches and patterns table (like HTML report)
        story.extend(self._build_full_matches_table(gate))
        story.append(Spacer(1, 15))
        
        # Recommendations section (like HTML report)
        story.extend(self._build_recommendations_section(gate))
        story.append(Spacer(1, 15))
        
        # Gate information section (like HTML report)
        story.extend(self._build_gate_information_section(gate))
        story.append(Spacer(1, 15))
        
        # Enhanced data section (technical details)
        story.extend(self._build_enhanced_data_section(gate))
        
        # Build PDF
        doc.build(story)
    
    def _build_header(self, gate: Dict[str, Any], scan_results: Dict[str, Any]) -> List:
        """Build the PDF header section"""
        elements = []
        
        # Title
        gate_name = gate.get("display_name", gate.get("gate", "Unknown Gate"))
        status = gate.get("status", "UNKNOWN")
        status_color = self._get_status_color(status)
        
        title_text = f"CodeGates Report: {gate_name}"
        elements.append(Paragraph(title_text, self.custom_styles['Title']))
        
        # Scan information table
        scan_info_data = [
            ["Scan ID", scan_results.get("scan_id", "unknown")],
            ["Repository", scan_results.get("repository_url", "unknown")],
            ["Branch", scan_results.get("branch", "unknown")],
            ["Scan Date", scan_results.get("scan_timestamp_formatted", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))],
            ["Overall Score", f"{scan_results.get('overall_score', 0):.1f}%"],
            ["Gate Status", status]
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
            ('BACKGROUND', (1, 5), (1, 5), status_color),  # Status cell color
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
            ["Name", gate.get("display_name", gate.get("gate", "Unknown"))],
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
    
    def _build_status_section(self, gate: Dict[str, Any]) -> List:
        """Build status and metrics section"""
        elements = []
        
        elements.append(Paragraph("Status & Metrics", self.custom_styles['Heading1']))
        
        status = gate.get("status", "UNKNOWN")
        score = gate.get("score", 0.0)
        patterns_used = gate.get("patterns_used", 0)
        matches_found = gate.get("matches_found", 0)
        relevant_files = gate.get("relevant_files", 0)
        total_files = gate.get("total_files", 0)
        
        status_color = self._get_status_color(status)
        
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
            ('BACKGROUND', (1, 0), (1, 0), status_color),  # Status value color
        ]))
        
        elements.append(metrics_table)
        return elements
    
    def _build_recommendations_section(self, gate: Dict[str, Any]) -> List:
        """Build AI recommendations section for all gate types using centralized formatter"""
        elements = []
        
        # Import the recommendation formatter
        from utils.recommendation_formatter import recommendation_formatter
        
        # Get formatted recommendation
        formatted_recommendation = recommendation_formatter.format_recommendation_for_details(gate)
        
        if not formatted_recommendation:
            return elements
        
        # Different titles based on gate status
        status = gate.get("status", "")
        if status == "PASS":
            title = "AI Best Practice Insights"
        else:  # FAIL, WARNING, etc.
            title = "AI Recommendations"
        
        elements.append(Paragraph(title, self.custom_styles['Heading1']))
        
        # Add the formatted recommendation content
        elements.append(Paragraph(formatted_recommendation, self.custom_styles['Normal']))
        elements.append(Paragraph("Generated by AI Assistant", self.custom_styles['Italic']))
        
        return elements
    
    def _build_enhanced_data_section(self, gate: Dict[str, Any]) -> List:
        """Build enhanced data section with technical details"""
        elements = []
        
        # Enhanced data from the gate
        enhanced_data = gate.get("enhanced_data", {})
        validation_sources = gate.get("validation_sources", {})
        patterns = gate.get("patterns", [])
        
        # Only show section if we have any enhanced data
        if not enhanced_data and not validation_sources and not patterns:
            return elements
        
        elements.append(Paragraph("Technical Details", self.custom_styles['Heading1']))
        
        # Validation sources
        if validation_sources:
            elements.append(Paragraph("Validation Sources:", self.custom_styles['Heading2']))
            
            llm_patterns = validation_sources.get("llm_patterns", {})
            static_patterns = validation_sources.get("static_patterns", {})
            
            sources_data = [
                ["LLM Patterns", f"{llm_patterns.get('count', 0)} patterns, {llm_patterns.get('matches', 0)} matches"],
                ["Static Patterns", f"{static_patterns.get('count', 0)} patterns, {static_patterns.get('matches', 0)} matches"],
                ["Combined Confidence", validation_sources.get("combined_confidence", "unknown")]
            ]
            
            sources_table = Table(sources_data, colWidths=[2*inch, 3*inch])
            sources_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(sources_table)
            elements.append(Spacer(1, 10))
        
        # Pattern information
        if patterns:
            elements.append(Paragraph("Patterns Used:", self.custom_styles['Heading2']))
            for pattern in patterns[:10]:  # Limit to first 10 patterns
                elements.append(Paragraph(pattern, self.custom_styles['Code']))
            if len(patterns) > 10:
                elements.append(Paragraph(f"... and {len(patterns) - 10} more patterns", self.custom_styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Additional enhanced data fields
        if enhanced_data:
            elements.append(Paragraph("Additional Analysis:", self.custom_styles['Heading2']))
            
            # Show relevant enhanced data fields
            relevant_fields = ['confidence_score', 'coverage_percentage', 'technology_detected', 'files_analyzed']
            for field in relevant_fields:
                if field in enhanced_data:
                    value = enhanced_data[field]
                    field_display = field.replace('_', ' ').title()
                    elements.append(Paragraph(f"• {field_display}: {value}", self.custom_styles['Normal']))
        
        return elements
    
    def _build_sample_matches_section(self, gate: Dict[str, Any]) -> List:
        """Build sample matches section (first 3 matches like HTML report)"""
        elements = []
        
        matches = gate.get("matches", [])
        matches_found = gate.get("matches_found", 0)
        
        if not matches or matches_found == 0:
            return elements
        
        elements.append(Paragraph("Sample Matches", self.custom_styles['Heading2']))
        
        # Show first 3 matches
        sample_matches = matches[:3]
        
        for match in sample_matches:
            if isinstance(match, dict):
                file_path = match.get("file", "Unknown")
                line_number = match.get("line", "Unknown")
                pattern_match = match.get("match", "Unknown")
                
                match_text = f"{file_path}:{line_number} → {pattern_match}"
                elements.append(Paragraph(f"• {match_text}", self.custom_styles['Code']))
        
        # Show count if more matches exist
        if matches_found > 3:
            elements.append(Paragraph(f"... and {matches_found - 3} more matches", self.custom_styles['Normal']))
        
        return elements
    
    def _build_splunk_reference_section(self, gate: Dict[str, Any]) -> List:
        """Build Splunk reference section like HTML report"""
        elements = []
        
        splunk_reference = gate.get("splunk_reference", {})
        if not splunk_reference or not splunk_reference.get("influenced"):
            return elements
        
        elements.append(Paragraph("Splunk Reference", self.custom_styles['Heading2']))
        
        splunk_query = splunk_reference.get("query", "")
        splunk_job_id = splunk_reference.get("job_id", "")
        splunk_message = splunk_reference.get("message", "")
        
        splunk_data = [
            ["Query", splunk_query],
            ["Job ID", splunk_job_id],
            ["Splunk Influence", "Yes"],
            ["Message", splunk_message]
        ]
        
        splunk_table = Table(splunk_data, colWidths=[1.5*inch, 4.5*inch])
        splunk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (0, -1), white),
            ('TEXTCOLOR', (1, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(splunk_table)
        return elements
    
    def _build_full_matches_table(self, gate: Dict[str, Any]) -> List:
        """Build full matches and patterns table like HTML report"""
        elements = []
        
        matches = gate.get("matches", [])
        matches_found = gate.get("matches_found", 0)
        num_patterns = len(gate.get("patterns", []))
        
        if not matches or matches_found == 0 or num_patterns == 0:
            return elements
        
        elements.append(Paragraph("All Matched Patterns and Files", self.custom_styles['Heading2']))
        
        # Create table header
        table_data = [["File", "Line", "Pattern Match", "Actual Pattern"]]
        
        # Add up to 100 matches (like HTML report)
        for match in matches[:100]:
            if isinstance(match, dict):
                file_path = match.get("file", "Unknown")
                line_number = str(match.get("line", "Unknown"))
                pattern_match = match.get("match", "Unknown")
                actual_pattern = match.get("pattern", "Unknown")
                
                # Truncate long content for table display
                if len(file_path) > 40:
                    file_path = file_path[:37] + "..."
                if len(pattern_match) > 50:
                    pattern_match = pattern_match[:47] + "..."
                if len(actual_pattern) > 50:
                    actual_pattern = actual_pattern[:47] + "..."
                
                table_data.append([file_path, line_number, pattern_match, actual_pattern])
        
        # Create table with proper styling
        matches_table = Table(table_data, colWidths=[2*inch, 0.5*inch, 2*inch, 1.5*inch])
        matches_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (2, 1), (2, -1), HexColor('#ecfdf5')),  # Pattern match column
            ('BACKGROUND', (3, 1), (3, -1), HexColor('#f3f4f6')),  # Actual pattern column
        ]))
        
        elements.append(matches_table)
        
        if len(matches) > 100:
            elements.append(Paragraph(f"... and {len(matches) - 100} more matches", self.custom_styles['Normal']))
        
        return elements
    
    def _build_gate_information_section(self, gate: Dict[str, Any]) -> List:
        """Build gate information section like HTML report"""
        elements = []
        
        elements.append(Paragraph("Gate Information", self.custom_styles['Heading2']))
        
        category = gate.get("category", "Unknown")
        priority = gate.get("priority", "Medium")
        description = gate.get("description", "No description available")
        
        gate_info_data = [
            ["Category", category],
            ["Priority", priority],
            ["Description", description]
        ]
        
        gate_info_table = Table(gate_info_data, colWidths=[1.5*inch, 4.5*inch])
        gate_info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(gate_info_table)
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
    
    def generate_summary_pdf(self, scan_results: Dict[str, Any], output_dir: str = "./reports/pdfs") -> Optional[str]:
        """Generate a summary PDF with all gates"""
        if not REPORTLAB_AVAILABLE:
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        
        scan_id = scan_results.get("scan_id", "unknown")
        filename = f"SUMMARY_{scan_id}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        # Title
        story.append(Paragraph("CodeGates Scan Summary", self.custom_styles['Title']))
        story.append(Spacer(1, 20))
        
        # Scan overview
        overall_score = scan_results.get("overall_score", 0)
        
        # Handle both gate_results (UI format) and gates (JSON report format)
        gate_results = scan_results.get("gate_results", [])
        if not gate_results:
            # Try to get from gates array (JSON report format)
            gate_results = scan_results.get("gates", [])
        
        passed = len([g for g in gate_results if g.get("status") == "PASS"])
        failed = len([g for g in gate_results if g.get("status") == "FAIL"])
        warnings = len([g for g in gate_results if g.get("status") == "WARNING"])
        not_applicable = len([g for g in gate_results if g.get("status") == "NOT_APPLICABLE"])
        
        summary_data = [
            ["Overall Score", f"{overall_score:.1f}%"],
            ["Total Gates", str(len(gate_results))],
            ["Passed", str(passed)],
            ["Failed", str(failed)],
            ["Warnings", str(warnings)],
            ["Not Applicable", str(not_applicable)]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Gates list
        story.append(Paragraph("Gate Results", self.custom_styles['Heading1']))
        
        gates_data = [["Gate", "Status", "Score", "Matches"]]
        for gate in gate_results:
            gates_data.append([
                gate.get("display_name", gate.get("gate", "Unknown")),
                gate.get("status", "UNKNOWN"),
                f"{gate.get('score', 0):.1f}%",
                str(gate.get("matches_found", 0))
            ])
        
        gates_table = Table(gates_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
        gates_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ]))
        
        story.append(gates_table)
        
        doc.build(story)
        print(f"📄 Generated summary PDF: {filename}")
        return filepath


def generate_gate_pdfs_from_scan_id(scan_id: str, base_dir: str = "./reports") -> List[str]:
    """
    Convenience function to generate PDFs from a scan ID
    
    Args:
        scan_id: The scan ID to generate PDFs for
        base_dir: Base directory where reports are stored
        
    Returns:
        List of generated PDF file paths
    """
    # Look for JSON report in the correct scan_id subdirectory
    json_path = os.path.join(base_dir, scan_id, f"codegates_report_{scan_id}.json")
    
    if not os.path.exists(json_path):
        print(f"❌ JSON report not found: {json_path}")
        return []
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            scan_results = json.load(f)
        
        pdf_generator = CodeGatesPDFGenerator()
        pdf_dir = os.path.join(base_dir, "pdfs", scan_id)
        
        # Generate individual gate PDFs
        pdf_files = pdf_generator.generate_individual_gate_pdfs(scan_results, pdf_dir)
        
        # Generate summary PDF
        summary_pdf = pdf_generator.generate_summary_pdf(scan_results, pdf_dir)
        if summary_pdf:
            pdf_files.append(summary_pdf)
        
        return pdf_files
        
    except Exception as e:
        print(f"❌ Failed to generate PDFs from scan {scan_id}: {e}")
        return []


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        scan_id = sys.argv[1]
        pdf_files = generate_gate_pdfs_from_scan_id(scan_id)
        
        if pdf_files:
            print(f"\n✅ Generated {len(pdf_files)} PDF files:")
            for pdf_file in pdf_files:
                print(f"   📄 {pdf_file}")
        else:
            print("❌ No PDF files generated")
    else:
        print("Usage: python pdf_generator.py <scan_id>") 