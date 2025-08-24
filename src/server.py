"""
FastAPI server for CodeGates Scan Process
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from flow.scan_flow import ScanFlow
from core.base import ScanContext
from fastapi.responses import HTMLResponse


# Pydantic models for API requests/responses
class ScanRequest(BaseModel):
    repo_url: str = Field(..., description="Repository URL to scan")
    branch: str = Field(default="main", description="Branch to scan")
    git_token: Optional[str] = Field(None, description="Git token for private repositories")
    scan_id: Optional[str] = Field(None, description="Custom scan ID")

class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, Any]
    timestamp: str

class ConfigRequest(BaseModel):
    vector_store: Dict[str, Any] = Field(default_factory=dict)
    embedding: Dict[str, Any] = Field(default_factory=dict)
    ast_parser: Dict[str, Any] = Field(default_factory=dict)
    llm: Dict[str, Any] = Field(default_factory=dict)

# Global variables
app = FastAPI(
    title="CodeGates Scan API",
    description="API for CodeGates scan process with CD repository support",
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

# Global scan flow instance
scan_flow: Optional[ScanFlow] = None
scan_results: Dict[str, Dict[str, Any]] = {}

# Default configuration
DEFAULT_CONFIG = {
    "vector_store": {
        "use_qdrant": True,
        "qdrant_path": "./qdrant_data",
        "vector_size": 768
    },
    "embedding": {
        "provider": "local",
        "model": "text-embedding-nomic-embed-text-v1.5-embedding",
        "base_url": "http://localhost:1234",
        "batch_size": 32,
        "vector_size": 768
    },
    "ast_parser": {
        "supported_languages": [
            "python", "javascript", "typescript", "java", 
            "csharp", "go", "rust", "c", "cpp"
        ]
    },
    "llm": {
        "provider": "local",
        "model": "llama-3.2-3b-instruct",
        "base_url": "http://localhost:1234",
        "temperature": 0.3,
        "max_tokens": 2000
    }
}


def initialize_scan_flow(config: Dict[str, Any] = None):
    """Initialize the scan flow with configuration"""
    global scan_flow
    try:
        if config is None:
            config = DEFAULT_CONFIG
        
        scan_flow = ScanFlow(config)
        print("✅ Scan flow initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize scan flow: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting CodeGates Scan API Server")
    initialize_scan_flow()


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "CodeGates Scan API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        services_status = {}
        
        if scan_flow:
            services_status = scan_flow.get_flow_status()
        else:
            services_status = {"status": "scan_flow_not_initialized"}
        
        return HealthResponse(
            status="healthy",
            services=services_status,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            services={"error": str(e)},
            timestamp=datetime.now().isoformat()
        )


@app.post("/api/v1/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest):
    """Start a new scan"""
    try:
        if not scan_flow:
            raise HTTPException(status_code=503, detail="Scan flow not initialized")
        
        print(f"🔍 Starting scan for: {request.repo_url}")
        
        # Generate scan_id if not provided
        scan_id = request.scan_id or f"scan_{int(datetime.now().timestamp())}"
        
        # Run scan
        result = await scan_flow.run_scan(
            repo_url=request.repo_url,
            branch=request.branch,
            git_token=request.git_token,
            scan_id=scan_id
        )
        
        # Store result - handle both the result wrapper and the actual scan data
        scan_id = result.get("scan_id", "unknown")
        
        # Store the complete result for API access
        scan_results[scan_id] = result
        
        # Also store the scan data separately for HTML report access
        if result.get("result"):
            scan_results[f"{scan_id}_data"] = result["result"]
        
        return ScanResponse(
            scan_id=scan_id,
            status=result.get("status", "unknown"),
            message="Scan completed successfully" if result.get("status") == "completed" else "Scan failed",
            result=result.get("result"),
            error=result.get("error")
        )
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@app.post("/api/v1/scan/async", response_model=ScanResponse)
async def start_async_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a scan asynchronously"""
    try:
        if not scan_flow:
            raise HTTPException(status_code=503, detail="Scan flow not initialized")
        
        scan_id = request.scan_id or f"scan_{int(datetime.now().timestamp())}"
        
        # Store initial result
        scan_results[scan_id] = {
            "scan_id": scan_id,
            "status": "running",
            "message": "Scan started"
        }
        
        # Add scan to background tasks
        background_tasks.add_task(run_scan_background, request, scan_id)
        
        return ScanResponse(
            scan_id=scan_id,
            status="running",
            message="Scan started asynchronously"
        )
        
    except Exception as e:
        print(f"❌ Async scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Async scan failed: {str(e)}")


async def run_scan_background(request: ScanRequest, scan_id: str):
    """Run scan in background"""
    try:
        print(f"🔍 Running background scan: {scan_id}")
        
        result = await scan_flow.run_scan(
            repo_url=request.repo_url,
            branch=request.branch,
            git_token=request.git_token,
            scan_id=scan_id
        )
        
        # Update stored result
        scan_results[scan_id] = result
        
        print(f"✅ Background scan completed: {scan_id}")
        
    except Exception as e:
        print(f"❌ Background scan failed: {scan_id} - {e}")
        scan_results[scan_id] = {
            "scan_id": scan_id,
            "status": "failed",
            "error": str(e)
        }


