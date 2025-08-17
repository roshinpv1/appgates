#!/usr/bin/env python3
"""
Enhanced CodeGates Streamlit UI with JIRA Upload Integration
Functionality: APP ID -> Repos -> Branches -> Scan -> JIRA Upload per Gate
"""

import streamlit as st
import sys
import os
import requests
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional

# Add the gates directory to the path
sys.path.append(str(Path(__file__).parent.parent / "gates"))

# Try to import git operations, but make it optional
try:
    from utils.git_operations import EnhancedGitIntegration, Repository, Branch
    GIT_INTEGRATION_AVAILABLE = True
except ImportError:
    # Create fallback classes if git operations not available
    GIT_INTEGRATION_AVAILABLE = False
    
    class Repository:
        def __init__(self, full_name, description=None):
            self.full_name = full_name
            self.description = description
    
    class Branch:
        def __init__(self, name, commit_sha="unknown", last_commit_date="unknown", protected=False):
            self.name = name
            self.commit_sha = commit_sha
            self.last_commit_date = last_commit_date
            self.protected = protected
    
    class EnhancedGitIntegration:
        def get_repository_branches(self, repo_full_name):
            # Return mock branches for popular repositories
            mock_branches = [
                Branch("main", "abcd1234", "2024-01-01", False),
                Branch("develop", "efgh5678", "2024-01-01", False),
                Branch("feature/new-ui", "ijkl9012", "2024-01-01", False)
            ]
            return mock_branches

# Configuration
API_BASE = "http://localhost:8000/api/v1"

# Auto-detect if running in integrated mode
try:
    import requests
    # Try to connect to the main server
    response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
    if response.status_code == 200:
        API_BASE = "http://localhost:8000/api/v1"
        print("🔗 Connected to integrated CodeGates server")
    else:
        # Fallback to standalone mode
        API_BASE = "http://localhost:8000/api/v1"
except:
    # Default to localhost
    API_BASE = "http://localhost:8000/api/v1"

