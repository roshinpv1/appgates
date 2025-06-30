import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface GitRepository {
    url: string;
    branch?: string;
    token?: string;
    name: string;
}

export interface TempWorkspace {
    path: string;
    repository: GitRepository;
    cleanup: () => Promise<void>;
}

export class GitManager {
    private tempDir: string;
    private activeWorkspaces: Map<string, TempWorkspace> = new Map();

    constructor() {
        // Create temp directory in system temp or workspace
        this.tempDir = path.join(require('os').tmpdir(), 'codegates-temp');
        this.ensureTempDir();
    }

    private ensureTempDir(): void {
        if (!fs.existsSync(this.tempDir)) {
            fs.mkdirSync(this.tempDir, { recursive: true });
        }
    }

    /**
     * Clone a GitHub repository to a temporary directory
     */
    async cloneRepository(repository: GitRepository): Promise<TempWorkspace> {
        const repoId = this.generateRepoId(repository);
        
        // Check if already cloned
        if (this.activeWorkspaces.has(repoId)) {
            return this.activeWorkspaces.get(repoId)!;
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

            const workspace: TempWorkspace = {
                path: tempPath,
                repository,
                cleanup: async () => {
                    await this.cleanupWorkspace(repoId);
                }
            };

            this.activeWorkspaces.set(repoId, workspace);
            
            vscode.window.showInformationMessage(`✅ Repository cloned: ${repository.name}`);
            
            return workspace;

        } catch (error) {
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
    parseGitHubUrl(url: string): Partial<GitRepository> {
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
    private buildAuthenticatedUrl(repository: GitRepository): string {
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
    private generateRepoId(repository: GitRepository): string {
        const name = repository.name.replace(/[^a-zA-Z0-9]/g, '_');
        const branch = (repository.branch || 'main').replace(/[^a-zA-Z0-9]/g, '_');
        const timestamp = Date.now();
        return `${name}_${branch}_${timestamp}`;
    }

    /**
     * Cleanup a specific workspace
     */
    async cleanupWorkspace(repoId: string): Promise<void> {
        const workspace = this.activeWorkspaces.get(repoId);
        if (workspace) {
            try {
                await this.removeDirectory(workspace.path);
                this.activeWorkspaces.delete(repoId);
                vscode.window.showInformationMessage(`🗑️ Cleaned up: ${workspace.repository.name}`);
            } catch (error) {
                console.error('Failed to cleanup workspace:', error);
            }
        }
    }

    /**
     * Cleanup all temporary workspaces
     */
    async cleanupAll(): Promise<void> {
        const cleanupPromises = Array.from(this.activeWorkspaces.keys()).map(
            repoId => this.cleanupWorkspace(repoId)
        );
        
        await Promise.all(cleanupPromises);
        
        // Remove temp directory if empty
        try {
            if (fs.existsSync(this.tempDir)) {
                const files = fs.readdirSync(this.tempDir);
                if (files.length === 0) {
                    fs.rmdirSync(this.tempDir);
                }
            }
        } catch (error) {
            console.error('Failed to remove temp directory:', error);
        }
    }

    /**
     * Remove directory recursively
     */
    private async removeDirectory(dirPath: string): Promise<void> {
        try {
            // Use system command for reliable directory removal
            const command = process.platform === 'win32' 
                ? `rmdir /s /q "${dirPath}"`
                : `rm -rf "${dirPath}"`;
                
            await execAsync(command);
        } catch (error) {
            // Fallback to Node.js fs methods
            if (fs.existsSync(dirPath)) {
                const files = fs.readdirSync(dirPath);
                for (const file of files) {
                    const filePath = path.join(dirPath, file);
                    const stat = fs.statSync(filePath);
                    if (stat.isDirectory()) {
                        await this.removeDirectory(filePath);
                    } else {
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
    getActiveWorkspaces(): TempWorkspace[] {
        return Array.from(this.activeWorkspaces.values());
    }

    /**
     * Check if git is available
     */
    async checkGitAvailability(): Promise<boolean> {
        try {
            await execAsync('git --version');
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Validate GitHub token
     */
    async validateGitHubToken(token: string): Promise<boolean> {
        try {
            const command = `curl -H "Authorization: token ${token}" https://api.github.com/user`;
            const { stdout } = await execAsync(command);
            const response = JSON.parse(stdout);
            return response.login !== undefined;
        } catch (error) {
            return false;
        }
    }
} 