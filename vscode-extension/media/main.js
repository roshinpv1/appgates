const vscode = acquireVsCodeApi();
let currentTab = 'local';

// Global storage for gate comments
let gateComments = {};

// Load comments from storage
function loadComments() {
    const stored = localStorage.getItem('codegates-comments');
    if (stored) {
        try {
            gateComments = JSON.parse(stored);
        } catch (e) {
            gateComments = {};
        }
    }
}

// Save comments to storage
function saveComments() {
    localStorage.setItem('codegates-comments', JSON.stringify(gateComments));
}

// Get comment for a gate
function getGateComment(gateName) {
    return gateComments[gateName] || '';
}

// Set comment for a gate
function setGateComment(gateName, comment) {
    if (comment.trim()) {
        gateComments[gateName] = comment.trim();
    } else {
        delete gateComments[gateName];
    }
    saveComments();
}

// Initialize comments on page load
document.addEventListener('DOMContentLoaded', function() {
    loadComments();
});

// Handle messages from the extension
window.addEventListener('message', event => {
    const message = event.data;
    
    switch (message.command) {
        case 'scanStarted':
            showStatus(message.data.message, 'info');
            hideResults();
            break;
            
        case 'scanCompleted':
            hideStatus();
            showResults(message.data);
            break;
            
        case 'showResults':  // Handle the actual command sent by the extension
            hideStatus();
            showResults(message.data);
            break;
            
        case 'scanError':
            showStatus(message.data.error, 'error');
            hideResults();
            break;
            
        case 'directorySelected':
            if (message.data.path) {
                document.getElementById('localPath').value = message.data.path;
            }
            break;

        case 'connectionResult':
            handleConnectionResult(message.data);
            break;
    }
});

function showTab(tab) {
    currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase().includes(tab));
    });
    
    // Update tab content
    document.getElementById('localTab').classList.toggle('hidden', tab !== 'local');
    document.getElementById('repositoryTab').classList.toggle('hidden', tab !== 'repository');
}