# Page configuration
st.set_page_config(
    page_title="CodeGates Scanner with JIRA Integration",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 1rem 0 0.5rem 0;
    }
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
    }
    .jira-upload-box {
        background-color: #f0f8ff;
        border: 2px solid #0066cc;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .gate-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f9f9f9;
    }
    .gate-card.fail {
        border-left: 4px solid #f44336;
        background-color: #ffebee;
    }
    .gate-card.warning {
        border-left: 4px solid #ff9800;
        background-color: #fff3e0;
    }
    .gate-card.pass {
        border-left: 4px solid #4caf50;
        background-color: #e8f5e8;
    }
    .stButton > button {
        width: 100%;
        margin: 0.2rem 0;
    }
    .jira-status {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .jira-success {
        background-color: #d4edda;
        color: #155724;
    }
    .jira-error {
        background-color: #f8d7da;
        color: #721c24;
    }
    .jira-pending {
        background-color: #fff3cd;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

def initialize_git_integration():
    """Initialize git integration"""
    if GIT_INTEGRATION_AVAILABLE:
        return EnhancedGitIntegration()
    else:
        st.warning("⚠️ Git integration not available. Using mock data.")
        return EnhancedGitIntegration()

def get_branches_for_repo(git: EnhancedGitIntegration, repo_full_name: str) -> List[Branch]:
    """Get branches for a repository"""
    try:
        return git.get_repository_branches(repo_full_name)
    except Exception as e:
        st.error(f"❌ Error getting branches: {e}")
        return []

def start_code_scan(repo_url: str, branch: str, github_token: str) -> Optional[str]:
    """Start a code scan"""
    try:
        payload = {
            "repository_url": repo_url,
            "branch": branch,
            "github_token": github_token if github_token else None
        }
        
        response = requests.post(f"{API_BASE}/scan", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("scan_id")
        else:
            st.error(f"❌ Scan failed: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Scan error: {e}")
        return None

def get_scan_status(scan_id: str) -> Optional[Dict]:
    """Get scan status"""
    try:
        response = requests.get(f"{API_BASE}/scan/{scan_id}/status", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_report_content(scan_id: str, report_type: str) -> Optional[str]:
    """Get report content"""
    try:
        response = requests.get(f"{API_BASE}/scan/{scan_id}/report/{report_type}", timeout=30)
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None

def format_recommendation_for_ui(gate: Dict) -> str:
    """Format recommendation for Streamlit UI display with clean, consistent formatting"""
    try:
        # Import the centralized recommendation formatter
        from gates.utils.recommendation_formatter import recommendation_formatter
        
        # Use the centralized formatter for consistent formatting
        return recommendation_formatter.format_recommendation_for_ui(gate, "streamlit")
        
    except ImportError:
        # Fallback to local formatting if import fails
        return _format_recommendation_fallback(gate)

def _clean_recommendation_text(text: str) -> str:
    """Clean recommendation text for consistent formatting without bullet points or graphics"""
    if not text:
        return ""
    
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove all bullet points and convert to plain text
    text = re.sub(r'^[\s]*[-•*][\s]*', '', text, flags=re.MULTILINE)
    
    # Clean up numbered lists
    text = re.sub(r'^[\s]*(\d+)[\s]*[\.\)][\s]*', r'\1. ', text, flags=re.MULTILINE)
    
    # Remove trailing whitespace
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    
    # Remove empty lines that might be left after removing bullets
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()

def _format_recommendation_fallback(gate: Dict) -> str:
    """Fallback recommendation formatting"""
    recommendations = gate.get("recommendations", [])
    if isinstance(recommendations, list) and recommendations:
        # Join multiple recommendations
        return _clean_recommendation_text(" ".join(recommendations))
    elif isinstance(recommendations, str):
        return _clean_recommendation_text(recommendations)
    else:
        # Generate a basic recommendation based on status
        status = gate.get("status", "UNKNOWN")
        gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
        score = gate.get("score", 0)
        
        if status == "FAIL":
            return f"Critical: {gate_name} needs immediate attention. Current score: {score:.1f}%. Implement recommended security measures."
        elif status == "WARNING":
            return f"Enhancement: {gate_name} could be improved. Current score: {score:.1f}%. Consider implementing additional security measures."
        elif status == "PASS":
            return f"Good: {gate_name} is compliant. Current score: {score:.1f}%. Continue maintaining current practices."
        else:
            return f"Review: {gate_name} status is {status}. Current score: {score:.1f}%."

def upload_gate_to_jira(scan_id: str, gate_index: int, gate_data: Dict, jira_ticket_id: str, comment: str) -> Dict:
    """Upload a specific gate to JIRA"""
    try:
        payload = {
            "app_id": st.session_state.get("app_id", "unknown"),
            "scan_id": scan_id,
            "report_type": "pdf",
            "gate_number": gate_index + 1,  # Gate numbers are 1-based
            "jira_ticket_id": jira_ticket_id,
            "comment": comment
        }
        
        response = requests.post(f"{API_BASE}/jira/upload", json=payload, timeout=60)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def show_jira_upload_interface(scan_id: str, gate_results: List[Dict]):
    """Show JIRA upload interface for individual gates"""
    st.header("🎯 JIRA Upload Interface")
    st.markdown("Upload individual gates to JIRA tickets with custom comments.")
    
    # JIRA Configuration Check
    st.subheader("🔧 JIRA Configuration")
    
    # Check if JIRA is configured
    try:
        response = requests.get(f"{API_BASE}/jira/status", timeout=10)
        if response.status_code == 200:
            jira_status = response.json()
            if jira_status.get("configured", False):
                st.success("✅ JIRA is configured and ready")
                st.info(f"📋 JIRA URL: {jira_status.get('url', 'Unknown')}")
            else:
                st.error("❌ JIRA is not configured")
                st.info("💡 Please configure JIRA environment variables (JIRA_URL, JIRA_USER, JIRA_TOKEN)")
                return
        else:
            st.warning("⚠️ Could not verify JIRA configuration")
    except Exception as e:
        st.warning(f"⚠️ JIRA status check failed: {e}")
    
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
        recommendation = format_recommendation_for_ui(gate)
        
        # Create gate card
        status_class = status.lower()
        st.markdown(f"""
        <div class="gate-card {status_class}">
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
                
                # Pre-filled comment based on gate status
                default_comment = ""
                if status == "FAIL":
                    default_comment = f"""CodeGates Gate Analysis - {gate_name}

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
                    default_comment = f"""CodeGates Gate Analysis - {gate_name}

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
                    default_comment = f"""CodeGates Gate Analysis - {gate_name}

COMPLIANCE: This gate passed compliance checks (score: {score:.1f}%).

Status: ✅ PASS
Category: {category}

This gate is compliant with security requirements. Use this report for audit documentation and reference.

Gate Details:
- Category: {category}
- Status: {status}
- Score: {score:.1f}%"""
                
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
                            result = upload_gate_to_jira(scan_id, gate_index, gate_data, jira_ticket_id.strip(), comment)
                            
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
                
                # Show upload history for this gate
                if f"upload_history_{gate_index}" not in st.session_state:
                    st.session_state[f"upload_history_{gate_index}"] = []
                
                if st.session_state[f"upload_history_{gate_index}"]:
                    st.markdown("**Recent Uploads:**")
                    for upload in st.session_state[f"upload_history_{gate_index}"][-3:]:  # Show last 3
                        st.markdown(f"- {upload['ticket']}: {upload['status']} ({upload['time']})")
        
        st.divider()

def show_scan_results(scan_id):
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
            
            # Store app_id in session state for JIRA uploads
            st.session_state.app_id = app_id
            
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
            tab1, tab2, tab3, tab4 = st.tabs([
                "🎯 JIRA Upload", 
                "📊 Gate Results", 
                "📄 PDF Generation",
                "📋 Reports"
            ])
            
            # ========================================
            # TAB 1: JIRA UPLOAD INTERFACE
            # ========================================
            with tab1:
                show_jira_upload_interface(scan_id, gate_results)
            
            # ========================================
            # TAB 2: GATE RESULTS
            # ========================================
            with tab2:
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
            # TAB 3: PDF GENERATION
            # ========================================
            with tab3:
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
            # TAB 4: REPORTS
            # ========================================
            with tab4:
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

def main():
    """Main application"""
    st.title("🔍 CodeGates Scanner with JIRA Integration")
    st.markdown("Enterprise-grade code security analysis with integrated JIRA upload functionality")
    
    # Initialize session state
    if "scan_id" not in st.session_state:
        st.session_state.scan_id = None
    if "scan_status" not in st.session_state:
        st.session_state.scan_status = None
    
    # Initialize git integration
    git = initialize_git_integration()
    
    # Main interface
    if st.session_state.scan_id and st.session_state.scan_status == "completed":
        # Show results
        show_scan_results(st.session_state.scan_id)
        
        # Option to start a new scan
        if st.button("🔄 Start New Scan"):
            st.session_state.scan_id = None
            st.session_state.scan_status = None
            st.rerun()
    
    elif st.session_state.scan_id and st.session_state.scan_status == "processing":
        # Show progress
        st.header("🔄 Scan in Progress")
        st.info("Your scan is currently processing. Please wait...")
        
        # Check status
        status = get_scan_status(st.session_state.scan_id)
        if status:
            if status.get("status") == "completed":
                st.session_state.scan_status = "completed"
                st.rerun()
            else:
                st.progress(status.get("progress", 0) / 100)
                st.write(f"Status: {status.get('current_step', 'Processing')}")
                st.write(f"Progress: {status.get('progress', 0)}%")
        
        # Auto-refresh
        import time
        time.sleep(2)
        st.rerun()
    
    else:
        # Show scan configuration
        st.markdown('<h2 class="section-header">1️⃣ Select Git Endpoint</h2>', unsafe_allow_html=True)
        
        git_endpoint = st.selectbox(
            "Git Endpoint:",
            ["github.com", "github.XYXY.com", "github.abc.com"],
            help="Select the Git platform to use"
        )
        
        st.markdown('<h2 class="section-header">2️⃣ Enter Application ID</h2>', unsafe_allow_html=True)
        
        app_id = st.text_input(
            "Application ID:",
            placeholder="e.g., mobile-app, web-service, data-pipeline",
            help="Enter the application identifier to search for related repositories"
        )
        
        if app_id:
            # Get repositories
            try:
                response = requests.post(
                    f"{API_BASE}/git/search-repositories",
                    json={"keywords": [app_id], "git_endpoint": git_endpoint, "limit": 10},
                    timeout=30
                )
                
                if response.status_code == 200:
                    repos_data = response.json()
                    if repos_data.get("success") and repos_data.get("repositories"):
                        st.markdown('<h2 class="section-header">3️⃣ Select Repository & Branch</h2>', unsafe_allow_html=True)
                        
                        # Repository selection
                        repo_options = [f"{repo['owner']}/{repo['name']}" for repo in repos_data["repositories"]]
                        selected_repo = st.selectbox("Repository:", repo_options)
                        
                        if selected_repo:
                            # Get branches
                            try:
                                branches_response = requests.post(
                                    f"{API_BASE}/git/list-branches",
                                    json={"owner": selected_repo.split("/")[0], "name": selected_repo.split("/")[1], "git_endpoint": git_endpoint},
                                    timeout=30
                                )
                                
                                if branches_response.status_code == 200:
                                    branches_data = branches_response.json()
                                    if branches_data.get("success") and branches_data.get("branches"):
                                        branch_names = [b["name"] for b in branches_data["branches"]]
                                        selected_branch = st.selectbox("Branch:", branch_names)
                                        
                                        if selected_branch:
                                            st.markdown('<h2 class="section-header">4️⃣ Configure & Start Scan</h2>', unsafe_allow_html=True)
                                            
                                            # GitHub Token
                                            github_token = st.text_input(
                                                "GitHub Token (Optional):",
                                                type="password",
                                                help="Provide GitHub token for private repositories or higher rate limits"
                                            )
                                            
                                            # Scan configuration
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                threshold = st.slider("Compliance Threshold (%)", 0, 100, 70)
                                            with col2:
                                                max_files = st.slider("Max Files to Process", 100, 10000, 1000)
                                            
                                            # Start scan
                                            if st.button("🚀 Start Security Scan", type="primary"):
                                                repo_url = f"https://{git_endpoint}/{selected_repo}"
                                                scan_id = start_code_scan(repo_url, selected_branch, github_token)
                                                
                                                if scan_id:
                                                    st.session_state.scan_id = scan_id
                                                    st.session_state.scan_status = "processing"
                                                    st.success(f"✅ Scan started! ID: {scan_id}")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Failed to start scan")
                                    else:
                                        st.error("❌ Failed to get branches")
                                else:
                                    st.error("❌ Failed to get branches")
                            except Exception as e:
                                st.error(f"❌ Error getting branches: {e}")
                    else:
                        st.warning("⚠️ No repositories found for this Application ID")
                else:
                    st.error("❌ Failed to search repositories")
            except Exception as e:
                st.error(f"❌ Error searching repositories: {e}")

if __name__ == "__main__":
    main() 