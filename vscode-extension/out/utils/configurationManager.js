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
exports.ConfigurationManager = void 0;
const vscode = __importStar(require("vscode"));
class ConfigurationManager {
    get(key, defaultValue) {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        return config.get(key, defaultValue);
    }
    async update(key, value, target) {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        await config.update(key, value, target || vscode.ConfigurationTarget.Workspace);
    }
    has(key) {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        return config.has(key);
    }
    inspect(key) {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
        return config.inspect(key);
    }
    getAll() {
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
    onDidChange(listener) {
        return vscode.workspace.onDidChangeConfiguration(listener);
    }
    isCodeGatesConfigurationChange(e) {
        return e.affectsConfiguration(ConfigurationManager.CONFIGURATION_SECTION);
    }
}
exports.ConfigurationManager = ConfigurationManager;
ConfigurationManager.CONFIGURATION_SECTION = 'codegates';
//# sourceMappingURL=configurationManager.js.map