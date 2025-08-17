#!/usr/bin/env python3
"""
Integration Guide: Adding JIRA Upload to Streamlit UI
This script shows how to integrate JIRA upload functionality into the existing Streamlit UI
"""

# Add this to the top of your existing simple_app.py file:

"""
# Add this import at the top of simple_app.py
from ui.jira_integration import show_jira_upload_interface, show_bulk_jira_upload
"""

# Then modify the show_scan_results function to include JIRA upload tabs:

"""
def show_scan_results(scan_id):
    # ... existing code ...
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 JIRA Upload", 
        "📦 Bulk JIRA Upload",
        "📊 Gate Results", 
        "📄 PDF Generation",
        "📋 Reports"
    ])
    
    # ========================================
    # TAB 1: INDIVIDUAL JIRA UPLOAD
    # ========================================
    with tab1:
        show_jira_upload_interface(API_BASE, scan_id, gate_results, app_id)
    
    # ========================================
    # TAB 2: BULK JIRA UPLOAD
    # ========================================
    with tab2:
        show_bulk_jira_upload(API_BASE, scan_id, gate_results, app_id)
    
    # ... rest of existing tabs ...
"""

# Example usage in the main function:

"""
def main():
    # ... existing code ...
    
    if st.session_state.scan_id and st.session_state.scan_status == "completed":
        # Show results with JIRA integration
        show_scan_results(st.session_state.scan_id)
        
        # Option to start a new scan
        if st.button("🔄 Start New Scan"):
            st.session_state.scan_id = None
            st.session_state.scan_status = None
            st.rerun()
    
    # ... rest of existing code ...
"""

# Complete integration example:

