import * as vscode from 'vscode';
import { ScanResult, GateScore } from '../runners/codeGatesRunner';

export class GateTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly gate?: GateScore,
        public readonly contextValue?: string
    ) {
        super(label, collapsibleState);
        
        if (gate) {
            this.tooltip = `${gate.gate}: ${gate.score}% (${gate.found}/${gate.expected})`;
            this.description = `${gate.score}%`;
            
            // Set icon based on status
            switch (gate.status) {
                case 'PASSED':
                    this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('testing.iconPassed'));
                    break;
                case 'WARNING':
                    this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('testing.iconQueued'));
                    break;
                case 'FAILED':
                    this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconFailed'));
                    break;
            }
            
            this.contextValue = 'gate';
            
            // Add command to show gate details
            this.command = {
                command: 'codegates.showGateDetails',
                title: 'Show Gate Details',
                arguments: [gate]
            };
        }
    }
}

export class GatesTreeProvider implements vscode.TreeDataProvider<GateTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<GateTreeItem | undefined | null | void> = new vscode.EventEmitter<GateTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<GateTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private scanResult: ScanResult | null = null;

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateResults(result: ScanResult): void {
        this.scanResult = result;
        this.refresh();
    }

    getTreeItem(element: GateTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: GateTreeItem): Thenable<GateTreeItem[]> {
        if (!this.scanResult) {
            return Promise.resolve([]);
        }

        if (!element) {
            // Root level - show categories
            return Promise.resolve([
                new GateTreeItem('Critical Gates', vscode.TreeItemCollapsibleState.Expanded, undefined, 'category'),
                new GateTreeItem('High Priority Gates', vscode.TreeItemCollapsibleState.Expanded, undefined, 'category'),
                new GateTreeItem('Medium Priority Gates', vscode.TreeItemCollapsibleState.Collapsed, undefined, 'category')
            ]);
        }

        // Show gates by category
        const gates = this.scanResult.gate_scores || [];
        
        switch (element.label) {
            case 'Critical Gates':
                return Promise.resolve(
                    gates
                        .filter(gate => this.getGateWeight(gate.gate) >= 1.8)
                        .map(gate => new GateTreeItem(
                            this.formatGateName(gate.gate),
                            vscode.TreeItemCollapsibleState.None,
                            gate
                        ))
                );
            
            case 'High Priority Gates':
                return Promise.resolve(
                    gates
                        .filter(gate => this.getGateWeight(gate.gate) >= 1.4 && this.getGateWeight(gate.gate) < 1.8)
                        .map(gate => new GateTreeItem(
                            this.formatGateName(gate.gate),
                            vscode.TreeItemCollapsibleState.None,
                            gate
                        ))
                );
            
            case 'Medium Priority Gates':
                return Promise.resolve(
                    gates
                        .filter(gate => this.getGateWeight(gate.gate) < 1.4)
                        .map(gate => new GateTreeItem(
                            this.formatGateName(gate.gate),
                            vscode.TreeItemCollapsibleState.None,
                            gate
                        ))
                );
            
            default:
                return Promise.resolve([]);
        }
    }

    private formatGateName(gateName: string): string {
        return gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    private getGateWeight(gateName: string): number {
        const weights: { [key: string]: number } = {
            'structured_logs': 2.0,
            'avoid_logging_secrets': 2.0,
            'audit_trail': 1.8,
            'error_logs': 1.8,
            'circuit_breakers': 1.7,
            'timeouts': 1.6,
            'ui_errors': 1.5,
            'correlation_id': 1.5,
            'automated_tests': 1.5,
            'ui_error_tools': 1.4,
            'retry_logic': 1.4,
            'api_logs': 1.3,
            'throttling': 1.3,
            'background_jobs': 1.2,
            'http_codes': 1.2
        };
        
        return weights[gateName] || 1.0;
    }
} 