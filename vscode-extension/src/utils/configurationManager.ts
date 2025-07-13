import * as vscode from 'vscode';

export class ConfigurationManager {
    private static readonly CONFIGURATION_SECTION = 'codegates';

    get<T>(key: string, defaultValue?: T): T {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        return config.get<T>(key, defaultValue as T);
    }

    async update(key: string, value: any, target?: vscode.ConfigurationTarget): Promise<void> {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        await config.update(key, value, target || vscode.ConfigurationTarget.Workspace);
    }

    has(key: string): boolean {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        return config.has(key);
    }

    inspect(key: string) {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        return config.inspect(key);
    }

    getAll(): { [key: string]: any } {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        return {
            // API Configuration (matches package.json settings)
            apiUrl: config.get('apiUrl'),
            apiTimeout: config.get('apiTimeout'),
            apiRetries: config.get('apiRetries'),
            
            // Debug information
            _inspectApiUrl: config.inspect('apiUrl'),
            _inspectApiTimeout: config.inspect('apiTimeout'),
            _inspectApiRetries: config.inspect('apiRetries')
        };
    }

    onDidChange(listener: (e: vscode.ConfigurationChangeEvent) => void): vscode.Disposable {
        return vscode.workspace.onDidChangeConfiguration(listener);
    }

    isCodeGatesConfigurationChange(e: vscode.ConfigurationChangeEvent): boolean {
        return e.affectsConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
    }
} 