function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type} visible`;
}

function hideStatus() {
    const statusEl = document.getElementById('status');
    statusEl.className = 'status hidden';
}

function showResults(result) {
    const resultsEl = document.getElementById('results');
    
    // Make results div visible
    resultsEl.style.display = 'block';
    
    // Check if we have server-generated HTML content
    if (result.htmlContent) {
        // Use server-generated HTML content directly
        resultsEl.innerHTML = result.htmlContent;
        
        // Add comment functionality for the scan ID
        if (result.scan_id) {
            addCommentHandlers(result.scan_id);
        }
        
        // Add generate report button if available
        if (result.canGenerateReport) {
            addGenerateReportButton(result);
        }
        
        return;
    }
    
    // Fallback to client-side generation for backward compatibility
    generateClientSideResults(result);
}

function addCommentHandlers(scanId) {
    // Add event listeners for comment inputs
    const commentInputs = document.querySelectorAll('.comment-input');
    let commentUpdateTimeout;
    
    commentInputs.forEach(input => {
        input.addEventListener('input', () => {
            // Debounce comment updates to avoid too many server calls
            clearTimeout(commentUpdateTimeout);
            commentUpdateTimeout = setTimeout(() => {
                const comments = collectComments();
                vscode.postMessage({
                    command: 'updateComments',
                    data: { scanId, comments }
                });
            }, 1000); // Wait 1 second after user stops typing
        });
    });
}

function collectComments() {
    const comments = {};
    const commentInputs = document.querySelectorAll('.comment-input');
    
    commentInputs.forEach(input => {
        const gateName = input.getAttribute('data-gate');
        const comment = input.value.trim();
        if (gateName && comment) {
            comments[gateName] = comment;
        }
    });
    
    return comments;
}

function addGenerateReportButton(result) {
    // Find existing generate report button or create one
    let generateBtn = document.getElementById('generateReportBtn');
    
    if (!generateBtn) {
        // Create generate report button if it doesn't exist
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'report-link';
        buttonContainer.style.cssText = 'margin-top: 30px; text-align: center;';
        
        generateBtn = document.createElement('button');
        generateBtn.id = 'generateReportBtn';
        generateBtn.className = 'detailed-report-link';
        generateBtn.style.cssText = 'background: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block;';
        generateBtn.textContent = '📊 Generate HTML Report';
        
        buttonContainer.appendChild(generateBtn);
        document.getElementById('results').appendChild(buttonContainer);
    }
    
    // Add click handler
    generateBtn.onclick = () => {
        const comments = collectComments();
        vscode.postMessage({
            command: 'generateHtmlReport',
            data: { 
                result: result,
                comments: comments
            }
        });
    };
}

function generateClientSideResults(result) {
    // Fallback client-side generation (existing logic)
    const resultsEl = document.getElementById('results');
    
    const timestamp = new Date().toLocaleString();
    const projectName = extractProjectName(result.repository_url || 'Repository Scan Results');
    
    // Calculate stats
    const totalGates = result.gates.length;
    let implementedGates = 0;
    let partialGates = 0;
    let notImplementedGates = 0;
    
    // Calculate gate statistics
    for (const gate of result.gates) {
        const found = gate.found || 0;
        const status = gate.status;
        
        // Apply logical consistency fixes
        if (found > 0 && gate.name === 'avoid_logging_secrets') {
            notImplementedGates += 1;
        } else if (found > 0 && status === 'PASS') {
            partialGates += 1;
        } else if (status === 'PASS') {
            implementedGates += 1;
        } else if (status === 'WARNING') {
            partialGates += 1;
        } else if (status === 'FAIL' || status === 'FAILED') {
            notImplementedGates += 1;
        } else {
            notImplementedGates += 1;
        }
    }
    
    // Generate HTML using the same template format
    let html = `
        <div class="report-container">
            <h1>${projectName}</h1>
            <p style="color: #2563eb; margin-bottom: 30px; font-weight: 500;">Hard Gate Assessment Report</p>
            
            <h2>Executive Summary</h2>
            
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-number">${totalGates}</div>
                    <div class="stat-label">Total Gates Evaluated</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${implementedGates}</div>
                    <div class="stat-label">Gates Met</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${partialGates}</div>
                    <div class="stat-label">Partially Met</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${notImplementedGates}</div>
                    <div class="stat-label">Not Met</div>
                </div>
            </div>
            
            <h3>Overall Compliance</h3>
            <div class="compliance-bar">
                <div class="compliance-fill" style="width: ${result.score}%"></div>
            </div>
            <p><strong>${result.score.toFixed(1)}% Hard Gates Compliance</strong></p>
        </div>`;
    
    // Generate gates table
    html += generateGatesTableHtml(result.gates);
    
    // Add report link if available
    if (result.report_url || result.scan_id) {
        html += `
            <div class="report-link">
                <p>
                    <button id="generateReportBtn" class="detailed-report-link" style="background: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block;">
                        📊 Generate HTML Report
                    </button>
                </p>
            </div>`;
    }
    
    // Footer
    html += `
        <footer style="margin-top: 50px; text-align: center; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px;">
            <p>Hard Gate Assessment Report generated on ${timestamp}</p>
        </footer>
    </div>`;

    resultsEl.innerHTML = html;
    
    // Add event listeners for comment inputs and generate button
    if (result.scan_id) {
        addCommentHandlers(result.scan_id);
    }
    
    const generateBtn = document.getElementById('generateReportBtn');
    if (generateBtn) {
        generateBtn.onclick = () => {
            const comments = collectComments();
            vscode.postMessage({
                command: 'generateHtmlReport',
                data: { 
                    result: result,
                    comments: comments
                }
            });
        };
    }
}

function extractProjectName(repositoryUrl) {
    try {
        const urlParts = repositoryUrl.split('/');
        let projectName = urlParts[urlParts.length - 1] || 'Repository Scan Results';
        if (projectName.endsWith('.git')) {
            projectName = projectName.slice(0, -4);
        }
        return projectName;
    } catch {
        return 'Repository Scan Results';
    }
}

function generateGatesTableHtml(gates) {
    const gateCategories = {
        'Auditability': ['structured_logs', 'avoid_logging_secrets', 'audit_trail', 'correlation_id', 'log_api_calls', 'log_background_jobs', 'ui_errors'],
        'Availability': ['retry_logic', 'timeouts', 'throttling', 'circuit_breakers'],
        'Error Handling': ['error_logs', 'http_codes', 'ui_error_tools'],
        'Testing': ['automated_tests']
    };

    const gateNameMap = {
        'structured_logs': 'Logs Searchable Available',
        'avoid_logging_secrets': 'Avoid Logging Confidential Data',
        'audit_trail': 'Create Audit Trail Logs',
        'correlation_id': 'Tracking ID For Log Messages',
        'log_api_calls': 'Log Rest API Calls',
        'log_background_jobs': 'Log Application Messages',
        'ui_errors': 'Client UI Errors Logged',
        'retry_logic': 'Retry Logic',
        'timeouts': 'Set Timeouts IO Operations',
        'throttling': 'Throttling Drop Request',
        'circuit_breakers': 'Circuit Breakers Outgoing Requests',
        'error_logs': 'Log System Errors',
        'http_codes': 'Use HTTP Standard Error Codes',
        'ui_error_tools': 'Include Client Error Tracking',
        'automated_tests': 'Automated Regression Testing'
    };

    let html = '';

    Object.entries(gateCategories).forEach(([categoryName, gateNames]) => {
        const categoryGates = gates.filter(gate => gateNames.includes(gate.name));
        
        if (categoryGates.length === 0) return;
        
        html += `
            <div class="gate-category">
                <h3>${categoryName}</h3>
                <table class="gates-table">
                    <thead>
                        <tr>
                            <th>Practice</th>
                            <th>Status</th>
                            <th>Evidence</th>
                            <th>Recommendation</th>
                            <th>Comments</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        categoryGates.forEach(gate => {
            const gateName = gateNameMap[gate.name] || formatGateName(gate.name);
            const statusInfo = getStatusInfo(gate);
            const evidence = formatEvidence(gate);
            const recommendation = getRecommendation(gate, gateName);
            const currentComment = ''; // Empty for new comments
            
            html += `
                        <tr>
                            <td><strong>${gateName}</strong></td>
                            <td><span class="status-${statusInfo.class}">${statusInfo.text}</span></td>
                            <td>${evidence}</td>
                            <td>${recommendation}</td>
                            <td>
                                <textarea 
                                    class="comment-input" 
                                    data-gate="${gate.name}"
                                    placeholder="Add your comments..."
                                    rows="2"
                                    style="width: 100%; resize: vertical; padding: 5px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;"
                                >${currentComment}</textarea>
                            </td>
                        </tr>`;
        });
        
        html += `
                    </tbody>
                </table>
            </div>`;
    });

    return html;
}

