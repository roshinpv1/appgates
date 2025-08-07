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

class DirectStreamlitUI:
    """
    Direct Streamlit UI integration without separate process
    Renders Streamlit-like components directly in FastAPI
    """
    
    def __init__(self):
        self.session_data = {}
        
    def render_main_page(self, api_base: str = "http://localhost:8000/api/v1") -> str:
        """Render the main CodeGates UI page"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🔍 CodeGates Scanner</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            
            <!-- Bootstrap CSS -->
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            
            <style>
                :root {{
                    --primary-color: #dc3545;
                    --primary-light: #f8d7da;
                    --text-color: #495057;
                    --border-color: #ced4da;
                    --bg-light: #f8f9fa;
                    --white: #ffffff;
                    --success-color: #28a745;
                    --warning-color: #ffc107;
                    --info-color: #17a2b8;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    background-color: #f5f5f5;
                    color: var(--text-color);
                    margin: 0;
                    padding: 20px;
                }}
                
                .main-container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: var(--white);
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                
                .header h1 {{
                    margin: 0;
                    font-size: 2rem;
                    font-weight: 600;
                }}
                
                .header p {{
                    margin: 8px 0 0 0;
                    opacity: 0.9;
                    font-size: 1.1rem;
                }}
                
                .content {{
                    padding: 40px;
                }}
                
                /* Form Styling */
                .form-group {{
                    margin-bottom: 25px;
                }}
                
                .form-label {{
                    font-weight: 600;
                    color: #343a40;
                    margin-bottom: 8px;
                    display: block;
                }}
                
                .form-control, .form-select {{
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    padding: 12px 16px;
                    font-size: 1rem;
                    transition: border-color 0.2s ease;
                    width: 100%;
                }}
                
                .form-control:focus, .form-select:focus {{
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1);
                    outline: none;
                }}
                
                .form-control:disabled, .form-select:disabled {{
                    background-color: #e9ecef;
                    opacity: 0.6;
                }}
                
                .form-control::placeholder {{
                    color: #6c757d;
                }}
                
                .form-text {{
                    font-size: 0.875rem;
                    color: #6c757d;
                    margin-top: 5px;
                }}
                
                .loading-indicator {{
                    display: none;
                    align-items: center;
                    gap: 8px;
                    color: var(--primary-color);
                    font-size: 0.875rem;
                }}
                
                .loading-indicator.show {{
                    display: flex;
                }}
                
                .spinner {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid #e9ecef;
                    border-radius: 50%;
                    border-top-color: var(--primary-color);
                    animation: spin 1s linear infinite;
                }}
                
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
                
                /* Button Styling */
                .btn {{
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-weight: 600;
                    transition: all 0.2s ease;
                    border: none;
                    cursor: pointer;
                }}
                
                .btn-primary {{
                    background: var(--primary-color);
                    color: white;
                }}
                
                .btn-primary:hover {{
                    background: #c82333;
                    transform: translateY(-1px);
                }}
                
                .btn-success {{
                    background: var(--success-color);
                    color: white;
                }}
                
                .btn-warning {{
                    background: var(--warning-color);
                    color: white;
                }}
                
                .btn-info {{
                    background: var(--info-color);
                    color: white;
                }}
                
                .btn-sm {{
                    padding: 8px 16px;
                    font-size: 0.875rem;
                }}
                
                .btn-primary:disabled {{
                    background: #6c757d;
                    cursor: not-allowed;
                    transform: none;
                }}
                
                .scan-btn {{
                    background: var(--primary-color);
                    color: white;
                    font-size: 1.1rem;
                    padding: 15px 30px;
                    border-radius: 8px;
                    width: 100%;
                    margin-top: 20px;
                }}
                
                /* Progress Section */
                .progress-section {{
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 25px;
                    margin-top: 30px;
                    display: none;
                }}
                
                .progress {{
                    height: 8px;
                    border-radius: 4px;
                    background: #e9ecef;
                    margin: 15px 0;
                }}
                
                .progress-bar {{
                    background: var(--primary-color);
                    border-radius: 4px;
                    transition: width 0.3s ease;
                }}
                
                /* Report Section */
                .report-section {{
                    margin-top: 30px;
                    display: none;
                }}
                
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                
                .metric-card {{
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                }}
                
                .metric-value {{
                    font-size: 2rem;
                    font-weight: 700;
                    color: var(--primary-color);
                }}
                
                .metric-label {{
                    color: #6c757d;
                    font-size: 0.9rem;
                    margin-top: 5px;
                }}
                
                /* Gate Card Styling */
                .gate-card {{
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    overflow: hidden;
                }}
                
                .gate-header {{
                    background: #f8f9fa;
                    padding: 15px 20px;
                    border-bottom: 1px solid #e9ecef;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                .gate-title {{
                    font-weight: 600;
                    color: #343a40;
                    margin: 0;
                }}
                
                .gate-status {{
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                }}
                
                .status-pass {{
                    background: #d4edda;
                    color: #155724;
                }}
                
                .status-fail {{
                    background: #f5c6cb;
                    color: #721c24;
                }}
                
                .status-warning {{
                    background: #fff3cd;
                    color: #856404;
                }}
                
                .status-na {{
                    background: #e2e3e5;
                    color: #383d41;
                }}
                
                .gate-body {{
                    padding: 20px;
                }}
                
                .gate-info {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                
                .gate-info-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #f8f9fa;
                }}
                
                .gate-info-label {{
                    font-weight: 500;
                    color: #6c757d;
                }}
                
                .gate-info-value {{
                    font-weight: 600;
                    color: #343a40;
                }}
                
                .gate-actions {{
                    background: #f8f9fa;
                    padding: 15px 20px;
                    border-top: 1px solid #e9ecef;
                }}
                
                .jira-section {{
                    display: grid;
                    grid-template-columns: 1fr auto;
                    gap: 15px;
                    align-items: end;
                }}
                
                .comment-section {{
                    margin-bottom: 15px;
                }}
                
                /* Alert Styling */
                .alert-toast {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    min-width: 350px;
                    border-radius: 8px;
                    border: none;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
                }}
                
                /* Responsive */
                @media (max-width: 768px) {{
                    body {{
                        padding: 10px;
                    }}
                    
                    .content {{
                        padding: 20px;
                    }}
                    
                    .header {{
                        padding: 20px;
                    }}
                    
                    .header h1 {{
                        font-size: 1.5rem;
                    }}
                    
                    .jira-section {{
                        grid-template-columns: 1fr;
                        gap: 10px;
                    }}
                    
                    .gate-info {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="main-container">
                
                <!-- Header -->
                <div class="header">
                    <h1><i class="fas fa-shield-alt me-2"></i>CodeGates Scanner</h1>
                    <p>Enterprise code security and compliance validation</p>
                </div>
                
                <div class="content">
                    
                    <!-- Scan Configuration Form -->
                    <div id="scanForm">
                        <h3><i class="fas fa-cogs me-2"></i>Scan Configuration</h3>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="applicationId" class="form-label">Application ID</label>
                                    <select class="form-select" id="applicationId" onchange="loadRepositoriesForApp()">
                                        <option value="">Select Application ID...</option>
                                        <option value="FRONTEND_REACT">Frontend React Apps</option>
                                        <option value="BACKEND_API">Backend API Services</option>
                                        <option value="MOBILE_APPS">Mobile Applications</option>
                                        <option value="DATA_SCIENCE">Data Science & Analytics</option>
                                        <option value="DEVOPS_TOOLS">DevOps & Infrastructure</option>
                                        <option value="ENTERPRISE_WEB">Enterprise Web Applications</option>
                                        <option value="MICROSERVICES">Microservices Architecture</option>
                                        <option value="CLOUD_NATIVE">Cloud Native Applications</option>
                                        <option value="SECURITY_TOOLS">Security & Compliance Tools</option>
                                        <option value="AI_ML_PLATFORMS">AI/ML Platforms</option>
                                    </select>
                                    <div class="form-text">Select the application category to scan</div>
                                    <div class="loading-indicator" id="appLoadingIndicator">
                                        <div class="spinner"></div>
                                        <span>Loading repositories...</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="gitEndpoint" class="form-label">Git Endpoint</label>
                                    <select class="form-select" id="gitEndpoint" onchange="resetRepositorySelection()">
                                        <option value="github.com">GitHub.com (Public)</option>
                                        <option value="github.abc.com">GitHub Enterprise (github.abc.com)</option>
                                    </select>
                                    <div class="form-text">Select your Git platform endpoint</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="repositorySelect" class="form-label">Repository Selection</label>
                                    <select class="form-select" id="repositorySelect" onchange="loadBranchesForRepo()" disabled>
                                        <option value="">Select Application ID first...</option>
                                    </select>
                                    <div class="form-text">Choose repository from search results</div>
                                    <div class="loading-indicator" id="repoLoadingIndicator">
                                        <div class="spinner"></div>
                                        <span>Loading branches...</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="branch" class="form-label">Branch Selection</label>
                                    <select class="form-select" id="branch" disabled>
                                        <option value="">Select repository first...</option>
                                    </select>
                                    <div class="form-text">Available branches for selected repository</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="repositoryUrl" class="form-label">Repository URL</label>
                                    <input type="text" class="form-control" id="repositoryUrl" readonly
                                           placeholder="URL will be auto-filled when repository is selected">
                                    <div class="form-text">Complete repository URL (auto-populated)</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label for="githubToken" class="form-label">Git Token</label>
                                    <input type="password" class="form-control" id="githubToken" 
                                           placeholder="Enter your Git access token (GitHub, GitLab, Bitbucket, etc.)">
                                    <div class="form-text">Required for private repositories and to avoid rate limits across all Git platforms</div>
                                </div>
                            </div>
                        </div>
                        
                        <button class="scan-btn" onclick="startScan()" id="scanBtn" disabled>
                            <i class="fas fa-rocket me-2"></i>Run Security Scan
                        </button>
                    </div>
                    
                    <!-- Progress Section -->
                    <div class="progress-section" id="progressSection">
                        <h5><i class="fas fa-clock me-2"></i>Scan Progress</h5>
                        <div class="progress">
                            <div class="progress-bar" id="progressBar" style="width: 0%"></div>
                        </div>
                        <div class="text-center">
                            <div><strong>Status:</strong> <span id="statusText">Initializing...</span></div>
                            <div class="text-muted" id="stepDetails">Preparing scan...</div>
                        </div>
                    </div>
                    
                    <!-- Report Section -->
                    <div class="report-section" id="reportSection">
                        
                        <!-- Report Header -->
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h3><i class="fas fa-shield-alt me-2"></i>Security Scan Report</h3>
                            <div>
                                <button class="btn btn-primary btn-sm me-2" onclick="exportFullReport()">
                                    <i class="fas fa-download me-1"></i>Export Full Report
                                </button>
                                <button class="btn btn-info btn-sm" onclick="refreshReport()">
                                    <i class="fas fa-sync me-1"></i>Refresh
                                </button>
                            </div>
                        </div>
                        
                        <!-- Metrics Summary -->
                        <div class="metrics-grid" id="metricsGrid">
                            <!-- Metrics will be populated here -->
                        </div>
                        
                        <!-- Security Gates Results -->
                        <h4><i class="fas fa-list me-2"></i>Security Gates Analysis</h4>
                        <div id="gatesContainer">
                            <!-- Gate cards will be populated here -->
                        </div>
                        
                    </div>
                </div>
            </div>
            
            <!-- Bootstrap JS -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            
            <script>
                const API_BASE = "{api_base}";
                let currentScanId = null;
                let scanResults = null;
                let currentAppData = null;
                
                // Application ID configuration with enterprise Git endpoints
                const APP_CONFIG = {{
                    "FRONTEND_REACT": {{
                        "name": "Frontend React Applications",
                        "description": "React, Next.js, and modern frontend frameworks",
                        "keywords": ["react", "nextjs", "frontend", "ui", "components", "web"],
                        "git_endpoints": ["github.com", "gitlab.com", "bitbucket.org"]
                    }},
                    "BACKEND_API": {{
                        "name": "Backend API Services",
                        "description": "REST APIs, microservices, and backend frameworks",
                        "keywords": ["api", "backend", "microservice", "rest", "graphql", "server"],
                        "git_endpoints": ["github.com", "gitlab.com", "bitbucket.org", "dev.azure.com"]
                    }},
                    "MOBILE_APPS": {{
                        "name": "Mobile Applications",
                        "description": "Native and cross-platform mobile development",
                        "keywords": ["mobile", "android", "ios", "react-native", "flutter", "xamarin"],
                        "git_endpoints": ["github.com", "gitlab.com"]
                    }},
                    "DATA_SCIENCE": {{
                        "name": "Data Science & Analytics",
                        "description": "Machine learning, data analysis, and AI projects",
                        "keywords": ["machine-learning", "data-science", "analytics", "ai", "ml", "python"],
                        "git_endpoints": ["github.com", "gitlab.com", "bitbucket.org"]
                    }},
                    "DEVOPS_TOOLS": {{
                        "name": "DevOps & Infrastructure",
                        "description": "Container orchestration, CI/CD, and infrastructure tools",
                        "keywords": ["devops", "kubernetes", "docker", "terraform", "ansible", "ci-cd"],
                        "git_endpoints": ["github.com", "gitlab.com", "bitbucket.org", "dev.azure.com"]
                    }},
                    "ENTERPRISE_WEB": {{
                        "name": "Enterprise Web Applications",
                        "description": "Large-scale web applications and enterprise software",
                        "keywords": ["enterprise", "web", "application", "portal", "dashboard", "admin"],
                        "git_endpoints": ["gitlab.com", "bitbucket.org", "dev.azure.com"]
                    }},
                    "MICROSERVICES": {{
                        "name": "Microservices Architecture",
                        "description": "Distributed systems and microservices implementations",
                        "keywords": ["microservices", "distributed", "service-mesh", "api-gateway", "messaging"],
                        "git_endpoints": ["github.com", "gitlab.com", "dev.azure.com"]
                    }},
                    "CLOUD_NATIVE": {{
                        "name": "Cloud Native Applications",
                        "description": "Cloud-first applications and serverless functions",
                        "keywords": ["cloud", "serverless", "lambda", "azure-functions", "gcp", "aws"],
                        "git_endpoints": ["github.com", "gitlab.com", "bitbucket.org"]
                    }},
                    "SECURITY_TOOLS": {{
                        "name": "Security & Compliance Tools",
                        "description": "Security scanning, compliance, and monitoring tools",
                        "keywords": ["security", "compliance", "scanning", "monitoring", "vulnerability", "audit"],
                        "git_endpoints": ["github.com", "gitlab.com"]
                    }},
                    "AI_ML_PLATFORMS": {{
                        "name": "AI/ML Platforms",
                        "description": "Artificial Intelligence and Machine Learning platforms",
                        "keywords": ["ai", "ml", "platform", "tensorflow", "pytorch", "model", "training"],
                        "git_endpoints": ["github.com", "gitlab.com", "bitbucket.org"]
                    }}
                }};
                
                // Enhanced API call function
                async function apiCall(url, options = {{}}) {{
                    try {{
                        const response = await fetch(url, {{
                            timeout: 30000,
                            ...options
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`API Error: ${{response.status}} - ${{response.statusText}}`);
                        }}
                        
                        return response;
                    }} catch (error) {{
                        console.error('API call failed:', error);
                        throw error;
                    }}
                }}
                
                // Load repositories for selected APP ID
                async function loadRepositoriesForApp() {{
                    const appId = document.getElementById('applicationId').value;
                    const gitEndpoint = document.getElementById('gitEndpoint').value;
                    const repoSelect = document.getElementById('repositorySelect');
                    const branchSelect = document.getElementById('branch');
                    const urlInput = document.getElementById('repositoryUrl');
                    const scanBtn = document.getElementById('scanBtn');
                    const loadingIndicator = document.getElementById('appLoadingIndicator');
                    
                    // Reset dependent fields
                    repoSelect.innerHTML = '<option value="">Loading repositories...</option>';
                    repoSelect.disabled = true;
                    branchSelect.innerHTML = '<option value="">Select repository first...</option>';
                    branchSelect.disabled = true;
                    urlInput.value = '';
                    scanBtn.disabled = true;
                    
                    if (!appId) {{
                        repoSelect.innerHTML = '<option value="">Select Application ID first...</option>';
                        return;
                    }}
                    
                    const appConfig = APP_CONFIG[appId];
                    if (!appConfig) {{
                        showAlert('Invalid Application ID selected', 'warning');
                        return;
                    }}
                    
                    currentAppData = appConfig;
                    
                    try {{
                        loadingIndicator.classList.add('show');
                        
                        // Search repositories on the selected Git endpoint
                        try {{
                            const response = await apiCall(`${{API_BASE}}/git/search-repositories`, {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json'
                                }},
                                body: JSON.stringify({{
                                    keywords: appConfig.keywords,
                                    git_endpoint: gitEndpoint,
                                    limit: 20
                                }})
                            }});
                            
                            const data = await response.json();
                            const repositories = data.repositories || [];
                            
                            // Populate repository dropdown
                            repoSelect.innerHTML = '<option value="">Select a repository...</option>';
                            
                            if (repositories.length === 0) {{
                                repoSelect.innerHTML = '<option value="">No repositories found for this APP ID on selected endpoint</option>';
                                showAlert(`No repositories found for ${{appConfig.name}} on ${{gitEndpoint}}`, 'info');
                            }} else {{
                                repositories.forEach(repo => {{
                                    const option = document.createElement('option');
                                    option.value = JSON.stringify(repo);
                                    option.textContent = `${{repo.owner}}/${{repo.name}} - ${{repo.stars || 0}} stars`;
                                    repoSelect.appendChild(option);
                                }});
                                
                                repoSelect.disabled = false;
                                showAlert(`Found ${{repositories.length}} repositories for ${{appConfig.name}} on ${{gitEndpoint}}`, 'success');
                            }}
                            
                        }} catch (error) {{
                            console.warn(`Failed to search ${{gitEndpoint}}:`, error);
                            repoSelect.innerHTML = '<option value="">Error loading repositories from selected endpoint</option>';
                            showAlert(`Failed to search repositories on ${{gitEndpoint}}: ${{error.message}}`, 'warning');
                        }}
                        
                    }} catch (error) {{
                        showAlert(`Failed to load repositories: ${{error.message}}`, 'danger');
                        repoSelect.innerHTML = '<option value="">Error loading repositories</option>';
                    }} finally {{
                        loadingIndicator.classList.remove('show');
                    }}
                }}
                
                // Reset repository selection when Git endpoint changes
                function resetRepositorySelection() {{
                    const repoSelect = document.getElementById('repositorySelect');
                    const branchSelect = document.getElementById('branch');
                    const urlInput = document.getElementById('repositoryUrl');
                    const scanBtn = document.getElementById('scanBtn');
                    const appId = document.getElementById('applicationId').value;
                    
                    // Reset dependent fields
                    repoSelect.innerHTML = '<option value="">Select Application ID first...</option>';
                    repoSelect.disabled = true;
                    branchSelect.innerHTML = '<option value="">Select repository first...</option>';
                    branchSelect.disabled = true;
                    urlInput.value = '';
                    scanBtn.disabled = true;
                    
                    // If an app ID is selected, reload repositories for the new endpoint
                    if (appId) {{
                        loadRepositoriesForApp();
                    }}
                }}
                
                // Load branches for selected repository
                async function loadBranchesForRepo() {{
                    const repoSelect = document.getElementById('repositorySelect');
                    const gitEndpoint = document.getElementById('gitEndpoint').value;
                    const branchSelect = document.getElementById('branch');
                    const urlInput = document.getElementById('repositoryUrl');
                    const scanBtn = document.getElementById('scanBtn');
                    const loadingIndicator = document.getElementById('repoLoadingIndicator');
                    
                    // Reset dependent fields
                    branchSelect.innerHTML = '<option value="">Loading branches...</option>';
                    branchSelect.disabled = true;
                    urlInput.value = '';
                    scanBtn.disabled = true;
                    
                    if (!repoSelect.value) {{
                        branchSelect.innerHTML = '<option value="">Select repository first...</option>';
                        return;
                    }}
                    
                    try {{
                        const repoData = JSON.parse(repoSelect.value);
                        loadingIndicator.classList.add('show');
                        
                        // Construct repository URL based on Git endpoint
                        let repositoryUrl;
                        if (gitEndpoint === 'github.com') {{
                            repositoryUrl = repoData.clone_url || repoData.html_url;
                        }} else if (gitEndpoint === 'github.abc.com') {{
                            // For enterprise GitHub, construct the URL
                            repositoryUrl = `https://${{gitEndpoint}}/${{repoData.owner}}/${{repoData.name}}.git`;
                        }} else {{
                            repositoryUrl = repoData.clone_url || repoData.html_url;
                        }}
                        
                        // Set repository URL immediately
                        urlInput.value = repositoryUrl;
                        
                        // Load branches from the repository
                        const response = await apiCall(`${{API_BASE}}/git/list-branches`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                repository_url: repositoryUrl,
                                git_endpoint: gitEndpoint,
                                owner: repoData.owner,
                                name: repoData.name
                            }})
                        }});
                        
                        const data = await response.json();
                        const branches = data.branches || [];
                        
                        // Populate branch dropdown
                        branchSelect.innerHTML = '<option value="">Select a branch...</option>';
                        
                        if (branches.length === 0) {{
                            branchSelect.innerHTML = '<option value="">No branches found</option>';
                            showAlert('No branches found for this repository', 'warning');
                        }} else {{
                            // Add default branches first
                            const defaultBranches = ['main', 'master', 'develop'];
                            const sortedBranches = [];
                            
                            defaultBranches.forEach(defaultBranch => {{
                                const branch = branches.find(b => b.name === defaultBranch);
                                if (branch) {{
                                    sortedBranches.push(branch);
                                }}
                            }});
                            
                            // Add remaining branches
                            branches.forEach(branch => {{
                                if (!defaultBranches.includes(branch.name)) {{
                                    sortedBranches.push(branch);
                                }}
                            }});
                            
                            sortedBranches.forEach(branch => {{
                                const option = document.createElement('option');
                                option.value = branch.name;
                                option.textContent = `${{branch.name}} ${{branch.is_default ? '(default)' : ''}}`;
                                branchSelect.appendChild(option);
                            }});
                            
                            // Auto-select default branch
                            const defaultBranch = branches.find(b => b.is_default);
                            if (defaultBranch) {{
                                branchSelect.value = defaultBranch.name;
                            }}
                            
                            branchSelect.disabled = false;
                            scanBtn.disabled = false;
                            showAlert(`Loaded ${{branches.length}} branches from ${{gitEndpoint}}`, 'success');
                        }}
                        
                    }} catch (error) {{
                        showAlert(`Failed to load branches: ${{error.message}}`, 'danger');
                        branchSelect.innerHTML = '<option value="">Error loading branches</option>';
                    }} finally {{
                        loadingIndicator.classList.remove('show');
                    }}
                }}
                
                // Start scan
                async function startScan() {{
                    const applicationId = document.getElementById('applicationId').value;
                    const repositoryUrl = document.getElementById('repositoryUrl').value.trim();
                    const branch = document.getElementById('branch').value;
                    const githubToken = document.getElementById('githubToken').value.trim();
                    
                    // Validation
                    if (!applicationId) {{
                        showAlert('Please select an Application ID', 'warning');
                        return;
                    }}
                    
                    if (!repositoryUrl) {{
                        showAlert('Please select a repository', 'warning');
                        return;
                    }}
                    
                    if (!branch) {{
                        showAlert('Please select a branch', 'warning');
                        return;
                    }}
                    
                    const scanBtn = document.getElementById('scanBtn');
                    const progressSection = document.getElementById('progressSection');
                    
                    try {{
                        scanBtn.disabled = true;
                        scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting Security Scan...';
                        
                        const response = await apiCall(`${{API_BASE}}/scan`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                repository_url: repositoryUrl,
                                branch: branch,
                                github_token: githubToken || null,
                                threshold: 70,
                                report_format: 'both',
                                app_id: applicationId
                            }})
                        }});
                        
                        const result = await response.json();
                        currentScanId = result.scan_id;
                        
                        progressSection.style.display = 'block';
                        showAlert(`Security scan started successfully! ID: ${{currentScanId}}`, 'success');
                        
                        pollProgress();
                        
                    }} catch (error) {{
                        showAlert(`Failed to start scan: ${{error.message}}`, 'danger');
                        scanBtn.disabled = false;
                        scanBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Run Security Scan';
                    }}
                }}
                
                // Poll for progress
                async function pollProgress() {{
                    if (!currentScanId) return;
                    
                    try {{
                        const response = await apiCall(`${{API_BASE}}/scan/${{currentScanId}}`);
                        const result = await response.json();
                        
                        const progressBar = document.getElementById('progressBar');
                        const statusText = document.getElementById('statusText');
                        const stepDetails = document.getElementById('stepDetails');
                        
                        const progress = result.progress_percentage || 0;
                        progressBar.style.width = `${{progress}}%`;
                        
                        statusText.textContent = result.status.toUpperCase();
                        stepDetails.textContent = result.current_step || 'Processing...';
                        
                        if (result.status === 'completed') {{
                            progressBar.style.width = '100%';
                            statusText.textContent = 'COMPLETED';
                            stepDetails.textContent = 'Security scan completed successfully';
                            
                            showAlert('Security scan completed successfully!', 'success');
                            await loadResults();
                        }} else if (result.status === 'failed') {{
                            statusText.textContent = 'FAILED';
                            stepDetails.textContent = result.errors?.[0] || 'Scan failed';
                            
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
                
                // Load results
                async function loadResults() {{
                    try {{
                        const response = await apiCall(`${{API_BASE}}/scan/${{currentScanId}}/results`);
                        scanResults = await response.json();
                        displayReport();
                    }} catch (error) {{
                        showAlert(`Failed to load results: ${{error.message}}`, 'danger');
                    }}
                }}
                
                // Display comprehensive report
                function displayReport() {{
                    if (!scanResults) return;
                    
                    const reportSection = document.getElementById('reportSection');
                    reportSection.style.display = 'block';
                    
                    // Display metrics
                    displayMetrics();
                    
                    // Display security gates
                    displaySecurityGates();
                    
                    resetScanButton();
                    
                    // Scroll to report
                    setTimeout(() => {{
                        reportSection.scrollIntoView({{ behavior: 'smooth' }});
                    }}, 300);
                }}
                
                // Display metrics summary
                function displayMetrics() {{
                    const metricsGrid = document.getElementById('metricsGrid');
                    const gateResults = scanResults.gate_results || [];
                    
                    const overallScore = scanResults.overall_score || 0;
                    const totalGates = gateResults.length;
                    const passedGates = gateResults.filter(g => g.status === 'PASS').length;
                    const failedGates = gateResults.filter(g => g.status === 'FAIL').length;
                    const warningGates = gateResults.filter(g => g.status === 'WARNING').length;
                    
                    metricsGrid.innerHTML = `
                        <div class="metric-card">
                            <div class="metric-value" style="color: ${{overallScore >= 70 ? '#28a745' : '#dc3545'}}">${{overallScore.toFixed(1)}}%</div>
                            <div class="metric-label">Overall Score</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${{totalGates}}</div>
                            <div class="metric-label">Total Gates</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" style="color: #28a745">${{passedGates}}</div>
                            <div class="metric-label">Passed</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" style="color: #dc3545">${{failedGates}}</div>
                            <div class="metric-label">Failed</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" style="color: #ffc107">${{warningGates}}</div>
                            <div class="metric-label">Warnings</div>
                        </div>
                    `;
                }}
                
                // Display security gates with interactive features
                function displaySecurityGates() {{
                    const gatesContainer = document.getElementById('gatesContainer');
                    const gateResults = scanResults.gate_results || [];
                    
                    gatesContainer.innerHTML = '';
                    
                    gateResults.forEach((gate, index) => {{
                        const gateCard = createGateCard(gate, index + 1);
                        gatesContainer.appendChild(gateCard);
                    }});
                }}
                
                // Create individual gate card
                function createGateCard(gate, gateNumber) {{
                    const card = document.createElement('div');
                    card.className = 'gate-card';
                    card.id = `gate-${{gateNumber}}`;
                    
                    const statusClass = {{
                        'PASS': 'status-pass',
                        'FAIL': 'status-fail',
                        'WARNING': 'status-warning',
                        'NOT_APPLICABLE': 'status-na'
                    }}[gate.status] || 'status-na';
                    
                    const statusIcon = {{
                        'PASS': 'fas fa-check-circle',
                        'FAIL': 'fas fa-times-circle',
                        'WARNING': 'fas fa-exclamation-triangle',
                        'NOT_APPLICABLE': 'fas fa-minus-circle'
                    }}[gate.status] || 'fas fa-question-circle';
                    
                    card.innerHTML = `
                        <div class="gate-header">
                            <div class="gate-title">
                                <i class="${{statusIcon}} me-2"></i>
                                Gate ${{gateNumber}}: ${{gate.display_name || gate.gate || 'Unknown Gate'}}
                            </div>
                            <span class="gate-status ${{statusClass}}">${{gate.status || 'UNKNOWN'}}</span>
                        </div>
                        
                        <div class="gate-body">
                            <div class="gate-info">
                                <div class="gate-info-item">
                                    <span class="gate-info-label">Category:</span>
                                    <span class="gate-info-value">${{gate.category || 'General'}}</span>
                                </div>
                                <div class="gate-info-item">
                                    <span class="gate-info-label">Score:</span>
                                    <span class="gate-info-value">${{gate.score?.toFixed(1) || 0}}%</span>
                                </div>
                                <div class="gate-info-item">
                                    <span class="gate-info-label">Issues Found:</span>
                                    <span class="gate-info-value">${{gate.matches_found || 0}}</span>
                                </div>
                                <div class="gate-info-item">
                                    <span class="gate-info-label">Description:</span>
                                    <span class="gate-info-value">${{gate.description || 'No description available'}}</span>
                                </div>
                            </div>
                            
                            ${{gate.matches && gate.matches.length > 0 ? `
                            <div class="mt-3">
                                <h6>Issues Details:</h6>
                                <div class="alert alert-light">
                                    ${{gate.matches.map(match => `
                                        <div class="mb-2">
                                            <strong>File:</strong> ${{match.file}}<br>
                                            <strong>Line:</strong> ${{match.line}}<br>
                                            <strong>Code:</strong> <code>${{match.content}}</code>
                                        </div>
                                    `).join('<hr>')}}
                                </div>
                            </div>
                            ` : ''}}
                        </div>
                        
                        <div class="gate-actions">
                            <div class="comment-section">
                                <label class="form-label">Comments:</label>
                                <textarea class="form-control" id="comment-${{gateNumber}}" rows="3" 
                                          placeholder="Add your comments about this security gate..."></textarea>
                            </div>
                            
                            <div class="jira-section">
                                <div>
                                    <label class="form-label">JIRA Ticket ID:</label>
                                    <input type="text" class="form-control" id="jira-id-${{gateNumber}}" 
                                           placeholder="PROJ-123">
                                </div>
                                <button class="btn btn-primary" onclick="uploadToJira(${{gateNumber}})">
                                    <i class="fas fa-upload me-1"></i>Upload to JIRA
                                </button>
                            </div>
                        </div>
                    `;
                    
                    return card;
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
                    
                    try {{
                        // Generate PDF for this specific gate
                        const pdfResponse = await apiCall(`${{API_BASE}}/scan/${{currentScanId}}/generate-jira-pdfs`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                gate_numbers: [gateNumber],
                                comments: {{
                                    [`gate_${{gateNumber}}`]: comment
                                }},
                                jira_ticket_id: jiraId
                            }})
                        }});
                        
                        const pdfResult = await pdfResponse.json();
                        
                        showAlert(`Successfully uploaded Gate ${{gateNumber}} report to JIRA ticket ${{jiraId}}!`, 'success');
                        
                        // Update button to show success
                        const uploadBtn = document.querySelector(`#gate-${{gateNumber}} .btn-primary`);
                        const originalHtml = uploadBtn.innerHTML;
                        uploadBtn.innerHTML = '<i class="fas fa-check me-1"></i>Uploaded!';
                        uploadBtn.classList.replace('btn-primary', 'btn-success');
                        
                        setTimeout(() => {{
                            uploadBtn.innerHTML = originalHtml;
                            uploadBtn.classList.replace('btn-success', 'btn-primary');
                        }}, 3000);
                        
                    }} catch (error) {{
                        showAlert(`Failed to upload to JIRA: ${{error.message}}`, 'danger');
                    }}
                }}
                
                // Export full report
                async function exportFullReport() {{
                    if (!currentScanId) {{
                        showAlert('No scan results available for export', 'warning');
                        return;
                    }}
                    
                    try {{
                        window.open(`${{API_BASE}}/scan/${{currentScanId}}/report/html`, '_blank');
                    }} catch (error) {{
                        showAlert(`Failed to export report: ${{error.message}}`, 'danger');
                    }}
                }}
                
                // Refresh report
                async function refreshReport() {{
                    if (!currentScanId) {{
                        showAlert('No scan to refresh', 'warning');
                        return;
                    }}
                    
                    showAlert('Refreshing report...', 'info');
                    await loadResults();
                    showAlert('Report refreshed successfully!', 'success');
                }}
                
                // Show alert
                function showAlert(message, type = 'info') {{
                    const existingAlerts = document.querySelectorAll('.alert-toast');
                    existingAlerts.forEach(alert => alert.remove());
                    
                    const alert = document.createElement('div');
                    alert.className = `alert alert-${{type}} alert-toast`;
                    alert.innerHTML = `
                        <div class="d-flex align-items-center">
                            <i class="fas fa-${{{{
                                'success': 'check-circle',
                                'danger': 'exclamation-circle',
                                'warning': 'exclamation-triangle',
                                'info': 'info-circle'
                            }}[type] || 'info-circle'}} me-2"></i>
                            <span>${{message}}</span>
                            <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
                        </div>
                    `;
                    
                    document.body.appendChild(alert);
                    
                    setTimeout(() => {{
                        if (alert.parentElement) {{
                            alert.remove();
                        }}
                    }}, 5000);
                }}
                
                // Reset scan button
                function resetScanButton() {{
                    const scanBtn = document.getElementById('scanBtn');
                    scanBtn.disabled = false;
                    scanBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Run Security Scan';
                }}
                
                // Initialize
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('CodeGates Scanner UI with Enterprise Git Integration initialized');
                }});
            </script>
        </body>
        </html>
        """
        
        return html_content

# Global instance
direct_ui = DirectStreamlitUI()

def get_integrated_ui_html(api_base: str = "http://localhost:8000/api/v1") -> str:
    """Get the integrated UI HTML"""
    return direct_ui.render_main_page(api_base) 