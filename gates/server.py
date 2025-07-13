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
from pydantic import BaseModel, Field

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow import create_validation_flow
from utils.hard_gates import HARD_GATES


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


class GateInfo(BaseModel):
    name: str
    description: str
    category: str


# FastAPI App
app = FastAPI(
    title="CodeGates API",
    description="Hard Gate Validation System with AI-powered pattern generation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
            "errors": []
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
        errors=result["errors"]
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
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "active_scans": len([s for s in scan_results.values() if s["status"] == "running"])
    }


async def perform_scan(scan_id: str, request: ScanRequest):
    """
    Perform the actual repository scan in background
    """
    try:
        # Update status
        scan_results[scan_id]["status"] = "running"
        
        # Initialize shared store
        shared = {
            "request": {
                "repository_url": request.repository_url,
                "branch": request.branch,
                "github_token": request.github_token,
                "threshold": request.threshold,
                "scan_id": scan_id,
                "output_dir": f"./reports/{scan_id}",
                "report_format": request.report_format,
                "verbose": False
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
            "temp_dir": tempfile.mkdtemp(prefix=f"codegates_{scan_id}_"),
            "errors": []
        }
        
        # Run validation flow
        validation_flow = create_validation_flow()
        validation_flow.run(shared)
        
        # Update scan results
        if shared["validation"]["gate_results"]:
            gate_results = shared["validation"]["gate_results"]
            passed = len([g for g in gate_results if g.get("status") == "PASS"])
            failed = len([g for g in gate_results if g.get("status") == "FAIL"])
            warnings = len([g for g in gate_results if g.get("status") == "WARNING"])
            
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
                "html_report_url": f"/api/v1/scan/{scan_id}/report/html" if shared["reports"]["html_path"] else None,
                "json_report_url": f"/api/v1/scan/{scan_id}/report/json" if shared["reports"]["json_path"] else None,
                "completed_at": datetime.now().isoformat(),
                "errors": shared["errors"]
            })
        else:
            scan_results[scan_id].update({
                "status": "failed",
                "errors": shared["errors"] + ["No validation results generated"]
            })
    
    except Exception as e:
        scan_results[scan_id].update({
            "status": "failed",
            "errors": [str(e)]
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 