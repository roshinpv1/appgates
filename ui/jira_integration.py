#!/usr/bin/env python3
"""
JIRA Integration Module for Streamlit UI
Provides functions for uploading gate results to JIRA tickets
"""

import streamlit as st
import requests
import json
from typing import Dict, List, Optional

def check_jira_configuration(api_base: str) -> Dict:
    """Check if JIRA is properly configured"""
    try:
        response = requests.get(f"{api_base}/jira/status", timeout=10)
        if response.status_code == 200:
            return {"configured": True, "data": response.json()}
        else:
            return {"configured": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"configured": False, "error": str(e)}

def upload_gate_to_jira(api_base: str, scan_id: str, gate_index: int, gate_data: Dict, 
                       jira_ticket_id: str, comment: str, app_id: str = "unknown") -> Dict:
    """Upload a specific gate to JIRA"""
    try:
        payload = {
            "app_id": app_id,
            "scan_id": scan_id,
            "report_type": "pdf",
            "gate_number": gate_index + 1,  # Gate numbers are 1-based
            "jira_ticket_id": jira_ticket_id,
            "comment": comment
        }
        
        response = requests.post(f"{api_base}/jira/upload", json=payload, timeout=60)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_gate_comment(gate_data: Dict, gate_name: str, status: str, score: float, 
                         category: str, recommendation: str) -> str:
    """Generate a default comment for JIRA upload"""
    if status == "FAIL":
        return f"""CodeGates Gate Analysis - {gate_name}

CRITICAL: This gate failed compliance checks with a score of {score:.1f}%.

Key Issues:
- {recommendation}

Action Required:
- Review the attached PDF for detailed analysis
- Implement recommended security measures
- Re-scan after fixes to verify compliance

Gate Details:
- Category: {category}
- Status: {status}
- Score: {score:.1f}%"""
    
    elif status == "WARNING":
        return f"""CodeGates Gate Analysis - {gate_name}

ENHANCEMENT: This gate passed but has improvement opportunities (score: {score:.1f}%).

Recommendations:
- {recommendation}

Suggested Actions:
- Review the attached PDF for enhancement suggestions
- Consider implementing additional security measures
- Monitor for future improvements

Gate Details:
- Category: {category}
- Status: {status}
- Score: {score:.1f}%"""
    
    else:
        return f"""CodeGates Gate Analysis - {gate_name}

COMPLIANCE: This gate passed compliance checks (score: {score:.1f}%).

Status: ✅ PASS
Category: {category}

This gate is compliant with security requirements. Use this report for audit documentation and reference.

Gate Details:
- Category: {category}
- Status: {status}
- Score: {score:.1f}%"""

def show_jira_upload_interface(api_base: str, scan_id: str, gate_results: List[Dict], app_id: str = "unknown"):
    """Show JIRA upload interface for individual gates"""
    st.header("🎯 JIRA Upload Interface")
    st.markdown("Upload individual gates to JIRA tickets with custom comments.")
    
    # JIRA Configuration Check
    st.subheader("🔧 JIRA Configuration")
    
    jira_config = check_jira_configuration(api_base)
    if jira_config["configured"]:
        st.success("✅ JIRA is configured and ready")
        if "data" in jira_config and "url" in jira_config["data"]:
            st.info(f"📋 JIRA URL: {jira_config['data']['url']}")
    else:
        st.error("❌ JIRA is not configured")
        st.info("💡 Please configure JIRA environment variables (JIRA_URL, JIRA_USER, JIRA_TOKEN)")
        return
    
    # Gate Upload Interface
    st.subheader("📤 Upload Gates to JIRA")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            ["FAIL", "WARNING", "PASS", "NOT_APPLICABLE"],
            default=["FAIL", "WARNING"],
            help="Select which gate statuses to show"
        )
    
    with col2:
        category_filter = st.multiselect(
            "Filter by Category",
            list(set([g.get("category", "Unknown") for g in gate_results])),
            help="Select which categories to show"
        )
    
    # Filter gates
    filtered_gates = gate_results.copy()
    if status_filter:
        filtered_gates = [g for g in filtered_gates if g.get("status") in status_filter]
    if category_filter:
        filtered_gates = [g for g in filtered_gates if g.get("category") in category_filter]
    
    st.info(f"📋 Showing {len(filtered_gates)} gates (filtered from {len(gate_results)} total)")
    
    # Display gates with upload interface
    for i, gate in enumerate(filtered_gates):
        gate_index = gate_results.index(gate)  # Get original index
        gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
        status = gate.get("status", "UNKNOWN")
        score = gate.get("score", 0)
        category = gate.get("category", "Unknown")
        recommendation = gate.get("recommendation", "No specific recommendation available")
        
        # Create gate card
        status_class = status.lower()
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; 
                    background-color: {'#ffebee' if status == 'FAIL' else '#fff3e0' if status == 'WARNING' else '#e8f5e8'};
                    border-left: 4px solid {'#f44336' if status == 'FAIL' else '#ff9800' if status == 'WARNING' else '#4caf50'};">
            <h4>{gate_name}</h4>
            <p><strong>Status:</strong> {status} | <strong>Score:</strong> {score:.1f}% | <strong>Category:</strong> {category}</p>
            <p><strong>Recommendation:</strong> {recommendation}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # JIRA Upload Interface for this gate
        with st.expander(f"📤 Upload {gate_name} to JIRA", expanded=(status in ["FAIL", "WARNING"])):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                jira_ticket_id = st.text_input(
                    f"JIRA Ticket ID for {gate_name}",
                    key=f"ticket_{gate_index}",
                    placeholder="PROJ-123",
                    help="Enter the JIRA ticket ID where this gate should be uploaded"
                )
                
                # Generate default comment
                default_comment = generate_gate_comment(gate, gate_name, status, score, category, recommendation)
                
                comment = st.text_area(
                    f"Comment for {gate_name}",
                    value=default_comment,
                    key=f"comment_{gate_index}",
                    height=200,
                    help="Customize the comment that will be added to the JIRA ticket"
                )
            
            with col2:
                st.markdown("**Upload Options:**")
                
                # Show gate details
                st.info(f"""
                **Gate #{gate_index + 1}**
                - **Name:** {gate_name}
                - **Status:** {status}
                - **Score:** {score:.1f}%
                - **Category:** {category}
                """)
                
                # Upload button
                if st.button(f"📤 Upload to JIRA", key=f"upload_{gate_index}", type="primary"):
                    if not jira_ticket_id.strip():
                        st.error("❌ Please enter a JIRA ticket ID")
                    else:
                        with st.spinner(f"Uploading {gate_name} to JIRA..."):
                            result = upload_gate_to_jira(api_base, scan_id, gate_index, gate, jira_ticket_id.strip(), comment, app_id)
                            
                            if result["success"]:
                                st.success(f"✅ Successfully uploaded {gate_name} to {jira_ticket_id}")
                                st.info(f"📊 Result: {result['data'].get('message', 'Upload completed')}")
                                
                                # Show detailed results
                                if "results" in result["data"]:
                                    for res in result["data"]["results"]:
                                        story = res.get("story", "Unknown")
                                        comment_status = res.get("comment", "Unknown")
                                        attachment_status = res.get("attachment", "Unknown")
                                        st.markdown(f"""
                                        - **Ticket {story}:**
                                          - Comment: {comment_status}
                                          - Attachment: {attachment_status}
                                        """)
                            else:
                                st.error(f"❌ Upload failed: {result['error']}")
        
        st.divider()

