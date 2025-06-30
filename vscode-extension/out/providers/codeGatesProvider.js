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
exports.CodeGatesProvider = void 0;
const vscode = __importStar(require("vscode"));
class CodeGatesProvider {
    constructor(context, runner) {
        this.lastScanResult = null;
        this.context = context;
        this.runner = runner;
    }
    async scanWorkspace() {
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
        }
        catch (error) {
            vscode.window.showErrorMessage(`CodeGates scan failed: ${error}`);
            return null;
        }
    }
    async scanFile(filePath) {
        try {
            const result = await this.runner.scanFile(filePath);
            return result;
        }
        catch (error) {
            vscode.window.showErrorMessage(`CodeGates file scan failed: ${error}`);
            return null;
        }
    }
    getLastScanResult() {
        return this.lastScanResult;
    }
    async testConnection() {
        try {
            return await this.runner.testConnection();
        }
        catch (error) {
            return false;
        }
    }
    createDiagnostics(result, uri) {
        const diagnostics = [];
        if (result.gate_scores) {
            result.gate_scores.forEach((gate) => {
                if (gate.status === 'FAILED' && gate.issues) {
                    gate.issues.forEach((issue) => {
                        const range = new vscode.Range(Math.max(0, (issue.line || 1) - 1), issue.column || 0, Math.max(0, (issue.line || 1) - 1), (issue.column || 0) + 10);
                        const diagnostic = new vscode.Diagnostic(range, `CodeGates - ${gate.gate}: ${issue.message}`, this.getSeverity(issue.severity));
                        diagnostic.source = 'CodeGates';
                        diagnostic.code = gate.gate;
                        diagnostics.push(diagnostic);
                    });
                }
            });
        }
        return diagnostics;
    }
    getSeverity(severity) {
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
    getGateStatusIcon(status) {
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
    getScoreColor(score) {
        if (score >= 80)
            return '#28a745';
        if (score >= 60)
            return '#ffc107';
        return '#dc3545';
    }
    formatGateName(gateName) {
        return gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
}
exports.CodeGatesProvider = CodeGatesProvider;
//# sourceMappingURL=codeGatesProvider.js.map