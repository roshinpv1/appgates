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
exports.StatusBarManager = void 0;
const vscode = __importStar(require("vscode"));
class StatusBarManager {
    constructor() {
        this.scanResult = null;
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.command = 'codegates.scan';
        this.statusBarItem.tooltip = 'Click to run CodeGates scan';
        this.updateStatusBar();
        this.statusBarItem.show();
    }
    updateScanResult(result) {
        this.scanResult = result;
        this.updateStatusBar();
    }
    showProgress(message) {
        this.statusBarItem.text = `$(sync~spin) CodeGates: ${message}`;
        this.statusBarItem.tooltip = 'CodeGates scan in progress...';
        this.statusBarItem.command = undefined;
    }
    hideProgress() {
        this.updateStatusBar();
    }
    updateStatusBar() {
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
    createTooltip() {
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
    dispose() {
        this.statusBarItem.dispose();
    }
}
exports.StatusBarManager = StatusBarManager;
//# sourceMappingURL=statusBarManager.js.map