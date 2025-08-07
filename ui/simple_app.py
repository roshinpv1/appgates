#!/usr/bin/env python3
"""
Simple CodeGates Streamlit UI App
Functionality: APP ID -> Repos -> Branches -> Scan
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
    page_title="CodeGates Scanner",
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
    .error-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sample APP ID data (replace with your actual data source)
APP_ID_DATA = {
    "FRONTEND_REACT": {
        "name": "Frontend React Apps",
        "description": "React-based frontend applications",
        "repos": [
            "facebook/react",
            "vercel/next.js",
            "remix-run/remix",
            "gatsbyjs/gatsby"
        ]
    },
    "BACKEND_API": {
        "name": "Backend API Services",
        "description": "Backend API and microservices",
        "repos": [
            "fastapi/fastapi",
            "pallets/flask",
            "django/django",
            "expressjs/express"
        ]
    },
    "MOBILE_APPS": {
        "name": "Mobile Applications",
        "description": "Mobile app development",
        "repos": [
            "facebook/react-native",
            "flutter/flutter",
            "ionic-team/ionic-framework",
            "expo/expo"
        ]
    },
    "DATA_SCIENCE": {
        "name": "Data Science Projects",
        "description": "ML and data analysis projects",
        "repos": [
            "pandas-dev/pandas",
            "scikit-learn/scikit-learn",
            "tensorflow/tensorflow",
            "pytorch/pytorch"
        ]
    },
    "DEVOPS_TOOLS": {
        "name": "DevOps & Infrastructure",
        "description": "DevOps and infrastructure tools",
        "repos": [
            "kubernetes/kubernetes",
            "docker/docker-ce",
            "ansible/ansible",
            "terraform-providers/terraform-provider-aws"
        ]
    }
}

# Initialize session state
if 'selected_app_id' not in st.session_state:
    st.session_state.selected_app_id = None
if 'selected_repo' not in st.session_state:
    st.session_state.selected_repo = None
if 'selected_branch' not in st.session_state:
    st.session_state.selected_branch = None
if 'available_branches' not in st.session_state:
    st.session_state.available_branches = []
if 'scan_id' not in st.session_state:
    st.session_state.scan_id = None

def initialize_git_integration():
    """Initialize git integration"""
    try:
        git_integration = EnhancedGitIntegration()
        if not GIT_INTEGRATION_AVAILABLE:
            st.info("ℹ️ Using mock git integration (git operations module not found)")
        return git_integration
    except Exception as e:
        st.error(f"❌ Failed to initialize git integration: {e}")
        return None

def get_branches_for_repo(git: EnhancedGitIntegration, repo_full_name: str) -> List[Branch]:
    """Get branches for a repository"""
    try:
        branches = git.get_repository_branches(repo_full_name)
        if not GIT_INTEGRATION_AVAILABLE:
            # Add repository-specific mock branches
            if "react" in repo_full_name.lower():
                branches.extend([Branch("gh-pages", "react123", "2024-01-01", True)])
            elif "fastapi" in repo_full_name.lower():
                branches.extend([Branch("release", "fast456", "2024-01-01", True)])
        return branches
    except Exception as e:
        if GIT_INTEGRATION_AVAILABLE:
            st.error(f"❌ Failed to get branches for {repo_full_name}: {e}")
        else:
            st.warning(f"⚠️ Using mock branches for {repo_full_name}")
        # Return default mock branches
        return [
            Branch("main", "default1", "2024-01-01", False),
            Branch("develop", "default2", "2024-01-01", False)
        ]

def start_code_scan(repo_url: str, branch: str, github_token: str) -> Optional[str]:
    """Start a code scan"""
    try:
        scan_request = {
            "repository_url": repo_url,
            "branch": branch,
            "github_token": github_token if github_token.strip() else None,
            "threshold": 70,
            "report_format": "both"
        }
        
        response = requests.post(
            f"{API_BASE}/scan",
            json=scan_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("scan_id")
        else:
            st.error(f"❌ Failed to start scan: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"❌ Scan request failed: {e}")
        return None

def get_scan_status(scan_id: str) -> Optional[Dict]:
    """Get scan status"""
    try:
        response = requests.get(
            f"{API_BASE}/scan/{scan_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        return None

def get_report_content(scan_id: str, report_type: str) -> Optional[str]:
    """Get report content (html or json)"""
    try:
        response = requests.get(
            f"{API_BASE}/scan/{scan_id}/report/{report_type}",
            timeout=10
        )
        
        if response.status_code == 200:
            if report_type == "json":
                return response.json()
            else:
                return response.text
        else:
            return None
            
    except Exception as e:
        return None

def show_scan_results(scan_id):
    """Display scan results with comprehensive PDF generation interface"""
    try:
        # Get scan results
        response = requests.get(f"{API_BASE}/scan/{scan_id}/results", timeout=30)
        if response.status_code == 200:
            results = response.json()
            
            # Display basic results
            overall_score = results.get("overall_score", 0)
            gate_results = results.get("gate_results", [])
            
            # Main results display
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Score", f"{overall_score:.1f}%")
            with col2:
                st.metric("Total Gates", len(gate_results))
            with col3:
                passed_gates = len([g for g in gate_results if g.get("status") == "PASS"])
                st.metric("Passed Gates", passed_gates)
            
            st.divider()
            
            # ========================================
            # COMPREHENSIVE PDF GENERATION INTERFACE
            # ========================================
            
            st.header("📄 PDF Generation for JIRA Integration")
            st.markdown("""
            Generate individual PDF documents for each gate with complete HTML report data. 
            Perfect for creating individual JIRA tickets with detailed analysis.
            """)
            
            # Create tabs for different PDF operations
            tab1, tab2, tab3, tab4 = st.tabs([
                "🔄 Quick Generate", 
                "🎯 Filtered Generate", 
                "📋 Manage Downloads", 
                "📊 PDF Status"
            ])
            
            # ========================================
            # TAB 1: QUICK GENERATE
            # ========================================
            with tab1:
                st.subheader("Quick PDF Generation")
                st.markdown("Generate PDFs quickly with common options.")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Quick generation options
                    st.markdown("**Choose Generation Type:**")
                    
                    if st.button("🚀 Generate All Individual Gate PDFs", 
                                type="primary", 
                                use_container_width=True,
                                help="Generate one PDF per gate (recommended for JIRA)"):
                        with st.spinner("Generating all gate PDFs..."):
                            try:
                                response = requests.get(f"{API_BASE}/scan/{scan_id}/pdfs", timeout=120)
                                if response.status_code == 200:
                                    pdf_data = response.json()
                                    st.success(f"✅ Generated {pdf_data['total_files']} PDF files!")
                                    st.info(f"📋 {pdf_data.get('individual_gates', 0)} individual gate PDFs created")
                                    st.session_state.pdf_generated = True
                                    st.rerun()
                                else:
                                    st.error(f"❌ Generation failed: {response.status_code}")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    
                    if st.button("⚡ Generate Only Failed Gates", 
                                use_container_width=True,
                                help="Generate PDFs only for FAIL status gates"):
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
                                    st.success(f"✅ Generated {pdf_data['total_files']} PDF files for failed gates!")
                                    st.session_state.pdf_generated = True
                                    st.rerun()
                                else:
                                    st.error(f"❌ Generation failed: {response.status_code}")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    
                    if st.button("⚠️ Generate Problem Gates (FAIL + WARNING)", 
                                use_container_width=True,
                                help="Generate PDFs for gates that need attention"):
                        with st.spinner("Generating problem gate PDFs..."):
                            try:
                                filter_data = {"status_filter": ["FAIL", "WARNING"]}
                                response = requests.post(
                                    f"{API_BASE}/scan/{scan_id}/generate-jira-pdfs",
                                    json=filter_data,
                                    timeout=120
                                )
                                if response.status_code == 200:
                                    pdf_data = response.json()
                                    st.success(f"✅ Generated {pdf_data['total_files']} PDF files for problem gates!")
                                    st.session_state.pdf_generated = True
                                    st.rerun()
                                else:
                                    st.error(f"❌ Generation failed: {response.status_code}")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                
                with col2:
                    # Status summary
                    st.markdown("**Gate Status Summary:**")
                    
                    fail_count = len([g for g in gate_results if g.get("status") == "FAIL"])
                    warning_count = len([g for g in gate_results if g.get("status") == "WARNING"])
                    pass_count = len([g for g in gate_results if g.get("status") == "PASS"])
                    na_count = len([g for g in gate_results if g.get("status") == "NOT_APPLICABLE"])
                    
                    st.metric("❌ Failed", fail_count)
                    st.metric("⚠️ Warnings", warning_count)
                    st.metric("✅ Passed", pass_count)
                    st.metric("➖ N/A", na_count)
            
            # ========================================
            # TAB 2: FILTERED GENERATE
            # ========================================
            with tab2:
                st.subheader("Advanced Filtered Generation")
                st.markdown("Generate PDFs with custom filters and options.")
                
                # Filter controls
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Filter by Status:**")
                    status_filter = st.multiselect(
                        "Select Statuses",
                        ["FAIL", "WARNING", "PASS", "NOT_APPLICABLE"],
                        default=[],
                        help="Choose which gate statuses to include"
                    )
                    
                    st.markdown("**Filter by Gate Numbers:**")
                    gate_numbers_input = st.text_input(
                        "Gate Numbers (comma-separated)",
                        placeholder="1,3,5,7",
                        help="Enter specific gate numbers to generate (e.g., 1,3,5)"
                    )
                
                with col2:
                    st.markdown("**Filter by Category:**")
                    categories = list(set([g.get("category", "Unknown") for g in gate_results]))
                    category_filter = st.multiselect(
                        "Select Categories",
                        categories,
                        default=[],
                        help="Choose which categories to include"
                    )
                    
                    st.markdown("**Filter by Gate Names:**")
                    gate_names = [g.get("gate", "Unknown") for g in gate_results]
                    gate_name_filter = st.multiselect(
                        "Select Specific Gates",
                        gate_names,
                        default=[],
                        help="Choose specific gates by name"
                    )
                
                # Generate with filters
                if st.button("🎯 Generate Filtered PDFs", 
                            type="primary", 
                            use_container_width=True):
                    
                    # Prepare filter data
                    filter_data = {}
                    
                    if status_filter:
                        filter_data["status_filter"] = status_filter
                    if category_filter:
                        filter_data["category_filter"] = category_filter
                    if gate_name_filter:
                        filter_data["gate_names"] = gate_name_filter
                    
                    # Parse gate numbers
                    if gate_numbers_input.strip():
                        try:
                            gate_numbers = [int(x.strip()) for x in gate_numbers_input.split(",") if x.strip()]
                            if gate_numbers:
                                filter_data["gate_numbers"] = gate_numbers
                        except ValueError:
                            st.error("❌ Invalid gate numbers. Use format: 1,3,5")
                            st.stop()
                    
                    if not filter_data:
                        st.warning("⚠️ Please select at least one filter option")
                        st.stop()
                    
                    with st.spinner("Generating filtered PDFs..."):
                        try:
                            response = requests.post(
                                f"{API_BASE}/scan/{scan_id}/generate-jira-pdfs",
                                json=filter_data,
                                timeout=120
                            )
                            if response.status_code == 200:
                                pdf_data = response.json()
                                st.success(f"✅ Generated {pdf_data['total_files']} filtered PDF files!")
                                
                                # Show filter summary
                                with st.expander("📊 Filter Applied"):
                                    st.json(filter_data)
                                
                                st.session_state.pdf_generated = True
                                st.rerun()
                            else:
                                st.error(f"❌ Generation failed: {response.status_code}")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                
                # Preview what will be generated
                if status_filter or category_filter or gate_name_filter or gate_numbers_input.strip():
                    st.markdown("**Preview: Gates that match your filters:**")
                    
                    preview_gates = gate_results.copy()
                    
                    if status_filter:
                        preview_gates = [g for g in preview_gates if g.get("status") in status_filter]
                    if category_filter:
                        preview_gates = [g for g in preview_gates if g.get("category") in category_filter]
                    if gate_name_filter:
                        preview_gates = [g for g in preview_gates if g.get("gate") in gate_name_filter]
                    
                    if gate_numbers_input.strip():
                        try:
                            gate_numbers = [int(x.strip()) for x in gate_numbers_input.split(",") if x.strip()]
                            if gate_numbers:
                                filtered_gates = []
                                for gate_num in gate_numbers:
                                    if 1 <= gate_num <= len(gate_results):
                                        filtered_gates.append(gate_results[gate_num - 1])
                                preview_gates = filtered_gates
                        except ValueError:
                            pass
                    
                    if preview_gates:
                        st.info(f"📋 Will generate {len(preview_gates)} PDFs")
                        for i, gate in enumerate(preview_gates[:5]):  # Show first 5
                            st.write(f"• Gate {i+1}: {gate.get('display_name', gate.get('gate', 'Unknown'))} ({gate.get('status', 'UNKNOWN')})")
                        if len(preview_gates) > 5:
                            st.write(f"... and {len(preview_gates) - 5} more gates")
                    else:
                        st.warning("⚠️ No gates match your current filters")
            
            # ========================================
            # TAB 3: MANAGE DOWNLOADS
            # ========================================
            with tab3:
                st.subheader("Download Generated PDFs")
                st.markdown("Download and manage your generated PDF files.")
                
                # Check for existing PDFs
                try:
                    response = requests.get(f"{API_BASE}/scan/{scan_id}/pdfs", timeout=10)
                    if response.status_code == 200:
                        pdf_data = response.json()
                        
                        if pdf_data["total_files"] > 0:
                            individual_gates = pdf_data.get('individual_gates', 0)
                            
                            # Summary
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total PDFs", pdf_data["total_files"])
                            with col2:
                                st.metric("Individual Gates", individual_gates)
                            with col3:
                                st.metric("Summary PDFs", pdf_data["total_files"] - individual_gates)
                            
                            st.divider()
                            
                            # Organized download interface
                            st.markdown("**📋 Individual Gate PDFs:**")
                            
                            # Group by status for better organization
                            status_groups = {"FAIL": [], "WARNING": [], "PASS": [], "NOT_APPLICABLE": [], "OTHER": []}
                            
                            for file_info in pdf_data["pdf_files"]:
                                if file_info["type"] == "individual_gate":
                                    # Get gate info to determine status
                                    gate_number = file_info.get("gate_number")
                                    if gate_number and gate_number <= len(gate_results):
                                        gate_data = gate_results[gate_number - 1]
                                        status = gate_data.get("status", "OTHER")
                                        if status in status_groups:
                                            status_groups[status].append((file_info, gate_data))
                                        else:
                                            status_groups["OTHER"].append((file_info, gate_data))
                            
                            # Display by status groups
                            for status, items in status_groups.items():
                                if items:
                                    status_emoji = {"FAIL": "❌", "WARNING": "⚠️", "PASS": "✅", "NOT_APPLICABLE": "➖", "OTHER": "❓"}
                                    
                                    with st.expander(f"{status_emoji[status]} {status} Gates ({len(items)} files)", expanded=(status in ["FAIL", "WARNING"])):
                                        for file_info, gate_data in items:
                                            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                                            
                                            with col1:
                                                st.write(f"**Gate {file_info.get('gate_number', '?')}**")
                                            with col2:
                                                st.write(gate_data.get('display_name', file_info.get('gate_name', 'Unknown')))
                                            with col3:
                                                file_size_kb = file_info["file_size"] // 1024
                                                st.write(f"{file_size_kb} KB")
                                            with col4:
                                                download_url = f"{API_BASE}{file_info['download_url']}"
                                                st.link_button("⬇️", download_url, key=f"download_gate_{file_info.get('gate_number', 'unknown')}")
                            
                            # Summary PDFs
                            summary_files = [f for f in pdf_data["pdf_files"] if f["type"] == "summary"]
                            if summary_files:
                                st.markdown("**📊 Summary PDFs:**")
                                for file_info in summary_files:
                                    col1, col2, col3 = st.columns([4, 1, 1])
                                    with col1:
                                        st.write(f"📄 {file_info['filename']}")
                                    with col2:
                                        file_size_kb = file_info["file_size"] // 1024
                                        st.write(f"{file_size_kb} KB")
                                    with col3:
                                        download_url = f"{API_BASE}{file_info['download_url']}"
                                        st.link_button("⬇️", download_url, key="download_summary")
                        
                        else:
                            st.info("📋 No PDFs generated yet. Use the generation tabs above to create PDFs.")
                    
                    else:
                        st.warning("⚠️ Unable to check for existing PDFs. Generate new ones using the tabs above.")
                
                except Exception as e:
                    st.error(f"❌ Error checking PDFs: {e}")
            
            # ========================================
            # TAB 4: PDF STATUS & JIRA INTEGRATION
            # ========================================
            with tab4:
                st.subheader("PDF Status & JIRA Integration Guide")
                
                # Check current PDF status
                try:
                    response = requests.get(f"{API_BASE}/scan/{scan_id}/pdfs", timeout=10)
                    if response.status_code == 200:
                        pdf_data = response.json()
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.markdown("**📊 Current PDF Status:**")
                            if pdf_data["total_files"] > 0:
                                st.success(f"✅ {pdf_data['total_files']} PDFs available")
                                st.info(f"📋 {pdf_data.get('individual_gates', 0)} individual gate PDFs")
                                
                                # Get status breakdown if using organized files
                                if hasattr(st.session_state, 'last_pdf_data'):
                                    last_data = st.session_state.last_pdf_data
                                    if "status_summary" in last_data:
                                        status_summary = last_data["status_summary"]
                                        st.markdown("**Status Breakdown:**")
                                        for status, count in status_summary.items():
                                            emoji = {"FAIL": "❌", "WARNING": "⚠️", "PASS": "✅", "NOT_APPLICABLE": "➖"}.get(status, "❓")
                                            st.write(f"{emoji} {status}: {count}")
                            else:
                                st.warning("⚠️ No PDFs generated yet")
                        
                        with col2:
                            st.markdown("**🎯 JIRA Integration Strategy:**")
                            
                            fail_count = len([g for g in gate_results if g.get("status") == "FAIL"])
                            warning_count = len([g for g in gate_results if g.get("status") == "WARNING"])
                            pass_count = len([g for g in gate_results if g.get("status") == "PASS"])
                            
                            if fail_count > 0:
                                st.error(f"🐛 Create {fail_count} BUG tickets for FAIL gates")
                            if warning_count > 0:
                                st.warning(f"📋 Create {warning_count} TASK tickets for WARNING gates")
                            if pass_count > 0:
                                st.success(f"✅ {pass_count} PASS gates for reference")
                            
                            st.info("💡 Use individual gate PDFs as attachments for each JIRA ticket")
                    
                    # JIRA Integration Instructions
                    st.markdown("**📝 JIRA Ticket Creation Guide:**")
                    
                    with st.expander("🐛 For FAIL Gates (Bug Tickets)", expanded=True):
                        st.markdown("""
                        **Title Format:** `[CodeGates] Gate XX - Fix {Gate Display Name}`  
                        **Priority:** High/Critical  
                        **Labels:** `codegates, gate-XX, {category}, compliance-fail`  
                        **Description Template:**
                        ```
                        CodeGates Gate XX scan identified critical compliance violations
                        - See attached PDF for detailed analysis and remediation steps
                        - Gate Score: X.X% (Critical - needs immediate attention)
                        - Files Affected: X files with X violations
                        
                        Attachment: Gate_XX_{GATE_NAME}_{SCAN_ID}.pdf
                        ```
                        """)
                    
                    with st.expander("📋 For WARNING Gates (Task Tickets)"):
                        st.markdown("""
                        **Title Format:** `[CodeGates] Gate XX - Improve {Gate Display Name}`  
                        **Priority:** Medium  
                        **Labels:** `codegates, gate-XX, {category}, enhancement`  
                        **Description Template:**
                        ```
                        CodeGates Gate XX scan identified improvement opportunities
                        - See attached PDF for recommendations and implementation guide
                        - Current Score: X.X% (Needs enhancement)
                        - Enhancement potential: {Specific recommendations}
                        
                        Attachment: Gate_XX_{GATE_NAME}_{SCAN_ID}.pdf
                        ```
                        """)
                    
                    with st.expander("✅ For PASS Gates (Reference)"):
                        st.markdown("""
                        **Usage:** Attach to main epic/story for documentation  
                        **Purpose:** Show compliance evidence and current implementation  
                        **Note:** No action required, use for reference and audit trail  
                        """)
                
                except Exception as e:
                    st.error(f"❌ Error checking PDF status: {e}")
            
            st.divider()
            
            # ========================================
            # GATE RESULTS TABLE (existing functionality)
            # ========================================
            if gate_results:
                st.subheader("🎯 Gate Results Summary")
                
                # Create a summary table
                gate_data = []
                for i, gate in enumerate(gate_results):
                    gate_data.append({
                        "Gate #": i + 1,
                        "Gate": gate.get("display_name", gate.get("gate", "Unknown")),
                        "Status": gate.get("status", "UNKNOWN"),
                        "Score": f"{gate.get('score', 0):.1f}%",
                        "Category": gate.get("category", "Unknown"),
                        "Matches": gate.get("matches_found", 0)
                    })
                
                # Display as dataframe
                df = pd.DataFrame(gate_data)
                st.dataframe(df, use_container_width=True)
            
            # Report Links (existing functionality)
            st.divider()
            st.subheader("📄 Full Reports")
            
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
    
    # Header
    st.markdown('<h1 class="main-header">🔍 CodeGates Scanner</h1>', unsafe_allow_html=True)
    
    # Initialize git integration
    git = initialize_git_integration()
    if not git:
        st.stop()
    
    # Step 1: APP ID Selection
    st.markdown('<h2 class="section-header">1️⃣ Select Application ID</h2>', unsafe_allow_html=True)
    
    app_id_options = list(APP_ID_DATA.keys())
    app_id_labels = [f"{app_id} - {APP_ID_DATA[app_id]['name']}" for app_id in app_id_options]
    
    selected_app_index = st.selectbox(
        "Choose an Application ID:",
        range(len(app_id_options)),
        format_func=lambda x: app_id_labels[x],
        help="Select the application category to scan"
    )
    
    selected_app_id = app_id_options[selected_app_index]
    
    if selected_app_id != st.session_state.selected_app_id:
        st.session_state.selected_app_id = selected_app_id
        st.session_state.selected_repo = None
        st.session_state.selected_branch = None
        st.session_state.available_branches = []
    
    # Display APP ID info
    app_info = APP_ID_DATA[selected_app_id]
    st.markdown(f"""
    <div class="info-box">
        <strong>{app_info['name']}</strong><br>
        {app_info['description']}<br>
        <small>Available repositories: {len(app_info['repos'])}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 2: Repository Selection
    st.markdown('<h2 class="section-header">2️⃣ Select Repository</h2>', unsafe_allow_html=True)
    
    available_repos = app_info['repos']
    
    selected_repo = st.selectbox(
        "Choose a Repository:",
        available_repos,
        help="Select the repository to scan"
    )
    
    if selected_repo != st.session_state.selected_repo:
        st.session_state.selected_repo = selected_repo
        st.session_state.selected_branch = None
        st.session_state.available_branches = []
        
        # Load branches for the selected repository
        with st.spinner(f"Loading branches for {selected_repo}..."):
            branches = get_branches_for_repo(git, selected_repo)
            st.session_state.available_branches = branches
    
    # Step 3: Branch Selection
    st.markdown('<h2 class="section-header">3️⃣ Select Branch</h2>', unsafe_allow_html=True)
    
    if st.session_state.available_branches:
        branch_names = [branch.name for branch in st.session_state.available_branches]
        
        # Try to find main/master branch as default
        default_index = 0
        for i, branch_name in enumerate(branch_names):
            if branch_name.lower() in ['main', 'master']:
                default_index = i
                break
        
        selected_branch_name = st.selectbox(
            "Choose a Branch:",
            branch_names,
            index=default_index,
            help="Select the branch to scan"
        )
        
        st.session_state.selected_branch = selected_branch_name
        
        # Display branch info
        selected_branch_obj = next(
            (b for b in st.session_state.available_branches if b.name == selected_branch_name), 
            None
        )
        
        if selected_branch_obj:
            st.markdown(f"""
            <div class="info-box">
                <strong>Branch:</strong> {selected_branch_obj.name}<br>
                <strong>Last Commit:</strong> {selected_branch_obj.commit_sha[:8]}<br>
                <strong>Date:</strong> {selected_branch_obj.last_commit_date[:10]}<br>
                <strong>Protected:</strong> {'Yes' if selected_branch_obj.protected else 'No'}
            </div>
            """, unsafe_allow_html=True)
    else:
        if st.session_state.selected_repo:
            if st.button("🔄 Load Branches"):
                with st.spinner(f"Loading branches for {st.session_state.selected_repo}..."):
                    branches = get_branches_for_repo(git, st.session_state.selected_repo)
                    st.session_state.available_branches = branches
                    st.rerun()
        
        st.info("👆 Select a repository to load branches")
    
    # Step 4: GitHub Token and Scan
    st.markdown('<h2 class="section-header">4️⃣ Configure & Start Scan</h2>', unsafe_allow_html=True)
    
    # GitHub Token input
    github_token = st.text_input(
        "GitHub Token (Optional):",
        type="password",
        help="Provide GitHub token for private repositories or higher rate limits",
        placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
    )
    
    # Scan configuration
    col1, col2 = st.columns(2)
    
    with col1:
        threshold = st.slider(
            "Compliance Threshold (%)",
            min_value=0,
            max_value=100,
            value=70,
            help="Minimum compliance score required"
        )
    
    with col2:
        max_files = st.slider(
            "Max Files to Process",
            min_value=100,
            max_value=10000,
            value=1000,
            help="Maximum number of files to process"
        )
    
    # Scan button
    if st.session_state.selected_repo and st.session_state.selected_branch:
        repo_url = f"https://github.com/{st.session_state.selected_repo}"
        
        st.markdown(f"""
        <div class="success-box">
            <strong>Ready to Scan:</strong><br>
            Repository: {st.session_state.selected_repo}<br>
            Branch: {st.session_state.selected_branch}<br>
            URL: {repo_url}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Code Scan", type="primary", use_container_width=True):
            with st.spinner("Starting code scan..."):
                scan_id = start_code_scan(
                    repo_url,
                    st.session_state.selected_branch,
                    github_token
                )
                
                if scan_id:
                    st.session_state.scan_id = scan_id
                    st.success(f"✅ Scan started successfully! Scan ID: {scan_id}")
                    st.rerun()
                else:
                    st.error("❌ Failed to start scan")
    else:
        st.info("👆 Complete all selections above to start scanning")
    
    # Step 5: Scan Progress and Results
    if st.session_state.scan_id:
        st.markdown('<h2 class="section-header">5️⃣ Scan Progress & Results</h2>', unsafe_allow_html=True)
        
        # Auto-refresh for scan progress
        scan_status = get_scan_status(st.session_state.scan_id)
        
        if scan_status:
            status = scan_status.get("status", "unknown")
            progress = scan_status.get("progress_percentage", 0)
            
            # Progress bar
            st.progress(progress / 100)
            
            # Status info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Status", status.upper())
            
            with col2:
                st.metric("Progress", f"{progress}%")
            
            with col3:
                st.metric("Scan ID", st.session_state.scan_id)
            
            # Current step
            current_step = scan_status.get("current_step", "Unknown")
            st.info(f"Current Step: {current_step}")
            
            if status == "completed":
                st.success("🎉 Scan completed successfully!")
                
                # Display results
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Overall Score", f"{scan_status.get('overall_score', 0)}%")
                
                with col2:
                    st.metric("Gates Passed", f"{scan_status.get('passed_gates', 0)}/{scan_status.get('total_gates', 0)}")
                
                with col3:
                    st.metric("Total Files", scan_status.get('total_files', 0))
                
                with col4:
                    st.metric("Total Lines", scan_status.get('total_lines', 0))
                
                # Automatically load reports when scan completes (if not already loaded)
                if not hasattr(st.session_state, 'reports_loaded') or not st.session_state.reports_loaded:
                    with st.spinner("Loading reports..."):
                        # Load HTML report
                        html_content = get_report_content(st.session_state.scan_id, "html")
                        if html_content:
                            st.session_state.html_report = html_content
                        
                        # Load JSON report
                        json_content = get_report_content(st.session_state.scan_id, "json")
                        if json_content:
                            st.session_state.json_report = json_content
                        
                        st.session_state.reports_loaded = True
                
                # View reports
                st.subheader("📊 Reports")
                
                # Create tabs for different report views
                tab1, tab2, tab3 = st.tabs(["📊 Summary", "📄 HTML Report", "🔢 JSON Report"])
                
                with tab1:
                    # Summary view
                    st.markdown("### 📈 Scan Summary")
                    
                    # Create a summary table
                    summary_data = {
                        "Metric": ["Overall Score", "Gates Passed", "Gates Failed", "Total Gates", 
                                 "Files Analyzed", "Lines Analyzed", "Scan Duration"],
                        "Value": [
                            f"{scan_status.get('overall_score', 0)}%",
                            f"{scan_status.get('passed_gates', 0)}",
                            f"{scan_status.get('failed_gates', 0)}",
                            f"{scan_status.get('total_gates', 0)}",
                            f"{scan_status.get('total_files', 0):,}",
                            f"{scan_status.get('total_lines', 0):,}",
                            "~10 seconds"
                        ]
                    }
                    
                    # Display as a nice table
                    df = pd.DataFrame(summary_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Progress visualization
                    passed_gates = scan_status.get('passed_gates', 0)
                    total_gates = scan_status.get('total_gates', 0)
                    if total_gates > 0:
                        st.markdown("### 🎯 Gates Performance")
                        st.progress(passed_gates / total_gates)
                        st.caption(f"{passed_gates} out of {total_gates} gates passed")
                
                with tab2:
                    # HTML Report
                    st.markdown("### 📄 HTML Report")
                    
                    if st.button("🔄 Load HTML Report", key="load_html"):
                        with st.spinner("Loading HTML report..."):
                            html_content = get_report_content(st.session_state.scan_id, "html")
                            if html_content:
                                st.session_state.html_report = html_content
                            else:
                                st.error("❌ Failed to load HTML report")
                    
                    # Display HTML report if available
                    if hasattr(st.session_state, 'html_report') and st.session_state.html_report:
                        st.markdown("#### 📋 Report Content:")
                        # Display HTML content safely
                        st.components.v1.html(st.session_state.html_report, height=600, scrolling=True)
                    else:
                        st.info("👆 Click 'Load HTML Report' to view the detailed report")
                
                with tab3:
                    # JSON Report
                    st.markdown("### 🔢 JSON Report")
                    
                    if st.button("🔄 Load JSON Report", key="load_json"):
                        with st.spinner("Loading JSON report..."):
                            json_content = get_report_content(st.session_state.scan_id, "json")
                            if json_content:
                                st.session_state.json_report = json_content
                            else:
                                st.error("❌ Failed to load JSON report")
                    
                    # Display JSON report if available
                    if hasattr(st.session_state, 'json_report') and st.session_state.json_report:
                        st.markdown("#### 📋 Report Data:")
                        
                        # Display JSON in a formatted way
                        st.json(st.session_state.json_report)
                        
                        # Also show key metrics from JSON
                        if isinstance(st.session_state.json_report, dict):
                            st.markdown("#### 🔍 Key Insights:")
                            json_data = st.session_state.json_report
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Repository", json_data.get("repository", "Unknown"))
                                st.metric("Branch", json_data.get("branch", "Unknown"))
                                st.metric("Overall Score", f"{json_data.get('overall_score', 0)}%")
                            
                            with col2:
                                if "gates" in json_data:
                                    gates = json_data["gates"]
                                    st.metric("Gates Passed", gates.get("passed", 0))
                                    st.metric("Gates Failed", gates.get("failed", 0))
                                    st.metric("Total Gates", gates.get("total", 0))
                    else:
                        st.info("👆 Click 'Load JSON Report' to view the structured report data")
            
            elif status == "failed":
                st.error("❌ Scan failed")
                errors = scan_status.get('errors', [])
                if errors:
                    for error in errors:
                        st.error(f"Error: {error}")
            
            elif status in ["running", "starting"]:
                st.info("⏳ Scan in progress...")
                # Auto-refresh every 3 seconds
                import time
                time.sleep(3)
                st.rerun()
        
        else:
            st.error("❌ Unable to get scan status")
        
        # Refresh button
        if st.button("🔄 Refresh Status"):
            st.rerun()

if __name__ == "__main__":
    main() 