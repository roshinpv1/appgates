#!/usr/bin/env python3
"""
CodeGates Server - FastAPI Web Server
"""

import sys
import os
import uuid
import tempfile
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow import create_static_only_flow
from utils.hard_gates import HARD_GATES

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

# Import JIRA integration
try:
    from utils.jira_integration import jira_integration
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False
    print("⚠️ JIRA integration not available - install required dependencies")

# Import Splunk integration
try:
    from utils.splunk_integration import splunk_integration
    SPLUNK_AVAILABLE = True
except ImportError:
    SPLUNK_AVAILABLE = False
    print("⚠️ Splunk integration not available - install required dependencies")

# Import AppDynamics integration
try:
    from utils.appdynamics_integration import appdynamics_integration
    APPDYNAMICS_AVAILABLE = True
except ImportError:
    APPDYNAMICS_AVAILABLE = False
    print("⚠️ AppDynamics integration not available - install required dependencies")

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
    threshold: int = Field(default=70, ge=0, le=100, description="Quality threshold percentage")
    report_format: str = Field(default="both", description="Report format: html, json, or both")
    llm_url: Optional[str] = Field(default=None, description="Custom LLM service URL")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API key")


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


class GateInfo(BaseModel):
    name: str
    description: str
    category: str


class JiraConnectionTest(BaseModel):
    status: str
    message: str
    jira_version: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None


class JiraPostReportRequest(BaseModel):
    scan_id: str
    app_id: str


class JiraPostReportResponse(BaseModel):
    status: str
    message: str
    stories_processed: int
    results: Optional[List[Dict[str, Any]]] = None


class JiraStoriesResponse(BaseModel):
    app_id: str
    stories: List[str]
    count: int


class SplunkConnectionTest(BaseModel):
    status: str
    message: str
    splunk_version: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None


class SplunkSearchRequest(BaseModel):
    query: str
    earliest_time: str = "-24h"
    latest_time: str = "now"
    max_results: Optional[int] = None


class SplunkSearchResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]]
    total_results: int
    query: str
    execution_time: Optional[float] = None


class SplunkValidationRequest(BaseModel):
    app_id: str
    time_range: str = "-24h"


class SplunkValidationResponse(BaseModel):
    status: str
    app_id: str
    time_range: str
    overall_status: str
    log_validation: Dict[str, Any]
    error_validation: Dict[str, Any]
    performance_validation: Dict[str, Any]


class AppDynamicsConnectionTest(BaseModel):
    status: str
    message: str
    appd_version: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None


class AppDynamicsApplicationsResponse(BaseModel):
    status: str
    applications: List[Dict[str, Any]]
    total_applications: int


class AppDynamicsValidationRequest(BaseModel):
    app_name: str
    time_range: str = "60"


class AppDynamicsValidationResponse(BaseModel):
    status: str
    app_name: str
    time_range: str
    overall_status: str
    app_details: Dict[str, Any]
    health_rules: Dict[str, Any]
    errors: Dict[str, Any]
    performance: Dict[str, Any]
    performance_analysis: Dict[str, Any]
    summary: Dict[str, Any]


# Initialize FastAPI app
app = FastAPI(
    title="CodeGates API",
    description="Hard Gate Validation API for Code Quality Assessment",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced CORS configuration with environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for scan results (in production, use Redis/Database)
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
        step_details=result.get("step_details")
    )


@app.get("/api/v1/scan/{scan_id}/report/html", response_class=HTMLResponse)
async def get_html_report(scan_id: str):
    """
    Get HTML report for a completed scan
    """
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = scan_results[scan_id]
    
    if result["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    html_path = result.get("html_report_path")
    if not html_path or not Path(html_path).exists():
        raise HTTPException(status_code=404, detail="HTML report not found")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)


@app.get("/api/v1/scan/{scan_id}/report/json")
async def get_json_report(scan_id: str):
    """
    Get JSON report for a completed scan
    """
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = scan_results[scan_id]
    
    if result["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    json_path = result.get("json_report_path")
    if not json_path or not Path(json_path).exists():
        raise HTTPException(status_code=404, detail="JSON report not found")
    
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    return JSONResponse(content=json_data)


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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "jira_available": JIRA_AVAILABLE,
        "splunk_available": SPLUNK_AVAILABLE,
        "appdynamics_available": APPDYNAMICS_AVAILABLE
    }