function getStatusInfo(status) {
    switch (status) {
        case 'PASS':
            return { class: 'implemented', text: '✓ Implemented' };
        case 'WARNING':
            return { class: 'partial', text: '⚬ Partial' };
        case 'NOT_APPLICABLE':
            return { class: 'partial', text: 'N/A' };
        default:
            return { class: 'not-implemented', text: '✗ Missing' };
    }
}

function formatEvidence(gate) {
    if (gate.status === 'NOT_APPLICABLE') {
        return 'Not applicable to this project type';
    }
    
    if (!gate.details || gate.details.length === 0) {
        return 'No relevant patterns found in codebase';
    }
    
    // Process details to avoid duplication
    const processedDetails = [];
    const seenContent = new Set();
    
    for (const detail of gate.details.slice(0, 3)) {
        // Skip if we've seen this content before (avoid duplicates)
        const cleanDetail = detail.trim().toLowerCase();
        if (!seenContent.has(cleanDetail) && detail.length > 5) {
            seenContent.add(cleanDetail);
            processedDetails.push(detail);
        }
    }
    
    // If we have basic statistics, show them first
    let evidence = '';
    if (gate.found !== undefined && gate.expected !== undefined && gate.coverage !== undefined) {
        if (gate.found > 0) {
            evidence = `Found ${gate.found} implementations with ${gate.coverage.toFixed(1)}% coverage`;
        } else {
            evidence = 'No relevant patterns found in codebase';
        }
    }
    
    // Add processed details if they provide additional value
    if (processedDetails.length > 0) {
        // Check if details provide more than just the basic "no patterns found" message
        const meaningfulDetails = processedDetails.filter(detail => 
            !detail.toLowerCase().includes('no') && 
            !detail.toLowerCase().includes('not found') &&
            detail.length > 20 // Filter out very short, likely redundant details
        );
        
        if (meaningfulDetails.length > 0) {
            if (evidence) {
                evidence += '<br>' + meaningfulDetails.join('<br>');
            } else {
                evidence = meaningfulDetails.join('<br>');
            }
        } else if (!evidence) {
            // Fall back to the first detail if no meaningful details and no basic stats
            evidence = processedDetails[0] || 'No relevant patterns found in codebase';
        }
    } else if (!evidence) {
        // Final fallback
        evidence = 'No relevant patterns found in codebase';
    }
    
    return evidence;
}

