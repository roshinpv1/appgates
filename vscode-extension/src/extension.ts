import * as vscode from 'vscode';
import { ApiRunner } from './runners/apiRunner';
import { ConfigurationManager } from './utils/configurationManager';
import { NotificationManager } from './utils/notificationManager';
import { ScanOptions } from './types/api';

class CodeGatesScanPanel {
    public static currentPanel: CodeGatesScanPanel | undefined;
    private readonly panel: vscode.WebviewPanel;
    private readonly extensionUri: vscode.Uri;
    private apiRunner: ApiRunner;
    private configManager: ConfigurationManager;
    private notificationManager: NotificationManager;

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        if (CodeGatesScanPanel.currentPanel) {
            CodeGatesScanPanel.currentPanel.panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'codegatesScan',
            'CodeGates Repository Scan',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        CodeGatesScanPanel.currentPanel = new CodeGatesScanPanel(panel, extensionUri);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this.panel = panel;
        this.extensionUri = extensionUri;
        this.configManager = new ConfigurationManager();
        this.notificationManager = new NotificationManager();
        this.apiRunner = new ApiRunner(this.configManager, this.notificationManager);

        this.update();

        this.panel.onDidDispose(() => this.dispose(), null);

        this.panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.command) {
                    case 'testConnection':
                        await this.handleTestConnection();
                        break;
                    case 'scan':
                        await this.handleScan(message.data);
                        break;
                    case 'generateHtmlReport':
                        await this.handleGenerateHtmlReport(message.data);
                        break;
                    case 'updateComments':
                        this.handleUpdateComments(message.data);
                        break;
                }
            }
        );
    }

    private async handleTestConnection() {
        try {
            const isConnected = await this.apiRunner.testConnection();
            this.panel.webview.postMessage({
                command: 'connectionResult',
                data: { connected: isConnected }
            });
        } catch (error) {
            this.panel.webview.postMessage({
                command: 'connectionResult',
                data: { connected: false, error: error instanceof Error ? error.message : 'Unknown error' }
            });
        }
    }

    private async handleScan(scanData: any) {
        try {
            this.panel.webview.postMessage({
                command: 'scanStarted',
                data: { message: 'Starting repository scan...' }
            });

            // Test connection first
            try {
                const isConnected = await this.apiRunner.testConnection();
                if (!isConnected) {
                    throw new Error('API server connection failed');
                }
            } catch (connectionError: any) {
                // Show user-friendly error dialog
                const startServer = await vscode.window.showErrorMessage(
                    'Failed to connect to API server. ' +
                    'To start the API server:\n1. Open terminal in VS Code (Terminal → New Terminal)\n2. Run: python3 start_server.py\n3. Wait for "Server started" message\n4. Try the scan again',
                    'Start Server',
                    'Show Instructions',
                    'Continue Anyway'
                );
                
                if (startServer === 'Start Server') {
                    // Start API server
                    const terminal = vscode.window.createTerminal('MyGates API Server');
                    terminal.show();
                    terminal.sendText('python3 start_server.py');
                    
                    vscode.window.showInformationMessage(
                        'Starting API server in terminal. Please wait for it to start, then try the scan again.'
                    );
                    
                    this.panel.webview.postMessage({
                        command: 'scanError',
                        data: { error: 'API server is starting. Please wait and try again in a few seconds.' }
                    });
                    return;
                } else if (startServer === 'Show Instructions') {
                    vscode.window.showInformationMessage(
                        'To start the API server:\n1. Open terminal in VS Code (Terminal → New Terminal)\n2. Run: python3 start_server.py\n3. Wait for "Server started" message\n4. Try the scan again'
                    );
                    
                    this.panel.webview.postMessage({
                        command: 'scanError',
                        data: { error: 'Please start the API server first. See the notification for instructions.' }
                    });
                    return;
                } else if (startServer !== 'Continue Anyway') {
                    this.panel.webview.postMessage({
                        command: 'scanError',
                        data: { error: 'API server connection required for scanning.' }
                    });
                    return;
                }
            }

            const options: ScanOptions = {
                threshold: scanData.threshold || 70
            };

            this.panel.webview.postMessage({
                command: 'scanProgress',
                data: { message: 'Connecting to repository...' }
            });

            const result = await this.apiRunner.scanRepository(
                scanData.repositoryUrl,
                scanData.branch || 'main',
                scanData.githubToken,
                options
            );

            // Add repository URL to result for better display
            result.repository_url = scanData.repositoryUrl;

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
                    
                    // Extract just the body content (remove html/head tags for embedding)
                    const bodyMatch = htmlContent.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
                    const reportContent = bodyMatch ? bodyMatch[1] : htmlContent;
                    
                    // Send server-generated content to webview
                    this.panel.webview.postMessage({
                        command: 'showResults',
                        data: {
                            ...result,
                            htmlContent: reportContent,
                            canGenerateReport: true
                        }
                    });
                    
                    console.log('Successfully loaded server-generated HTML content');
                    
                } catch (error: any) {
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

        } catch (error: any) {
            console.error('Scan error:', error);
            
            let errorMessage = error.message || 'Unknown error occurred';
            
            // Provide helpful error messages
            if (errorMessage.includes('Repository is private')) {
                errorMessage = 'This repository is private. Please provide a GitHub token with "repo" scope access.';
            } else if (errorMessage.includes('Invalid GitHub token')) {
                errorMessage = 'The GitHub token is invalid or expired. Please generate a new token with "repo" scope.';
            } else if (errorMessage.includes('Cannot access repository')) {
                errorMessage = 'Cannot access this repository. Check if the URL is correct and the token has proper permissions.';
            } else if (errorMessage.includes('ECONNREFUSED')) {
                errorMessage = 'Cannot connect to API server. Please start the server first.';
            }
            
            this.panel.webview.postMessage({
                command: 'scanError',
                data: { error: errorMessage }
            });
            
            // Show notification for critical errors
            if (errorMessage.includes('API server')) {
                vscode.window.showErrorMessage(`CodeGates: ${errorMessage}`);
            }
        }
    }

    private async handleGenerateHtmlReport(data: any) {
        try {
            // Get a better default path - use workspace folder or home directory
            let defaultUri: vscode.Uri;
            
            if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
                // Use the workspace folder if available
                defaultUri = vscode.Uri.joinPath(vscode.workspace.workspaceFolders[0].uri, 'codegates-report.html');
            } else {
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
            const openFile = await vscode.window.showInformationMessage(
                `HTML report generated successfully: ${saveUri.fsPath}`,
                'Open Report',
                'Open in Browser'
            );
            
            if (openFile === 'Open Report') {
                vscode.window.showTextDocument(saveUri);
            } else if (openFile === 'Open in Browser') {
                vscode.env.openExternal(saveUri);
            }
            
        } catch (error: any) {
            console.error('Generate HTML report error:', error);
            vscode.window.showErrorMessage(`Failed to generate HTML report: ${error.message}`);
        }
    }

    private async fetchHtmlReportFromServer(scanId: string, comments: any): Promise<string> {
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
            
        } catch (error: any) {
            console.error('Failed to fetch HTML report from server:', error);
            
            // Check if it's a server connection issue
            if (error.message.includes('ECONNREFUSED') || error.message.includes('connect')) {
                vscode.window.showWarningMessage(
                    'Server unavailable. Please start the API server to generate HTML reports.'
                );
                throw new Error('Server unavailable for HTML report generation. Please start the API server.');
            }
            
            throw new Error(`Failed to fetch report from server: ${error.message}`);
        }
    }

    private async handleUpdateComments(data: any) {
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
            
        } catch (error: any) {
            console.error('Failed to update comments:', error);
            
            // Show user-friendly error message
            if (error.message.includes('ECONNREFUSED') || error.message.includes('connect')) {
                vscode.window.showWarningMessage(
                    'Cannot update comments: API server is not available.'
                );
            } else {
                vscode.window.showWarningMessage(
                    `Failed to update comments: ${error.message}`
                );
            }
        }
    }

    private update() {
        if (this.panel) {
            this.panel.webview.html = this.getHtmlForWebview(this.panel.webview);
        }
    }

    private getHtmlForWebview(webview: vscode.Webview) {
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'main.js'));
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'style.css'));

        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleUri}" rel="stylesheet">
                <title>CodeGates Repository Scan</title>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>CodeGates Repository Scan</h1>
                        <p>Validate your repository against production-ready quality gates</p>
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
                            <small>The branch to scan, defaults to 'main' if not specified</small>
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
                            <button id="scanButton" onclick="startScan()">Start Scan</button>
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

    public dispose() {
        CodeGatesScanPanel.currentPanel = undefined;
        this.panel.dispose();
    }
}