@app.get("/api/v1/jira/test", response_model=JiraConnectionTest)
async def test_jira_connection():
    """Test JIRA connection and authentication"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="JIRA integration not available")
    
    result = jira_integration.test_connection()
    return JiraConnectionTest(**result)


@app.get("/api/v1/jira/stories/{app_id}", response_model=JiraStoriesResponse)
async def get_jira_stories(app_id: str):
    """Get JIRA stories associated with an app_id"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="JIRA integration not available")
    
    try:
        from utils.db_integration import fetch_jira_stories
        stories = fetch_jira_stories(app_id=app_id)
        
        return JiraStoriesResponse(
            app_id=app_id,
            stories=stories,
            count=len(stories)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching JIRA stories: {str(e)}")


@app.post("/api/v1/jira/post-report", response_model=JiraPostReportResponse)
async def post_report_to_jira(request: JiraPostReportRequest):
    """Post scan report to JIRA stories for the given app_id"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="JIRA integration not available")
    
    try:
        # Get scan results from storage
        scan_results_path = os.path.join(REPORTS_DIR, request.scan_id, "scan_results.json")
        if not os.path.exists(scan_results_path):
            raise HTTPException(status_code=404, detail=f"Scan results not found for scan_id: {request.scan_id}")
        
        with open(scan_results_path, 'r') as f:
            scan_results = json.load(f)
        
        # Get HTML report path
        html_report_path = os.path.join(REPORTS_DIR, request.scan_id, "report.html")
        
        # Post to JIRA
        result = jira_integration.post_report_to_jira(
            app_id=request.app_id,
            report_path=html_report_path,
            scan_results=scan_results
        )
        
        return JiraPostReportResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error posting report to JIRA: {str(e)}")


@app.get("/api/v1/jira/issue/{issue_key}")
async def get_jira_issue(issue_key: str):
    """Get JIRA issue details"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="JIRA integration not available")
    
    try:
        issue = jira_integration.get_issue(issue_key)
        if not issue:
            raise HTTPException(status_code=404, detail=f"JIRA issue {issue_key} not found")
        
        return issue
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting JIRA issue: {str(e)}")


@app.post("/api/v1/jira/issue/{issue_key}/comment")
async def add_jira_comment(issue_key: str, comment: Dict[str, str]):
    """Add comment to JIRA issue"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="JIRA integration not available")
    
    try:
        comment_body = comment.get("body", "")
        if not comment_body:
            raise HTTPException(status_code=400, detail="Comment body is required")
        
        result = jira_integration.add_comment(issue_key, comment_body)
        if not result:
            raise HTTPException(status_code=500, detail=f"Failed to add comment to {issue_key}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")


@app.post("/api/v1/jira/issue/{issue_key}/attach")
async def attach_file_to_jira(issue_key: str, file_path: str, filename: Optional[str] = None):
    """Attach file to JIRA issue"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="JIRA integration not available")
    
    try:
        success = jira_integration.attach_file(issue_key, file_path, filename)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to attach file to {issue_key}")
        
        return {"status": "success", "message": f"File attached to {issue_key}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error attaching file: {str(e)}")


@app.get("/api/v1/splunk/test", response_model=SplunkConnectionTest)
async def test_splunk_connection():
    """Test Splunk connection and authentication"""
    if not SPLUNK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Splunk integration not available")
    
    result = splunk_integration.test_connection()
    return SplunkConnectionTest(**result)


@app.post("/api/v1/splunk/search", response_model=SplunkSearchResponse)
async def execute_splunk_search(request: SplunkSearchRequest):
    """Execute a Splunk search query"""
    if not SPLUNK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Splunk integration not available")
    
    try:
        result = splunk_integration.execute_search(
            query=request.query,
            earliest_time=request.earliest_time,
            latest_time=request.latest_time,
            max_results=request.max_results
        )
        
        return SplunkSearchResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing Splunk search: {str(e)}")


@app.post("/api/v1/splunk/validate-app", response_model=SplunkValidationResponse)
async def validate_app_in_splunk(request: SplunkValidationRequest):
    """Validate application data in Splunk"""
    if not SPLUNK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Splunk integration not available")
    
    try:
        result = splunk_integration.comprehensive_app_validation(
            app_id=request.app_id,
            time_range=request.time_range
        )
        
        if result["status"] == "success":
            return SplunkValidationResponse(
                status=result["status"],
                app_id=result["app_id"],
                time_range=result["time_range"],
                overall_status=result["overall_status"],
                log_validation=result["log_validation"],
                error_validation=result["error_validation"],
                performance_validation=result["performance_validation"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating app in Splunk: {str(e)}")


@app.get("/api/v1/splunk/job/{job_id}")
async def get_splunk_job_status(job_id: str):
    """Get Splunk search job status"""
    if not SPLUNK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Splunk integration not available")
    
    try:
        result = splunk_integration.get_job_status(job_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")


@app.get("/api/v1/splunk/job/{job_id}/results")
async def get_splunk_job_results(job_id: str, offset: int = 0, count: int = 1000):
    """Get results from a Splunk search job"""
    if not SPLUNK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Splunk integration not available")
    
    try:
        result = splunk_integration.get_job_results(job_id, offset, count)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job results: {str(e)}")


@app.post("/api/v1/splunk/job")
async def start_splunk_search_job(request: SplunkSearchRequest):
    """Start a Splunk search job"""
    if not SPLUNK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Splunk integration not available")
    
    try:
        job_id = splunk_integration.execute_search_job(
            query=request.query,
            earliest_time=request.earliest_time,
            latest_time=request.latest_time
        )
        
        if job_id:
            return {"status": "success", "job_id": job_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to start search job")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting search job: {str(e)}")


@app.get("/api/v1/appdynamics/test", response_model=AppDynamicsConnectionTest)
async def test_appdynamics_connection():
    """Test AppDynamics connection and authentication"""
    if not APPDYNAMICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="AppDynamics integration not available")
    
    result = appdynamics_integration.test_connection()
    return AppDynamicsConnectionTest(**result)


@app.get("/api/v1/appdynamics/applications", response_model=AppDynamicsApplicationsResponse)
async def get_appdynamics_applications():
    """Get list of applications from AppDynamics"""
    if not APPDYNAMICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="AppDynamics integration not available")
    
    try:
        result = appdynamics_integration.get_applications()
        return AppDynamicsApplicationsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting applications: {str(e)}")


@app.get("/api/v1/appdynamics/application/{app_name}")
async def get_appdynamics_application(app_name: str):
    """Get specific application by name"""
    if not APPDYNAMICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="AppDynamics integration not available")
    
    try:
        result = appdynamics_integration.get_application_by_name(app_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting application: {str(e)}")


@app.post("/api/v1/appdynamics/validate-app", response_model=AppDynamicsValidationResponse)
async def validate_app_in_appdynamics(request: AppDynamicsValidationRequest):
    """Validate application data in AppDynamics"""
    if not APPDYNAMICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="AppDynamics integration not available")
    
    try:
        result = appdynamics_integration.comprehensive_app_validation(
            app_name=request.app_name,
            time_range=request.time_range
        )
        
        if result["status"] == "success":
            return AppDynamicsValidationResponse(**result)
        else:
            raise HTTPException(status_code=500, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating app in AppDynamics: {str(e)}")


@app.get("/api/v1/appdynamics/app/{app_id}/metrics")
async def get_appdynamics_metrics(app_id: int, metric_path: str = "Business Transaction Performance|Business Transactions|*|*|Calls per Minute"):
    """Get application metrics from AppDynamics"""
    if not APPDYNAMICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="AppDynamics integration not available")
    
    try:
        result = appdynamics_integration.get_application_metrics(app_id, metric_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@app.get("/api/v1/appdynamics/app/{app_id}/health-rules")
async def get_appdynamics_health_rules(app_id: int):
    """Get health rules for an application"""
    if not APPDYNAMICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="AppDynamics integration not available")
    
    try:
        result = appdynamics_integration.get_health_rules(app_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting health rules: {str(e)}")


@app.get("/api/v1/appdynamics/app/{app_id}/errors")
async def get_appdynamics_errors(app_id: int, time_range: str = "60"):
    """Get error information for an application"""
    if not APPDYNAMICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="AppDynamics integration not available")
    
    try:
        result = appdynamics_integration.get_errors(app_id, time_range)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting errors: {str(e)}")


@app.get("/api/v1/appdynamics/app/{app_id}/performance")
async def get_appdynamics_performance(app_id: int, time_range: str = "60"):
    """Get performance data for an application"""
    if not APPDYNAMICS_AVAILABLE:
        raise HTTPException(status_code=503, detail="AppDynamics integration not available")
    
    try:
        result = appdynamics_integration.get_performance_data(app_id, time_range)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance data: {str(e)}")


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
        shared = {
            "request": {
                "repository_url": request.repository_url,
                "branch": request.branch,
                "github_token": request.github_token,
                "threshold": request.threshold,
                "scan_id": scan_id,
                "output_dir": scan_reports_dir,
                "report_format": request.report_format,
                "verbose": False
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
        result_data = validation_flow.run(shared)
        
        # Update scan results
        # Store results
        scan_results[scan_id] = {
            "status": "completed",
            "overall_score": result_data.get("overall_score", 0.0),
            "total_files": result_data.get("total_files", 0),
            "total_lines": result_data.get("total_lines", 0),
            "passed_gates": result_data.get("passed_gates", 0),
            "failed_gates": result_data.get("failed_gates", 0),
            "warning_gates": result_data.get("warning_gates", 0),
            "total_gates": result_data.get("total_gates", 0),
            "html_report_url": f"{server_url}/api/v1/scan/{scan_id}/report/html",
            "json_report_url": f"{server_url}/api/v1/scan/{scan_id}/report/json",
            "completed_at": datetime.now().isoformat(),
            "errors": shared.get("errors", []),
            "current_step": None,
            "progress_percentage": 100,
            "step_details": "Scan completed successfully"
        }
        
        # Save scan results to file for JIRA integration
        scan_results_dir = os.path.join(scan_reports_dir, scan_id)
        os.makedirs(scan_results_dir, exist_ok=True)
        
        scan_results_file = os.path.join(scan_results_dir, "scan_results.json")
        with open(scan_results_file, 'w') as f:
            json.dump(scan_results[scan_id], f, indent=2)
        
        print(f"✅ Scan completed successfully: {scan_id}")
        print(f"📊 Overall Score: {scan_results[scan_id]['overall_score']:.1f}%")
        print(f"📁 Results saved to: {scan_results_file}")
        
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