@app.get("/api/v1/scan/{scan_id}", response_model=ScanResponse)
async def get_scan_result(scan_id: str):
    """Get scan result by ID"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = scan_results[scan_id]
    
    return ScanResponse(
        scan_id=scan_id,
        status=result.get("status", "unknown"),
        message="Scan result retrieved",
        result=result.get("result"),
        error=result.get("error")
    )


@app.get("/api/v1/scans", response_model=List[Dict[str, Any]])
async def list_scans():
    """List all scans"""
    scans = []
    for scan_id, result in scan_results.items():
        scans.append({
            "scan_id": scan_id,
            "status": result.get("status", "unknown"),
            "repo_url": result.get("result", {}).get("repo_url", "unknown"),
            "timestamp": result.get("result", {}).get("scan_timestamp", "unknown"),
            "total_gates": result.get("result", {}).get("total_gates", 0),
            "passed_gates": result.get("result", {}).get("passed_gates", 0)
        })
    
    return scans


@app.post("/api/v1/config")
async def update_config(config: ConfigRequest):
    """Update server configuration"""
    try:
        # Merge with default config
        new_config = DEFAULT_CONFIG.copy()
        new_config.update(config.dict())
        
        # Reinitialize scan flow
        success = initialize_scan_flow(new_config)
        
        if success:
            return {"message": "Configuration updated successfully", "config": new_config}
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")


@app.get("/api/v1/config")
async def get_config():
    """Get current configuration"""
    return DEFAULT_CONFIG


@app.delete("/api/v1/scan/{scan_id}")
async def delete_scan(scan_id: str):
    """Delete a scan result"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    del scan_results[scan_id]
    return {"message": f"Scan {scan_id} deleted successfully"}


@app.delete("/api/v1/scans")
async def clear_all_scans():
    """Clear all scan results"""
    global scan_results
    count = len(scan_results)
    scan_results = {}
    return {"message": f"Cleared {count} scan results"}


@app.get("/api/v1/report/{scan_id}/html")
async def get_html_report(scan_id: str):
    """Get HTML report for a specific scan"""
    try:
        # Check if scan exists - try both formats
        scan_data = None
        if scan_id in scan_results:
            scan_data = scan_results[scan_id]
        elif f"{scan_id}_data" in scan_results:
            scan_data = scan_results[f"{scan_id}_data"]
        
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Check if HTML report exists in scan data
        if "html_report" in scan_data:
            return HTMLResponse(
                content=scan_data["html_report"],
                status_code=200
            )
        else:
            # Generate HTML report on demand
            from services.html_report_service import HTMLReportService
            from models.scan_models import ScanResult, GateResult, GateStatus
            
            # Get the actual scan result data
            result_data = scan_data.get("result", scan_data)
            
            # Convert scan data to ScanResult object
            gate_results = []
            for gate_data in result_data.get("gate_results", []):
                gate_result = GateResult(
                    gate_id=gate_data.get("gate_id", ""),
                    gate_name=gate_data.get("gate_name", ""),
                    status=GateStatus(gate_data.get("status", "unknown")),
                    expected_count=gate_data.get("expected_count", 0),
                    actual_count=gate_data.get("actual_count", 0),
                    threshold=gate_data.get("threshold", 0),
                    patterns_found=gate_data.get("patterns_found", []),
                    recommendations=gate_data.get("recommendations", []),
                    confidence_score=gate_data.get("confidence_score", 0.0),
                    reasoning=gate_data.get("reasoning", "")
                )
                gate_results.append(gate_result)
            
            scan_result = ScanResult(
                scan_id=scan_id,
                repo_url=result_data.get("repo_url", "Unknown"),
                branch=result_data.get("branch", "Unknown"),
                scan_timestamp=datetime.fromisoformat(result_data.get("scan_timestamp", datetime.now().isoformat())),
                total_gates=result_data.get("total_gates", 0),
                passed_gates=result_data.get("passed_gates", 0),
                failed_gates=result_data.get("failed_gates", 0),
                partial_gates=result_data.get("partial_gates", 0),
                skipped_gates=result_data.get("skipped_gates", 0),
                gate_results=gate_results,
                recommendations=result_data.get("recommendations", []),
                risk_score=result_data.get("risk_score", 0.0),
                scan_duration=result_data.get("scan_duration", 0.0),
                metadata=result_data.get("metadata", {})
            )
            
            # Generate HTML report
            html_service = HTMLReportService()
            html_report = html_service.generate_html_report(scan_result)
            
            # Store the generated report
            scan_data["html_report"] = html_report
            
            return HTMLResponse(
                content=html_report,
                status_code=200
            )
            
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>CodeGates Report - {scan_id}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .error {{ 
                        background: #fee; 
                        padding: 20px; 
                        border-radius: 8px; 
                        border: 1px solid #fcc;
                        color: #c33;
                    }}
                </style>
            </head>
            <body>
                <h1>CodeGates Scan Report</h1>
                <div class="error">
                    <h2>Error Generating Report</h2>
                    <p>Failed to generate HTML report for scan: {scan_id}</p>
                    <p>Error: {str(e)}</p>
                </div>
                <p><a href="/api/v1/scan/{scan_id}">View JSON Results</a></p>
            </body>
            </html>
            """,
            status_code=500
        )


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