export function activate(context: vscode.ExtensionContext) {
    let scanDisposable = vscode.commands.registerCommand('codegates.scan', () => {
        CodeGatesScanPanel.createOrShow(context.extensionUri);
    });

    let configureDisposable = vscode.commands.registerCommand('codegates.configure', () => {
        // Open VS Code settings for CodeGates
        vscode.commands.executeCommand('workbench.action.openSettings', 'codegates');
    });

    // Add debug command to test configuration
    let debugConfigDisposable = vscode.commands.registerCommand('codegates.debugConfig', () => {
        const configManager = new ConfigurationManager();
        const config = configManager.getAll();
        
        const message = `CodeGates Configuration:
API URL: ${config.apiUrl}
API Timeout: ${config.apiTimeout}
API Retries: ${config.apiRetries}

Settings inspection:
${JSON.stringify(config, null, 2)}`;
        
        vscode.window.showInformationMessage('Configuration details logged to console');
        console.log(message);
        
        // Also show in output channel
        const outputChannel = vscode.window.createOutputChannel('CodeGates Config');
        outputChannel.clear();
        outputChannel.appendLine(message);
        outputChannel.show();
    });

    context.subscriptions.push(scanDisposable, configureDisposable, debugConfigDisposable);
}

export function deactivate() {} 