def show_bulk_jira_upload(api_base: str, scan_id: str, gate_results: List[Dict], app_id: str = "unknown"):
    """Show bulk JIRA upload interface"""
    st.header("📦 Bulk JIRA Upload")
    st.markdown("Upload multiple gates to JIRA tickets at once.")
    
    # JIRA Configuration Check
    jira_config = check_jira_configuration(api_base)
    if not jira_config["configured"]:
        st.error("❌ JIRA is not configured")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.multiselect(
            "Select Gates by Status",
            ["FAIL", "WARNING", "PASS", "NOT_APPLICABLE"],
            default=["FAIL", "WARNING"],
            help="Select which gate statuses to include in bulk upload"
        )
    
    with col2:
        category_filter = st.multiselect(
            "Select Gates by Category",
            list(set([g.get("category", "Unknown") for g in gate_results])),
            help="Select which categories to include in bulk upload"
        )
    
    # Filter gates
    filtered_gates = gate_results.copy()
    if status_filter:
        filtered_gates = [g for g in filtered_gates if g.get("status") in status_filter]
    if category_filter:
        filtered_gates = [g for g in filtered_gates if g.get("category") in category_filter]
    
    st.info(f"📋 {len(filtered_gates)} gates selected for bulk upload")
    
    # Bulk upload configuration
    st.subheader("📋 Bulk Upload Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ticket_prefix = st.text_input(
            "JIRA Ticket Prefix",
            value="PROJ",
            help="Prefix for JIRA ticket IDs (e.g., PROJ-123)"
        )
        
        start_number = st.number_input(
            "Starting Ticket Number",
            min_value=1,
            value=1,
            help="Starting number for ticket sequence"
        )
    
    with col2:
        include_passed = st.checkbox(
            "Include PASS gates",
            value=False,
            help="Include gates that passed compliance checks"
        )
        
        auto_comment = st.checkbox(
            "Use auto-generated comments",
            value=True,
            help="Use automatically generated comments based on gate status"
        )
    
    # Show selected gates
    if filtered_gates:
        st.subheader("📋 Selected Gates for Upload")
        
        gate_list = []
        for i, gate in enumerate(filtered_gates):
            gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
            status = gate.get("status", "UNKNOWN")
            score = gate.get("score", 0)
            ticket_id = f"{ticket_prefix}-{start_number + i}"
            
            gate_list.append({
                "Gate": gate_name,
                "Status": status,
                "Score": f"{score:.1f}%",
                "Ticket ID": ticket_id
            })
        
        # Display as table
        import pandas as pd
        df = pd.DataFrame(gate_list)
        st.dataframe(df, use_container_width=True)
        
        # Bulk upload button
        if st.button("📤 Start Bulk Upload", type="primary"):
            with st.spinner("Processing bulk upload..."):
                success_count = 0
                failed_count = 0
                
                for i, gate in enumerate(filtered_gates):
                    gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
                    status = gate.get("status", "UNKNOWN")
                    score = gate.get("score", 0)
                    category = gate.get("category", "Unknown")
                    recommendation = gate.get("recommendation", "No specific recommendation available")
                    ticket_id = f"{ticket_prefix}-{start_number + i}"
                    
                    # Generate comment
                    if auto_comment:
                        comment = generate_gate_comment(gate, gate_name, status, score, category, recommendation)
                    else:
                        comment = f"CodeGates analysis for {gate_name} - Status: {status}, Score: {score:.1f}%"
                    
                    # Upload gate
                    result = upload_gate_to_jira(api_base, scan_id, i, gate, ticket_id, comment, app_id)
                    
                    if result["success"]:
                        success_count += 1
                    else:
                        failed_count += 1
                
                # Show results
                st.success(f"✅ Bulk upload completed!")
                st.info(f"📊 Results: {success_count} successful, {failed_count} failed")
                
                if failed_count > 0:
                    st.warning("⚠️ Some uploads failed. Check the logs above for details.")
    
    else:
        st.warning("⚠️ No gates selected for bulk upload. Please adjust your filters.") 