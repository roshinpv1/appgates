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
exports.GitManager = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
class GitManager {
    constructor() {
        this.activeWorkspaces = new Map();
        // Create temp directory in system temp or workspace
        this.tempDir = path.join(require('os').tmpdir(), 'codegates-temp');
        this.ensureTempDir();
    }
    ensureTempDir() {
        if (!fs.existsSync(this.tempDir)) {
            fs.mkdirSync(this.tempDir, { recursive: true });
        }
    }
    /**
     * Clone a GitHub repository to a temporary directory
     */
    async cloneRepository(repository) {
        const repoId = this.generateRepoId(repository);
        // Check if already cloned
        if (this.activeWorkspaces.has(repoId)) {
            return this.activeWorkspaces.get(repoId);
        }
        const tempPath = path.join(this.tempDir, repoId);
        try {
            // Clean up if directory exists
            if (fs.existsSync(tempPath)) {
                await this.removeDirectory(tempPath);
            }
            // Build git clone command
            const cloneUrl = this.buildAuthenticatedUrl(repository);
            const branch = repository.branch || 'main';
            const command = `git clone --depth 1 --branch ${branch} "${cloneUrl}" "${tempPath}"`;
            vscode.window.showInformationMessage(`🔄 Cloning repository: ${repository.name}`);
            await execAsync(command, {
                timeout: 30000, // 30 second timeout
                maxBuffer: 1024 * 1024 * 10 // 10MB buffer
            });
            const workspace = {
                path: tempPath,
                repository,
                cleanup: async () => {
                    await this.cleanupWorkspace(repoId);
                }
            };
            this.activeWorkspaces.set(repoId, workspace);
            vscode.window.showInformationMessage(`✅ Repository cloned: ${repository.name}`);
            return workspace;
        }
        catch (error) {
            // Cleanup on failure
            if (fs.existsSync(tempPath)) {
                await this.removeDirectory(tempPath);
            }
            throw new Error(`Failed to clone repository: ${error}`);
        }
    }
    /**
     * Parse GitHub URL and extract repository information
     */
    parseGitHubUrl(url) {
        // Support various GitHub URL formats
        const patterns = [
            /https:\/\/github\.com\/([^\/]+)\/([^\/]+)(?:\.git)?(?:\/tree\/([^\/]+))?/,
            /git@github\.com:([^\/]+)\/([^\/]+)(?:\.git)?/,
            /([^\/]+)\/([^\/]+)/ // Simple owner/repo format
        ];
        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) {
                const [, owner, repo, branch] = match;
                return {
                    url: `https://github.com/${owner}/${repo}.git`,
                    name: `${owner}/${repo}`,
                    branch: branch || 'main'
                };
            }
        }
        throw new Error('Invalid GitHub URL format');
    }
    /**
     * Build authenticated URL with token
     */
    buildAuthenticatedUrl(repository) {
        if (repository.token) {
            // Use token authentication
            const url = new URL(repository.url);
            return `https://${repository.token}@${url.host}${url.pathname}`;
        }
        return repository.url;
    }
    /**
     * Generate unique repository ID
     */
    generateRepoId(repository) {
        const name = repository.name.replace(/[^a-zA-Z0-9]/g, '_');
        const branch = (repository.branch || 'main').replace(/[^a-zA-Z0-9]/g, '_');
        const timestamp = Date.now();
        return `${name}_${branch}_${timestamp}`;
    }
    /**
     * Cleanup a specific workspace
     */
    async cleanupWorkspace(repoId) {
        const workspace = this.activeWorkspaces.get(repoId);
        if (workspace) {
            try {
                await this.removeDirectory(workspace.path);
                this.activeWorkspaces.delete(repoId);
                vscode.window.showInformationMessage(`🗑️ Cleaned up: ${workspace.repository.name}`);
            }
            catch (error) {
                console.error('Failed to cleanup workspace:', error);
            }
        }
    }
    /**
     * Cleanup all temporary workspaces
     */
    async cleanupAll() {
        const cleanupPromises = Array.from(this.activeWorkspaces.keys()).map(repoId => this.cleanupWorkspace(repoId));
        await Promise.all(cleanupPromises);
        // Remove temp directory if empty
        try {
            if (fs.existsSync(this.tempDir)) {
                const files = fs.readdirSync(this.tempDir);
                if (files.length === 0) {
                    fs.rmdirSync(this.tempDir);
                }
            }
        }
        catch (error) {
            console.error('Failed to remove temp directory:', error);
        }
    }
    /**
     * Remove directory recursively
     */
    async removeDirectory(dirPath) {
        try {
            // Use system command for reliable directory removal
            const command = process.platform === 'win32'
                ? `rmdir /s /q "${dirPath}"`
                : `rm -rf "${dirPath}"`;
            await execAsync(command);
        }
        catch (error) {
            // Fallback to Node.js fs methods
            if (fs.existsSync(dirPath)) {
                const files = fs.readdirSync(dirPath);
                for (const file of files) {
                    const filePath = path.join(dirPath, file);
                    const stat = fs.statSync(filePath);
                    if (stat.isDirectory()) {
                        await this.removeDirectory(filePath);
                    }
                    else {
                        fs.unlinkSync(filePath);
                    }
                }
                fs.rmdirSync(dirPath);
            }
        }
    }
    /**
     * Get list of active temporary workspaces
     */
    getActiveWorkspaces() {
        return Array.from(this.activeWorkspaces.values());
    }
    /**
     * Check if git is available
     */
    async checkGitAvailability() {
        try {
            await execAsync('git --version');
            return true;
        }
        catch (error) {
            return false;
        }
    }
    /**
     * Validate GitHub token
     */
    async validateGitHubToken(token) {
        try {
            const command = `curl -H "Authorization: token ${token}" https://api.github.com/user`;
            const { stdout } = await execAsync(command);
            const response = JSON.parse(stdout);
            return response.login !== undefined;
        }
        catch (error) {
            return false;
        }
    }
}
exports.GitManager = GitManager;
//# sourceMappingURL=gitManager.js.map