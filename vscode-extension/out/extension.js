"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const apiRunner_1 = require("./runners/apiRunner");
const configurationManager_1 = require("./utils/configurationManager");
const notificationManager_1 = require("./utils/notificationManager");
const screenshot_1 = require("./utils/screenshot");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
class CodeGatesAssessmentPanel {
    static createOrShow(extensionUri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;
        if (CodeGatesAssessmentPanel.currentPanel) {
            CodeGatesAssessmentPanel.currentPanel.panel.reveal(column);
            return;
        }
        const panel = vscode.window.createWebviewPanel('codegatesAssessment', 'CodeGates Hard Gate Assessment', column || vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        CodeGatesAssessmentPanel.currentPanel = new CodeGatesAssessmentPanel(panel, extensionUri);
    }
    constructor(panel, extensionUri) {
        this.panel = panel;
        this.extensionUri = extensionUri;
        this.configManager = new configurationManager_1.ConfigurationManager();
        this.notificationManager = new notificationManager_1.NotificationManager();
        this.apiRunner = new apiRunner_1.ApiRunner(this.configManager, this.notificationManager);
        this.update();
        this.panel.onDidDispose(() => this.dispose(), null);
        this.panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'testConnection':
                    await this.handleTestConnection();
                    break;
                case 'assess':
                    await this.handleAssessment(message.data);
                    break;
                case 'generateHtmlReport':
                    await this.handleGenerateHtmlReport(message.data);
                    break;
                case 'updateComments':
                    this.handleUpdateComments(message.data);
                    break;
                case 'captureScreenshot':
                    await this.handleCaptureScreenshot(message.data);
                    break;
            }
        });
    }
    async handleTestConnection() {
        try {
            const isConnected = await this.apiRunner.testConnection();
            this.panel.webview.postMessage({
                command: 'connectionResult',
                data: { connected: isConnected }
            });
        }
        catch (error) {
            this.panel.webview.postMessage({
                command: 'connectionResult',
                data: { connected: false, error: error instanceof Error ? error.message : 'Unknown error' }
            });
        }
    }
    async handleAssessment(assessmentData) {
        try {
            this.panel.webview.postMessage({
                command: 'assessmentStarted',
                data: { message: 'Starting hard gate assessment...' }
            });
            // Test connection first
            try {
                const isConnected = await this.apiRunner.testConnection();
                if (!isConnected) {
                    throw new Error('API server connection failed');
                }
            }
            catch (connectionError) {
                // Show user-friendly error dialog
                const startServer = await vscode.window.showErrorMessage('Failed to connect to API server. ' +
                    'To start the API server:\n1. Open terminal in VS Code (Terminal → New Terminal)\n2. Run: python3 start_server.py\n3. Wait for "Server started" message\n4. Try the assessment again', 'Start Server', 'Show Instructions', 'Continue Anyway');
                if (startServer === 'Start Server') {
                    // Start API server
                    const terminal = vscode.window.createTerminal('CodeGates API Server');
                    terminal.show();
                    terminal.sendText('python3 start_server.py');
                    vscode.window.showInformationMessage('Starting API server in terminal. Please wait for it to start, then try the assessment again.');
                    this.panel.webview.postMessage({
                        command: 'assessmentError',
                        data: { error: 'API server is starting. Please wait and try again in a few seconds.' }
                    });
                    return;
                }
                else if (startServer === 'Show Instructions') {
                    vscode.window.showInformationMessage('To start the API server:\n1. Open terminal in VS Code (Terminal → New Terminal)\n2. Run: python3 start_server.py\n3. Wait for "Server started" message\n4. Try the assessment again');
                    this.panel.webview.postMessage({
                        command: 'assessmentError',
                        data: { error: 'Please start the API server first. See the notification for instructions.' }
                    });
                    return;
                }
                else if (startServer !== 'Continue Anyway') {
                    this.panel.webview.postMessage({
                        command: 'assessmentError',
                        data: { error: 'API server connection required for assessment.' }
                    });
                    return;
                }
            }
            const options = {
                threshold: assessmentData.threshold || 70
            };
            const splunkQuery = assessmentData.splunk_query;
            this.panel.webview.postMessage({
                command: 'assessmentProgress',
                data: { message: 'Connecting to repository...' }
            });
            const result = await this.apiRunner.scanRepository(assessmentData.repositoryUrl, assessmentData.branch || 'main', assessmentData.githubToken, options, splunkQuery);
            // Add repository URL to result for better display
            result.repository_url = assessmentData.repositoryUrl;
            // If scan is running, poll for completion (up to 15 minutes)
            if (result.status === 'running') {
                console.log('Scan started, polling for completion (timeout: 15 minutes)...');
                return await this.pollForCompletion(result.scan_id);
            }
            // Send results to webview
            this.panel.webview.postMessage({
                command: 'showResults',
                data: result
            });
            // Try to fetch server-generated HTML content for display
            if (result.scan_id) {
                try {
                    console.log('Fetching server-generated HTML content for display...');
                    const htmlContent = await this.apiRunner.getHtmlReport(result.scan_id);
                    // Use the full HTML content to preserve all scripts/styles/interactivity
                    this.panel.webview.postMessage({
                        command: 'showResults',
                        data: {
                            ...result,
                            htmlContent: htmlContent,
                            canGenerateReport: true,
                            hasEnhancedFeatures: true // Flag to indicate enhanced report features
                        }
                    });
                    console.log('Successfully loaded server-generated HTML content with enhanced features');
                }
                catch (error) {
                    console.warn('Failed to fetch server-generated HTML content, using fallback:', error.message);
                    // Send basic result without server content (fallback)
                    this.panel.webview.postMessage({
                        command: 'showResults',
                        data: {
                            ...result,
                            canGenerateReport: false,
                            hasEnhancedFeatures: false
                        }
                    });
                }
            }
        }
        catch (error) {
            console.error('Assessment error:', error);
            // Enhanced error handling for different types of errors
            let errorMessage = error.message || 'Unknown error occurred';
            // Provide more specific error messages
            if (error.message?.includes('Repository is private')) {
                errorMessage = 'Repository is private. Please provide a GitHub token with repo scope.';
            }
            else if (error.message?.includes('Invalid GitHub token')) {
                errorMessage = 'Invalid GitHub token. Please check if the token has the required repo scope.';
            }
            else if (error.message?.includes('Cannot access repository')) {
                errorMessage = 'Cannot access repository. Please check if the token has access to this repository.';
            }
            else if (error.message?.includes('timeout')) {
                errorMessage = 'Repository scan timed out. Large repositories may take longer to analyze. Please try again.';
            }
            else if (error.message?.includes('ECONNREFUSED')) {
                errorMessage = 'Cannot connect to API server. Please start the API server first.';
            }
            this.panel.webview.postMessage({
                command: 'assessmentError',
                data: { error: errorMessage }
            });
        }
        // Return void to satisfy TypeScript
        return;
    }
    async pollForCompletion(scanId) {
        const startTime = Date.now();
        const timeout = 15 * 60 * 1000; // 15 minutes
        while (Date.now() - startTime < timeout) {
            const result = await this.apiRunner.getScanStatus(scanId);
            // Compose a user-friendly progress message
            let progressMsg = '';
            if (result.current_step && result.progress_percentage !== undefined) {
                progressMsg = `${result.current_step} (${result.progress_percentage}%)`;
            }
            else if (result.current_step) {
                progressMsg = result.current_step;
            }
            else if (result.progress_percentage !== undefined) {
                progressMsg = `Progress: ${result.progress_percentage}%`;
            }
            else {
                progressMsg = 'Assessment in progress...';
            }
            // Send progress update with current step information
            this.panel.webview.postMessage({
                command: 'assessmentProgress',
                data: {
                    current_step: result.current_step,
                    progress_percentage: result.progress_percentage,
                    step_details: result.step_details,
                    message: progressMsg
                }
            });
            if (result.status === 'completed') {
                this.panel.webview.postMessage({
                    command: 'assessmentProgress',
                    data: { message: 'Assessment completed!' }
                });
                this.panel.webview.postMessage({
                    command: 'showResults',
                    data: result
                });
                // Try to fetch server-generated HTML content for display
                if (result.scan_id) {
                    try {
                        console.log('Fetching server-generated HTML content for display...');
                        const htmlContent = await this.apiRunner.getHtmlReport(result.scan_id);
                        // Use the full HTML content to preserve all scripts/styles/interactivity
                        this.panel.webview.postMessage({
                            command: 'showResults',
                            data: {
                                ...result,
                                htmlContent: htmlContent,
                                canGenerateReport: true
                            }
                        });
                        console.log('Successfully loaded server-generated HTML content');
                    }
                    catch (error) {
                        console.warn('Failed to fetch server-generated HTML content, using fallback:', error.message);
                        // Send basic result without server content (fallback)
                        this.panel.webview.postMessage({
                            command: 'showResults',
                            data: {
                                ...result,
                                canGenerateReport: true
                            }
                        });
                    }
                }
                return result;
            }
            else if (result.status === 'failed') {
                this.panel.webview.postMessage({
                    command: 'assessmentError',
                    data: { error: `Assessment failed: ${result.message || 'Unknown error'}` }
                });
                throw new Error(`Assessment failed: ${result.message || 'Unknown error'}`);
            }
            await new Promise(resolve => setTimeout(resolve, 5000)); // Poll every 5 seconds
        }
        this.panel.webview.postMessage({
            command: 'assessmentError',
            data: { error: 'Assessment timed out after 15 minutes.' }
        });
        throw new Error('Assessment timed out after 15 minutes.');
    }
    async handleGenerateHtmlReport(data) {
        try {
            // Get a better default path - use workspace folder or home directory
            let defaultUri;
            if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
                // Use the workspace folder if available
                defaultUri = vscode.Uri.joinPath(vscode.workspace.workspaceFolders[0].uri, 'codegates-report.html');
            }
            else {
                // Fall back to home directory
                const os = require('os');
                const path = require('path');
                const homePath = path.join(os.homedir(), 'codegates-report.html');
                defaultUri = vscode.Uri.file(homePath);
            }
            // Show save dialog to let user choose where to save the HTML report
            const saveUri = await vscode.window.showSaveDialog({
                defaultUri: defaultUri,
                filters: {
                    'HTML Files': ['html'],
                    'All Files': ['*']
                }
            });
            if (!saveUri) {
                return; // User cancelled
            }
            // Fetch HTML report from server instead of generating locally
            const htmlContent = await this.fetchHtmlReportFromServer(data.result.scan_id, data.comments);
            // Write to file
            await vscode.workspace.fs.writeFile(saveUri, Buffer.from(htmlContent, 'utf8'));
            // Show success message with option to open
            const openFile = await vscode.window.showInformationMessage(`HTML report generated successfully: ${saveUri.fsPath}`, 'Open Report', 'Open in Browser');
            if (openFile === 'Open Report') {
                vscode.window.showTextDocument(saveUri);
            }
            else if (openFile === 'Open in Browser') {
                vscode.env.openExternal(saveUri);
            }
        }
        catch (error) {
            console.error('Generate HTML report error:', error);
            vscode.window.showErrorMessage(`Failed to generate HTML report: ${error.message}`);
        }
    }
    async fetchHtmlReportFromServer(scanId, comments) {
        try {
            // First, update comments on server if they exist
            if (comments && Object.keys(comments).length > 0) {
                console.log('Updating comments on server before generating report...');
                await this.apiRunner.updateReportComments(scanId, comments);
            }
            // Fetch HTML report from server
            console.log('Fetching HTML report from server...');
            const htmlContent = await this.apiRunner.getHtmlReport(scanId, comments);
            console.log('Successfully fetched HTML report from server');
            return htmlContent;
        }
        catch (error) {
            console.error('Failed to fetch HTML report from server:', error);
            // Check if it's a server connection issue
            if (error.message.includes('ECONNREFUSED') || error.message.includes('connect')) {
                vscode.window.showWarningMessage('Server unavailable. Please start the API server to generate HTML reports.');
                throw new Error('Server unavailable for HTML report generation. Please start the API server.');
            }
            throw new Error(`Failed to fetch report from server: ${error.message}`);
        }
    }
    async handleUpdateComments(data) {
        try {
            const { scanId, comments } = data;
            if (!scanId) {
                console.warn('No scan ID provided for comment update');
                return;
            }
            console.log(`Updating comments for scan ${scanId}:`, comments);
            // Update comments on server
            await this.apiRunner.updateReportComments(scanId, comments);
            console.log('Comments updated successfully on server');
        }
        catch (error) {
            console.error('Failed to update comments:', error);
            // Show user-friendly error message
            if (error.message.includes('ECONNREFUSED') || error.message.includes('connect')) {
                vscode.window.showWarningMessage('Cannot update comments: API server is not available.');
            }
            else {
                vscode.window.showWarningMessage(`Failed to update comments: ${error.message}`);
            }
        }
    }
    async handleCaptureScreenshot(data) {
        try {
            const scanId = data.scan_id;
            const appId = data.app_id;
            if (!scanId) {
                vscode.window.showErrorMessage('Scan ID not found. Run a scan first.');
                return;
            }
            // Prompt for URL, default to http://abc.com/appid={app_id} if blank
            const url = await vscode.window.showInputBox({
                prompt: 'Enter the URL to capture a screenshot (leave blank to use default)',
                placeHolder: 'https://example.com',
                value: appId ? `http://abc.com/appid=${appId}` : 'https://example.com'
            });
            const finalUrl = url && url.trim() !== '' ? url : (appId ? `http://abc.com/appid=${appId}` : 'https://example.com');
            if (!finalUrl)
                return;
            // Save screenshot to the scan's report directory
            const reportsDir = path.join(__dirname, '..', '..', 'reports', scanId);
            if (!fs.existsSync(reportsDir)) {
                fs.mkdirSync(reportsDir, { recursive: true });
            }
            const screenshotPath = path.join(reportsDir, `screenshot_${Date.now()}.png`);
            await (0, screenshot_1.captureScreenshot)(finalUrl, screenshotPath);
            vscode.window.showInformationMessage('Screenshot captured and saved. Regenerating report...');
            // Append screenshot to the HTML report
            const htmlReportPath = path.join(reportsDir, `codegates_report_${scanId}.html`);
            if (fs.existsSync(htmlReportPath)) {
                let html = fs.readFileSync(htmlReportPath, 'utf-8');
                // Append screenshot at the bottom before </body>
                const imgTag = `<div style="margin-top:40px;"><h2>Captured Screenshot</h2><img src="file://${screenshotPath}" style="max-width:100%;border:1px solid #ccc;" /></div>`;
                if (html.includes('</body>')) {
                    html = html.replace('</body>', `${imgTag}</body>`);
                }
                else {
                    html += imgTag;
                }
                fs.writeFileSync(htmlReportPath, html, 'utf-8');
            }
            vscode.window.showInformationMessage('Screenshot appended to the report.');
        }
        catch (err) {
            vscode.window.showErrorMessage('Failed to capture screenshot: ' + err.message);
        }
    }
    update() {
        if (this.panel) {
            this.panel.webview.html = this.getHtmlForWebview(this.panel.webview);
        }
    }
    getHtmlForWebview(webview) {
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'main.js'));
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'style.css'));
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleUri}" rel="stylesheet">
                <title>CodeGates Hard Gate Assessment</title>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>CodeGates Hard Gate Assessment</h1>
                        <p>Comprehensive validation of your repository against production-ready quality gates with feedback integration</p>
                    </div>

                    <div class="scan-form">
                        <div class="form-group">
                            <label for="repositoryUrl">GitHub Repository URL</label>
                            <input type="text" id="repositoryUrl" placeholder="https://github.com/owner/repo or https://github.enterprise.com/owner/repo">
                            <small>Enter the full GitHub repository URL (supports github.com and GitHub Enterprise)</small>
                        </div>
                        <div class="form-group">
                            <label for="branch">Branch (defaults to main)</label>
                            <input type="text" id="branch" value="main" placeholder="main">
                            <small>The branch to assess, defaults to 'main' if not specified</small>
                        </div>
                        <div class="form-group">
                            <label for="githubToken">GitHub Token (Optional)</label>
                            <input type="password" id="githubToken" placeholder="ghp_xxxxxxxxxxxx">
                            <small>
                                A GitHub token with 'repo' scope is required for private repositories. 
                                <a href="https://github.com/settings/tokens" target="_blank">Generate one here</a>
                            </small>
                        </div>
                        <div class="form-group">
                            <label for="threshold">Quality Threshold</label>
                            <select id="threshold">
                                <option value="60">60% - Basic (Lenient)</option>
                                <option value="70" selected>70% - Standard (Recommended)</option>
                                <option value="80">80% - High (Strict)</option>
                                <option value="90">90% - Enterprise (Very Strict)</option>
                            </select>
                        </div>

                        <div class="form-actions">
                            <button id="scanButton" onclick="startAssessment()">Start Assessment</button>
                            <button class="secondary" onclick="testConnection()">Test API Connection</button>
                        </div>
                    </div>

                    <div id="status" class="status hidden"></div>
                    <div id="results" class="results" style="display: none;"></div>
                </div>
                <script src="${scriptUri}"></script>
            </body>
            </html>`;
    }
    dispose() {
        CodeGatesAssessmentPanel.currentPanel = undefined;
        this.panel.dispose();
    }
}
function activate(context) {
    let assessDisposable = vscode.commands.registerCommand('codegates.assess', () => {
        CodeGatesAssessmentPanel.createOrShow(context.extensionUri);
    });
    let configureDisposable = vscode.commands.registerCommand('codegates.configure', () => {
        // Open VS Code settings for CodeGates
        vscode.commands.executeCommand('workbench.action.openSettings', 'codegates');
    });
    context.subscriptions.push(assessDisposable, configureDisposable);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map