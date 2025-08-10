#!/usr/bin/env python3
"""
Direct Streamlit Integration for FastAPI
Serves Streamlit UI components directly through FastAPI without separate port
"""

import sys
import os
import io
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Try to import Streamlit components
try:
    import streamlit as st
    from streamlit.runtime.state import SessionState
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def get_integrated_ui_html(api_base: str = "http://localhost:8000/api/v1") -> str:
    """Get the integrated UI HTML content"""
    
    # Create the HTML content with proper string formatting
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XYXY Scanner</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <style>
        :root {{
            --primary-color: #dc3545;
            --primary-dark: #b02a37;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #212529;
            line-height: 1.6;
        }}

        .main-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            min-height: 100vh;
        }}

        .app-header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 0.75rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: center;
            backdrop-filter: blur(10px);
        }}

        .app-title {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
        }}

        .scan-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 0.75rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            padding: 2rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
        }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #212529;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .form-control, .form-select {{
            border: 2px solid #dee2e6;
            border-radius: 0.5rem;
            padding: 0.75rem;
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }}

        .form-control:focus, .form-select:focus {{
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
            outline: 0;
        }}

        .btn {{
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            color: white;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }}

        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }}

        .report-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 0.75rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            padding: 2rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background: white;
            border-radius: 0.5rem;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
            border: 1px solid #dee2e6;
            transition: transform 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        .metric-label {{
            font-size: 0.9rem;
            color: #6c757d;
            font-weight: 500;
        }}

        .gate-card {{
            background: white;
            border-radius: 0.5rem;
            border: 1px solid #dee2e6;
            margin-bottom: 1.5rem;
            overflow: hidden;
            transition: transform 0.3s ease;
        }}

        .gate-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }}

        .gate-header {{
            padding: 1.5rem;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .gate-body {{
            padding: 1.5rem;
        }}

        .status-badge {{
            padding: 0.4rem 0.8rem;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-pass {{ background: #d4edda; color: #155724; }}
        .status-fail {{ background: #f8d7da; color: #721c24; }}
        .status-warning {{ background: #fff3cd; color: #856404; }}
        .status-not-applicable {{ background: #e2e3e5; color: #383d41; }}

        .loading-indicator {{
            display: inline-block;
            width: 1rem;
            height: 1rem;
            border: 2px solid #f3f3f3;
            border-top: 2px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .hidden {{ display: none !important; }}

        .toast-container {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1055;
        }}

        .progress {{
            height: 1rem;
            border-radius: 0.5rem;
            background-color: #e9ecef;
            overflow: hidden;
        }}

        .progress-bar {{
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            transition: width 0.6s ease;
        }}

        .alert {{
            border: none;
            border-radius: 0.5rem;
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }}

        .gates-summary-container {{
            background: white;
            border-radius: 0.5rem;
            border: 1px solid #dee2e6;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .gates-summary-table {{
            background: white;
            border-radius: 0.5rem;
        }}

        .table {{
            margin-bottom: 0;
        }}

        .table th {{
            border-top: none;
            font-weight: 600;
            color: #495057;
            background-color: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
        }}

        .table td {{
            vertical-align: middle;
            border-bottom: 1px solid #dee2e6;
        }}

        .table tbody tr:hover {{
            background-color: #f8f9fa;
        }}

        .badge {{
            font-size: 0.75rem;
            padding: 0.35rem 0.65rem;
        }}

        .gates-detailed-view {{
            border-top: 2px solid #dee2e6;
            padding-top: 1.5rem;
        }}

        .btn-outline-secondary {{
            border-color: #dee2e6;
            color: #495057;
        }}

        .btn-outline-secondary:hover {{
            background-color: #f8f9fa;
            border-color: #adb5bd;
            color: #495057;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <!-- App Header -->
        <div class="app-header">
            <h1 class="app-title">
                <i class="fas fa-shield-alt"></i>
                Hard Gates Analyzer
            </h1>
            <p class="text-muted">Enterprise-grade code security analysis with JIRA integration</p>
        </div>

        <!-- Scan Configuration -->
        <div class="scan-section">
            <h2 class="section-title">
                <i class="fas fa-cog"></i>
                Scan Configuration
            </h2>
            
            <form id="scanForm">
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group mb-3">
                            <label for="gitEndpoint" class="form-label">Git Endpoint</label>
                            <select class="form-select" id="gitEndpoint" onchange="resetRepositorySelection()">
                                <option value="github.com">GitHub.com (Public)</option>
                                <option value="github.XYXY.com">GitHub Enterprise (github.XYXY.com)</option>
                                <option value="github.abc.com">GitHub Enterprise (github.abc.com)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="form-group mb-3">
                            <label for="applicationId" class="form-label">Application ID</label>
                            <input type="text" class="form-control" id="applicationId" 
                                   placeholder="Enter APP ID (e.g., mobile-app, web-service, data-pipeline)"
                                   onchange="loadRepositoriesForApp()" 
                                   onkeyup="handleAppIdKeyup(event)">
                            <div class="form-text">Enter the application identifier to search for related repositories</div>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group mb-3">
                            <label for="repositorySelect" class="form-label">Repository Selection</label>
                            <select class="form-select" id="repositorySelect" onchange="loadBranchesForRepo()" disabled>
                                <option value="">First select an Application ID</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="form-group mb-3">
                            <label for="branch" class="form-label">Branch</label>
                            <select class="form-select" id="branch" disabled>
                                <option value="">First select a repository</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group mb-3">
                            <label for="repositoryUrl" class="form-label">Repository URL</label>
                            <input type="text" class="form-control" id="repositoryUrl" readonly placeholder="URL will be populated automatically">
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="form-group mb-3">
                            <label for="githubToken" class="form-label">GitHub Token (Optional)</label>
                            <input type="password" class="form-control" id="githubToken" placeholder="ghp_xxxxxxxxxxxx">
                        </div>
                    </div>
                </div>

                <div class="d-flex gap-3 mt-4">
                    <button type="button" class="btn btn-primary" id="runScanBtn" onclick="startScan()">
                        <i class="fas fa-play me-2"></i>Run Security Scan
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="resetForm()">
                        <i class="fas fa-redo me-2"></i>Reset Form
                    </button>
                </div>
            </form>
        </div>

        <!-- Progress Section -->
        <div class="scan-section hidden" id="progressSection">
            <h2 class="section-title">
                <i class="fas fa-tasks"></i>
                Scan Progress
            </h2>
            
            <div class="mb-3">
                <div class="d-flex justify-content-between mb-2">
                    <span id="statusText" class="fw-bold">INITIALIZING</span>
                    <span id="progressPercent">0%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar" id="progressBar" role="progressbar" style="width: 0%"></div>
                </div>
                <div class="mt-2">
                    <small id="stepDetails" class="text-muted">Preparing scan...</small>
                </div>
            </div>
        </div>

        <!-- Report Section -->
        <div class="report-section hidden" id="reportSection">
            <div class="report-header">
                <h2 class="section-title">
                    <i class="fas fa-file-alt me-2"></i>
                    Security Analysis Report
                </h2>
            </div>

            <!-- Metrics Grid -->
            <div class="metrics-grid" id="metricsGrid">
                <!-- Metrics will be populated here -->
            </div>

            <!-- Security Gates -->
            <div class="gates-container">
                <h3 class="section-title">
                    <i class="fas fa-shield-alt"></i>
                    Security Gates Analysis
                </h3>
                <div id="gatesContainer">
                    <!-- Gate cards will be populated here -->
                </div>
            </div>

            <!-- Export Options -->
            <div class="d-flex gap-3 mt-4">
                <button type="button" class="btn btn-outline-secondary" onclick="exportFullReport()">
                    <i class="fas fa-download me-2"></i>Export Full Report
                </button>
                <button type="button" class="btn btn-outline-secondary" onclick="generatePDFs()">
                    <i class="fas fa-file-pdf me-2"></i>Generate PDFs
                </button>
            </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        const API_BASE = "{api_base}";
        let currentScanId = null;
        let scanResults = null;

        // Application configuration - now simplified for flexible APP IDs
        // No longer needed for predefined categories, but kept for potential future use
        const EXAMPLE_APP_IDS = [
            'mobile-app', 'web-service', 'data-pipeline', 'auth-service', 
            'api-gateway', 'user-portal', 'payment-service', 'analytics-dashboard'
        ];

        // Global API call function
        async function apiCall(url, options = {{}}) {{
            const response = await fetch(url, {{
                ...options,
                headers: {{
                    'Content-Type': 'application/json',
                    ...options.headers
                }}
            }});
            
            if (!response.ok) {{
                throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
            }}
            
            return response;
        }}

        // Load repositories based on entered app ID
        async function loadRepositoriesForApp() {{
            const appId = document.getElementById('applicationId').value.trim();
            const gitEndpoint = document.getElementById('gitEndpoint').value;
            const githubToken = document.getElementById('githubToken').value;
            const repositorySelect = document.getElementById('repositorySelect');
            const branchSelect = document.getElementById('branch');
            
            if (!appId) {{
                repositorySelect.innerHTML = '<option value="">Enter an Application ID first</option>';
                repositorySelect.disabled = true;
                branchSelect.innerHTML = '<option value="">First select a repository</option>';
                branchSelect.disabled = true;
                return;
            }}
            
            repositorySelect.innerHTML = '<option value="">Loading repositories...</option>';
            repositorySelect.disabled = true;
            
            try {{
                // Generate search keywords from APP ID
                const keywords = generateKeywordsFromAppId(appId);
                const requestBody = {{
                    keywords: keywords,
                    git_endpoint: gitEndpoint,
                    limit: 20
                }};
                
                // Add GitHub token if provided
                if (githubToken && githubToken.trim()) {{
                    requestBody.github_token = githubToken.trim();
                }}
                
                const response = await apiCall(`${{API_BASE}}/git/search-repositories`, {{
                    method: 'POST',
                    body: JSON.stringify(requestBody)
                }});
                
                const data = await response.json();
                
                repositorySelect.innerHTML = '<option value="">Select a repository</option>';
                
                if (data.success && data.repositories && data.repositories.length > 0) {{
                    data.repositories.forEach(repo => {{
                        const option = document.createElement('option');
                        option.value = JSON.stringify(repo);
                        option.textContent = `${{repo.name}} (${{repo.owner}})`;
                        repositorySelect.appendChild(option);
                    }});
                    repositorySelect.disabled = false;
                    showAlert(`Found ${{data.repositories.length}} repositories for "${{appId}}"`, 'success');
                }} else {{
                    repositorySelect.innerHTML = '<option value="">No repositories found</option>';
                    showAlert(`No repositories found for APP ID "${{appId}}"`, 'warning');
                }}
                
            }} catch (error) {{
                console.error('Error loading repositories:', error);
                repositorySelect.innerHTML = '<option value="">Error loading repositories</option>';
                showAlert(`Failed to load repositories: ${{error.message}}`, 'danger');
            }}
        }}

        // Generate search keywords from APP ID
        function generateKeywordsFromAppId(appId) {{
            // Convert APP ID to search keywords
            const keywords = [];
            
            // Add the APP ID itself
            keywords.push(appId);
            
            // Split by common separators and add parts
            const parts = appId.split(/[-_\\s]+/).filter(part => part.length > 2);
            keywords.push(...parts);
            
            // Add common variations
            if (appId.includes('mobile')) keywords.push('app', 'ios', 'android');
            if (appId.includes('web')) keywords.push('frontend', 'react', 'angular', 'vue');
            if (appId.includes('api')) keywords.push('service', 'rest', 'microservice');
            if (appId.includes('data')) keywords.push('pipeline', 'etl', 'analytics');
            if (appId.includes('auth')) keywords.push('authentication', 'security', 'oauth');
            
            // Remove duplicates and return
            return [...new Set(keywords)];
        }}

        // Handle keyup events for APP ID input (search on Enter key)
        function handleAppIdKeyup(event) {{
            if (event.key === 'Enter') {{
                loadRepositoriesForApp();
            }}
        }}

        // Load branches for selected repository
        async function loadBranchesForRepo() {{
            const repositorySelect = document.getElementById('repositorySelect');
            const branchSelect = document.getElementById('branch');
            const repositoryUrlInput = document.getElementById('repositoryUrl');
            const gitEndpoint = document.getElementById('gitEndpoint').value;
            const githubToken = document.getElementById('githubToken').value;
            
            if (!repositorySelect.value) {{
                branchSelect.innerHTML = '<option value="">First select a repository</option>';
                branchSelect.disabled = true;
                repositoryUrlInput.value = '';
                return;
            }}
            
            try {{
                const repoData = JSON.parse(repositorySelect.value);
                const repositoryUrl = `https://${{gitEndpoint}}/${{repoData.owner}}/${{repoData.name}}`;
                repositoryUrlInput.value = repositoryUrl;
                
                const requestBody = {{
                    repository_url: repositoryUrl,
                    git_endpoint: gitEndpoint,
                    owner: repoData.owner,
                    name: repoData.name
                }};
                
                // Add GitHub token if provided
                if (githubToken && githubToken.trim()) {{
                    requestBody.github_token = githubToken.trim();
                }}
                
                const response = await apiCall(`${{API_BASE}}/git/list-branches`, {{
                    method: 'POST',
                    body: JSON.stringify(requestBody)
                }});
                
                const data = await response.json();
                
                branchSelect.innerHTML = '<option value="">Select a branch</option>';
                
                if (data.branches && data.branches.length > 0) {{
                    data.branches.forEach(branch => {{
                        const option = document.createElement('option');
                        option.value = branch.name;
                        option.textContent = `${{branch.name}}${{branch.is_default ? ' (default)' : ''}}`;
                        branchSelect.appendChild(option);
                    }});
                    branchSelect.disabled = false;
                    
                    // Auto-select default branch
                    const defaultBranch = data.branches.find(b => b.is_default);
                    if (defaultBranch) {{
                        branchSelect.value = defaultBranch.name;
                    }}
                }}
                
            }} catch (error) {{
                console.error('Error loading branches:', error);
                showAlert(`Failed to load branches: ${{error.message}}`, 'danger');
            }}
        }}

        // Reset repository selection
        function resetRepositorySelection() {{
            const repositorySelect = document.getElementById('repositorySelect');
            const branchSelect = document.getElementById('branch');
            const repositoryUrlInput = document.getElementById('repositoryUrl');
            
            repositorySelect.innerHTML = '<option value="">Enter an Application ID first</option>';
            repositorySelect.disabled = true;
            branchSelect.innerHTML = '<option value="">First select a repository</option>';
            branchSelect.disabled = true;
            repositoryUrlInput.value = '';
        }}

        // Start scan
        async function startScan() {{
            const applicationId = document.getElementById('applicationId').value.trim();
            const repositoryUrl = document.getElementById('repositoryUrl').value;
            const branch = document.getElementById('branch').value;
            const githubToken = document.getElementById('githubToken').value;
            
            if (!applicationId || !repositoryUrl || !branch) {{
                showAlert('Please fill in all required fields: Application ID, Repository, and Branch', 'warning');
                return;
            }}
            
            const runScanBtn = document.getElementById('runScanBtn');
            runScanBtn.disabled = true;
            runScanBtn.innerHTML = '<span class="loading-indicator me-2"></span>Starting scan...';
            
            try {{
                const scanRequest = {{
                    repository_url: repositoryUrl,
                    branch: branch,
                    github_token: githubToken || null,
                    threshold: 70,
                    app_id: applicationId
                }};
                
                const response = await apiCall(`${{API_BASE}}/scan`, {{
                    method: 'POST',
                    body: JSON.stringify(scanRequest)
                }});
                
                const data = await response.json();
                currentScanId = data.scan_id;
                
                showAlert('Scan started successfully! AI recommendations will be included automatically.', 'success');
                
                // Show progress section
                document.getElementById('progressSection').classList.remove('hidden');
                document.getElementById('reportSection').classList.add('hidden');
                
                // Start polling for progress
                pollProgress();
                
            }} catch (error) {{
                console.error('Error starting scan:', error);
                showAlert(`Failed to start scan: ${{error.message}}`, 'danger');
                resetScanButton();
            }}
        }}

        // Poll scan progress
        async function pollProgress() {{
            if (!currentScanId) return;
            
            try {{
                const response = await apiCall(`${{API_BASE}}/scan/${{currentScanId}}`);
                const result = await response.json();
                
                const progressBar = document.getElementById('progressBar');
                const statusText = document.getElementById('statusText');
                const stepDetails = document.getElementById('stepDetails');
                const progressPercent = document.getElementById('progressPercent');
                
                const progress = result.progress_percentage || 0;
                progressBar.style.width = `${{progress}}%`;
                progressPercent.textContent = `${{progress}}%`;
                
                statusText.textContent = result.status.toUpperCase();
                stepDetails.textContent = result.current_step || 'Processing...';
                
                // Enhanced progress tracking display
                displayEnhancedProgress(result);

                if (result.status === 'completed') {{
                    showAlert('Scan completed successfully!', 'success');
                    await loadResults();
                }} else if (result.status === 'failed') {{
                    showAlert(`Scan failed: ${{result.errors?.[0] || 'Unknown error'}}`, 'danger');
                    resetScanButton();
                }} else {{
                    setTimeout(pollProgress, 2000);
                }}
            }} catch (error) {{
                console.error('Error polling progress:', error);
                setTimeout(pollProgress, 5000);
            }}
        }}

        // Enhanced progress tracking display
        function displayEnhancedProgress(data) {{
            const progressSection = document.getElementById('progressSection');
            if (!progressSection) return;
            
            let enhancedHtml = '';
            
            // Evidence collection progress
            if (data.evidence_collection_progress) {{
                enhancedHtml += '<div class="mb-3"><h6>📊 Evidence Collection Progress</h6><div class="row">';
                for (const [method, methodData] of Object.entries(data.evidence_collection_progress)) {{
                    if (typeof methodData === 'object' && methodData !== null) {{
                        const status = methodData.status || 'unknown';
                        const score = methodData.score || 0;
                        const emoji = status === 'completed' ? '✅' : status === 'in_progress' ? '🔄' : '❌';
                        const statusClass = status === 'completed' ? 'text-success' : status === 'in_progress' ? 'text-warning' : 'text-danger';
                        
                        enhancedHtml += `
                            <div class="col-md-6 mb-2">
                                <div class="card">
                                    <div class="card-body p-2">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <span>${{emoji}} ${{method}}</span>
                                            <span class="${{statusClass}}">${{status}} (${{score.toFixed(1)}}%)</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }}
                }}
                enhancedHtml += '</div></div>';
            }}
            
            // Mandatory collectors status
            if (data.mandatory_collectors_status) {{
                enhancedHtml += '<div class="mb-3"><h6>🔒 Mandatory Collectors Status</h6><div class="row">';
                for (const [collector, status] of Object.entries(data.mandatory_collectors_status)) {{
                    const emoji = status === 'passed' ? '✅' : status === 'failed' ? '❌' : '⚠️';
                    const statusClass = status === 'passed' ? 'text-success' : status === 'failed' ? 'text-danger' : 'text-warning';
                    
                    enhancedHtml += `
                        <div class="col-md-6 mb-2">
                            <div class="card">
                                <div class="card-body p-2">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span>${{emoji}} ${{collector}}</span>
                                        <span class="${{statusClass}}">${{status}}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }}
                enhancedHtml += '</div></div>';
            }}
            
            // Gate validation progress
            if (data.gate_validation_progress && Array.isArray(data.gate_validation_progress)) {{
                enhancedHtml += '<div class="mb-3"><h6>🎯 Gate Validation Progress</h6>';
                for (const gateData of data.gate_validation_progress) {{
                    const gateName = gateData.gate || 'Unknown';
                    const status = gateData.status || 'unknown';
                    const progress = gateData.progress || 0;
                    const emoji = status === 'completed' ? '✅' : status === 'in_progress' ? '🔄' : '❌';
                    const statusClass = status === 'completed' ? 'text-success' : status === 'in_progress' ? 'text-warning' : 'text-danger';
                    
                    enhancedHtml += `
                        <div class="card mb-2">
                            <div class="card-body p-2">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span>${{emoji}} <strong>${{gateName}}</strong></span>
                                    <span class="${{statusClass}}">${{status}} (${{progress}}%)</span>
                                </div>
                    `;
                    
                    if (gateData.mandatory_failures && gateData.mandatory_failures.length > 0) {{
                        enhancedHtml += `
                            <div class="mt-2">
                                <small class="text-danger">
                                    ❌ <strong>Mandatory Failures:</strong> ${{gateData.mandatory_failures.join(', ')}}
                                </small>
                            </div>
                        `;
                    }}
                    
                    enhancedHtml += '</div></div>';
                }}
                enhancedHtml += '</div>';
            }}
            
            // Add enhanced progress to the progress section
            const existingEnhanced = progressSection.querySelector('.enhanced-progress');
            if (existingEnhanced) {{
                existingEnhanced.remove();
            }}
            
            if (enhancedHtml) {{
                progressSection.insertAdjacentHTML('beforeend', `<div class="enhanced-progress">${{enhancedHtml}}</div>`);
            }}
        }}

        // Load scan results
        async function loadResults() {{
            if (!currentScanId) return;

            try {{
                const response = await apiCall(`${{API_BASE}}/scan/${{currentScanId}}/results`);
                const data = await response.json();
                
                // Debug logging to see what data we're actually receiving
                console.log('🔍 Debug: Full response data:', data);
                console.log('🔍 Debug: Overall score:', data.overall_score);
                console.log('🔍 Debug: Total gates:', data.total_gates);
                console.log('🔍 Debug: Passed gates:', data.passed_gates);
                console.log('🔍 Debug: Failed gates:', data.failed_gates);
                console.log('🔍 Debug: Warning gates:', data.warning_gates);
                console.log('🔍 Debug: Gate results length:', data.gate_results?.length || 0);
                
                scanResults = data;
                displayReport(data);
                resetScanButton();
                
            }} catch (error) {{
                console.error('Error loading results:', error);
                showAlert(`Failed to load results: ${{error.message}}`, 'danger');
                resetScanButton();
            }}
        }}

        // Display the complete report
        function displayReport(data) {{
            // Show report section
            document.getElementById('progressSection').classList.add('hidden');
            document.getElementById('reportSection').classList.remove('hidden');
            
            // Display metrics
            displayMetrics(data);
            
            // Display security gates
            displaySecurityGates(data);
        }}

        // Display metrics grid - Updated to match executive summary format
        function displayMetrics(data) {{
            const metricsGrid = document.getElementById('metricsGrid');
            
            // Handle both UI format and JSON report format
            const overallScore = data.overall_score || 0;
            
            // Try UI format first, then JSON report format
            let totalGates = data.total_gates || data.summary?.total_gates || 0;
            let passedGates = data.passed_gates || data.summary?.passed_gates || 0;
            let failedGates = data.failed_gates || data.summary?.failed_gates || 0;
            let warningGates = data.warning_gates || data.summary?.warning_gates || 0;
            let notApplicableGates = data.summary?.not_applicable_gates || 0;
            
            // Calculate partially met (assuming warnings are partially met)
            let partiallyMet = warningGates;
            
            // Debug logging for metrics parsing
            console.log('📊 Debug: Executive Summary Metrics:');
            console.log('   Overall Score:', overallScore, '(type:', typeof overallScore, ')');
            console.log('   Total Gates:', totalGates, '(type:', typeof totalGates, ')');
            console.log('   Gates Met (Passed):', passedGates, '(type:', typeof passedGates, ')');
            console.log('   Partially Met (Warnings):', partiallyMet, '(type:', typeof partiallyMet, ')');
            console.log('   Not Met (Failed):', failedGates, '(type:', typeof failedGates, ')');
            console.log('   Not Applicable:', notApplicableGates, '(type:', typeof notApplicableGates, ')');
            console.log('   Data structure:', data.summary ? 'JSON report format' : 'UI format');
            
            metricsGrid.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value" style="color: ${{overallScore >= 80 ? '#28a745' : overallScore >= 60 ? '#ffc107' : '#dc3545'}}">${{Math.round(overallScore)}}%</div>
                    <div class="metric-label">Overall Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #17a2b8">${{totalGates}}</div>
                    <div class="metric-label">Total Gates Evaluated</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #28a745">${{passedGates}}</div>
                    <div class="metric-label">Gates Met</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #ffc107">${{partiallyMet}}</div>
                    <div class="metric-label">Partially Met</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #dc3545">${{failedGates}}</div>
                    <div class="metric-label">Not Met</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #6c757d">${{notApplicableGates}}</div>
                    <div class="metric-label">Not Applicable</div>
                </div>
            `;
        }}

        // Display security gates with expandable summary
        function displaySecurityGates(data) {{
            const gatesContainer = document.getElementById('gatesContainer');
            
            // Handle both UI format and JSON report format
            let gateResults = data.gate_results || data.gates || [];
            
            console.log('🔍 Debug: Gate results format:', gateResults.length > 0 ? 'Found gates' : 'No gates');
            console.log('   Using field:', data.gate_results ? 'gate_results' : data.gates ? 'gates' : 'none');
            
            if (gateResults.length === 0) {{
                gatesContainer.innerHTML = `
                    <div class="alert alert-info">
                        <h4>No Gate Results Available</h4>
                        <p>The scan completed but no detailed gate analysis is available.</p>
                    </div>
                `;
                return;
            }}

            // Create expandable summary
            gatesContainer.innerHTML = `
                <div class="gates-summary-container">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h4 class="mb-0">Security Gates Summary</h4>
                        <button class="btn btn-outline-secondary btn-sm" onclick="toggleGateDetails()" id="toggleDetailsBtn">
                            <i class="fas fa-chevron-down me-2"></i>Show Details
                        </button>
                    </div>
                    
                    <div class="gates-summary-table">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Gate Name</th>
                                        <th>Category</th>
                                        <th>Status</th>
                                        <th>Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${{gateResults.map((gate, index) => createGateSummaryRow(gate, index + 1)).join('')}}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="gates-detailed-view hidden mt-4" id="gatesDetailedView">
                        <h5 class="mb-3">
                            <i class="fas fa-list-ul me-2"></i>Detailed Gate Analysis
                        </h5>
                        ${{gateResults.map((gate, index) => createDetailedGateCard(gate, index + 1)).join('')}}
                    </div>
                </div>
            `;
        }}

        // Create gate summary row for the table
        function createGateSummaryRow(gate, gateNumber) {{
            const status = gate.status || 'UNKNOWN';
            const statusClass = `status-${{status.toLowerCase().replace('_', '-')}}`;
            const statusText = status === 'NOT_APPLICABLE' ? 'Not Applicable' : 
                             status === 'PASS' ? 'Met' : 
                             status === 'WARNING' ? 'Partially Met' : 
                             status === 'FAIL' ? 'Not Met' : status;
            
            // Use display_name if available, otherwise fall back to gate name
            const gateName = gate.display_name || gate.name || gate.gate || `Gate ${{gateNumber}}`;
            
            return `
                <tr>
                    <td>
                        <strong>${{gateName}}</strong>
                        <br>
                        <small class="text-muted">${{gate.description || 'No description available'}}</small>
                    </td>
                    <td>
                        <span class="badge bg-secondary">${{gate.category || 'General'}}</span>
                    </td>
                    <td>
                        <span class="status-badge ${{statusClass}}">${{statusText}}</span>
                    </td>
                    <td>
                        <strong>${{(gate.score || 0).toFixed(1)}}%</strong>
                    </td>
                </tr>
            `;
        }}

        // Create detailed gate card (same as before but updated gate name)
        function createDetailedGateCard(gate, gateNumber) {{
            const status = gate.status || 'UNKNOWN';
            const statusClass = `status-${{status.toLowerCase().replace('_', '-')}}`;
            const statusText = status === 'NOT_APPLICABLE' ? 'Not Applicable' : 
                             status === 'PASS' ? 'Met' : 
                             status === 'WARNING' ? 'Partially Met' : 
                             status === 'FAIL' ? 'Not Met' : status;
            
            // Use display_name if available, otherwise fall back to gate name
            const gateName = gate.display_name || gate.name || gate.gate || `Gate ${{gateNumber}}`;
            
            const matches = gate.matches || [];
            const matchesHtml = matches.length > 0 ? `
                <div class="mt-3">
                    <h6>Code Matches (${{matches.length}})</h6>
                    ${{matches.slice(0, 5).map(match => `
                        <div class="border rounded p-2 mb-2 small">
                            <strong>${{match.file || 'Unknown file'}}</strong> - Line ${{match.line || 'Unknown'}}<br>
                            <code>${{match.code || match.content || 'No code available'}}</code>
                        </div>
                    `).join('')}}
                    ${{matches.length > 5 ? `<small class="text-muted">... and ${{matches.length - 5}} more matches</small>` : ''}}
                </div>
            ` : '<div class="alert alert-success mt-3">No issues found for this gate</div>';
            
            // Enhanced markdown to HTML formatter for LLM recommendations
            function formatLLMRecommendation(recommendation) {{
                if (!recommendation) return '';
                
                // Split the recommendation into lines and format them
                let formattedHtml = '';
                const lines = recommendation.split('\\n');
                let inList = false;
                
                for (let line of lines) {{
                    const originalLine = line;
                    line = line.trim();
                    
                    if (!line) {{
                        if (inList) {{
                            formattedHtml += '</ul>';
                            inList = false;
                        }}
                        formattedHtml += '<br>';
                        continue;
                    }}
                    
                    // Check for markdown bold headers (**text**)
                    if (line.match(/^\\*\\*.*\\*\\*:?$/)) {{
                        if (inList) {{
                            formattedHtml += '</ul>';
                            inList = false;
                        }}
                        const cleanHeader = line.replace(/^\\*\\*|\\*\\*:?$/g, '');
                        formattedHtml += `<h6 class="mt-3 mb-2 fw-bold text-primary">${{cleanHeader}}</h6>`;
                    }}
                    // Check for simple headers (ending with colon)
                    else if (line.endsWith(':') && !line.includes('Language:')) {{
                        if (inList) {{
                            formattedHtml += '</ul>';
                            inList = false;
                        }}
                        const cleanHeader = line.replace(/:$/, '');
                        formattedHtml += `<h6 class="mt-3 mb-2 fw-bold text-primary">${{cleanHeader}}</h6>`;
                    }}
                    // Check for bullet points (-, •, *)
                    else if (line.match(/^[-•*]\\\\s+/)) {{
                        if (!inList) {{
                            formattedHtml += '<ul class="list-unstyled ms-3">';
                            inList = true;
                        }}
                        const content = line.replace(/^[-•*]\\\\s+/, '');
                        formattedHtml += `<li class="mb-2"><i class="fas fa-chevron-right text-primary me-2"></i>${{content}}</li>`;
                    }}
                    // Check for numbered points (1., 2., etc.)
                    else if (line.match(/^\\\\d+\\\\.\\\\s+/)) {{
                        if (inList) {{
                            formattedHtml += '</ul>';
                            inList = false;
                        }}
                        const number = line.match(/^(\\\\d+)/)[1];
                        const content = line.replace(/^\\\\d+\\\\.\\\\s+/, '');
                        formattedHtml += `<div class="ms-3 mb-2"><span class="badge bg-primary me-2">${{number}}</span>${{content}}</div>`;
                    }}
                    // Check for programming language detection
                    else if (line.toLowerCase().includes('programming language:')) {{
                        if (inList) {{
                            formattedHtml += '</ul>';
                            inList = false;
                        }}
                        formattedHtml += `<div class="mb-3 p-2 bg-light rounded border-start border-info border-3"><small class="text-muted"><i class="fas fa-code me-2"></i>${{line}}</small></div>`;
                    }}
                    // Check for inline markdown bold (**text**)
                    else if (line.includes('**')) {{
                        if (inList) {{
                            formattedHtml += '</ul>';
                            inList = false;
                        }}
                        // Replace **text** with <strong>text</strong>
                        const formattedLine = line.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
                        formattedHtml += `<p class="mb-2">${{formattedLine}}</p>`;
                    }}
                    // Regular paragraph text
                    else {{
                        if (inList) {{
                            formattedHtml += '</ul>';
                            inList = false;
                        }}
                        formattedHtml += `<p class="mb-2">${{line}}</p>`;
                    }}
                }}
                
                // Close any open list
                if (inList) {{
                    formattedHtml += '</ul>';
                }}
                
                return formattedHtml;
            }}

            // Add LLM recommendation section for all gates with recommendations
            const llmRecommendationHtml = gate.llm_recommendation ? (() => {{
                const isSuccess = status === 'PASS';
                const bgColor = isSuccess ? '#d4edda' : '#e7f3ff';
                const borderColor = isSuccess ? '#28a745' : '#2563eb';
                const iconColor = isSuccess ? '#28a745' : '#2563eb';
                const title = isSuccess ? 'AI Best Practice Insights' : 'AI Recommendations';
                const icon = isSuccess ? 'fa-check-circle' : 'fa-robot';
                
                const formattedRecommendation = formatLLMRecommendation(gate.llm_recommendation);
                
                return `
                    <div class="mt-3 p-3 rounded" style="background-color: ${{bgColor}} !important; border-left: 4px solid ${{borderColor}};">
                        <h6 style="color: ${{iconColor}};"><i class="fas ${{icon}} me-2"></i>${{title}}</h6>
                        <div class="llm-recommendation" style="line-height: 1.6;">
                            ${{formattedRecommendation}}
                        </div>
                        ${{gate.recommendation_generated ? 
                            `<small class="text-muted"><i class="fas fa-check-circle"></i> Generated by AI Assistant</small>` : ''
                        }}
                    </div>
                `;
            }})() : '';
            
            return `
                <div class="gate-card">
                    <div class="gate-header">
                        <div>
                            <h4 class="mb-1">
                                ${{gateName}}
                                <span class="status-badge ${{statusClass}} ms-2">${{statusText}}</span>
                            </h4>
                            <p class="text-muted mb-0">${{gate.description || 'No description available'}}</p>
                        </div>
                        <div class="text-end">
                            <div class="h5 mb-0">${{(gate.score || 0).toFixed(1)}}%</div>
                            <small class="text-muted">Score</small>
                        </div>
                    </div>
                    
                    <div class="gate-body">
                        <div class="row">
                            <div class="col-md-3">
                                <strong>Category:</strong><br>
                                <span class="text-muted">${{gate.category || 'General'}}</span>
                            </div>
                            <div class="col-md-3">
                                <strong>Patterns:</strong><br>
                                <span class="text-muted">${{gate.patterns_used || gate.pattern_count || (gate.patterns ? gate.patterns.length : 0)}}</span>
                            </div>
                            <div class="col-md-3">
                                <strong>Matches:</strong><br>
                                <span class="text-muted">${{matches.length}}</span>
                            </div>
                            <div class="col-md-3">
                                <strong>Files:</strong><br>
                                <span class="text-muted">${{gate.files_with_matches || 0}}</span>
                            </div>
                        </div>
                        
                        <div class="row mt-2">
                            <div class="col-md-6">
                                <strong>Confidence:</strong><br>
                                <span class="text-muted">${{(gate.confidence || 0).toFixed(1)}}%</span>
                            </div>
                            <div class="col-md-6">
                                <strong>Score:</strong><br>
                                <span class="text-muted">${{(gate.score || 0).toFixed(1)}}%</span>
                            </div>
                        </div>
                        
                        ${{matchesHtml}}
                        
                        ${{llmRecommendationHtml}}
                        
                        <div class="mt-3 p-3 bg-light rounded">
                            <h6>JIRA Integration</h6>
                            <div class="row">
                                <div class="col-md-6 mb-2">
                                    <label class="form-label">Comments:</label>
                                    <textarea class="form-control" id="comment-${{gateNumber}}" rows="2" 
                                              placeholder="Add your analysis and comments..."></textarea>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">JIRA Ticket ID:</label>
                                    <input type="text" class="form-control mb-2" id="jira-id-${{gateNumber}}" 
                                           placeholder="PROJ-123">
                                    <button class="btn btn-primary btn-sm" onclick="uploadToJira(${{gateNumber}})">
                                        <i class="fas fa-upload me-1"></i>Upload to JIRA
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }}

        // Toggle gate details visibility
        function toggleGateDetails() {{
            const detailsView = document.getElementById('gatesDetailedView');
            const toggleBtn = document.getElementById('toggleDetailsBtn');
            
            if (detailsView.classList.contains('hidden')) {{
                detailsView.classList.remove('hidden');
                toggleBtn.innerHTML = '<i class="fas fa-chevron-up me-2"></i>Hide Details';
            }} else {{
                detailsView.classList.add('hidden');
                toggleBtn.innerHTML = '<i class="fas fa-chevron-down me-2"></i>Show Details';
            }}
        }}

        // Upload gate report to JIRA
        async function uploadToJira(gateNumber) {{
            const comment = document.getElementById(`comment-${{gateNumber}}`).value;
            const jiraId = document.getElementById(`jira-id-${{gateNumber}}`).value;
            
            if (!jiraId.trim()) {{
                showAlert('Please enter a JIRA ticket ID', 'warning');
                return;
            }}
            
            if (!currentScanId) {{
                showAlert('No scan results available for upload', 'warning');
                return;
            }}
            
            const uploadBtn = event.target;
            const originalText = uploadBtn.innerHTML;
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="loading-indicator me-1"></span>Uploading to JIRA...';
            
            try {{
                const appId = scanResults?.app_id || document.getElementById('applicationId')?.value || 'unknown';
                
                const jiraResponse = await apiCall(`${{API_BASE}}/jira/upload`, {{
                    method: 'POST',
                    body: JSON.stringify({{
                        app_id: appId,
                        scan_id: currentScanId,
                        report_type: 'html',
                        jira_ticket_id: jiraId,
                        gate_number: gateNumber,
                        comment: comment
                    }})
                }});
                
                const jiraResult = await jiraResponse.json();
                
                if (jiraResult.success) {{
                    showAlert(`Successfully uploaded Gate ${{gateNumber}} to JIRA ticket ${{jiraId}}`, 'success');
                    uploadBtn.innerHTML = '<i class="fas fa-check me-1"></i>Uploaded!';
                    uploadBtn.classList.remove('btn-primary');
                    uploadBtn.classList.add('btn-success');
                }} else {{
                    throw new Error(jiraResult.message || 'JIRA upload failed');
                }}
                
            }} catch (error) {{
                console.error('Error uploading to JIRA:', error);
                showAlert(`Failed to upload to JIRA: ${{error.message}}`, 'danger');
                uploadBtn.innerHTML = originalText;
                uploadBtn.disabled = false;
            }}
        }}

        // Export full report
        async function exportFullReport() {{
            if (!currentScanId) {{
                showAlert('No scan results available for export', 'warning');
                return;
            }}
            
            try {{
                const response = await apiCall(`${{API_BASE}}/scan/${{currentScanId}}/report/html`);
                const htmlContent = await response.text();
                
                const blob = new Blob([htmlContent], {{ type: 'text/html' }});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `codegates_report_${{currentScanId.substr(0, 8)}}.html`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('Report exported successfully!', 'success');
            }} catch (error) {{
                showAlert(`Failed to export report: ${{error.message}}`, 'danger');
            }}
        }}

        // Generate PDFs
        async function generatePDFs() {{
            if (!currentScanId) {{
                showAlert('No scan results available for PDF generation', 'warning');
                return;
            }}
            
            try {{
                const response = await apiCall(`${{API_BASE}}/scan/${{currentScanId}}/pdfs`);
                const data = await response.json();
                
                showAlert(`Generated ${{data.total_files}} PDF files successfully!`, 'success');
            }} catch (error) {{
                showAlert(`Failed to generate PDFs: ${{error.message}}`, 'danger');
            }}
        }}

        // Reset form
        function resetForm() {{
            document.getElementById('scanForm').reset();
            resetRepositorySelection();
            document.getElementById('progressSection').classList.add('hidden');
            document.getElementById('reportSection').classList.add('hidden');
            currentScanId = null;
            scanResults = null;
        }}

        // Reset scan button
        function resetScanButton() {{
            const runScanBtn = document.getElementById('runScanBtn');
            runScanBtn.disabled = false;
            runScanBtn.innerHTML = '<i class="fas fa-play me-2"></i>Run Security Scan';
        }}

        // Show alert notification
        function showAlert(message, type = 'info') {{
            const toastContainer = document.getElementById('toastContainer');
            const toastId = 'toast-' + Date.now();
            
            const alertColors = {{
                'success': '#28a745',
                'danger': '#dc3545',
                'warning': '#ffc107',
                'info': '#17a2b8'
            }};
            
            const toast = document.createElement('div');
            toast.id = toastId;
            toast.className = `alert alert-${{type}}`;
            toast.style.cssText = `
                margin-bottom: 0.5rem;
                border-left: 4px solid ${{alertColors[type]}};
                min-width: 300px;
                cursor: pointer;
            `;
            
            toast.innerHTML = `
                <span>${{message}}</span>
                <button type="button" class="btn-close ms-auto" onclick="document.getElementById('${{toastId}}').remove()"></button>
            `;
            
            toast.onclick = () => toast.remove();
            toastContainer.appendChild(toast);
            
            // Auto remove after 5 seconds
            setTimeout(() => {{
                if (document.getElementById(toastId)) {{
                    document.getElementById(toastId).remove();
                }}
            }}, 5000);
        }}

        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Hard Gates Analyzer initialized');
            showAlert('Welcome to Hard Gates Analyzer!', 'info');
        }});
        
    </script>
</body>
</html>'''
    
    return html_content