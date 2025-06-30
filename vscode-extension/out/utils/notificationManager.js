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
exports.NotificationManager = void 0;
const vscode = __importStar(require("vscode"));
class NotificationManager {
    constructor() {
        this.level = this.getNotificationLevel();
        // Listen for configuration changes
        vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('codegates.notifications.level')) {
                this.level = this.getNotificationLevel();
            }
        });
    }
    getNotificationLevel() {
        const config = vscode.workspace.getConfiguration('codegates');
        return config.get('notifications.level', 'info');
    }
    shouldShow(messageLevel) {
        const levels = ['none', 'error', 'warning', 'info', 'verbose'];
        const currentLevelIndex = levels.indexOf(this.level);
        const messageLevelIndex = levels.indexOf(messageLevel);
        return currentLevelIndex >= messageLevelIndex && currentLevelIndex > 0;
    }
    showError(message, ...items) {
        if (!this.shouldShow('error')) {
            return Promise.resolve(undefined);
        }
        return vscode.window.showErrorMessage(`CodeGates: ${message}`, ...items);
    }
    showWarning(message, ...items) {
        if (!this.shouldShow('warning')) {
            return Promise.resolve(undefined);
        }
        return vscode.window.showWarningMessage(`CodeGates: ${message}`, ...items);
    }
    showInfo(message, ...items) {
        if (!this.shouldShow('info')) {
            return Promise.resolve(undefined);
        }
        return vscode.window.showInformationMessage(`CodeGates: ${message}`, ...items);
    }
    showVerbose(message) {
        if (this.shouldShow('verbose')) {
            console.log(`CodeGates: ${message}`);
        }
    }
    showProgress(title, task) {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `CodeGates: ${title}`,
            cancellable: true
        }, task);
    }
    showStatusBarMessage(message, hideAfterTimeout = 0) {
        if (hideAfterTimeout > 0) {
            return vscode.window.setStatusBarMessage(`CodeGates: ${message}`, hideAfterTimeout);
        }
        else {
            return vscode.window.setStatusBarMessage(`CodeGates: ${message}`);
        }
    }
}
exports.NotificationManager = NotificationManager;
//# sourceMappingURL=notificationManager.js.map