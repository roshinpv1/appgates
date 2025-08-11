#!/usr/bin/env python3
"""
CodeGates Server - FastAPI Web Server with Integrated Streamlit UI
"""

import sys
import os
import uuid
import tempfile
import asyncio
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow import create_static_only_flow
from utils.hard_gates import HARD_GATES
from utils.db_integration import extract_app_id_from_url
from utils.jira_upload import upload_report_to_jira

# Import Git operations for enterprise integration
try:
    from utils.git_operations import EnhancedGitIntegration
    GIT_INTEGRATION_AVAILABLE = True
except ImportError:
    print("⚠️ Git integration not available")
    GIT_INTEGRATION_AVAILABLE = False

# Import pattern cache for performance optimization
try:
    from utils.pattern_cache import get_pattern_cache, get_cache_stats
    PATTERN_CACHE_AVAILABLE = True
except ImportError:
    print("⚠️ PatternCache not available")
    PATTERN_CACHE_AVAILABLE = False

# Import PDF generation
try:
    from utils.pdf_generator import EnhancedPDFGenerator, generate_pdfs_from_scan_id
    PDF_GENERATION_AVAILABLE = True
except ImportError:
    print("⚠️ PDF generation not available. Install ReportLab: pip install reportlab")
    PDF_GENERATION_AVAILABLE = False

# Add server configuration at the top of the file
import socket

