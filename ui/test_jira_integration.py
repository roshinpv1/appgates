#!/usr/bin/env python3
"""
Test Script for JIRA Integration in Streamlit UI
Demonstrates the JIRA upload functionality
"""

import streamlit as st
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jira_integration import (
    check_jira_configuration,
    upload_gate_to_jira,
    generate_gate_comment,
    show_jira_upload_interface,
    show_bulk_jira_upload
)

# Configuration
API_BASE = "http://localhost:8000/api/v1"

# Page configuration
st.set_page_config(
    page_title="JIRA Integration Test",
    page_icon="🔍",
    layout="wide"
)

def main():
    """Test the JIRA integration functionality"""
    st.title("🧪 JIRA Integration Test")
    st.markdown("Testing JIRA upload functionality for individual gates")
    
    # Test JIRA Configuration
    st.header("🔧 JIRA Configuration Test")
    
    jira_config = check_jira_configuration(API_BASE)
    if jira_config["configured"]:
        st.success("✅ JIRA is configured and ready")
        if "data" in jira_config and "url" in jira_config["data"]:
            st.info(f"📋 JIRA URL: {jira_config['data']['url']}")
    else:
        st.error("❌ JIRA is not configured")
        st.info("💡 Please configure JIRA environment variables (JIRA_URL, JIRA_USER, JIRA_TOKEN)")
        st.stop()
    
    # Test Comment Generation
    st.header("📝 Comment Generation Test")
    
    # Sample gate data
    sample_gates = [
        {
            "display_name": "Structured Logging",
            "status": "FAIL",
            "score": 25.0,
            "category": "Auditability",
            "recommendation": "Implement structured logging with proper log levels and context information"
        },
        {
            "display_name": "Auto Scaling",
            "status": "WARNING",
            "score": 65.0,
            "category": "Availability",
            "recommendation": "Configure horizontal pod autoscaler and connection pooling"
        },
        {
            "display_name": "Error Handling",
            "status": "PASS",
            "score": 95.0,
            "category": "Error Handling",
            "recommendation": "Continue maintaining current error handling practices"
        }
    ]
    
    # Test comment generation for each gate
    for i, gate in enumerate(sample_gates):
        with st.expander(f"Test Comment for {gate['display_name']}"):
            comment = generate_gate_comment(
                gate, 
                gate['display_name'], 
                gate['status'], 
                gate['score'], 
                gate['category'], 
                gate['recommendation']
            )
            st.text_area(f"Generated Comment for {gate['display_name']}", comment, height=200)
    
    # Test Upload Interface
    st.header("📤 Upload Interface Test")
    
    # Create mock scan data
    mock_scan_id = "test-scan-123"
    mock_app_id = "test-app-123"
    
    # Show the upload interface with sample data
    show_jira_upload_interface(API_BASE, mock_scan_id, sample_gates, mock_app_id)
    
    # Test Bulk Upload Interface
    st.header("📦 Bulk Upload Interface Test")
    
    show_bulk_jira_upload(API_BASE, mock_scan_id, sample_gates, mock_app_id)
    
    # Test Upload Function
    st.header("🔧 Upload Function Test")
    
    st.subheader("Test Individual Upload")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_ticket_id = st.text_input("Test JIRA Ticket ID", "TEST-123")
        test_comment = st.text_area("Test Comment", "This is a test upload from the integration test")
    
    with col2:
        if st.button("🧪 Test Upload Function"):
            if test_ticket_id.strip():
                with st.spinner("Testing upload function..."):
                    # Note: This will fail because TEST-123 doesn't exist, but it tests the function
                    result = upload_gate_to_jira(
                        API_BASE, 
                        mock_scan_id, 
                        0,  # First gate
                        sample_gates[0], 
                        test_ticket_id.strip(), 
                        test_comment, 
                        mock_app_id
                    )
                    
                    if result["success"]:
                        st.success("✅ Upload function test successful!")
                        st.json(result["data"])
                    else:
                        st.warning("⚠️ Upload function test failed (expected for test ticket)")
                        st.info(f"Error: {result['error']}")
                        st.info("This is expected behavior for a test ticket that doesn't exist")
            else:
                st.error("❌ Please enter a test ticket ID")
    
    # Integration Instructions
    st.header("📚 Integration Instructions")
    
    st.markdown("""
    ### How to Integrate JIRA Upload into Your Streamlit UI:
    
    1. **Copy the jira_integration.py file** to your ui/ directory
    
    2. **Add the import** at the top of your simple_app.py:
    ```python
    from ui.jira_integration import show_jira_upload_interface, show_bulk_jira_upload
    ```
    
    3. **Modify your show_scan_results function** to include JIRA upload tabs:
    ```python
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 JIRA Upload", 
        "📦 Bulk JIRA Upload",
        "📊 Gate Results", 
        "📄 PDF Generation",
        "📋 Reports"
    ])
    
    # TAB 1: INDIVIDUAL JIRA UPLOAD
    with tab1:
        show_jira_upload_interface(API_BASE, scan_id, gate_results, app_id)
    
    # TAB 2: BULK JIRA UPLOAD
    with tab2:
        show_bulk_jira_upload(API_BASE, scan_id, gate_results, app_id)
    ```
    
    4. **Configure JIRA environment variables**:
    ```bash
    export JIRA_URL="https://your-instance.atlassian.net"
    export JIRA_USER="your-username"
    export JIRA_TOKEN="your-api-token"
    ```
    
    5. **Test the integration** by running a scan and using the JIRA upload tabs
    
    ### Features Available:
    
    - ✅ **Individual Gate Upload**: Upload each gate to a specific JIRA ticket
    - ✅ **Custom Comments**: Edit comments before uploading
    - ✅ **Bulk Upload**: Upload multiple gates at once
    - ✅ **Auto-generated Comments**: Comments based on gate status and score
    - ✅ **Status Filtering**: Filter gates by status (FAIL, WARNING, PASS)
    - ✅ **Category Filtering**: Filter gates by category
    - ✅ **Upload Status Tracking**: See success/failure for each upload
    - ✅ **Error Handling**: Proper error messages and user feedback
    """)

if __name__ == "__main__":
    main() 