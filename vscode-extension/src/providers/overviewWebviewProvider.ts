import * as vscode from 'vscode';
import { ScanResult } from '../runners/codeGatesRunner';

export class OverviewWebviewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'codegatesOverview';

    private _view?: vscode.WebviewView;
    private _scanResult?: ScanResult;
    private _extensionUri: vscode.Uri;

    constructor(extensionUri: vscode.Uri) {
        this._extensionUri = extensionUri;
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        this.updateView();

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'scan':
                        vscode.commands.executeCommand('codegates.scan');
                        break;
                    case 'configure':
                        vscode.commands.executeCommand('codegates.configure');
                        break;
                    case 'showReport':
                        vscode.commands.executeCommand('codegates.showReport');
                        break;
                    case 'showGateDetails':
                        if (message.gate) {
                            vscode.commands.executeCommand('codegates.showGateDetails', message.gate);
                        }
                        break;
                }
            },
            undefined,
            []
        );
    }

    public updateResults(result: ScanResult) {
        this._scanResult = result;
        this.updateView();
    }

    private updateView() {
        if (this._view) {
            this._view.webview.html = this.getWebviewContent();
        }
    }

    private getWebviewContent(): string {
        if (!this._scanResult) {
            return this.getWelcomeContent();
        }

        return this.getResultsContent(this._scanResult);
    }

    private getWelcomeContent(): string {
        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CodeGates Overview</title>
            <style>
                ${this.getCommonStyles()}
                
                .welcome-container {
                    text-align: center;
                    padding: 40px 20px;
                }
                
                .welcome-icon {
                    font-size: 4em;
                    margin-bottom: 20px;
                }
                
                .welcome-title {
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #1f2937;
                    margin-bottom: 15px;
                }
                
                .welcome-subtitle {
                    color: #6b7280;
                    margin-bottom: 30px;
                    line-height: 1.6;
                }
                
                .action-buttons {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    max-width: 200px;
                    margin: 0 auto;
                }
                
                .action-button {
                    background: #2563eb;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: background-color 0.2s;
                }
                
                .action-button:hover {
                    background: #1d4ed8;
                }
                
                .action-button.secondary {
                    background: #6b7280;
                }
                
                .action-button.secondary:hover {
                    background: #4b5563;
                }
            </style>
        </head>
        <body>
            <div class="welcome-container">
                <div class="welcome-icon">🛡️</div>
                <div class="welcome-title">Welcome to CodeGates</div>
                <div class="welcome-subtitle">
                    Production-ready hard gate validation for enterprise-grade code quality.
                    Start by scanning your workspace to identify areas for improvement.
                </div>
                <div class="action-buttons">
                    <button class="action-button" onclick="scan()">
                        🔍 Scan Workspace
                    </button>
                    <button class="action-button secondary" onclick="configure()">
                        ⚙️ Configure Settings
                    </button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                
                function scan() {
                    vscode.postMessage({ command: 'scan' });
                }
                
                function configure() {
                    vscode.postMessage({ command: 'configure' });
                }
            </script>
        </body>
        </html>`;
    }

    private getResultsContent(result: ScanResult): string {
        const totalGates = result.gate_scores?.length || 0;
        const passedGates = result.gate_scores?.filter(g => g.status === 'PASSED').length || 0;
        const warningGates = result.gate_scores?.filter(g => g.status === 'WARNING').length || 0;
        const failedGates = result.gate_scores?.filter(g => g.status === 'FAILED').length || 0;
        
        const compliancePercentage = totalGates > 0 ? (passedGates / totalGates * 100) : 0;
        const overallScore = result.overall_score || 0;

        // Generate gate categories
        const gateCategories = this.generateGateCategories(result);

        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CodeGates Results</title>
            <style>
                ${this.getCommonStyles()}
                
                .results-container {
                    padding: 20px;
                }
                
                .project-header {
                    border-bottom: 3px solid #2563eb;
                    padding-bottom: 15px;
                    margin-bottom: 30px;
                }
                
                .project-title {
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #1f2937;
                    margin-bottom: 5px;
                }
                
                .project-subtitle {
                    color: #2563eb;
                    font-weight: 500;
                }
                
                .summary-stats {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }
                
                .stat-card {
                    background: #fff;
                    padding: 15px;
                    border-radius: 8px;
                    border: 1px solid #e5e7eb;
                    text-align: center;
                    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
                }
                
                .stat-number {
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #2563eb;
                }
                
                .stat-label {
                    color: #6b7280;
                    font-size: 0.9em;
                    margin-top: 5px;
                }
                
                .compliance-section {
                    margin: 20px 0;
                }
                
                .compliance-bar {
                    width: 100%;
                    height: 16px;
                    background: #e5e7eb;
                    border-radius: 8px;
                    overflow: hidden;
                    margin: 10px 0;
                }
                
                .compliance-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #dc2626 0%, #d97706 50%, #059669 100%);
                    transition: width 0.3s ease;
                }
                
                .compliance-text {
                    font-weight: bold;
                    color: #374151;
                }
                
                .category-section {
                    margin: 25px 0;
                }
                
                .category-title {
                    font-weight: bold;
                    color: #374151;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #e5e7eb;
                    padding-bottom: 5px;
                }
                
                .gate-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    margin: 5px 0;
                    background: #f9fafb;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                
                .gate-item:hover {
                    background: #f3f4f6;
                }
                
                .gate-name {
                    font-weight: 500;
                    color: #374151;
                    flex: 1;
                }
                
                .gate-status {
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 0.8em;
                    font-weight: 500;
                }
                
                .status-passed {
                    color: #059669;
                    background: #ecfdf5;
                }
                
                .status-warning {
                    color: #d97706;
                    background: #fffbeb;
                }
                
                .status-failed {
                    color: #dc2626;
                    background: #fef2f2;
                }
                
                .action-buttons {
                    display: flex;
                    gap: 10px;
                    margin-top: 20px;
                }
                
                .action-button {
                    flex: 1;
                    background: #2563eb;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    font-size: 0.9em;
                    transition: background-color 0.2s;
                }
                
                .action-button:hover {
                    background: #1d4ed8;
                }
                
                .action-button.secondary {
                    background: #6b7280;
                }
                
                .action-button.secondary:hover {
                    background: #4b5563;
                }
            </style>
        </head>
        <body>
            <div class="results-container">
                <div class="project-header">
                    <div class="project-title">${result.project_name || 'Unknown Project'}</div>
                    <div class="project-subtitle">Hard Gate Assessment Results</div>
                </div>

                <div class="summary-stats">
                    <div class="stat-card">
                        <div class="stat-number">${totalGates}</div>
                        <div class="stat-label">Total Gates</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${passedGates}</div>
                        <div class="stat-label">Gates Met</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${warningGates}</div>
                        <div class="stat-label">Partially Met</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${failedGates}</div>
                        <div class="stat-label">Not Met</div>
                    </div>
                </div>

                <div class="compliance-section">
                    <div class="compliance-bar">
                        <div class="compliance-fill" style="width: ${compliancePercentage}%"></div>
                    </div>
                    <div class="compliance-text">${compliancePercentage.toFixed(1)}% Hard Gates Compliance</div>
                </div>

                ${gateCategories}

                <div class="action-buttons">
                    <button class="action-button" onclick="showReport()">
                        📊 View Report
                    </button>
                    <button class="action-button secondary" onclick="scan()">
                        🔄 Rescan
                    </button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                
                function showReport() {
                    vscode.postMessage({ command: 'showReport' });
                }
                
                function scan() {
                    vscode.postMessage({ command: 'scan' });
                }
                
                function showGateDetails(gate) {
                    vscode.postMessage({ command: 'showGateDetails', gate: gate });
                }
            </script>
        </body>
        </html>`;
    }

    private generateGateCategories(result: ScanResult): string {
        const gateCategories = {
            'Auditability': [
                'structured_logs',
                'avoid_logging_secrets', 
                'audit_trail',
                'correlation_id',
                'api_logs',
                'background_jobs',
                'ui_errors'
            ],
            'Availability': [
                'retry_logic',
                'timeouts',
                'throttling',
                'circuit_breakers'
            ],
            'Error Handling': [
                'error_logs',
                'http_codes',
                'ui_error_tools'
            ],
            'Testing': [
                'automated_tests'
            ]
        };

        let categoriesHtml = '';

        for (const [category, gateNames] of Object.entries(gateCategories)) {
            const categoryGates = result.gate_scores?.filter(g => gateNames.includes(g.gate)) || [];
            
            if (categoryGates.length === 0) continue;

            let gatesHtml = '';
            for (const gate of categoryGates) {
                const gateName = this.formatGateName(gate.gate);
                const statusClass = this.getStatusClass(gate.status);
                const statusText = this.getStatusText(gate.status);

                gatesHtml += `
                    <div class="gate-item" onclick="showGateDetails(${JSON.stringify(gate).replace(/"/g, '&quot;')})">
                        <div class="gate-name">${gateName}</div>
                        <div class="gate-status ${statusClass}">${statusText}</div>
                    </div>
                `;
            }

            categoriesHtml += `
                <div class="category-section">
                    <div class="category-title">${category}</div>
                    ${gatesHtml}
                </div>
            `;
        }

        return categoriesHtml;
    }

    private formatGateName(gateName: string): string {
        const nameMapping: { [key: string]: string } = {
            'structured_logs': 'Logs Searchable Available',
            'avoid_logging_secrets': 'Avoid Logging Confidential Data',
            'audit_trail': 'Create Audit Trail Logs',
            'correlation_id': 'Tracking ID For Log Messages',
            'api_logs': 'Log Rest API Calls',
            'background_jobs': 'Log Application Messages',
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
        return nameMapping[gateName] || gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    private getStatusClass(status: string): string {
        switch (status) {
            case 'PASSED': return 'status-passed';
            case 'WARNING': return 'status-warning';
            default: return 'status-failed';
        }
    }

    private getStatusText(status: string): string {
        switch (status) {
            case 'PASSED': return '✓ Implemented';
            case 'WARNING': return '⚠ Partial';
            default: return '✗ Missing';
        }
    }

    private getCommonStyles(): string {
        return `
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #374151;
                margin: 0;
                padding: 0;
                background: #f9fafb;
            }
            
            * {
                box-sizing: border-box;
            }
        `;
    }
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
} 