def show_scan_results_with_jira(scan_id):
    """Display scan results with JIRA upload integration"""
    try:
        # Get scan results
        response = requests.get(f"{API_BASE}/scan/{scan_id}/results", timeout=30)
        if response.status_code == 200:
            results = response.json()
            
            # Display basic results
            overall_score = results.get("overall_score", 0)
            gate_results = results.get("gate_results", [])
            app_id = results.get("app_id", "unknown")
            
            # Main results display
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Overall Score", f"{overall_score:.1f}%")
            with col2:
                st.metric("Total Gates", len(gate_results))
            with col3:
                passed_gates = len([g for g in gate_results if g.get("status") == "PASS"])
                st.metric("Passed Gates", passed_gates)
            with col4:
                failed_gates = len([g for g in gate_results if g.get("status") == "FAIL"])
                st.metric("Failed Gates", failed_gates)
            
            st.divider()
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🎯 JIRA Upload", 
                "📦 Bulk JIRA Upload",
                "📊 Gate Results", 
                "📄 PDF Generation",
                "📋 Reports"
            ])
            
            # ========================================
            # TAB 1: INDIVIDUAL JIRA UPLOAD
            # ========================================
            with tab1:
                from ui.jira_integration import show_jira_upload_interface
                show_jira_upload_interface(API_BASE, scan_id, gate_results, app_id)
            
            # ========================================
            # TAB 2: BULK JIRA UPLOAD
            # ========================================
            with tab2:
                from ui.jira_integration import show_bulk_jira_upload
                show_bulk_jira_upload(API_BASE, scan_id, gate_results, app_id)
            
            # ========================================
            # TAB 3: GATE RESULTS (existing functionality)
            # ========================================
            with tab3:
                st.subheader("📊 Gate Results Summary")
                
                # Create a comprehensive summary table
                gate_data = []
                for i, gate in enumerate(gate_results):
                    recommendation = format_recommendation_for_ui(gate)
                    gate_data.append({
                        "Gate #": i + 1,
                        "Gate": gate.get("display_name", gate.get("gate", "Unknown")),
                        "Status": gate.get("status", "UNKNOWN"),
                        "Score": f"{gate.get('score', 0):.1f}%",
                        "Category": gate.get("category", "Unknown"),
                        "Matches": gate.get("matches_found", 0),
                        "Recommendation": recommendation
                    })
                
                # Display as dataframe with better formatting
                df = pd.DataFrame(gate_data)
                
                # Style the dataframe
                def style_status(val):
                    if val == "PASS":
                        return "background-color: #d4edda; color: #155724"
                    elif val == "FAIL":
                        return "background-color: #f8d7da; color: #721c24"
                    elif val == "WARNING":
                        return "background-color: #fff3cd; color: #856404"
                    else:
                        return "background-color: #e2e3e5; color: #383d41"
                
                styled_df = df.style.applymap(style_status, subset=['Status'])
                st.dataframe(styled_df, use_container_width=True, height=400)
            
            # ========================================
            # TAB 4: PDF GENERATION (existing functionality)
            # ========================================
            with tab4:
                st.subheader("📄 PDF Generation")
                st.markdown("Generate PDFs for JIRA attachments.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚀 Generate All Gate PDFs", type="primary"):
                        with st.spinner("Generating PDFs..."):
                            try:
                                response = requests.get(f"{API_BASE}/scan/{scan_id}/pdfs", timeout=120)
                                if response.status_code == 200:
                                    pdf_data = response.json()
                                    st.success(f"✅ Generated {pdf_data['total_files']} PDF files!")
                                else:
                                    st.error(f"❌ Generation failed: {response.status_code}")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    
                    if st.button("⚡ Generate Failed Gates Only"):
                        with st.spinner("Generating failed gate PDFs..."):
                            try:
                                filter_data = {"status_filter": ["FAIL"]}
                                response = requests.post(
                                    f"{API_BASE}/scan/{scan_id}/generate-jira-pdfs",
                                    json=filter_data,
                                    timeout=120
                                )
                                if response.status_code == 200:
                                    pdf_data = response.json()
                                    st.success(f"✅ Generated {pdf_data['total_files']} PDF files!")
                                else:
                                    st.error(f"❌ Generation failed: {response.status_code}")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                
                with col2:
                    # PDF Status
                    try:
                        response = requests.get(f"{API_BASE}/scan/{scan_id}/pdfs", timeout=10)
                        if response.status_code == 200:
                            pdf_data = response.json()
                            if pdf_data["total_files"] > 0:
                                st.success(f"✅ {pdf_data['total_files']} PDFs available")
                                st.info(f"📋 {pdf_data.get('individual_gates', 0)} individual gate PDFs")
                            else:
                                st.warning("⚠️ No PDFs generated yet")
                    except Exception as e:
                        st.error(f"❌ Error checking PDF status: {e}")
            
            # ========================================
            # TAB 5: REPORTS (existing functionality)
            # ========================================
            with tab5:
                st.subheader("📋 Full Reports")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📄 View HTML Report"):
                        try:
                            html_response = requests.get(f"{API_BASE}/scan/{scan_id}/report/html", timeout=30)
                            if html_response.status_code == 200:
                                st.components.v1.html(html_response.text, height=600, scrolling=True)
                            else:
                                st.error(f"❌ HTML Report Failed: {html_response.status_code}")
                        except Exception as e:
                            st.error(f"❌ HTML Report Error: {e}")
                
                with col2:
                    if st.button("📋 View JSON Report"):
                        try:
                            json_response = requests.get(f"{API_BASE}/scan/{scan_id}/report/json", timeout=30)
                            if json_response.status_code == 200:
                                json_data = json_response.json()
                                st.json(json_data)
                            else:
                                st.error(f"❌ JSON Report Failed: {json_response.status_code}")
                        except Exception as e:
                            st.error(f"❌ JSON Report Error: {e}")
            
        else:
            st.error(f"❌ Failed to get scan results: {response.status_code}")
    
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. The scan might still be processing.")
    except Exception as e:
        st.error(f"❌ Results Error: {e}")

# Usage instructions:

"""
To integrate JIRA upload into your existing Streamlit UI:

1. Copy the jira_integration.py file to your ui/ directory
2. Add the import statement at the top of your simple_app.py:
   from ui.jira_integration import show_jira_upload_interface, show_bulk_jira_upload

3. Replace your existing show_scan_results function with show_scan_results_with_jira
   OR modify your existing function to include the JIRA upload tabs

4. Make sure your JIRA environment variables are configured:
   - JIRA_URL
   - JIRA_USER  
   - JIRA_TOKEN

5. The JIRA upload functionality will be available in two tabs:
   - Individual gate upload with custom comments
   - Bulk upload for multiple gates

Features included:
- ✅ Individual gate upload with custom comments
- ✅ Bulk upload for multiple gates
- ✅ Automatic comment generation based on gate status
- ✅ JIRA configuration validation
- ✅ Upload status tracking
- ✅ Error handling and user feedback
- ✅ Filtering by status and category
- ✅ Integration with existing PDF generation
"""

if __name__ == "__main__":
    print("This is an integration guide. Copy the code above into your Streamlit UI.")
    print("See the comments for detailed integration instructions.") 