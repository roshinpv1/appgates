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
        case 'assessmentStarted':
            showStatus(message.data.message, 'info');
            hideResults();
            break;
            
        case 'assessmentCompleted':
            hideStatus();
            showResults(message.data);
            // Re-enable the Start Assessment button
            const scanBtn = document.getElementById('scanButton');
            if (scanBtn) scanBtn.disabled = false;
            break;
            
        case 'showResults':  // Handle the actual command sent by the extension
            hideStatus();
            showResults(message.data);
            break;
            
        case 'assessmentError':
            showStatus(message.data.error, 'error');
            hideResults();
            // Re-enable the Start Assessment button
            const scanBtnErr = document.getElementById('scanButton');
            if (scanBtnErr) scanBtnErr.disabled = false;
            break;
            
        case 'assessmentProgress':
            // Show progress information
            if (message.data.current_step) {
                const progressText = message.data.progress_percentage ? 
                    `${message.data.current_step} (${message.data.progress_percentage}%)` : 
                    message.data.current_step;
                showStatus(progressText, 'info');
            } else {
                showStatus(message.data.message, 'info');
            }
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
    
    // Add JIRA upload button if app_id and scan_id are available
    if (result.app_id && result.scan_id) {
        let jiraBtn = document.getElementById('jira-upload-btn');
        if (!jiraBtn) {
            jiraBtn = document.createElement('button');
            jiraBtn.id = 'jira-upload-btn';
            jiraBtn.textContent = 'Upload Report to JIRA';
            jiraBtn.style.margin = '10px 0';
            jiraBtn.onclick = async () => {
                jiraBtn.disabled = true;
                jiraBtn.textContent = 'Uploading to JIRA...';
                try {
                    const reportType = result.htmlContent ? 'html' : 'json';
                    const response = await fetch('/api/v1/jira/upload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            app_id: result.app_id,
                            scan_id: result.scan_id,
                            report_type: reportType
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        alert('JIRA upload started!');
                    } else {
                        alert('JIRA upload failed: ' + (data.message || 'Unknown error'));
                    }
                } catch (err) {
                    alert('JIRA upload failed: ' + err.message);
                } finally {
                    jiraBtn.disabled = false;
                    jiraBtn.textContent = 'Upload Report to JIRA';
                }
            };
            resultsEl.prepend(jiraBtn);
        }
    }
    
    // Check if we have server-generated HTML content
    if (result.htmlContent) {
        // Use server-generated HTML content directly
        resultsEl.innerHTML = result.htmlContent;
        
        // Ensure the toggleDetails function is available in the webview context
        if (typeof window.toggleDetails === 'undefined') {
            // Add the toggleDetails function if it's not already present
            const toggleScript = document.createElement('script');
            toggleScript.textContent = `
                function toggleDetails(button, detailsId) {
                    const details = document.getElementById(detailsId);
                    const isExpanded = button.getAttribute('aria-expanded') === 'true';
                    
                    button.setAttribute('aria-expanded', !isExpanded);
                    details.setAttribute('aria-hidden', isExpanded);
                    
                    // Smooth scroll to expanded content
                    if (!isExpanded) {
                        setTimeout(() => {
                            details.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }, 100);
                    }
                }
                
                // Enhanced function to handle pattern details expansion
                function togglePatternDetails(button, patternId) {
                    const patternDetails = document.getElementById(patternId);
                    const isExpanded = button.getAttribute('aria-expanded') === 'true';
                    
                    button.setAttribute('aria-expanded', !isExpanded);
                    patternDetails.setAttribute('aria-hidden', isExpanded);
                    
                    // Update button text
                    const buttonText = button.querySelector('.toggle-text');
                    if (buttonText) {
                        buttonText.textContent = isExpanded ? 'Show Pattern Details' : 'Hide Pattern Details';
                    }
                    
                    // Smooth scroll to expanded content
                    if (!isExpanded) {
                        setTimeout(() => {
                            patternDetails.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }, 100);
                    }
                }
                
                // Function to handle coverage analysis expansion
                function toggleCoverageAnalysis(button, coverageId) {
                    const coverageDetails = document.getElementById(coverageId);
                    const isExpanded = button.getAttribute('aria-expanded') === 'true';
                    
                    button.setAttribute('aria-expanded', !isExpanded);
                    coverageDetails.setAttribute('aria-hidden', isExpanded);
                    
                    // Update button text
                    const buttonText = button.querySelector('.toggle-text');
                    if (buttonText) {
                        buttonText.textContent = isExpanded ? 'Show Coverage Analysis' : 'Hide Coverage Analysis';
                    }
                }
            `;
            document.head.appendChild(toggleScript);
        }
        
        // Add interactive UI enhancements for enhanced report features
        if (result.hasEnhancedFeatures) {
            addEnhancedReportFeatures(result.scan_id);
        }
        
        // Add interactive UI enhancements for comment functionality
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

function addInteractiveGateUI(scanId) {
    // Add expandable gate sections with + buttons
    const gateSections = document.querySelectorAll('.gate-result, .gate-item, [data-gate]');
    
    gateSections.forEach((section, index) => {
        const gateName = section.getAttribute('data-gate') || 
                        section.querySelector('[data-gate]')?.getAttribute('data-gate') ||
                        section.querySelector('.gate-name')?.textContent?.trim();
        
        if (gateName) {
            // Create expandable container
            const expandableContainer = document.createElement('div');
            expandableContainer.className = 'gate-expandable';
            expandableContainer.style.cssText = `
                margin: 15px 0;
                border: 1px solid #e1e5e9;
                border-radius: 8px;
                overflow: hidden;
            `;
            
            // Create header with + button
            const header = document.createElement('div');
            header.className = 'gate-header';
            header.style.cssText = `
                background: #f8f9fa;
                padding: 12px 15px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 1px solid #e1e5e9;
                transition: background-color 0.2s;
            `;
            
            const headerContent = document.createElement('div');
            headerContent.style.cssText = `
                display: flex;
                align-items: center;
                gap: 10px;
            `;
            
            // Create + button
            const expandButton = document.createElement('button');
            expandButton.className = 'gate-expand-btn';
            expandButton.innerHTML = '+';
            expandButton.style.cssText = `
                background: #007acc;
                color: white;
                border: none;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            `;
            
            const gateTitle = document.createElement('span');
            gateTitle.textContent = formatGateName(gateName);
            gateTitle.style.cssText = `
                font-weight: 600;
                color: #2c3e50;
            `;
            
            const gateStatus = document.createElement('span');
            gateStatus.className = 'gate-status';
            gateStatus.style.cssText = `
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            `;
            
            // Get status from existing content
            const existingStatus = section.querySelector('.status-implemented, .status-partial, .status-not-implemented');
            if (existingStatus) {
                gateStatus.textContent = existingStatus.textContent;
                gateStatus.className = existingStatus.className;
            } else {
                gateStatus.textContent = 'Unknown';
                gateStatus.style.cssText += 'background: #f3f4f6; color: #6b7280;';
            }
            
            headerContent.appendChild(expandButton);
            headerContent.appendChild(gateTitle);
            headerContent.appendChild(gateStatus);
            
            const headerRight = document.createElement('div');
            headerRight.style.cssText = `
                display: flex;
                align-items: center;
                gap: 10px;
            `;
            
            // Add action buttons
            const actionButtons = createGateActionButtons(gateName, scanId);
            headerRight.appendChild(actionButtons);
            
            header.appendChild(headerContent);
            header.appendChild(headerRight);
            
            // Create content container
            const content = document.createElement('div');
            content.className = 'gate-content';
            content.style.cssText = `
                padding: 0;
                max-height: 0;
                overflow: hidden;
                transition: all 0.3s ease;
                background: white;
            `;
            
            // Move existing content into expandable container
            const originalContent = section.cloneNode(true);
            content.appendChild(originalContent);
            
            // Add to expandable container
            expandableContainer.appendChild(header);
            expandableContainer.appendChild(content);
            
            // Add click handler for expand/collapse
            header.addEventListener('click', (e) => {
                if (e.target === expandButton) return; // Don't trigger on button click
                
                const isExpanded = content.style.maxHeight !== '0px';
                
                if (isExpanded) {
                    content.style.maxHeight = '0px';
                    content.style.padding = '0';
                    expandButton.innerHTML = '+';
                    expandButton.style.transform = 'rotate(0deg)';
                    header.style.background = '#f8f9fa';
                } else {
                    content.style.maxHeight = content.scrollHeight + 'px';
                    content.style.padding = '15px';
                    expandButton.innerHTML = '−';
                    expandButton.style.transform = 'rotate(0deg)';
                    header.style.background = '#e3f2fd';
                }
            });
            
            // Replace original section with expandable container
            section.parentNode.replaceChild(expandableContainer, section);
        }
    });
}

function createGateActionButtons(gateName, scanId) {
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        gap: 5px;
    `;
    
    // Add comment button
    const commentBtn = document.createElement('button');
    commentBtn.innerHTML = '💬';
    commentBtn.title = 'Add comment';
    commentBtn.style.cssText = `
        background: #28a745;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        cursor: pointer;
        font-size: 12px;
        transition: background-color 0.2s;
    `;
    
    commentBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showCommentDialog(gateName, scanId);
    });
    
    // Add details button
    const detailsBtn = document.createElement('button');
    detailsBtn.innerHTML = '📋';
    detailsBtn.title = 'View details';
    detailsBtn.style.cssText = `
        background: #17a2b8;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        cursor: pointer;
        font-size: 12px;
        transition: background-color 0.2s;
    `;
    
    detailsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showGateDetails(gateName, scanId);
    });
    
    buttonContainer.appendChild(commentBtn);
    buttonContainer.appendChild(detailsBtn);
    
    return buttonContainer;
}

function showCommentDialog(gateName, scanId) {
    // Create modal dialog
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: white;
        padding: 20px;
        border-radius: 8px;
        min-width: 400px;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
    `;
    
    const title = document.createElement('h3');
    title.textContent = `Add Comment for ${formatGateName(gateName)}`;
    title.style.cssText = `
        margin: 0 0 15px 0;
        color: #2c3e50;
    `;
    
    const textarea = document.createElement('textarea');
    textarea.placeholder = 'Enter your comment, feedback, or notes for this gate...';
    textarea.style.cssText = `
        width: 100%;
        min-height: 120px;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-family: inherit;
        font-size: 14px;
        resize: vertical;
        margin-bottom: 15px;
    `;
    
    // Load existing comment
    const existingComment = getGateComment(gateName);
    if (existingComment) {
        textarea.value = existingComment;
    }
    
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        gap: 10px;
        justify-content: flex-end;
    `;
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.style.cssText = `
        padding: 8px 16px;
        border: 1px solid #ddd;
        background: white;
        border-radius: 4px;
        cursor: pointer;
    `;
    
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save Comment';
    saveBtn.style.cssText = `
        padding: 8px 16px;
        background: #007acc;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    `;
    
    cancelBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    saveBtn.addEventListener('click', () => {
        const comment = textarea.value.trim();
        setGateComment(gateName, comment);
        
        // Update comments on server if scan ID is available
        if (scanId) {
            const comments = collectComments();
            vscode.postMessage({
                command: 'updateComments',
                data: { scanId, comments }
            });
        }
        
        document.body.removeChild(modal);
        
        // Show success message
        showStatus('Comment saved successfully!', 'success');
        setTimeout(hideStatus, 2000);
    });
    
    buttonContainer.appendChild(cancelBtn);
    buttonContainer.appendChild(saveBtn);
    
    dialog.appendChild(title);
    dialog.appendChild(textarea);
    dialog.appendChild(buttonContainer);
    modal.appendChild(dialog);
    
    document.body.appendChild(modal);
    
    // Focus on textarea
    textarea.focus();
}

function showGateDetails(gateName, scanId) {
    // Create modal dialog for gate details
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: white;
        padding: 20px;
        border-radius: 8px;
        min-width: 500px;
        max-width: 700px;
        max-height: 80vh;
        overflow-y: auto;
    `;
    
    const title = document.createElement('h3');
    title.textContent = `${formatGateName(gateName)} - Gate Details`;
    title.style.cssText = `
        margin: 0 0 15px 0;
        color: #2c3e50;
        border-bottom: 2px solid #007acc;
        padding-bottom: 10px;
    `;
    
    const content = document.createElement('div');
    content.innerHTML = `
        <div style="margin-bottom: 15px;">
            <h4 style="color: #495057; margin: 0 0 5px 0;">Gate Description</h4>
            <p style="margin: 0; color: #6c757d;">This gate validates ${formatGateName(gateName).toLowerCase()} implementation in your codebase.</p>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #495057; margin: 0 0 5px 0;">What We Check</h4>
            <ul style="margin: 0; color: #6c757d; padding-left: 20px;">
                <li>Pattern matching for ${formatGateName(gateName).toLowerCase()}</li>
                <li>Code quality indicators</li>
                <li>Best practice implementation</li>
                <li>Security and reliability standards</li>
            </ul>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #495057; margin: 0 0 5px 0;">Recommendations</h4>
            <p style="margin: 0; color: #6c757d;">Review the assessment results and implement missing patterns to improve your code quality score.</p>
        </div>
    `;
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.style.cssText = `
        padding: 8px 16px;
        background: #6c757d;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 15px;
    `;
    
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    dialog.appendChild(title);
    dialog.appendChild(content);
    dialog.appendChild(closeBtn);
    modal.appendChild(dialog);
    
    document.body.appendChild(modal);
}

function addProminentFeedbackBoxes(scanId) {
    // Find all gate result containers
    const gateContainers = document.querySelectorAll('.gate-result, .gate-item, [data-gate]');
    
    gateContainers.forEach(container => {
        const gateName = container.getAttribute('data-gate') || 
                        container.querySelector('[data-gate]')?.getAttribute('data-gate') ||
                        container.querySelector('.gate-name')?.textContent?.trim();
        
        if (gateName) {
            // Create prominent feedback section
            const feedbackSection = document.createElement('div');
            feedbackSection.className = 'gate-feedback-section';
            feedbackSection.style.cssText = `
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                border-left: 4px solid #007acc;
            `;
            
            const feedbackTitle = document.createElement('h4');
            feedbackTitle.textContent = `📝 Feedback for ${formatGateName(gateName)}`;
            feedbackTitle.style.cssText = `
                margin: 0 0 10px 0;
                color: #495057;
                font-size: 16px;
                font-weight: 600;
            `;
            
            const feedbackTextarea = document.createElement('textarea');
            feedbackTextarea.className = 'gate-feedback-input';
            feedbackTextarea.setAttribute('data-gate', gateName);
            feedbackTextarea.placeholder = `Add your feedback, comments, or notes for ${formatGateName(gateName)}...`;
            feedbackTextarea.style.cssText = `
                width: 100%;
                min-height: 80px;
                padding: 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-family: inherit;
                font-size: 14px;
                resize: vertical;
                box-sizing: border-box;
            `;
            
            // Load existing comment if any
            const existingComment = getGateComment(gateName);
            if (existingComment) {
                feedbackTextarea.value = existingComment;
            }
            
            // Add change handler
            feedbackTextarea.addEventListener('input', () => {
                setGateComment(gateName, feedbackTextarea.value);
                
                // Update comments on server if scan ID is available
                if (scanId) {
                    const comments = collectComments();
                    vscode.postMessage({
                        command: 'updateComments',
                        data: { scanId, comments }
                    });
                }
            });
            
            feedbackSection.appendChild(feedbackTitle);
            feedbackSection.appendChild(feedbackTextarea);
            
            // Insert feedback section after the gate container
            container.appendChild(feedbackSection);
        }
    });
}

function addCommentHandlers(scanId) {
    // Add event listeners for comment inputs
    const commentInputs = document.querySelectorAll('.comment-input, .gate-feedback-input');
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
    const commentInputs = document.querySelectorAll('.comment-input, .gate-feedback-input');
    
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
        generateBtn.textContent = '📊 Generate Final HTML Report with Comments';
        
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

function startAssessment() {
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

    // Disable the Start Assessment button
    const scanBtn = document.getElementById('scanButton');
    if (scanBtn) scanBtn.disabled = true;

    vscode.postMessage({
        command: 'assess',
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

// New function to handle enhanced report features
function addEnhancedReportFeatures(scanId) {
    // Add enhanced styling for pattern details sections
    const patternDetailsSections = document.querySelectorAll('.pattern-details-section');
    patternDetailsSections.forEach((section, index) => {
        section.style.cssText = `
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
        `;
        
        // Add collapsible functionality
        const toggleButton = document.createElement('button');
        toggleButton.className = 'pattern-toggle-btn';
        toggleButton.style.cssText = `
            background: #007acc;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-bottom: 10px;
        `;
        toggleButton.innerHTML = '<span class="toggle-text">Show Pattern Details</span>';
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.onclick = () => togglePatternDetails(toggleButton, `pattern-details-${index}`);
        
        section.insertBefore(toggleButton, section.firstChild);
        
        // Create collapsible content
        const detailsContent = document.createElement('div');
        detailsContent.id = `pattern-details-${index}`;
        detailsContent.setAttribute('aria-hidden', 'true');
        detailsContent.style.cssText = `
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        `;
        
        // Move the pattern details content into the collapsible section
        const detailsContentNodes = Array.from(section.childNodes).slice(1); // Skip the button
        detailsContentNodes.forEach(node => {
            if (node !== toggleButton) {
                detailsContent.appendChild(node.cloneNode(true));
                node.remove();
            }
        });
        
        section.appendChild(detailsContent);
    });
    
    // Add enhanced styling for coverage analysis sections
    const coverageSections = document.querySelectorAll('.coverage-analysis-section');
    coverageSections.forEach((section, index) => {
        section.style.cssText = `
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
        `;
        
        // Add collapsible functionality
        const toggleButton = document.createElement('button');
        toggleButton.className = 'coverage-toggle-btn';
        toggleButton.style.cssText = `
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-bottom: 10px;
        `;
        toggleButton.innerHTML = '<span class="toggle-text">Show Coverage Analysis</span>';
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.onclick = () => toggleCoverageAnalysis(toggleButton, `coverage-analysis-${index}`);
        
        section.insertBefore(toggleButton, section.firstChild);
        
        // Create collapsible content
        const analysisContent = document.createElement('div');
        analysisContent.id = `coverage-analysis-${index}`;
        analysisContent.setAttribute('aria-hidden', 'true');
        analysisContent.style.cssText = `
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border: 1px solid #c3e6cb;
        `;
        
        // Move the coverage analysis content into the collapsible section
        const analysisContentNodes = Array.from(section.childNodes).slice(1); // Skip the button
        analysisContentNodes.forEach(node => {
            if (node !== toggleButton) {
                analysisContent.appendChild(node.cloneNode(true));
                node.remove();
            }
        });
        
        section.appendChild(analysisContent);
    });
    
    // Add enhanced styling for NOT_APPLICABLE gates
    const notApplicableGates = document.querySelectorAll('[data-status="NOT_APPLICABLE"]');
    notApplicableGates.forEach(gate => {
        gate.style.cssText = `
            background: #f8f9fa;
            border-left: 4px solid #6c757d;
            opacity: 0.8;
        `;
        
        // Add a badge to clearly indicate NOT_APPLICABLE status
        const statusBadge = document.createElement('span');
        statusBadge.style.cssText = `
            background: #6c757d;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            margin-left: 10px;
        `;
        statusBadge.textContent = 'Not Applicable';
        
        const gateHeader = gate.querySelector('.gate-header, .gate-title, h3, h4');
        if (gateHeader) {
            gateHeader.appendChild(statusBadge);
        }
    });
    
    // Add enhanced styling for pattern matches
    const patternMatches = document.querySelectorAll('.pattern-match, .match-item');
    patternMatches.forEach(match => {
        match.style.cssText = `
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 8px;
            margin: 4px 0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        `;
    });
    
    // Add tooltips for pattern details
    const patternInfoElements = document.querySelectorAll('[data-pattern-info]');
    patternInfoElements.forEach(element => {
        const patternInfo = element.getAttribute('data-pattern-info');
        if (patternInfo) {
            element.title = patternInfo;
            element.style.cssText = `
                cursor: help;
                text-decoration: underline dotted;
            `;
        }
    });
} 