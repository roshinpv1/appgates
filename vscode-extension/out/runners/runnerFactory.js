"use strict";
/**
 * Runner Factory
 *
 * Creates appropriate runner instance based on configuration.
 * Supports both local CLI execution and remote API calls.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.RunnerFactory = void 0;
const apiRunner_1 = require("./apiRunner");
const configurationManager_1 = require("../utils/configurationManager");
const notificationManager_1 = require("../utils/notificationManager");
class RunnerFactory {
    constructor() {
        this.configManager = new configurationManager_1.ConfigurationManager();
        this.notificationManager = new notificationManager_1.NotificationManager();
    }
    async createRunner() {
        // We now only support API mode
        return new apiRunner_1.ApiRunner(this.configManager, this.notificationManager);
    }
    async testConnection() {
        try {
            const runner = await this.createRunner();
            return await runner.testConnection();
        }
        catch (error) {
            console.error('Connection test failed:', error);
            return false;
        }
    }
}
exports.RunnerFactory = RunnerFactory;
//# sourceMappingURL=runnerFactory.js.map