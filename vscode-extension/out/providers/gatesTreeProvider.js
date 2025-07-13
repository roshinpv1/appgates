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
exports.GatesTreeProvider = exports.GateTreeItem = void 0;
const vscode = __importStar(require("vscode"));
class GateTreeItem extends vscode.TreeItem {
    constructor(label, collapsibleState, gate, contextValue) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.gate = gate;
        this.contextValue = contextValue;
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
exports.GateTreeItem = GateTreeItem;
class GatesTreeProvider {
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
                return Promise.resolve(gates
                    .filter(gate => this.getGateWeight(gate.gate) >= 1.8)
                    .map(gate => new GateTreeItem(this.formatGateName(gate.gate), vscode.TreeItemCollapsibleState.None, gate)));
            case 'High Priority Gates':
                return Promise.resolve(gates
                    .filter(gate => this.getGateWeight(gate.gate) >= 1.4 && this.getGateWeight(gate.gate) < 1.8)
                    .map(gate => new GateTreeItem(this.formatGateName(gate.gate), vscode.TreeItemCollapsibleState.None, gate)));
            case 'Medium Priority Gates':
                return Promise.resolve(gates
                    .filter(gate => this.getGateWeight(gate.gate) < 1.4)
                    .map(gate => new GateTreeItem(this.formatGateName(gate.gate), vscode.TreeItemCollapsibleState.None, gate)));
            default:
                return Promise.resolve([]);
        }
    }
    formatGateName(gateName) {
        return gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    getGateWeight(gateName) {
        const weights = {
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
exports.GatesTreeProvider = GatesTreeProvider;
//# sourceMappingURL=gatesTreeProvider.js.map