function getRecommendation(gate, gateName) {
    switch (gate.status) {
        case 'PASS':
            return 'Continue maintaining good practices';
        case 'WARNING':
            return `Expand implementation of ${gateName.toLowerCase()}`;
        case 'NOT_APPLICABLE':
            return 'Not applicable to this project type';
        default:
            return `Implement ${gateName.toLowerCase()}`;
    }
}

function hideResults() {
    const resultsEl = document.getElementById('results');
    resultsEl.style.display = 'none';
    resultsEl.innerHTML = '';
}

function handleConnectionResult(data) {
    if (data.connected) {
        showStatus('Successfully connected to CodeGates API', 'success');
    } else {
        showStatus(data.error || 'Failed to connect to CodeGates API', 'error');
    }
    setTimeout(hideStatus, 3000);
}

function browseDirectory() {
    vscode.postMessage({ command: 'browseDirectory' });
}

function testConnection() {
    vscode.postMessage({
        command: 'testConnection'
    });
}

function startScan() {
    const repositoryUrl = document.getElementById('repositoryUrl').value.trim();
    const branch = document.getElementById('branch').value.trim() || 'main';
    const githubToken = document.getElementById('githubToken').value.trim();
    const threshold = document.getElementById('threshold').value;

    if (!repositoryUrl) {
        showStatus('Please enter a repository URL', 'error');
        return;
    }

    // Validate GitHub URL format (support both github.com and GitHub Enterprise)
    try {
        const url = new URL(repositoryUrl);
        const hostname = url.hostname.toLowerCase();
        
        // Check if hostname contains 'github' (for both github.com and GitHub Enterprise like github.company.com)
        if (!hostname.includes('github')) {
            showStatus('Please enter a valid GitHub repository URL (github.com or GitHub Enterprise)', 'error');
            return;
        }
        
        // Check if path has owner/repo format
        const pathParts = url.pathname.replace(/^\/+|\/+$/g, '').split('/');
        if (pathParts.length < 2 || !pathParts[0] || !pathParts[1]) {
            showStatus('Please enter a valid repository URL format: https://github.example.com/owner/repo', 'error');
            return;
        }
        
    } catch (e) {
        showStatus('Please enter a valid repository URL', 'error');
        return;
    }

    vscode.postMessage({
        command: 'scan',
        data: {
            repositoryUrl,
            branch,
            githubToken,
            threshold: parseInt(threshold)
        }
    });
}

function formatGateName(name) {
    return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
} 