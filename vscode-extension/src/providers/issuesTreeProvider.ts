import * as vscode from 'vscode';
import { ScanResult, Issue } from '../runners/codeGatesRunner';

export class IssueTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly issue?: Issue,
        public readonly contextValue?: string
    ) {
        super(label, collapsibleState);
        
        if (issue) {
            this.tooltip = `${issue.gate}: ${issue.message}`;
            this.description = issue.file ? `Line ${issue.line || 1}` : '';
            
            // Set icon based on severity
            switch (issue.severity) {
                case 'error':
                    this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
                    break;
                case 'warning':
                    this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('editorWarning.foreground'));
                    break;
                case 'info':
                    this.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('editorInfo.foreground'));
                    break;
            }
            
            this.contextValue = 'issue';
            
            // Add command to navigate to issue location
            if (issue.file && issue.line) {
                this.command = {
                    command: 'vscode.open',
                    title: 'Go to Issue',
                    arguments: [
                        vscode.Uri.file(issue.file),
                        {
                            selection: new vscode.Range(
                                Math.max(0, (issue.line || 1) - 1),
                                issue.column || 0,
                                Math.max(0, (issue.line || 1) - 1),
                                (issue.column || 0) + 10
                            )
                        }
                    ]
                };
            }
        }
    }
}

export class IssuesTreeProvider implements vscode.TreeDataProvider<IssueTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<IssueTreeItem | undefined | null | void> = new vscode.EventEmitter<IssueTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<IssueTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private scanResult: ScanResult | null = null;

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateResults(result: ScanResult): void {
        this.scanResult = result;
        this.refresh();
    }

    getTreeItem(element: IssueTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: IssueTreeItem): Thenable<IssueTreeItem[]> {
        if (!this.scanResult) {
            return Promise.resolve([]);
        }

        if (!element) {
            // Root level - show severity categories
            const issues = this.scanResult.issues || [];
            const errorCount = issues.filter(i => i.severity === 'error').length;
            const warningCount = issues.filter(i => i.severity === 'warning').length;
            const infoCount = issues.filter(i => i.severity === 'info').length;

            const categories: IssueTreeItem[] = [];
            
            if (errorCount > 0) {
                categories.push(new IssueTreeItem(
                    `Errors (${errorCount})`,
                    vscode.TreeItemCollapsibleState.Expanded,
                    undefined,
                    'severity'
                ));
            }
            
            if (warningCount > 0) {
                categories.push(new IssueTreeItem(
                    `Warnings (${warningCount})`,
                    vscode.TreeItemCollapsibleState.Expanded,
                    undefined,
                    'severity'
                ));
            }
            
            if (infoCount > 0) {
                categories.push(new IssueTreeItem(
                    `Info (${infoCount})`,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    undefined,
                    'severity'
                ));
            }

            return Promise.resolve(categories);
        }

        // Show issues by severity
        const issues = this.scanResult.issues || [];
        
        if (element.label.startsWith('Errors')) {
            return Promise.resolve(
                issues
                    .filter(issue => issue.severity === 'error')
                    .map(issue => new IssueTreeItem(
                        `${this.formatGateName(issue.gate)}: ${issue.message}`,
                        vscode.TreeItemCollapsibleState.None,
                        issue
                    ))
            );
        } else if (element.label.startsWith('Warnings')) {
            return Promise.resolve(
                issues
                    .filter(issue => issue.severity === 'warning')
                    .map(issue => new IssueTreeItem(
                        `${this.formatGateName(issue.gate)}: ${issue.message}`,
                        vscode.TreeItemCollapsibleState.None,
                        issue
                    ))
            );
        } else if (element.label.startsWith('Info')) {
            return Promise.resolve(
                issues
                    .filter(issue => issue.severity === 'info')
                    .map(issue => new IssueTreeItem(
                        `${this.formatGateName(issue.gate)}: ${issue.message}`,
                        vscode.TreeItemCollapsibleState.None,
                        issue
                    ))
            );
        }

        return Promise.resolve([]);
    }

    private formatGateName(gateName: string): string {
        return gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
} 