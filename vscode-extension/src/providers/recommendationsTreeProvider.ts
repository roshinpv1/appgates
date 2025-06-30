import * as vscode from 'vscode';
import { ScanResult } from '../runners/codeGatesRunner';

export class RecommendationTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly recommendation?: string,
        public readonly contextValue?: string
    ) {
        super(label, collapsibleState);
        
        if (recommendation) {
            this.tooltip = recommendation;
            this.iconPath = new vscode.ThemeIcon('lightbulb', new vscode.ThemeColor('editorLightBulb.foreground'));
            this.contextValue = 'recommendation';
        } else {
            this.iconPath = new vscode.ThemeIcon('list-unordered');
        }
    }
}

export class RecommendationsTreeProvider implements vscode.TreeDataProvider<RecommendationTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<RecommendationTreeItem | undefined | null | void> = new vscode.EventEmitter<RecommendationTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<RecommendationTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private scanResult: ScanResult | null = null;

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateResults(result: ScanResult): void {
        this.scanResult = result;
        this.refresh();
    }

    getTreeItem(element: RecommendationTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: RecommendationTreeItem): Thenable<RecommendationTreeItem[]> {
        if (!this.scanResult) {
            return Promise.resolve([]);
        }

        if (!element) {
            // Root level - show categories
            const gateRecommendations = this.getGateRecommendations();
            const generalRecommendations = this.scanResult.recommendations || [];

            const categories: RecommendationTreeItem[] = [];
            
            if (gateRecommendations.length > 0) {
                categories.push(new RecommendationTreeItem(
                    `Gate-Specific (${gateRecommendations.length})`,
                    vscode.TreeItemCollapsibleState.Expanded,
                    undefined,
                    'category'
                ));
            }
            
            if (generalRecommendations.length > 0) {
                categories.push(new RecommendationTreeItem(
                    `General (${generalRecommendations.length})`,
                    vscode.TreeItemCollapsibleState.Expanded,
                    undefined,
                    'category'
                ));
            }

            return Promise.resolve(categories);
        }

        // Show recommendations by category
        if (element.label.startsWith('Gate-Specific')) {
            const gateRecommendations = this.getGateRecommendations();
            return Promise.resolve(
                gateRecommendations.map((rec, index) => new RecommendationTreeItem(
                    `${rec.gate}: ${rec.recommendation.substring(0, 50)}${rec.recommendation.length > 50 ? '...' : ''}`,
                    vscode.TreeItemCollapsibleState.None,
                    rec.recommendation
                ))
            );
        } else if (element.label.startsWith('General')) {
            const generalRecommendations = this.scanResult!.recommendations || [];
            return Promise.resolve(
                generalRecommendations.map((rec, index) => new RecommendationTreeItem(
                    rec.length > 60 ? `${rec.substring(0, 60)}...` : rec,
                    vscode.TreeItemCollapsibleState.None,
                    rec
                ))
            );
        }

        return Promise.resolve([]);
    }

    private getGateRecommendations(): Array<{ gate: string; recommendation: string }> {
        if (!this.scanResult || !this.scanResult.gate_scores) {
            return [];
        }

        const gateRecommendations: Array<{ gate: string; recommendation: string }> = [];
        
        for (const gateScore of this.scanResult.gate_scores) {
            if (gateScore.recommendations && gateScore.recommendations.length > 0) {
                for (const recommendation of gateScore.recommendations) {
                    gateRecommendations.push({
                        gate: this.formatGateName(gateScore.gate),
                        recommendation
                    });
                }
            }
        }

        return gateRecommendations;
    }

    private formatGateName(gateName: string): string {
        return gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
} 