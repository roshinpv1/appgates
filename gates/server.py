#!/usr/bin/env python3
"""
CodeGates Server - FastAPI Web Server
"""

import sys
import os
import uuid
import tempfile
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow import create_static_only_flow
from utils.hard_gates import HARD_GATES
from utils.db_integration import extract_app_id_from_url
from utils.jira_upload import upload_report_to_jira

# Import pattern cache for performance optimization
try:
    from utils.pattern_cache import get_pattern_cache, get_cache_stats
    PATTERN_CACHE_AVAILABLE = True
except ImportError:
    print("⚠️ PatternCache not available")
    PATTERN_CACHE_AVAILABLE = False

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


# Pydantic Models
class ScanRequest(BaseModel):
    repository_url: str = Field(..., description="Git repository URL")
    branch: str = Field(default="main", description="Branch to scan")
    github_token: Optional[str] = Field(default=None, description="GitHub token for private repos")
    threshold: int = Field(default=None, ge=0, le=100, description="Quality threshold percentage (uses global config default if not specified)")
    report_format: str = Field(default="both", description="Report format: html, json, or both")
    llm_url: Optional[str] = Field(default=None, description="Custom LLM service URL")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API key")
    splunk_query: Optional[str] = Field(default=None, description="Optional Splunk query to execute during scan")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Set default threshold from global config if not provided
        if self.threshold is None:
            try:
                # Only keep enhanced pattern library logic
                # Remove fallback/legacy pattern loader logic
                # Remove lines: 77, 78, 79
                pass # No pattern loader to get UI config
            except Exception:
                self.threshold = 70  # Fallback to hardcoded value


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


class GateInfo(BaseModel):
    name: str
    description: str
    category: str


class JiraUploadRequest(BaseModel):
    app_id: str
    scan_id: str
    report_type: str = Field(default="html", description="Report type: html or json")

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
                if dict_patterns:
                    print(f"   📋 {gate_name}: {len(dict_patterns)} patterns (dict format)")
        
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

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 CodeGates server shutting down...")
    print("✅ Shutdown complete")

# Store scan results in memory (could be replaced with Redis for production)
scan_results: Dict[str, Dict[str, Any]] = {}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic information"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CodeGates API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .code { background: #e9ecef; padding: 5px; border-radius: 3px; font-family: monospace; }
        </style>
    </head>
    <body>
        <h1 class="header">🚀 CodeGates API v2.0.0</h1>
        <p>Hard Gate Validation System with AI-powered pattern generation</p>
        
        <h2>Quick Start</h2>
        <div class="endpoint">
            <h3>Start a Scan</h3>
            <p><strong>POST</strong> <span class="code">/api/v1/scan</span></p>
            <pre class="code">{
  "repository_url": "https://github.com/owner/repo",
  "branch": "main",
  "threshold": 70
}</pre>
        </div>
        
        <div class="endpoint">
            <h3>Get Scan Status</h3>
            <p><strong>GET</strong> <span class="code">/api/v1/scan/{scan_id}</span></p>
        </div>
        
        <div class="endpoint">
            <h3>List Available Gates</h3>
            <p><strong>GET</strong> <span class="code">/api/v1/gates</span></p>
        </div>
        
        <h2>Documentation</h2>
        <ul>
            <li><a href="/docs">Interactive API Documentation (Swagger)</a></li>
            <li><a href="/redoc">ReDoc Documentation</a></li>
        </ul>
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
            "warning_gates": 0,
            "total_gates": 0,
            "errors": [],
            "current_step": None,
            "progress_percentage": None,
            "step_details": None
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
        app_id=result["request"].get("app_id") if "request" in result else None
    )


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
    if request.report_type == "html":
        pattern = os.path.join(report_dir, f"codegates_report_{request.scan_id}.html")
    else:
        pattern = os.path.join(report_dir, f"codegates_report_{request.scan_id}.json")
    matches = glob.glob(pattern)
    if not matches:
        raise HTTPException(status_code=404, detail=f"Report file not found: {pattern}")
    report_path = matches[0]
    # Start background upload
    results = {}
    def upload_all():
        nonlocal results
        results = upload_report_to_jira(
            jira_url, jira_user, jira_token, request.app_id, report_path, request.report_type
        )
    background_tasks.add_task(upload_all)
    return {"success": True, "message": f"Upload started for app_id {request.app_id}.", "results": []}


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
                "splunk_query": request.splunk_query
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
                "api_key": request.llm_api_key
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
        
        # Update scan results
        if shared["validation"]["gate_results"]:
            gate_results = shared["validation"]["gate_results"]
            passed = len([g for g in gate_results if g.get("status") == "PASS"])
            failed = len([g for g in gate_results if g.get("status") == "FAIL"])
            warnings = len([g for g in gate_results if g.get("status") == "WARNING"])
            
            # Generate report URLs
            html_report_url = f"{server_url}/api/v1/scan/{scan_id}/report/html" if shared["reports"]["html_path"] else None
            json_report_url = f"{server_url}/api/v1/scan/{scan_id}/report/json" if shared["reports"]["json_path"] else None
            
            scan_results[scan_id].update({
                "status": "completed",
                "overall_score": shared["validation"]["overall_score"],
                "total_files": shared["repository"]["metadata"].get("total_files", 0),
                "total_lines": shared["repository"]["metadata"].get("total_lines", 0),
                "passed_gates": passed,
                "failed_gates": failed,
                "warning_gates": warnings,
                "total_gates": len(gate_results),
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
            if html_report_url:
                print(f"🌐 HTML Report URL: {html_report_url}")
            if json_report_url:
                print(f"🌐 JSON Report URL: {json_report_url}")
        else:
            scan_results[scan_id].update({
                "status": "failed",
                "errors": shared["errors"] + ["No validation results generated"],
                "current_step": "Failed",
                "progress_percentage": 0,
                "step_details": "Scan failed - no validation results generated"
            })
    
    except Exception as e:
        scan_results[scan_id].update({
            "status": "failed",
            "errors": [str(e)],
            "current_step": "Failed",
            "progress_percentage": 0,
            "step_details": f"Scan failed with error: {str(e)}"
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