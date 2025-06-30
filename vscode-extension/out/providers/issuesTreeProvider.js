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
exports.IssuesTreeProvider = exports.IssueTreeItem = void 0;
const vscode = __importStar(require("vscode"));
class IssueTreeItem extends vscode.TreeItem {
    constructor(label, collapsibleState, issue, contextValue) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.issue = issue;
        this.contextValue = contextValue;
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
                            selection: new vscode.Range(Math.max(0, (issue.line || 1) - 1), issue.column || 0, Math.max(0, (issue.line || 1) - 1), (issue.column || 0) + 10)
                        }
                    ]
                };
            }
        }
    }
}
exports.IssueTreeItem = IssueTreeItem;
class IssuesTreeProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.scanResult = null;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    updateResults(result) {
        this.scanResult = result;
        this.refresh();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!this.scanResult) {
            return Promise.resolve([]);
        }
        if (!element) {
            // Root level - show severity categories
            const issues = this.scanResult.issues || [];
            const errorCount = issues.filter(i => i.severity === 'error').length;
            const warningCount = issues.filter(i => i.severity === 'warning').length;
            const infoCount = issues.filter(i => i.severity === 'info').length;
            const categories = [];
            if (errorCount > 0) {
                categories.push(new IssueTreeItem(`Errors (${errorCount})`, vscode.TreeItemCollapsibleState.Expanded, undefined, 'severity'));
            }
            if (warningCount > 0) {
                categories.push(new IssueTreeItem(`Warnings (${warningCount})`, vscode.TreeItemCollapsibleState.Expanded, undefined, 'severity'));
            }
            if (infoCount > 0) {
                categories.push(new IssueTreeItem(`Info (${infoCount})`, vscode.TreeItemCollapsibleState.Collapsed, undefined, 'severity'));
            }
            return Promise.resolve(categories);
        }
        // Show issues by severity
        const issues = this.scanResult.issues || [];
        if (element.label.startsWith('Errors')) {
            return Promise.resolve(issues
                .filter(issue => issue.severity === 'error')
                .map(issue => new IssueTreeItem(`${this.formatGateName(issue.gate)}: ${issue.message}`, vscode.TreeItemCollapsibleState.None, issue)));
        }
        else if (element.label.startsWith('Warnings')) {
            return Promise.resolve(issues
                .filter(issue => issue.severity === 'warning')
                .map(issue => new IssueTreeItem(`${this.formatGateName(issue.gate)}: ${issue.message}`, vscode.TreeItemCollapsibleState.None, issue)));
        }
        else if (element.label.startsWith('Info')) {
            return Promise.resolve(issues
                .filter(issue => issue.severity === 'info')
                .map(issue => new IssueTreeItem(`${this.formatGateName(issue.gate)}: ${issue.message}`, vscode.TreeItemCollapsibleState.None, issue)));
        }
        return Promise.resolve([]);
    }
    formatGateName(gateName) {
        return gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
}
exports.IssuesTreeProvider = IssuesTreeProvider;
//# sourceMappingURL=issuesTreeProvider.js.map