# Environment variable configuration
SERVER_HOST = os.getenv("CODEGATES_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("CODEGATES_PORT", "8000"))
REPORTS_DIR = os.getenv("CODEGATES_REPORTS_DIR", "./reports")
LOGS_DIR = os.getenv("CODEGATES_LOGS_DIR", "./logs")
TEMP_DIR = os.getenv("CODEGATES_TEMP_DIR", None)  # None means use system temp
CORS_ORIGINS = os.getenv("CODEGATES_CORS_ORIGINS", "*").split(",")
LOG_LEVEL = os.getenv("CODEGATES_LOG_LEVEL", "info")

# Streamlit integration configuration
STREAMLIT_PORT = SERVER_PORT + 1  # Run Streamlit on adjacent port
STREAMLIT_PROCESS = None  # Global reference to Streamlit process

def get_server_url():
    """Get the server URL for report access"""
    # Try to get the actual IP address
    try:
        # Connect to a remote address to get the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return f"http://{local_ip}:{SERVER_PORT}"
    except:
        # Fallback to localhost
        return f"http://localhost:{SERVER_PORT}"

def ensure_directories():
    """Ensure required directories exist"""
    directories = [REPORTS_DIR, LOGS_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Ensured directory exists: {directory}")


# Pydantic Models for API
class ScanRequest(BaseModel):
    repository_url: str = Field(..., description="Repository URL to scan")
    branch: str = Field(default="main", description="Branch to scan")
    github_token: Optional[str] = Field(None, description="GitHub token for private repos")
    threshold: int = Field(default=70, description="Compliance threshold percentage")
    report_format: str = Field(default="both", description="Report format: 'html', 'json', or 'both'")
    max_files: int = Field(default=1000, description="Maximum files to process")
    app_id: Optional[str] = Field(None, description="Application ID for categorization")
    splunk_query: Optional[str] = Field(None, description="Optional Splunk query to execute during scan")
    llm_url: Optional[str] = Field(None, description="LLM service URL for AI recommendations (e.g., https://api.openai.com/v1/chat/completions)")
    llm_api_key: Optional[str] = Field(None, description="LLM API key for authentication")
    llm_model: Optional[str] = Field(default="gpt-3.5-turbo", description="LLM model to use for recommendations")
    enable_llm_recommendations: bool = Field(default=True, description="Enable AI-powered recommendations for failed gates")

class GitSearchRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to search for")
    git_endpoint: str = Field(..., description="Git endpoint (github.com, gitlab.com, etc.)")
    limit: int = Field(default=20, description="Maximum number of repositories to return (up to 20, prioritizing private repos)")
    github_token: Optional[str] = Field(None, description="GitHub token for authentication")

class GitBranchRequest(BaseModel):
    repository_url: str = Field(..., description="Repository URL")
    git_endpoint: str = Field(..., description="Git endpoint")
    owner: str = Field(..., description="Repository owner")
    name: str = Field(..., description="Repository name")
    github_token: Optional[str] = Field(None, description="GitHub token for authentication")


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str
    created_at: str


class ScanResult(BaseModel):
    scan_id: str
    status: str
    overall_score: float
    total_files: int
    total_lines: int
    passed_gates: int
    failed_gates: int
    warning_gates: int
    total_gates: int
    html_report_url: Optional[str] = None
    json_report_url: Optional[str] = None
    completed_at: Optional[str] = None
    errors: List[str] = []
    current_step: Optional[str] = None
    progress_percentage: Optional[int] = None
    step_details: Optional[str] = None
    app_id: Optional[str] = None
    # NEW: Enhanced progress tracking fields
    evidence_collection_progress: Optional[Dict[str, Any]] = None  # Progress for each evidence method
    mandatory_collectors_status: Optional[Dict[str, str]] = None   # Status of mandatory collectors
    gate_validation_progress: Optional[List[Dict[str, Any]]] = None  # Progress for each gate
    # Backward compatibility aliases for VSCode extension and other clients
    score: Optional[float] = None  # Alias for overall_score
    gates: Optional[List[Dict[str, Any]]] = None  # Alias for gate_results
    progress: Optional[int] = None  # Alias for progress_percentage


class GateInfo(BaseModel):
    name: str
    description: str
    category: str


class JiraUploadRequest(BaseModel):
    app_id: str
    scan_id: str
    report_type: str = Field(default="html", description="Report type: html, json, or pdf")
    jira_ticket_id: Optional[str] = Field(None, description="Specific JIRA ticket ID to upload to")
    gate_number: Optional[int] = Field(None, description="Specific gate number for individual upload")
    comment: Optional[str] = Field(None, description="Additional comment for the JIRA ticket")

# ============================================
# STREAMLIT INTEGRATION FUNCTIONS
# ============================================

def start_streamlit_app():
    """Start Streamlit app in a separate process"""
    global STREAMLIT_PROCESS
    try:
        # Skip Streamlit process startup for direct integration
        print(f"🎨 Using direct UI integration on port {SERVER_PORT}...")
        print(f"✅ Direct UI integration ready")
        return None
            
    except Exception as e:
        print(f"❌ Error in UI integration: {e}")
        return None

def stop_streamlit_app():
    """Stop Streamlit app"""
    global STREAMLIT_PROCESS
    # No process to stop in direct integration
    print("🎨 Direct UI integration - no process to stop")

# Initialize FastAPI app
app = FastAPI(
    title="CodeGates API",
    description="Hard gate validation service for code repositories",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services at startup"""
    print("🚀 CodeGates server starting up...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize direct UI integration (no separate process needed)
    print("🎨 Initializing direct UI integration...")
    start_streamlit_app()
    
    # Pre-compile regex patterns for performance
    if PATTERN_CACHE_AVAILABLE:
        print("🔧 Initializing pattern cache...")
        pattern_cache = get_pattern_cache()
        
        # Collect all patterns from hard gates
        all_patterns = []
        
        for gate in HARD_GATES:
            gate_name = gate.get("name", "Unknown")
            patterns = gate.get("patterns", [])
            
            if isinstance(patterns, list):
                # Simple list format: patterns: ["pattern1", "pattern2"]
                all_patterns.extend(patterns)
                if patterns:
                    print(f"   📋 {gate_name}: {len(patterns)} patterns (list format)")
            elif isinstance(patterns, dict):
                # Dictionary format: patterns: {"positive": [...], "negative": [...]}
                dict_patterns = []
                for pattern_type, pattern_list in patterns.items():
                    if isinstance(pattern_list, list):
                        dict_patterns.extend(pattern_list)
                        all_patterns.extend(pattern_list)
        
        # Add static patterns from static_patterns module if available
        try:
            from utils.static_patterns import get_all_static_patterns
            static_patterns = get_all_static_patterns()
            if static_patterns:
                all_patterns.extend(static_patterns)
                print(f"   📋 Static patterns: {len(static_patterns)} additional patterns")
        except ImportError:
            pass  # static_patterns module not available
        
        # Pre-compile patterns
        if all_patterns:
            print(f"   🔧 Pre-compiling {len(all_patterns)} total patterns...")
            successful, failed = pattern_cache.pre_compile_patterns(all_patterns)
            print(f"✅ Pattern cache initialized: {successful} patterns compiled, {failed} failed")
        else:
            print("⚠️ No patterns found in HARD_GATES for pre-compilation")
    else:
        print("⚠️ Pattern cache not available - patterns will be compiled per request")
    
    print("✅ CodeGates server startup complete")
    print(f"🎯 Direct UI available at: http://localhost:{SERVER_PORT}/ui/")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 CodeGates server shutting down...")
    
    # Clean up direct UI integration (no process to stop)
    print("🎨 Cleaning up direct UI integration...")
    stop_streamlit_app()
    
    print("✅ Shutdown complete")

# Store scan results in memory (could be replaced with Redis for production)
scan_results: Dict[str, Dict[str, Any]] = {}

# ============================================
# UI INTEGRATION ROUTES
# ============================================

@app.get("/ui", response_class=HTMLResponse)
async def ui_redirect():
    """Redirect to the main UI"""
    return RedirectResponse(url="/ui/")

@app.get("/ui/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the Streamlit UI through FastAPI"""
    try:
        # Import and use direct UI integration
        import sys
        import os
        from pathlib import Path
        
        # Add the gates directory to Python path for imports
        gates_dir = Path(__file__).parent
        if str(gates_dir) not in sys.path:
            sys.path.insert(0, str(gates_dir))
        
        from streamlit_integration import get_integrated_ui_html
        
        # Get the current server URL for API base
        server_url = f"http://localhost:{SERVER_PORT}"
        api_base = f"{server_url}/api/v1"
        
        # Get the integrated UI HTML
        html_content = get_integrated_ui_html(api_base)
        
        return HTMLResponse(content=html_content)
            
    except Exception as e:
        print(f"❌ Error serving UI: {e}")
        
        # Fallback error page
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CodeGates Scanner - UI Error</title>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    margin: 0;
                    padding: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }}
                .error {{
                    font-size: 48px;
                    margin-bottom: 20px;
                }}
                .message {{
                    font-size: 18px;
                    margin-bottom: 30px;
                    line-height: 1.6;
                }}
                .solution {{
                    background: rgba(255, 255, 255, 0.2);
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    text-align: left;
                }}
                .refresh-btn {{
                    background: white;
                    color: #667eea;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    transition: transform 0.2s;
                }}
                .refresh-btn:hover {{
                    transform: translateY(-2px);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">🚫</div>
                <div class="message">
                    <strong>UI Service Error</strong><br>
                    Failed to load the integrated UI interface.
                </div>
                <div class="solution">
                    <strong>📋 Error Details:</strong><br>
                    {str(e)}<br><br>
                    <strong>🔧 Solution:</strong><br>
                    Check server logs for details and restart the server.
                </div>
                <a href="/ui/" class="refresh-btn">🔄 Refresh Page</a>
                <br><br>
                <a href="/docs" class="refresh-btn">📊 API Documentation</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic information"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CodeGates API</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
            .header {{ color: white; text-align: center; margin-bottom: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: rgba(255, 255, 255, 0.1); padding: 40px; border-radius: 15px; backdrop-filter: blur(10px); }}
            .endpoint {{ background: rgba(255, 255, 255, 0.2); padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .code {{ background: rgba(0, 0, 0, 0.3); padding: 5px; border-radius: 3px; font-family: monospace; }}
            .ui-link {{ background: white; color: #667eea; padding: 15px 30px; border-radius: 25px; text-decoration: none; font-weight: 600; display: inline-block; margin: 20px 0; transition: transform 0.2s; }}
            .ui-link:hover {{ transform: translateY(-2px); }}
            .integration-badge {{ background: #28a745; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8rem; margin-left: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 CodeGates API Server</h1>
                <p>Hard gate validation service with integrated UI on single port</p>
                <span class="integration-badge">✅ True Same-Port Integration</span>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/ui/" class="ui-link">🎨 Open Integrated UI</a>
                <br>
                <small style="color: #ffeb3b;">Complete scanning interface with PDF generation - all on port {SERVER_PORT}</small>
            </div>
            
            <div class="endpoint">
                <h3>🚀 Quick Start</h3>
                <p><strong>Integrated UI:</strong> <a href="/ui/" style="color: #ffeb3b;">/ui/</a> - Complete scanning interface with PDF generation</p>
                <p><strong>API Documentation:</strong> <a href="/docs" style="color: #ffeb3b;">/docs</a> - Interactive API documentation</p>
                <p><strong>Health Check:</strong> <a href="/api/v1/health" style="color: #ffeb3b;">/api/v1/health</a> - Server status and performance metrics</p>
            </div>
            
            <div class="endpoint">
                <h3>📄 PDF Generation Features</h3>
                <p>✅ Individual gate PDFs with complete HTML report data</p>
                <p>✅ Status-based filtering (FAIL, WARNING, PASS, N/A)</p>
                <p>✅ Advanced filtering by category, gate numbers, and names</p>
                <p>✅ JIRA integration templates and workflows</p>
                <p>✅ Organized download management</p>
            </div>
            
            <div class="endpoint">
                <h3>🔧 System Status</h3>
                <p><strong>Server:</strong> Running on port {SERVER_PORT}</p>
                <p><strong>UI Integration:</strong> <span style="color: #28a745;">✅ Direct HTML Integration</span></p>
                <p><strong>Architecture:</strong> Single-port FastAPI + Direct UI rendering</p>
                <p><strong>PDF Engine:</strong> ReportLab integration</p>
                <p><strong>Pattern Cache:</strong> {"✅ Available" if PATTERN_CACHE_AVAILABLE else "❌ Not Available"}</p>
            </div>
            
            <div class="endpoint">
                <h3>🏗️ Architecture Benefits</h3>
                <p>🎯 <strong>True Same-Port:</strong> No iframe, no separate processes</p>
                <p>⚡ <strong>Fast Loading:</strong> Direct HTML rendering without external dependencies</p>
                <p>🔒 <strong>Secure:</strong> No cross-origin issues or port management</p>
                <p>📦 <strong>Simple Deployment:</strong> Single service, single port, single process</p>
                <p>🔧 <strong>Easy Maintenance:</strong> No Streamlit subprocess management</p>
            </div>
            
            <div class="endpoint">
                <h3>📋 API Endpoints</h3>
                <p><span class="code">POST /api/v1/scan</span> - Start a new code scan</p>
                <p><span class="code">GET /api/v1/scan/{{scan_id}}</span> - Get scan status</p>
                <p><span class="code">GET /api/v1/scan/{{scan_id}}/results</span> - Get scan results</p>
                <p><span class="code">GET /api/v1/scan/{{scan_id}}/pdfs</span> - Generate all gate PDFs</p>
                <p><span class="code">POST /api/v1/scan/{{scan_id}}/generate-jira-pdfs</span> - Generate filtered PDFs</p>
            </div>
            
            <div class="endpoint">
                <h3>🚀 How to Run</h3>
                <p><strong>Option 1 (Integrated):</strong> <span class="code">python run_integrated_server.py</span></p>
                <p><strong>Option 2 (Direct):</strong> <span class="code">python gates/server.py</span></p>
                <p><strong>Access:</strong> <a href="http://localhost:{SERVER_PORT}/ui/" style="color: #ffeb3b;">http://localhost:{SERVER_PORT}/ui/</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/v1/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Start a new repository scan
    """
    try:
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Initialize scan result
        scan_results[scan_id] = {
            "scan_id": scan_id,
            "status": "running",
            "request": request.dict(),
            "created_at": datetime.now().isoformat(),
            "overall_score": 0.0,
            "total_files": 0,
            "total_lines": 0,
            "passed_gates": 0,
            "failed_gates": 0,
            "warning_gates": 0,  # Added for backward compatibility
            "total_gates": 0,
            "errors": [],
            "current_step": None,
            "progress_percentage": None,
            "step_details": None,
            # NEW: Enhanced progress tracking
            "evidence_collection_progress": {},
            "mandatory_collectors_status": {},
            "gate_validation_progress": []
        }
        
        # Start background scan
        background_tasks.add_task(perform_scan, scan_id, request)
        
        return ScanResponse(
            scan_id=scan_id,
            status="running",
            message="Scan started successfully",
            created_at=scan_results[scan_id]["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/scan/{scan_id}", response_model=ScanResult)
async def get_scan_status(scan_id: str):
    """
    Get scan status and results
    """
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = scan_results[scan_id]
    
    return ScanResult(
        scan_id=result["scan_id"],
        status=result["status"],
        overall_score=result["overall_score"],
        total_files=result["total_files"],
        total_lines=result["total_lines"],
        passed_gates=result["passed_gates"],
        failed_gates=result["failed_gates"],
        warning_gates=result["warning_gates"],
        total_gates=result["total_gates"],
        html_report_url=result.get("html_report_url"),
        json_report_url=result.get("json_report_url"),
        completed_at=result.get("completed_at"),
        errors=result["errors"],
        current_step=result.get("current_step"),
        progress_percentage=result.get("progress_percentage"),
        step_details=result.get("step_details"),
        app_id=result.get("app_id"),
        # NEW: Enhanced progress tracking
        evidence_collection_progress=result.get("evidence_collection_progress"),
        mandatory_collectors_status=result.get("mandatory_collectors_status"),
        gate_validation_progress=result.get("gate_validation_progress"),
        # Backward compatibility aliases
        score=result["overall_score"],  # Alias for overall_score
        gates=result.get("gate_results", []),  # Alias for gate_results
        progress=result.get("progress_percentage", 0)  # Alias for progress_percentage
    )


@app.get("/api/v1/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """
    Get detailed scan results with gate results for UI display
    """
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    try:
        result = scan_results[scan_id]
        
        # Check if scan is completed
        if result["status"] != "completed":
            return {
                "scan_id": scan_id,
                "status": result["status"],
                "message": f"Scan is {result['status']}. Results not available yet.",
                "gate_results": [],
                "overall_score": 0
            }
        
        # Try to get detailed results from the stored scan data
        detailed_results = {}
        
        # Start with the stored scan data (same as status endpoint)
        detailed_results = {
            "scan_id": scan_id,
            "repository_url": result["request"].get("repository_url", ""),
            "branch": result["request"].get("branch", ""),
            "overall_score": result.get("overall_score", 0),
            "total_gates": result.get("total_gates", 0),
            "passed_gates": result.get("passed_gates", 0),
            "failed_gates": result.get("failed_gates", 0),
            "warning_gates": result.get("warning_gates", 0),
            "gate_results": result.get("gate_results", []),  # Try stored first
            "scan_timestamp": result.get("completed_at", result.get("created_at", "")),
            "app_id": result["request"].get("app_id", "")
        }
        
        # If no detailed gate_results in stored data, get from JSON report
        if not detailed_results["gate_results"] or len(detailed_results["gate_results"]) == 0:
            json_path = result.get("json_report_path")
            if json_path and os.path.exists(json_path):
                try:
                    import json
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # Get detailed gates from JSON report
                    gates = json_data.get("gates", [])
                    if gates:
                        detailed_results["gate_results"] = gates
                        print(f"📄 Loaded {len(gates)} detailed gate results from JSON report")
                    else:
                        print("⚠️ No gates found in JSON report")
                        
                except Exception as e:
                    print(f"Error reading JSON report: {e}")
                    
        print(f"📊 Results endpoint returning: {detailed_results['total_gates']} total gates, {len(detailed_results['gate_results'])} detailed gates")
        
        # Return the detailed results
        return detailed_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scan results: {str(e)}")


@app.get("/api/v1/scan/{scan_id}/report/html", response_class=HTMLResponse)
async def get_html_report(scan_id: str):
    """
    Get HTML report for a completed scan
    """
    import glob
    from pathlib import Path
    
    # Try in-memory first
    if scan_id in scan_results:
        result = scan_results[scan_id]
        html_path = result.get("html_report_path")
        if html_path and Path(html_path).exists():
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
    
    # Look for report in main reports directory first
    pattern1 = os.path.join(REPORTS_DIR, f"codegates_report_{scan_id}.html")
    if os.path.exists(pattern1):
        with open(pattern1, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    
    # Fallback: look for file in scan-specific subdirectory
    report_dir = os.path.join(REPORTS_DIR, scan_id)
    pattern2 = os.path.join(report_dir, f"codegates_report_{scan_id}.html")
    if os.path.exists(pattern2):
        with open(pattern2, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    
    # Final fallback: use glob to find any matching file
    patterns = [
        os.path.join(REPORTS_DIR, f"*{scan_id}*.html"),
        os.path.join(REPORTS_DIR, scan_id, "*.html"),
        os.path.join(REPORTS_DIR, "**", f"*{scan_id}*.html")
    ]
    
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            html_path = matches[0]
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
    
    raise HTTPException(status_code=404, detail="HTML report not found")


@app.get("/api/v1/scan/{scan_id}/report/json")
async def get_json_report(scan_id: str):
    """
    Get JSON report for a completed scan
    """
    import glob
    from pathlib import Path
    
    # Try in-memory first
    if scan_id in scan_results:
        result = scan_results[scan_id]
        json_path = result.get("json_report_path")
        if json_path and Path(json_path).exists():
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            return JSONResponse(content=json_data)
    
    # Look for report in main reports directory first
    pattern1 = os.path.join(REPORTS_DIR, f"codegates_report_{scan_id}.json")
    if os.path.exists(pattern1):
        import json
        with open(pattern1, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return JSONResponse(content=json_data)
    
    # Fallback: look for file in scan-specific subdirectory
    report_dir = os.path.join(REPORTS_DIR, scan_id)
    pattern2 = os.path.join(report_dir, f"codegates_report_{scan_id}.json")
    if os.path.exists(pattern2):
        import json
        with open(pattern2, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return JSONResponse(content=json_data)
    
    # Final fallback: use glob to find any matching file
    patterns = [
        os.path.join(REPORTS_DIR, f"*{scan_id}*.json"),
        os.path.join(REPORTS_DIR, scan_id, "*.json"),
        os.path.join(REPORTS_DIR, "**", f"*{scan_id}*.json")
    ]
    
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            json_path = matches[0]
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            return JSONResponse(content=json_data)
    
    raise HTTPException(status_code=404, detail="JSON report not found")


@app.post("/api/v1/jira/upload")
async def jira_upload(request: JiraUploadRequest, background_tasks: BackgroundTasks):
    """
    Upload the report for a scan to all JIRA stories for the given app_id.
    JIRA config is read from environment variables.
    """
    import os
    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_TOKEN")
    if not jira_url or not jira_user or not jira_token:
        raise HTTPException(status_code=400, detail="JIRA_URL, JIRA_USER, and JIRA_TOKEN must be set in the environment.")
    
    # Find report file
    import glob
    import os
    report_dir = os.path.join(REPORTS_DIR, request.scan_id)
    report_path = None
    
    # Determine report type and find the appropriate file
    if request.report_type == "pdf":
        # For individual gate PDFs, we need to find the specific gate PDF
        if request.gate_number is not None:
            # Find the gate PDF filename based on gate number (using zero-padded format)
            pdf_dir = os.path.join("./reports/pdfs", request.scan_id)
            gate_pdf_pattern = os.path.join(pdf_dir, f"Gate_{request.gate_number:02d}_*_{request.scan_id}.pdf")
            matches = glob.glob(gate_pdf_pattern)
            if not matches:
                raise HTTPException(status_code=404, detail=f"Gate PDF for gate number {request.gate_number} not found.")
            report_path = matches[0]
        else:
            # For summary PDF
            pdf_dir = os.path.join("./reports/pdfs", request.scan_id)
            summary_pdf_pattern = os.path.join(pdf_dir, f"SUMMARY_{request.scan_id}.pdf")
            matches = glob.glob(summary_pdf_pattern)
            if not matches:
                raise HTTPException(status_code=404, detail=f"Summary PDF not found.")
            report_path = matches[0]
    else:
        # For HTML or JSON reports
        if request.report_type == "html":
            pattern = os.path.join(report_dir, f"codegates_report_{request.scan_id}.html")
        elif request.report_type == "json":
            pattern = os.path.join(report_dir, f"codegates_report_{request.scan_id}.json")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported report_type: {request.report_type}")
            
        matches = glob.glob(pattern)
        if not matches:
            raise HTTPException(status_code=404, detail=f"Report file not found: {pattern}")
        report_path = matches[0]
    
    # Start background upload
    results = {}
    def upload_all():
        nonlocal results
        results = upload_report_to_jira(
            jira_url, jira_user, jira_token, request.app_id, report_path, request.report_type,
            jira_ticket_id=request.jira_ticket_id,
            gate_number=request.gate_number,
            comment=request.comment
        )
    background_tasks.add_task(upload_all)
    
    return {
        "success": True, 
        "message": f"Upload started for app_id {request.app_id}" + (f" to JIRA ticket {request.jira_ticket_id}" if request.jira_ticket_id else ""), 
        "report_path": report_path,
        "report_type": request.report_type,
        "results": []
    }


@app.get("/api/v1/gates", response_model=List[GateInfo])
async def list_gates():
    """
    List all available hard gates
    """
    return [
        GateInfo(
            name=gate["name"],
            description=gate.get("description", ""),
            category=gate.get("category", "General")
        )
        for gate in HARD_GATES
    ]


# Git Integration Endpoints for Enterprise Support
@app.post("/api/v1/git/search-repositories")
async def search_repositories(request: GitSearchRequest):
    """
    Search repositories across different Git endpoints (GitHub, GitLab, Bitbucket, etc.)
    based on keywords and application category
    """
    if not GIT_INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Git integration not available")
    
    try:
        git_integration = EnhancedGitIntegration()
        
        # Search repositories using the Git integration with GitHub token
        repositories = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: git_integration.search_repositories(
                keywords=request.keywords,
                git_endpoint=request.git_endpoint,
                limit=request.limit,
                github_token=request.github_token
            )
        )
        
        return {
            "success": True,
            "repositories": repositories,
            "count": len(repositories),
            "git_endpoint": request.git_endpoint,
            "keywords": request.keywords
        }
        
    except Exception as e:
        print(f"Error searching repositories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search repositories: {str(e)}")


@app.post("/api/v1/git/list-branches")
async def list_branches(request: GitBranchRequest):
    """
    List branches for a specific repository across different Git endpoints
    """
    if not GIT_INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Git integration not available")
    
    try:
        git_integration = EnhancedGitIntegration()
        
        # Get branches using the Git integration with GitHub token
        branches = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: git_integration.list_branches(
                owner=request.owner,
                name=request.name,
                git_endpoint=request.git_endpoint,
                github_token=request.github_token
            )
        )
        
        return {
            "success": True,
            "branches": branches,
            "count": len(branches),
            "repository": f"{request.owner}/{request.name}",
            "git_endpoint": request.git_endpoint
        }
        
    except Exception as e:
        print(f"Error listing branches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list branches: {str(e)}")


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint with system information"""
    
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "server": {
            "host": SERVER_HOST,
            "port": SERVER_PORT,
            "url": get_server_url()
        },
        "directories": {
            "reports": REPORTS_DIR,
            "logs": LOGS_DIR,
            "temp": TEMP_DIR or "system_default"
        },
        "configuration": {
            "cors_origins": CORS_ORIGINS,
            "log_level": LOG_LEVEL
        },
        "active_scans": len(scan_results)
    }
    
    # Add pattern cache information if available
    if PATTERN_CACHE_AVAILABLE:
        try:
            cache_info = get_cache_stats()
            health_info["pattern_cache"] = cache_info
        except Exception as e:
            health_info["pattern_cache"] = {"error": str(e)}
    else:
        health_info["pattern_cache"] = {"status": "not_available"}
    
    # Add file processor information if available
    try:
        from utils.file_processor import get_file_processor_stats
        processor_stats = get_file_processor_stats()
        health_info["file_processor"] = processor_stats
    except ImportError:
        health_info["file_processor"] = {"status": "not_available"}
    except Exception as e:
        health_info["file_processor"] = {"error": str(e)}
    
    return health_info


async def perform_scan(scan_id: str, request: ScanRequest):
    """
    Perform the actual repository scan in background
    """
    try:
        # Update status
        scan_results[scan_id]["status"] = "running"
        scan_results[scan_id]["current_step"] = "Initializing scan..."
        scan_results[scan_id]["progress_percentage"] = 0
        
        # Get server URL for report access
        server_url = get_server_url()
        
        # Create scan-specific directories
        scan_reports_dir = os.path.join(REPORTS_DIR, scan_id)
        os.makedirs(scan_reports_dir, exist_ok=True)
        
        # Create temp directory for this scan
        if TEMP_DIR:
            scan_temp_dir = tempfile.mkdtemp(prefix=f"codegates_{scan_id}_", dir=TEMP_DIR)
        else:
            scan_temp_dir = tempfile.mkdtemp(prefix=f"codegates_{scan_id}_")
        
        # Initialize shared store with environment-based paths
        app_id = extract_app_id_from_url(request.repository_url) or '<APP ID>'
        shared = {
            "request": {
                "repository_url": request.repository_url,
                "branch": request.branch,
                "github_token": request.github_token,
                "threshold": request.threshold,
                "scan_id": scan_id,
                "output_dir": scan_reports_dir,
                "report_format": request.report_format,
                "verbose": False,
                "app_id": app_id,
                "splunk_query": request.splunk_query,
                "enable_llm_recommendations": request.enable_llm_recommendations
            },
            "server": {
                "url": server_url,
                "host": SERVER_HOST,
                "port": SERVER_PORT
            },
            "directories": {
                "reports": REPORTS_DIR,
                "logs": LOGS_DIR,
                "temp": TEMP_DIR,
                "scan_reports": scan_reports_dir,
                "scan_temp": scan_temp_dir
            },
            "llm_config": {
                "url": request.llm_url,
                "api_key": request.llm_api_key,
                "model": request.llm_model
            },
            "repository": {
                "local_path": None,
                "metadata": {}
            },
            "config": {
                "build_files": {},
                "config_files": {},
                "dependencies": []
            },
            "llm": {
                "prompt": None,
                "response": None,
                "patterns": {}
            },
            "validation": {
                "gate_results": [],
                "overall_score": 0.0
            },
            "reports": {
                "html_path": None,
                "json_path": None
            },
            "hard_gates": HARD_GATES,
            "temp_dir": scan_temp_dir,
            "errors": [],
            "current_step": None,
            "progress_percentage": None,
            "step_details": None
        }
        
        # Create progress-aware flow
        validation_flow = create_progress_aware_flow(scan_id)
        
        # Run the flow with progress tracking
        validation_flow.run(shared)
        
        # Update scan results with data consistency checks
        gate_results = shared["validation"].get("gate_results", [])
        overall_score = shared["validation"].get("overall_score", 0.0)
        
        # Ensure data consistency: if no gate results, overall score should be 0
        if not gate_results or len(gate_results) == 0:
            if overall_score > 0:
                print(f"⚠️ Data inconsistency detected: overall_score={overall_score} but no gate_results. Resetting to 0.")
            overall_score = 0.0
            shared["validation"]["overall_score"] = 0.0
        
        # Check if we have valid results
        if gate_results and len(gate_results) > 0:
            passed = len([g for g in gate_results if g.get("status") == "PASS"])
            failed = len([g for g in gate_results if g.get("status") == "FAIL"])
            warnings = len([g for g in gate_results if g.get("status") == "WARNING"])
            
            # Generate report URLs
            html_report_url = f"{server_url}/api/v1/scan/{scan_id}/report/html" if shared["reports"]["html_path"] else None
            json_report_url = f"{server_url}/api/v1/scan/{scan_id}/report/json" if shared["reports"]["json_path"] else None
            
            scan_results[scan_id].update({
                "status": "completed",
                "overall_score": overall_score,
                "total_files": shared["repository"]["metadata"].get("total_files", 0),
                "total_lines": shared["repository"]["metadata"].get("total_lines", 0),
                "passed_gates": passed,
                "failed_gates": failed,
                "warning_gates": warnings,  # Ensure warning_gates is set for backward compatibility
                "total_gates": len(gate_results),
                "gate_results": gate_results,  # Store detailed gate results for UI
                "html_report_path": shared["reports"]["html_path"],
                "json_report_path": shared["reports"]["json_path"],
                "html_report_url": html_report_url,
                "json_report_url": json_report_url,
                "completed_at": datetime.now().isoformat(),
                "errors": shared["errors"],
                "current_step": "Completed",
                "progress_percentage": 100,
                "step_details": "Scan completed successfully"
            })
            
            # Print report URLs to logs
            print(f"📄 Scan {scan_id} completed successfully!")
            print(f"📊 Results: {overall_score:.1f}% overall score, {len(gate_results)} gates analyzed")
            print(f"   ✅ Passed: {passed}, ❌ Failed: {failed}, ⚠️ Warnings: {warnings}")
            if html_report_url:
                print(f"🌐 HTML Report URL: {html_report_url}")
            if json_report_url:
                print(f"🌐 JSON Report URL: {json_report_url}")
        else:
            # No valid gate results - mark as failed
            error_msg = "No gate validation results generated"
            if overall_score > 0:
                error_msg += f" (inconsistent state: overall_score={overall_score} with no gate results)"
            
            scan_results[scan_id].update({
                "status": "failed",
                "overall_score": 0.0,
                "total_gates": 0,
                "passed_gates": 0,
                "failed_gates": 0,
                "warning_gates": 0,  # Ensure warning_gates is set for backward compatibility
                "gate_results": [],
                "errors": shared["errors"] + [error_msg],
                "current_step": "Failed",
                "progress_percentage": 0,
                "step_details": f"Scan failed - {error_msg}"
            })
            print(f"❌ Scan {scan_id} failed: {error_msg}")
    
    except Exception as e:
        scan_results[scan_id].update({
            "status": "failed",
            "errors": [str(e)],
            "current_step": "Failed",
            "progress_percentage": 0,
            "step_details": f"Scan failed with error: {str(e)}",
            "warning_gates": 0  # Ensure warning_gates is set for backward compatibility
        })


def create_progress_aware_flow(scan_id: str):
    """
    Create a progress-aware validation flow that reports progress to scan_results
    """
    from flow import create_static_only_flow
    
    # Get the static-only flow
    original_flow = create_static_only_flow()
    
    # Define step mappings for static-only flow (no LLM steps)
    step_mappings = {
        'FetchRepositoryNode': ('Fetching repository...', 15),
        'ProcessCodebaseNode': ('Processing codebase...', 35),
        'ExtractConfigNode': ('Extracting configuration...', 50),
        'ValidateGatesNode': ('Validating gates with static patterns...', 80),
        'GenerateReportNode': ('Generating reports...', 95),
        'CleanupNode': ('Cleaning up...', 100)
    }
    
    # Create a wrapper that updates progress
    def update_progress(node_name: str, step_details: str = None):
        if node_name in step_mappings:
            step_name, progress = step_mappings[node_name]
            scan_results[scan_id]["current_step"] = step_name
            scan_results[scan_id]["progress_percentage"] = progress
            if step_details:
                scan_results[scan_id]["step_details"] = step_details
            else:
                scan_results[scan_id]["step_details"] = f"Executing: {step_name}"
    
    # Override the flow's run method to track progress
    original_run = original_flow.run
    
    def progress_aware_run(shared):
        try:
            # Update initial progress
            scan_results[scan_id]["current_step"] = "Starting validation..."
            scan_results[scan_id]["progress_percentage"] = 5
            scan_results[scan_id]["step_details"] = "Initializing validation flow"
            
            # Run the original flow
            result = original_run(shared)
            
            # Update final progress
            scan_results[scan_id]["current_step"] = "Completed"
            scan_results[scan_id]["progress_percentage"] = 100
            scan_results[scan_id]["step_details"] = "Validation completed successfully"
            
            return result
        except Exception as e:
            scan_results[scan_id]["current_step"] = "Failed"
            scan_results[scan_id]["progress_percentage"] = 0
            scan_results[scan_id]["step_details"] = f"Validation failed: {str(e)}"
            raise
    
    # Replace the run method
    original_flow.run = progress_aware_run
    
    return original_flow


# Add PDF generation import
try:
    from gates.pdf_generator import CodeGatesPDFGenerator, generate_gate_pdfs_from_scan_id
    PDF_GENERATION_AVAILABLE = True
except ImportError:
    PDF_GENERATION_AVAILABLE = False
    print("⚠️ PDF generation not available. Install ReportLab with: pip install reportlab")

@app.get("/api/v1/scan/{scan_id}/pdfs")
async def generate_scan_pdfs(scan_id: str):
    """Generate summary PDF and individual gate PDFs with proper naming convention"""
    if not PDF_GENERATION_AVAILABLE:
        raise HTTPException(
            status_code=501, 
            detail="PDF generation not available. Install ReportLab with: pip install reportlab"
        )
    
    try:
        # Check if scan exists in memory or as a JSON file
        scan_exists = False
        scan_status = "UNKNOWN"
        
        # First check in-memory scan results
        if scan_id in scan_results:
            scan_exists = True
            scan_status = scan_results[scan_id].get("status", "UNKNOWN")
            print(f"🔍 Debug: Scan {scan_id} found in memory with status: '{scan_status}'")
        else:
            # Check if JSON report exists
            json_path = os.path.join(REPORTS_DIR, scan_id, f"codegates_report_{scan_id}.json")
            if os.path.exists(json_path):
                scan_exists = True
                # Try to read status from JSON file
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        scan_status = json_data.get("status", "COMPLETED")  # Assume completed if file exists
                except:
                    scan_status = "COMPLETED"  # Default to completed if we can't read status
                print(f"🔍 Debug: Scan {scan_id} found in file with status: '{scan_status}'")
        
        if not scan_exists:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # For file-based scans, check if scan is completed
        if scan_id not in scan_results and scan_status.upper() not in ["COMPLETED", "COMPLETE"]:
            raise HTTPException(status_code=400, detail="Scan not completed yet")
        
        # Generate PDFs using the enhanced PDF generator
        pdf_results = generate_pdfs_from_scan_id(scan_id, "./reports")
        
        if not pdf_results["summary"] and not pdf_results["gates"]:
            raise HTTPException(status_code=500, detail="Failed to generate PDF files")
        
        # Return information about generated files
        pdf_info = []
        
        # Add summary PDF info
        if pdf_results["summary"]:
            summary_path = pdf_results["summary"][0]
            filename = os.path.basename(summary_path)
            file_size = os.path.getsize(summary_path) if os.path.exists(summary_path) else 0
            
            pdf_info.append({
                "filename": filename,
                "filepath": summary_path,
                "file_size": file_size,
                "type": "summary",
                "gate_name": "All Gates Summary",
                "download_url": f"/api/v1/scan/{scan_id}/pdf/{filename}"
            })
        
        # Add individual gate PDFs info
        for pdf_path in pdf_results["gates"]:
            filename = os.path.basename(pdf_path)
            file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
            
            # Extract gate name from filename: project-scanid-gatename.pdf
            parts = filename.split("-")
            if len(parts) >= 3:
                gate_name = parts[2].replace(".pdf", "").replace("_", " ").title()
            else:
                gate_name = "Unknown Gate"
            
            pdf_info.append({
                "filename": filename,
                "filepath": pdf_path,
                "file_size": file_size,
                "type": "individual_gate",
                "gate_name": gate_name,
                "download_url": f"/api/v1/scan/{scan_id}/pdf/{filename}"
            })
        
        return {
            "scan_id": scan_id,
            "total_files": len(pdf_results["summary"]) + len(pdf_results["gates"]),
            "summary_pdfs": len(pdf_results["summary"]),
            "individual_gates": len(pdf_results["gates"]),
            "pdf_files": pdf_info,
            "message": f"Generated {len(pdf_results['summary'])} summary and {len(pdf_results['gates'])} individual gate PDF files",
            "naming_convention": "project-scanid-summary.pdf and project-scanid-gatename.pdf"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/api/v1/scan/{scan_id}/pdf/{filename}")
async def download_pdf_file(scan_id: str, filename: str):
    """Download a specific PDF file"""
    # Check if scan exists in memory or as a JSON file
    scan_exists = False
    
    # First check in-memory scan results
    if scan_id in scan_results:
        scan_exists = True
    else:
        # Check if JSON report exists
        json_path = os.path.join(REPORTS_DIR, scan_id, f"codegates_report_{scan_id}.json")
        if os.path.exists(json_path):
            scan_exists = True
    
    if not scan_exists:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Construct file path
    pdf_dir = os.path.join(REPORTS_DIR, "pdfs", scan_id)
    file_path = os.path.join(pdf_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # Security check: ensure filename is safe
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    try:
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve PDF: {str(e)}")

@app.post("/api/v1/scan/{scan_id}/generate-jira-pdfs")
async def generate_jira_pdfs(scan_id: str, request: Dict[str, Any] = None):
    """Generate PDFs specifically formatted for JIRA upload with optional filtering"""
    if not PDF_GENERATION_AVAILABLE:
        raise HTTPException(
            status_code=501, 
            detail="PDF generation not available. Install ReportLab with: pip install reportlab"
        )
    
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    try:
        # Get scan results directly from the scan_results structure
        result_data = scan_results[scan_id]
        
        # Check if scan is completed
        if result_data.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Scan not completed yet")
        
        # Extract gate results
        gate_results = result_data.get("gate_results", [])
        if not gate_results:
            # Try to get from JSON report if available
            json_path = result_data.get("json_report_path")
            if json_path and os.path.exists(json_path):
                try:
                    import json
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        gate_results = json_data.get("gate_results", [])
                except Exception as e:
                    print(f"Error reading JSON report for PDF generation: {e}")
        
        if not gate_results:
            raise HTTPException(status_code=404, detail="No gate results found for PDF generation")
        
        # Apply filters if requested
        if request:
            status_filter = request.get("status_filter", [])  # e.g., ["FAIL", "WARNING"]
            category_filter = request.get("category_filter", [])  # e.g., ["Security", "Performance"]
            gate_numbers = request.get("gate_numbers", [])  # e.g., [1, 3, 5] - specific gate numbers
            gate_names = request.get("gate_names", [])  # e.g., ["AVOID_LOGGING_SECRETS", "RETRY_LOGIC"]
            
            if status_filter:
                gate_results = [g for g in gate_results if g.get("status") in status_filter]
            
            if category_filter:
                gate_results = [g for g in gate_results if g.get("category") in category_filter]
            
            if gate_numbers:
                # Filter by specific gate numbers (1-based)
                filtered_results = []
                for gate_num in gate_numbers:
                    if 1 <= gate_num <= len(gate_results):
                        filtered_results.append(gate_results[gate_num - 1])
                gate_results = filtered_results
            
            if gate_names:
                gate_results = [g for g in gate_results if g.get("gate") in gate_names]
        
        # Prepare scan results for PDF generation
        scan_data = {
            "scan_id": scan_id,
            "repository_url": result_data["request"].get("repository_url", "unknown"),
            "branch": result_data["request"].get("branch", "unknown"),
            "scan_timestamp_formatted": result_data.get("completed_at", result_data.get("created_at", "unknown")),
            "overall_score": result_data.get("overall_score", 0),
            "gate_results": gate_results
        }
        
        # Generate PDFs
        pdf_generator = CodeGatesPDFGenerator()
        pdf_dir = os.path.join("./reports/pdfs", scan_id)
        
        # Generate individual gate PDFs
        pdf_files = pdf_generator.generate_individual_gate_pdfs(scan_data, pdf_dir)
        
        # Generate summary PDF
        summary_pdf = pdf_generator.generate_summary_pdf(scan_data, pdf_dir)
        if summary_pdf:
            pdf_files.append(summary_pdf)
        
        # Organize by gate number and status for JIRA upload
        organized_files = {
            "individual_gates": [],
            "summary": []
        }
        
        status_counts = {"FAIL": 0, "WARNING": 0, "PASS": 0, "NOT_APPLICABLE": 0}
        
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
            
            if filename.startswith("SUMMARY_"):
                organized_files["summary"].append({
                    "filename": filename,
                    "filepath": pdf_path,
                    "file_size": file_size,
                    "download_url": f"/api/v1/scan/{scan_id}/pdf/{filename}"
                })
            elif filename.startswith("Gate_"):
                # Parse gate number and find corresponding gate data
                parts = filename.split("_", 3)
                gate_number = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                
                # Find gate data to get status
                gate_data = None
                if gate_number and gate_number <= len(gate_results):
                    gate_data = gate_results[gate_number - 1]
                
                gate_status = gate_data.get("status", "UNKNOWN") if gate_data else "UNKNOWN"
                gate_name = gate_data.get("gate", parts[2] if len(parts) > 2 else "unknown") if gate_data else (parts[2] if len(parts) > 2 else "unknown")
                gate_display_name = gate_data.get("display_name", gate_name) if gate_data else gate_name
                
                if gate_status in status_counts:
                    status_counts[gate_status] += 1
                
                organized_files["individual_gates"].append({
                    "filename": filename,
                    "filepath": pdf_path,
                    "file_size": file_size,
                    "gate_number": gate_number,
                    "gate_name": gate_name,
                    "gate_display_name": gate_display_name,
                    "status": gate_status,
                    "download_url": f"/api/v1/scan/{scan_id}/pdf/{filename}"
                })
        
        # Sort individual gates by gate number
        organized_files["individual_gates"].sort(key=lambda x: x.get("gate_number", 999))
        
        return {
            "scan_id": scan_id,
            "total_files": len(pdf_files),
            "individual_gates_count": len(organized_files["individual_gates"]),
            "organized_files": organized_files,
            "status_summary": status_counts,
            "jira_upload_instructions": {
                "individual_gates": f"Upload {len(organized_files['individual_gates'])} individual gate PDFs as separate JIRA tickets",
                "failed_gates": f"{status_counts['FAIL']} FAIL gates - create as Bug tickets",
                "warning_gates": f"{status_counts['WARNING']} WARNING gates - create as Task tickets",
                "passed_gates": f"{status_counts['PASS']} PASS gates - attach for reference",
                "not_applicable_gates": f"{status_counts['NOT_APPLICABLE']} NOT_APPLICABLE gates - skip or attach for documentation",
                "summary": "Upload SUMMARY PDF as overall scan report",
                "recommendation": "Create individual JIRA tickets for each gate PDF. Use gate number and name for ticket titles."
            },
            "message": f"Generated {len(pdf_files)} PDFs organized for individual JIRA ticket upload"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JIRA PDF generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Ensure required directories exist
    ensure_directories()
    
    # Print configuration information
    print("🔧 Configuration:")
    print("=" * 60)
    print(f"📁 Reports Directory: {REPORTS_DIR}")
    print(f"📁 Logs Directory: {LOGS_DIR}")
    print(f"📁 Temp Directory: {TEMP_DIR or 'System default'}")
    print(f"🌐 CORS Origins: {', '.join(CORS_ORIGINS)}")
    print(f"📊 Log Level: {LOG_LEVEL}")
    print("=" * 60)
    
    # Print startup information
    server_url = get_server_url()
    print("🚀 Starting CodeGates Server...")
    print("=" * 60)
    print(f"🌐 Server URL: {server_url}")
    print(f"🏠 Host: {SERVER_HOST}")
    print(f"🚪 Port: {SERVER_PORT}")
    print(f"📋 API Documentation: {server_url}/docs")
    print(f"🏥 Health Check: {server_url}/api/v1/health")
    print(f"🔍 Available Gates: {server_url}/api/v1/gates")
    print("=" * 60)
    print("📄 Report URLs will be printed in the logs when scans complete")
    print("🔍 Example: POST to /api/v1/scan to start a scan")
    print("=" * 60)
    
    uvicorn.run(
        "server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level=LOG_LEVEL
    ) 