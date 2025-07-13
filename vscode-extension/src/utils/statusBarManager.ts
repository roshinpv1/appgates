import * as vscode from 'vscode';
import { ScanResult } from '../runners/codeGatesRunner';

export class StatusBarManager implements vscode.Disposable {
    private statusBarItem: vscode.StatusBarItem;
    private scanResult: ScanResult | null = null;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        
        this.statusBarItem.command = 'codegates.scan';
        this.statusBarItem.tooltip = 'Click to run CodeGates scan';
        this.updateStatusBar();
        this.statusBarItem.show();
    }

    public updateScanResult(result: ScanResult): void {
        this.scanResult = result;
        this.updateStatusBar();
    }

    public showProgress(message: string): void {
        this.statusBarItem.text = `$(sync~spin) CodeGates: ${message}`;
        this.statusBarItem.tooltip = 'CodeGates scan in progress...';
        this.statusBarItem.command = undefined;
    }

    public hideProgress(): void {
        this.updateStatusBar();
    }

    private updateStatusBar(): void {
        if (!this.scanResult) {
            this.statusBarItem.text = '$(shield) CodeGates';
            this.statusBarItem.tooltip = 'Click to run CodeGates scan';
            this.statusBarItem.command = 'codegates.scan';
            this.statusBarItem.backgroundColor = undefined;
            return;
        }

        const score = Math.round(this.scanResult.overall_score || 0);
        const statusIcon = score >= 80 ? '$(check)' : score >= 60 ? '$(warning)' : '$(error)';
        const statusColor = score >= 80 ? undefined : 
                          score >= 60 ? new vscode.ThemeColor('statusBarItem.warningBackground') :
                          new vscode.ThemeColor('statusBarItem.errorBackground');

        this.statusBarItem.text = `${statusIcon} CodeGates: ${score}%`;
        this.statusBarItem.tooltip = this.createTooltip();
        this.statusBarItem.command = 'codegates.showReport';
        this.statusBarItem.backgroundColor = statusColor;
    }

    private createTooltip(): string {
        if (!this.scanResult) {
            return 'Click to run CodeGates scan';
        }

        const score = Math.round(this.scanResult.overall_score || 0);
        const passedGates = this.scanResult.gate_scores?.filter(g => g.status === 'PASSED').length || 0;
        const warningGates = this.scanResult.gate_scores?.filter(g => g.status === 'WARNING').length || 0;
        const failedGates = this.scanResult.gate_scores?.filter(g => g.status === 'FAILED').length || 0;
        const totalGates = this.scanResult.gate_scores?.length || 0;

        const status = score >= 80 ? 'Production Ready' : 
                      score >= 60 ? 'Needs Improvement' : 
                      'Not Production Ready';

        return [
            `CodeGates Analysis Results`,
            `Overall Score: ${score}% (${status})`,
            ``,
            `Gates: ${passedGates} passed, ${warningGates} warning, ${failedGates} failed`,
            `Project: ${this.scanResult.project_name}`,
            ``,
            `Click to view detailed report`
        ].join('\n');
    }

    public dispose(): void {
        this.statusBarItem.dispose();
    }
} 