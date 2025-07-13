import * as vscode from 'vscode';
import { CodeGatesRunner, ScanResult } from '../runners/codeGatesRunner';

export class CodeGatesProvider {
    private context: vscode.ExtensionContext;
    private runner: CodeGatesRunner;
    private lastScanResult: ScanResult | null = null;

    constructor(context: vscode.ExtensionContext, runner: CodeGatesRunner) {
        this.context = context;
        this.runner = runner;
    }

    public async scanWorkspace(): Promise<ScanResult | null> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showErrorMessage('No workspace folder found');
            return null;
        }

        const workspacePath = workspaceFolders[0].uri.fsPath;
        
        try {
            const result = await this.runner.scanWorkspace(workspacePath);
            this.lastScanResult = result;
            return result;
        } catch (error) {
            vscode.window.showErrorMessage(`CodeGates scan failed: ${error}`);
            return null;
        }
    }

    public async scanFile(filePath: string): Promise<ScanResult | null> {
        try {
            const result = await this.runner.scanFile(filePath);
            return result;
        } catch (error) {
            vscode.window.showErrorMessage(`CodeGates file scan failed: ${error}`);
            return null;
        }
    }

    public getLastScanResult(): ScanResult | null {
        return this.lastScanResult;
    }

    public async testConnection(): Promise<boolean> {
        try {
            return await this.runner.testConnection();
        } catch (error) {
            return false;
        }
    }

    public createDiagnostics(result: ScanResult, uri: vscode.Uri): vscode.Diagnostic[] {
        const diagnostics: vscode.Diagnostic[] = [];
        
        if (result.gate_scores) {
            result.gate_scores.forEach((gate) => {
                if (gate.status === 'FAILED' && gate.issues) {
                    gate.issues.forEach((issue) => {
                        const range = new vscode.Range(
                            Math.max(0, (issue.line || 1) - 1),
                            issue.column || 0,
                            Math.max(0, (issue.line || 1) - 1),
                            (issue.column || 0) + 10
                        );
                        
                        const diagnostic = new vscode.Diagnostic(
                            range,
                            `CodeGates - ${gate.gate}: ${issue.message}`,
                            this.getSeverity(issue.severity)
                        );
                        
                        diagnostic.source = 'CodeGates';
                        diagnostic.code = gate.gate;
                        diagnostics.push(diagnostic);
                    });
                }
            });
        }
        
        return diagnostics;
    }

    private getSeverity(severity: string): vscode.DiagnosticSeverity {
        switch (severity) {
            case 'error':
                return vscode.DiagnosticSeverity.Error;
            case 'warning':
                return vscode.DiagnosticSeverity.Warning;
            case 'info':
                return vscode.DiagnosticSeverity.Information;
            default:
                return vscode.DiagnosticSeverity.Warning;
        }
    }

    public getGateStatusIcon(status: string): string {
        switch (status) {
            case 'PASSED':
                return '✅';
            case 'WARNING':
                return '⚠️';
            case 'FAILED':
                return '❌';
            default:
                return '❓';
        }
    }

    public getScoreColor(score: number): string {
        if (score >= 80) return '#28a745';
        if (score >= 60) return '#ffc107';
        return '#dc3545';
    }

    public formatGateName(gateName: string): string {
        return gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
} 