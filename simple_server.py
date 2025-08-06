#!/usr/bin/env python3
"""
Simple FastAPI Server with Streamlit UI Integration
Serves the simple_app.py Streamlit app through FastAPI endpoints
"""

import sys
import os
import uuid
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Add gates directory to Python path
sys.path.append(str(Path(__file__).parent / "gates"))

try:
    from flow import create_static_only_flow
    from utils.hard_gates import HARD_GATES
    from utils.db_integration import extract_app_id_from_url
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")

# Configuration
SERVER_HOST = os.getenv("CODEGATES_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("CODEGATES_PORT", "8000"))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

# Initialize FastAPI app
app = FastAPI(
    title="CodeGates Simple Server",
    description="Simple FastAPI server with Streamlit UI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scan results storage
scan_results: Dict[str, Dict[str, Any]] = {}

# Pydantic Models
class ScanRequest(BaseModel):
    repository_url: str = Field(..., description="Git repository URL")
    branch: str = Field(default="main", description="Branch to scan")
    github_token: Optional[str] = Field(default=None, description="GitHub token")
    threshold: int = Field(default=70, ge=0, le=100, description="Quality threshold")
    report_format: str = Field(default="both", description="Report format")

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
    total_gates: int
    html_report_url: Optional[str] = None
    json_report_url: Optional[str] = None
    completed_at: Optional[str] = None
    errors: List[str] = []
    current_step: Optional[str] = None
    progress_percentage: Optional[int] = None

class GateInfo(BaseModel):
    name: str
    description: str
    category: str

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main page that serves the Streamlit UI"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CodeGates Simple Scanner</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
            .header {{ background: #1f77b4; color: white; padding: 1rem; text-align: center; }}
            .nav {{ background: #f8f9fa; padding: 1rem; margin-bottom: 1rem; }}
            .nav a {{ margin-right: 1rem; text-decoration: none; color: #1f77b4; }}
            .nav a:hover {{ text-decoration: underline; }}
            #streamlit-frame {{ width: 100%; height: calc(100vh - 120px); border: none; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 CodeGates Simple Scanner</h1>
            <p>APP ID → Repository → Branch → Scan</p>
        </div>
        <div class="nav">
            <a href="/">🏠 Home</a>
            <a href="/ui">🎨 UI Interface</a>
            <a href="/docs">📚 API Docs</a>
            <a href="http://localhost:{STREAMLIT_PORT}" target="_blank">🚀 Direct Streamlit</a>
        </div>
        <iframe id="streamlit-frame" src="http://localhost:{STREAMLIT_PORT}" frameborder="0"></iframe>
    </body>
    </html>
    """

@app.get("/ui", response_class=HTMLResponse)
async def ui():
    """UI endpoint that serves the Streamlit app"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CodeGates Scanner</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ margin: 0; padding: 0; }}
            #streamlit-frame {{ width: 100vw; height: 100vh; border: none; }}
        </style>
    </head>
    <body>
        <iframe id="streamlit-frame" src="http://localhost:{STREAMLIT_PORT}" frameborder="0"></iframe>
    </body>
    </html>
    """

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "CodeGates Simple Server",
        "version": "1.0.0",
        "streamlit_port": STREAMLIT_PORT
    }

@app.post("/api/v1/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new scan"""
    scan_id = str(uuid.uuid4())
    
    # Initialize scan result
    scan_results[scan_id] = {
        "scan_id": scan_id,
        "status": "starting",
        "created_at": datetime.now().isoformat(),
        "request": request.dict(),
        "progress_percentage": 0,
        "current_step": "Initializing scan...",
        "errors": []
    }
    
    # Add background task
    background_tasks.add_task(perform_scan, scan_id, request)
    
    return ScanResponse(
        scan_id=scan_id,
        status="started",
        message="Scan initiated successfully",
        created_at=scan_results[scan_id]["created_at"]
    )

@app.get("/api/v1/scan/{scan_id}", response_model=ScanResult)
async def get_scan_status(scan_id: str):
    """Get scan status and results"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = scan_results[scan_id]
    
    return ScanResult(
        scan_id=result["scan_id"],
        status=result["status"],
        overall_score=result.get("overall_score", 0),
        total_files=result.get("total_files", 0),
        total_lines=result.get("total_lines", 0),
        passed_gates=result.get("passed_gates", 0),
        failed_gates=result.get("failed_gates", 0),
        total_gates=result.get("total_gates", 0),
        html_report_url=f"/api/v1/scan/{scan_id}/report/html" if result.get("html_report") else None,
        json_report_url=f"/api/v1/scan/{scan_id}/report/json" if result.get("json_report") else None,
        completed_at=result.get("completed_at"),
        errors=result.get("errors", []),
        current_step=result.get("current_step"),
        progress_percentage=result.get("progress_percentage")
    )

@app.get("/api/v1/scan/{scan_id}/report/html", response_class=HTMLResponse)
async def get_html_report(scan_id: str):
    """Get HTML report"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = scan_results[scan_id]
    html_report = result.get("html_report")
    
    if not html_report:
        return HTMLResponse(
            content="<h1>Report not ready</h1><p>HTML report is being generated...</p>",
            status_code=202
        )
    
    return HTMLResponse(content=html_report, status_code=200)

@app.get("/api/v1/scan/{scan_id}/report/json")
async def get_json_report(scan_id: str):
    """Get JSON report"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = scan_results[scan_id]
    json_report = result.get("json_report")
    
    if not json_report:
        return JSONResponse(
            content={"message": "JSON report is being generated..."},
            status_code=202
        )
    
    return JSONResponse(content=json_report, status_code=200)

@app.get("/api/v1/gates", response_model=List[GateInfo])
async def list_gates():
    """List available gates"""
    try:
        gates = []
        for gate_name, gate_info in HARD_GATES.items():
            gates.append(GateInfo(
                name=gate_name,
                description=gate_info.get("description", "No description available"),
                category=gate_info.get("category", "Unknown")
            ))
        return gates
    except:
        # Return sample gates if HARD_GATES is not available
        return [
            GateInfo(name="SECURITY_SCAN", description="Security vulnerability scan", category="Security"),
            GateInfo(name="CODE_QUALITY", description="Code quality assessment", category="Quality"),
            GateInfo(name="DEPENDENCY_CHECK", description="Dependency vulnerability check", category="Security")
        ]

async def perform_scan(scan_id: str, request: ScanRequest):
    """Perform the actual scan (simplified version)"""
    try:
        # Update status
        scan_results[scan_id]["status"] = "running"
        scan_results[scan_id]["progress_percentage"] = 10
        scan_results[scan_id]["current_step"] = "Fetching repository..."
        
        # Simulate scan progress
        steps = [
            (20, "Analyzing code structure..."),
            (40, "Running security checks..."),
            (60, "Checking dependencies..."),
            (80, "Generating report..."),
            (100, "Scan completed")
        ]
        
        for progress, step in steps:
            scan_results[scan_id]["progress_percentage"] = progress
            scan_results[scan_id]["current_step"] = step
            time.sleep(2)  # Simulate processing time
        
        # Generate mock results
        scan_results[scan_id].update({
            "status": "completed",
            "progress_percentage": 100,
            "current_step": "Scan completed",
            "completed_at": datetime.now().isoformat(),
            "overall_score": 85.5,
            "total_files": 157,
            "total_lines": 12847,
            "passed_gates": 12,
            "failed_gates": 3,
            "total_gates": 15,
            "html_report": f"<h1>Scan Report for {request.repository_url}</h1><p>Overall Score: 85.5%</p><p>This is a mock report.</p>",
            "json_report": {
                "repository": request.repository_url,
                "branch": request.branch,
                "overall_score": 85.5,
                "gates": {
                    "passed": 12,
                    "failed": 3,
                    "total": 15
                },
                "files_analyzed": 157,
                "lines_analyzed": 12847
            }
        })
        
    except Exception as e:
        scan_results[scan_id].update({
            "status": "failed",
            "errors": [str(e)],
            "completed_at": datetime.now().isoformat()
        })

def start_streamlit():
    """Start Streamlit in background"""
    try:
        ui_path = Path(__file__).parent / "ui" / "simple_app.py"
        if ui_path.exists():
            subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", str(ui_path),
                "--server.port", str(STREAMLIT_PORT),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ])
            print(f"✅ Streamlit UI started on port {STREAMLIT_PORT}")
        else:
            print(f"⚠️ Streamlit UI file not found: {ui_path}")
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting CodeGates Simple Server...")
    
    # Start Streamlit in background
    start_streamlit()
    
    # Wait for Streamlit to start
    time.sleep(3)
    
    print(f"🌐 Server starting on http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"🎨 UI available at http://{SERVER_HOST}:{SERVER_PORT}/ui")
    print(f"📚 API docs at http://{SERVER_HOST}:{SERVER_PORT}/docs")
    print(f"🚀 Direct Streamlit at http://localhost:{STREAMLIT_PORT}")
    
    uvicorn.run(
        "simple_server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=False
    ) 