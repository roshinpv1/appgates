/**
 * Runner Factory
 * 
 * Creates appropriate runner instance based on configuration.
 * Supports both local CLI execution and remote API calls.
 */

import * as vscode from 'vscode';
import { ApiRunner } from './apiRunner';
import { ConfigurationManager } from '../utils/configurationManager';
import { NotificationManager } from '../utils/notificationManager';
import { ICodeGatesRunner } from '../types/api';

export class RunnerFactory {
    private configManager: ConfigurationManager;
    private notificationManager: NotificationManager;

    constructor() {
        this.configManager = new ConfigurationManager();
        this.notificationManager = new NotificationManager();
    }

    async createRunner(): Promise<ICodeGatesRunner> {
        // We now only support API mode
        return new ApiRunner(this.configManager, this.notificationManager);
    }

    async testConnection(): Promise<boolean> {
        try {
            const runner = await this.createRunner();
            return await runner.testConnection();
        } catch (error) {
            console.error('Connection test failed:', error);
            return false;
        }
    }
} 