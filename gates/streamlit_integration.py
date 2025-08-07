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
    
    # Use string concatenation instead of f-strings to avoid CSS parsing issues
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeGates Security Scanner</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #dc3545;
            --primary-dark: #b02a37;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #212529;
            line-height: 1.6;
        }

        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            min-height: 100vh;
        }

        .app-header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 0.75rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: center;
            backdrop-filter: blur(10px);
        }

        .app-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
        }

        .scan-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 0.75rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            padding: 2rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
        }

        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #212529;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .form-control, .form-select {
            border: 2px solid #dee2e6;
            border-radius: 0.5rem;
            padding: 0.75rem;
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }

        .form-control:focus, .form-select:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
            outline: 0;
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            color: white;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }

        .report-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 0.75rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            padding: 2rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: white;
            border-radius: 0.5rem;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
            border: 1px solid #dee2e6;
            transition: transform 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .metric-label {
            font-size: 0.9rem;
            color: #6c757d;
            font-weight: 500;
        }

        .gate-card {
            background: white;
            border-radius: 0.5rem;
            border: 1px solid #dee2e6;
            margin-bottom: 1.5rem;
            overflow: hidden;
            transition: transform 0.3s ease;
        }

        .gate-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }

        .gate-header {
            padding: 1.5rem;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .gate-body {
            padding: 1.5rem;
        }

        .status-badge {
            padding: 0.4rem 0.8rem;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-pass { background: #d4edda; color: #155724; }
        .status-fail { background: #f8d7da; color: #721c24; }
        .status-warning { background: #fff3cd; color: #856404; }
        .status-not-applicable { background: #e2e3e5; color: #383d41; }

        .loading-indicator {
            display: inline-block;
            width: 1rem;
            height: 1rem;
            border: 2px solid #f3f3f3;
            border-top: 2px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .hidden { display: none !important; }

        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1055;
        }

        .progress {
            height: 1rem;
            border-radius: 0.5rem;
            background-color: #e9ecef;
            overflow: hidden;
        }

        .progress-bar {
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            transition: width 0.6s ease;
        }

        .alert {
            border: none;
            border-radius: 0.5rem;
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }
    </style>
</head>
<body>
    <div class="main-container">
        <!-- App Header -->
        <div class="app-header">
            <h1 class="app-title">
                <i class="fas fa-shield-alt"></i>
                CodeGates Security Scanner
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
                                <option value="github.abc.com">GitHub Enterprise (github.abc.com)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="form-group mb-3">
                            <label for="applicationId" class="form-label">Application ID</label>
                            <select class="form-select" id="applicationId" onchange="loadRepositoriesForApp()">
                                <option value="">Select Application Category</option>
                                <option value="FRONTEND_REACT">Frontend - React Applications</option>
                                <option value="BACKEND_PYTHON">Backend - Python Services</option>
                                <option value="BACKEND_JAVA">Backend - Java Applications</option>
                                <option value="API_MICROSERVICES">API - Microservices</option>
                            </select>
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

    <script>''' + '''
        const API_BASE = "''' + api_base + '''";
        let currentScanId = null;
        let scanResults = null;

        // Application configuration mapping
        const APP_CONFIG = {
            'FRONTEND_REACT': {
                name: 'Frontend - React Applications',
                keywords: ['react', 'nextjs', 'gatsby', 'frontend'],
                git_endpoints: ['github.com', 'gitlab.com']
            },
            'BACKEND_PYTHON': {
                name: 'Backend - Python Services',
                keywords: ['python', 'django', 'flask', 'fastapi'],
                git_endpoints: ['github.com', 'gitlab.com']
            },
            'BACKEND_JAVA': {
                name: 'Backend - Java Applications',
                keywords: ['java', 'spring', 'springboot'],
                git_endpoints: ['github.com', 'gitlab.com']
            },
            'API_MICROSERVICES': {
                name: 'API - Microservices',
                keywords: ['microservices', 'api', 'rest'],
                git_endpoints: ['github.com', 'gitlab.com']
            }
        };

        // Global API call function
        async function apiCall(url, options = {}) {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
        }

        // Load repositories based on selected app
        async function loadRepositoriesForApp() {
            const appId = document.getElementById('applicationId').value;
            const gitEndpoint = document.getElementById('gitEndpoint').value;
            const repositorySelect = document.getElementById('repositorySelect');
            const branchSelect = document.getElementById('branch');
            
            if (!appId) {
                repositorySelect.innerHTML = '<option value="">First select an Application ID</option>';
                repositorySelect.disabled = true;
                branchSelect.innerHTML = '<option value="">First select a repository</option>';
                branchSelect.disabled = true;
                return;
            }
            
            repositorySelect.innerHTML = '<option value="">Loading repositories...</option>';
            repositorySelect.disabled = true;
            
            try {
                const appConfig = APP_CONFIG[appId];
                const response = await apiCall(`${API_BASE}/git/search-repositories`, {
                    method: 'POST',
                    body: JSON.stringify({
                        keywords: appConfig.keywords,
                        git_endpoint: gitEndpoint,
                        limit: 20
                    })
                });
                
                const data = await response.json();
                
                repositorySelect.innerHTML = '<option value="">Select a repository</option>';
                
                if (data.success && data.repositories && data.repositories.length > 0) {
                    data.repositories.forEach(repo => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(repo);
                        option.textContent = `${repo.name} (${repo.owner}) - ⭐ ${repo.stars || 0}`;
                        repositorySelect.appendChild(option);
                    });
                    repositorySelect.disabled = false;
                    showAlert(`Found ${data.repositories.length} repositories`, 'success');
                } else {
                    repositorySelect.innerHTML = '<option value="">No repositories found</option>';
                    showAlert('No repositories found', 'warning');
                }
                
            } catch (error) {
                console.error('Error loading repositories:', error);
                repositorySelect.innerHTML = '<option value="">Error loading repositories</option>';
                showAlert(`Failed to load repositories: ${error.message}`, 'danger');
            }
        }

        // Load branches for selected repository
        async function loadBranchesForRepo() {
            const repositorySelect = document.getElementById('repositorySelect');
            const branchSelect = document.getElementById('branch');
            const repositoryUrlInput = document.getElementById('repositoryUrl');
            const gitEndpoint = document.getElementById('gitEndpoint').value;
            
            if (!repositorySelect.value) {
                branchSelect.innerHTML = '<option value="">First select a repository</option>';
                branchSelect.disabled = true;
                repositoryUrlInput.value = '';
                return;
            }
            
            try {
                const repoData = JSON.parse(repositorySelect.value);
                const repositoryUrl = `https://${gitEndpoint}/${repoData.owner}/${repoData.name}`;
                repositoryUrlInput.value = repositoryUrl;
                
                const response = await apiCall(`${API_BASE}/git/list-branches`, {
                    method: 'POST',
                    body: JSON.stringify({
                        repository_url: repositoryUrl,
                        git_endpoint: gitEndpoint,
                        owner: repoData.owner,
                        name: repoData.name
                    })
                });
                
                const data = await response.json();
                
                branchSelect.innerHTML = '<option value="">Select a branch</option>';
                
                if (data.branches && data.branches.length > 0) {
                    data.branches.forEach(branch => {
                        const option = document.createElement('option');
                        option.value = branch.name;
                        option.textContent = `${branch.name}${branch.is_default ? ' (default)' : ''}`;
                        branchSelect.appendChild(option);
                    });
                    branchSelect.disabled = false;
                    
                    // Auto-select default branch
                    const defaultBranch = data.branches.find(b => b.is_default);
                    if (defaultBranch) {
                        branchSelect.value = defaultBranch.name;
                    }
                }
                
            } catch (error) {
                console.error('Error loading branches:', error);
                showAlert(`Failed to load branches: ${error.message}`, 'danger');
            }
        }

        // Reset repository selection
        function resetRepositorySelection() {
            const repositorySelect = document.getElementById('repositorySelect');
            const branchSelect = document.getElementById('branch');
            const repositoryUrlInput = document.getElementById('repositoryUrl');
            
            repositorySelect.innerHTML = '<option value="">First select an Application ID</option>';
            repositorySelect.disabled = true;
            branchSelect.innerHTML = '<option value="">First select a repository</option>';
            branchSelect.disabled = true;
            repositoryUrlInput.value = '';
        }

        // Start scan
        async function startScan() {
            const applicationId = document.getElementById('applicationId').value;
            const repositoryUrl = document.getElementById('repositoryUrl').value;
            const branch = document.getElementById('branch').value;
            const githubToken = document.getElementById('githubToken').value;
            
            if (!applicationId || !repositoryUrl || !branch) {
                showAlert('Please fill in all required fields', 'warning');
                return;
            }
            
            const runScanBtn = document.getElementById('runScanBtn');
            runScanBtn.disabled = true;
            runScanBtn.innerHTML = '<span class="loading-indicator me-2"></span>Starting scan...';
            
            try {
                const response = await apiCall(`${API_BASE}/scan`, {
                    method: 'POST',
                    body: JSON.stringify({
                        repository_url: repositoryUrl,
                        branch: branch,
                        github_token: githubToken || null,
                        threshold: 70,
                        app_id: applicationId
                    })
                });
                
                const data = await response.json();
                currentScanId = data.scan_id;
                
                showAlert('Scan started successfully!', 'success');
                
                // Show progress section
                document.getElementById('progressSection').classList.remove('hidden');
                document.getElementById('reportSection').classList.add('hidden');
                
                // Start polling for progress
                pollProgress();
                
            } catch (error) {
                console.error('Error starting scan:', error);
                showAlert(`Failed to start scan: ${error.message}`, 'danger');
                resetScanButton();
            }
        }

        // Poll scan progress
        async function pollProgress() {
            if (!currentScanId) return;
            
            try {
                const response = await apiCall(`${API_BASE}/scan/${currentScanId}`);
                const result = await response.json();
                
                const progressBar = document.getElementById('progressBar');
                const statusText = document.getElementById('statusText');
                const stepDetails = document.getElementById('stepDetails');
                const progressPercent = document.getElementById('progressPercent');
                
                const progress = result.progress_percentage || 0;
                progressBar.style.width = `${progress}%`;
                progressPercent.textContent = `${progress}%`;
                
                statusText.textContent = result.status.toUpperCase();
                stepDetails.textContent = result.current_step || 'Processing...';
                
                if (result.status === 'completed') {
                    showAlert('Scan completed successfully!', 'success');
                    await loadResults();
                } else if (result.status === 'failed') {
                    showAlert(`Scan failed: ${result.errors?.[0] || 'Unknown error'}`, 'danger');
                    resetScanButton();
                } else {
                    setTimeout(pollProgress, 2000);
                }
            } catch (error) {
                console.error('Error polling progress:', error);
                setTimeout(pollProgress, 5000);
            }
        }

        // Load scan results
        async function loadResults() {
            if (!currentScanId) return;

            try {
                const response = await apiCall(`${API_BASE}/scan/${currentScanId}/results`);
                const data = await response.json();
                
                scanResults = data;
                displayReport(data);
                resetScanButton();
                
            } catch (error) {
                console.error('Error loading results:', error);
                showAlert(`Failed to load results: ${error.message}`, 'danger');
                resetScanButton();
            }
        }

        // Display the complete report
        function displayReport(data) {
            // Show report section
            document.getElementById('progressSection').classList.add('hidden');
            document.getElementById('reportSection').classList.remove('hidden');
            
            // Display metrics
            displayMetrics(data);
            
            // Display security gates
            displaySecurityGates(data);
        }

        // Display metrics grid
        function displayMetrics(data) {
            const metricsGrid = document.getElementById('metricsGrid');
            
            const overallScore = data.overall_score || 0;
            const totalGates = data.total_gates || 0;
            const passedGates = data.passed_gates || 0;
            const failedGates = data.failed_gates || 0;
            const warningGates = data.warning_gates || 0;
            
            metricsGrid.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value" style="color: ${overallScore >= 80 ? '#28a745' : overallScore >= 60 ? '#ffc107' : '#dc3545'}">${Math.round(overallScore)}%</div>
                    <div class="metric-label">Overall Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #17a2b8">${totalGates}</div>
                    <div class="metric-label">Total Gates</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #28a745">${passedGates}</div>
                    <div class="metric-label">Passed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #dc3545">${failedGates}</div>
                    <div class="metric-label">Failed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: #ffc107">${warningGates}</div>
                    <div class="metric-label">Warnings</div>
                </div>
            `;
        }

        // Display security gates
        function displaySecurityGates(data) {
            const gatesContainer = document.getElementById('gatesContainer');
            const gateResults = data.gate_results || [];
            
            if (gateResults.length === 0) {
                gatesContainer.innerHTML = `
                    <div class="alert alert-info">
                        <h4>No Gate Results Available</h4>
                        <p>The scan completed but no detailed gate analysis is available.</p>
                    </div>
                `;
                return;
            }

            gatesContainer.innerHTML = gateResults.map((gate, index) => createGateCard(gate, index + 1)).join('');
        }

        // Create individual gate card
        function createGateCard(gate, gateNumber) {
            const status = gate.status || 'UNKNOWN';
            const statusClass = `status-${status.toLowerCase().replace('_', '-')}`;
            
            const matches = gate.matches || [];
            const matchesHtml = matches.length > 0 ? `
                <div class="mt-3">
                    <h6>Code Matches (${matches.length})</h6>
                    ${matches.slice(0, 5).map(match => `
                        <div class="border rounded p-2 mb-2 small">
                            <strong>${match.file || 'Unknown file'}</strong> - Line ${match.line || 'Unknown'}<br>
                            <code>${match.code || match.content || 'No code available'}</code>
                        </div>
                    `).join('')}
                    ${matches.length > 5 ? `<small class="text-muted">... and ${matches.length - 5} more matches</small>` : ''}
                </div>
            ` : '<div class="alert alert-success mt-3">No issues found for this gate</div>';
            
            return `
                <div class="gate-card">
                    <div class="gate-header">
                        <div>
                            <h4 class="mb-1">
                                Gate ${gateNumber}: ${gate.name || 'Unknown Gate'}
                                <span class="status-badge ${statusClass} ms-2">${status}</span>
                            </h4>
                            <p class="text-muted mb-0">${gate.description || 'No description available'}</p>
                        </div>
                        <div class="text-end">
                            <div class="h5 mb-0">${(gate.score || 0).toFixed(1)}%</div>
                            <small class="text-muted">Score</small>
                        </div>
                    </div>
                    
                    <div class="gate-body">
                        <div class="row">
                            <div class="col-md-3">
                                <strong>Category:</strong><br>
                                <span class="text-muted">${gate.category || 'General'}</span>
                            </div>
                            <div class="col-md-3">
                                <strong>Matches:</strong><br>
                                <span class="text-muted">${matches.length}</span>
                            </div>
                            <div class="col-md-3">
                                <strong>Files:</strong><br>
                                <span class="text-muted">${gate.files_with_matches || 0}</span>
                            </div>
                            <div class="col-md-3">
                                <strong>Confidence:</strong><br>
                                <span class="text-muted">${(gate.confidence || 0).toFixed(1)}%</span>
                            </div>
                        </div>
                        
                        ${matchesHtml}
                        
                        <div class="mt-3 p-3 bg-light rounded">
                            <h6>JIRA Integration</h6>
                            <div class="row">
                                <div class="col-md-6 mb-2">
                                    <label class="form-label">Comments:</label>
                                    <textarea class="form-control" id="comment-${gateNumber}" rows="2" 
                                              placeholder="Add your analysis and comments..."></textarea>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">JIRA Ticket ID:</label>
                                    <input type="text" class="form-control mb-2" id="jira-id-${gateNumber}" 
                                           placeholder="PROJ-123">
                                    <button class="btn btn-primary btn-sm" onclick="uploadToJira(${gateNumber})">
                                        <i class="fas fa-upload me-1"></i>Upload to JIRA
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Upload gate report to JIRA
        async function uploadToJira(gateNumber) {
            const comment = document.getElementById(`comment-${gateNumber}`).value;
            const jiraId = document.getElementById(`jira-id-${gateNumber}`).value;
            
            if (!jiraId.trim()) {
                showAlert('Please enter a JIRA ticket ID', 'warning');
                return;
            }
            
            if (!currentScanId) {
                showAlert('No scan results available for upload', 'warning');
                return;
            }
            
            const uploadBtn = event.target;
            const originalText = uploadBtn.innerHTML;
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="loading-indicator me-1"></span>Uploading...';
            
            try {
                const pdfResponse = await apiCall(`${API_BASE}/scan/${currentScanId}/generate-jira-pdfs`, {
                    method: 'POST',
                    body: JSON.stringify({
                        gate_numbers: [gateNumber],
                        comments: {
                            [`gate_${gateNumber}`]: comment
                        },
                        jira_ticket_id: jiraId
                    })
                });
                
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                showAlert(`Successfully uploaded Gate ${gateNumber} PDF to JIRA ticket ${jiraId}`, 'success');
                
                uploadBtn.innerHTML = '<i class="fas fa-check me-1"></i>Uploaded!';
                uploadBtn.classList.remove('btn-primary');
                uploadBtn.classList.add('btn-success');
                
                setTimeout(() => {
                    uploadBtn.innerHTML = originalText;
                    uploadBtn.classList.remove('btn-success');
                    uploadBtn.classList.add('btn-primary');
                    uploadBtn.disabled = false;
                }, 3000);
                
            } catch (error) {
                console.error('Error uploading to JIRA:', error);
                showAlert(`Failed to upload to JIRA: ${error.message}`, 'danger');
                
                uploadBtn.innerHTML = originalText;
                uploadBtn.disabled = false;
            }
        }

        // Export full report
        async function exportFullReport() {
            if (!currentScanId) {
                showAlert('No scan results available for export', 'warning');
                return;
            }
            
            try {
                const response = await apiCall(`${API_BASE}/scan/${currentScanId}/report/html`);
                const htmlContent = await response.text();
                
                const blob = new Blob([htmlContent], { type: 'text/html' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `codegates_report_${currentScanId.substr(0, 8)}.html`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('Report exported successfully!', 'success');
            } catch (error) {
                showAlert(`Failed to export report: ${error.message}`, 'danger');
            }
        }

        // Generate PDFs
        async function generatePDFs() {
            if (!currentScanId) {
                showAlert('No scan results available for PDF generation', 'warning');
                return;
            }
            
            try {
                const response = await apiCall(`${API_BASE}/scan/${currentScanId}/pdfs`);
                const data = await response.json();
                
                showAlert(`Generated ${data.total_files} PDF files successfully!`, 'success');
            } catch (error) {
                showAlert(`Failed to generate PDFs: ${error.message}`, 'danger');
            }
        }

        // Reset form
        function resetForm() {
            document.getElementById('scanForm').reset();
            resetRepositorySelection();
            document.getElementById('progressSection').classList.add('hidden');
            document.getElementById('reportSection').classList.add('hidden');
            currentScanId = null;
            scanResults = null;
        }

        // Reset scan button
        function resetScanButton() {
            const runScanBtn = document.getElementById('runScanBtn');
            runScanBtn.disabled = false;
            runScanBtn.innerHTML = '<i class="fas fa-play me-2"></i>Run Security Scan';
        }

        // Show alert notification
        function showAlert(message, type = 'info') {
            const toastContainer = document.getElementById('toastContainer');
            const toastId = 'toast-' + Date.now();
            
            const alertColors = {
                'success': '#28a745',
                'danger': '#dc3545',
                'warning': '#ffc107',
                'info': '#17a2b8'
            };
            
            const toast = document.createElement('div');
            toast.id = toastId;
            toast.className = `alert alert-${type}`;
            toast.style.cssText = `
                margin-bottom: 0.5rem;
                border-left: 4px solid ${alertColors[type]};
                min-width: 300px;
                cursor: pointer;
            `;
            
            toast.innerHTML = `
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" onclick="document.getElementById('${toastId}').remove()"></button>
            `;
            
            toast.onclick = () => toast.remove();
            toastContainer.appendChild(toast);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                if (document.getElementById(toastId)) {
                    document.getElementById(toastId).remove();
                }
            }, 5000);
        }

        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            console.log('CodeGates Security Scanner initialized');
            showAlert('Welcome to CodeGates Security Scanner!', 'info');
        });
    ''' + '''</script>
</body>
</html>'''
    
    return html_content 