import * as vscode from 'vscode';

export type NotificationLevel = 'none' | 'error' | 'warning' | 'info' | 'verbose';

export class NotificationManager {
    private level: NotificationLevel;

    constructor() {
        this.level = this.getNotificationLevel();
        
        // Listen for configuration changes
        vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('codegates.notifications.level')) {
                this.level = this.getNotificationLevel();
            }
        });
    }

    private getNotificationLevel(): NotificationLevel {
        const config = vscode.workspace.getConfiguration('codegates');
        return config.get<NotificationLevel>('notifications.level', 'info');
    }

    private shouldShow(messageLevel: NotificationLevel): boolean {
        const levels: NotificationLevel[] = ['none', 'error', 'warning', 'info', 'verbose'];
        const currentLevelIndex = levels.indexOf(this.level);
        const messageLevelIndex = levels.indexOf(messageLevel);
        
        return currentLevelIndex >= messageLevelIndex && currentLevelIndex > 0;
    }

    showError(message: string, ...items: string[]): Thenable<string | undefined> {
        if (!this.shouldShow('error')) {
            return Promise.resolve(undefined);
        }
        return vscode.window.showErrorMessage(`CodeGates: ${message}`, ...items);
    }

    showWarning(message: string, ...items: string[]): Thenable<string | undefined> {
        if (!this.shouldShow('warning')) {
            return Promise.resolve(undefined);
        }
        return vscode.window.showWarningMessage(`CodeGates: ${message}`, ...items);
    }

    showInfo(message: string, ...items: string[]): Thenable<string | undefined> {
        if (!this.shouldShow('info')) {
            return Promise.resolve(undefined);
        }
        return vscode.window.showInformationMessage(`CodeGates: ${message}`, ...items);
    }

    showVerbose(message: string): void {
        if (this.shouldShow('verbose')) {
            console.log(`CodeGates: ${message}`);
        }
    }

    showProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ message?: string; increment?: number }>, token: vscode.CancellationToken) => Thenable<T>
    ): Thenable<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `CodeGates: ${title}`,
                cancellable: true
            },
            task
        );
    }

    showStatusBarMessage(message: string, hideAfterTimeout: number = 0): vscode.Disposable {
        if (hideAfterTimeout > 0) {
            return vscode.window.setStatusBarMessage(`CodeGates: ${message}`, hideAfterTimeout);
        } else {
            return vscode.window.setStatusBarMessage(`CodeGates: ${message}`);
        }
    }
} 