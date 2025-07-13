import { exec, spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { ConfigurationManager } from '../utils/configurationManager';
import { NotificationManager } from '../utils/notificationManager';

export interface ScanResult {
    overall_score: number;
    gate_scores: GateScore[];
    recommendations: string[];
    issues: Issue[];
    project_name: string;
    scan_duration: number;
    languages: string[];
}

export interface GateScore {
    gate: string;
    expected: number;
    found: number;
    coverage: number;
    score: number;
    status: 'PASSED' | 'WARNING' | 'FAILED';
    details: string[];
    recommendations: string[];
    issues?: Issue[];
}

export interface Issue {
    file: string;
    line?: number;
    column?: number;
    message: string;
    severity: 'error' | 'warning' | 'info';
    gate: string;
}

export class CodeGatesRunner {
    private configManager: ConfigurationManager;
    private notificationManager: NotificationManager;
    private pythonPath: string;
    private codeGatesPath: string;

    constructor(configManager: ConfigurationManager, notificationManager: NotificationManager) {
        this.configManager = configManager;
        this.notificationManager = notificationManager;
        this.pythonPath = this.configManager.get<string>('pythonPath', 'python');
        this.codeGatesPath = this.configManager.get<string>('codegatePath', '');
        
        if (!this.codeGatesPath) {
            this.codeGatesPath = this.detectCodeGatesPath();
        }
    }

    private detectCodeGatesPath(): string {
        // Try to find CodeGates in common locations
        const possiblePaths = [
            path.join(process.cwd(), 'main.py'),
            path.join(process.cwd(), 'codegates', 'main.py'),
            path.join(process.cwd(), '..', 'main.py'),
            'codegates',  // If installed globally
            'main.py'     // If in current directory
        ];

        for (const possiblePath of possiblePaths) {
            if (fs.existsSync(possiblePath)) {
                return possiblePath;
            }
        }

        return 'python main.py'; // Default fallback
    }

    async scanWorkspace(workspacePath: string): Promise<ScanResult> {
        const args = this.buildScanArgs(workspacePath, false);
        
        try {
            const output = await this.executeCodeGates(args);
            return this.parseScanOutput(output, workspacePath);
        } catch (error) {
            throw new Error(`Failed to scan workspace: ${error}`);
        }
    }

    async scanFile(filePath: string): Promise<ScanResult> {
        const args = this.buildScanArgs(filePath, true);
        
        try {
            const output = await this.executeCodeGates(args);
            return this.parseScanOutput(output, filePath);
        } catch (error) {
            throw new Error(`Failed to scan file: ${error}`);
        }
    }

    private buildScanArgs(targetPath: string, isFile: boolean): string[] {
        const args = ['scan', targetPath];
        
        // Add format for JSON output
        args.push('--format', 'json');
        
        // Add LLM options if enabled
        if (this.configManager.get<boolean>('llm.enabled', false)) {
            args.push('--enable-llm');
            
            const provider = this.configManager.get<string>('llm.provider', 'openai');
            args.push('--llm-provider', provider);
            
            const model = this.configManager.get<string>('llm.model', 'gpt-4');
            if (model) {
                args.push('--llm-model', model);
            }
            
            const temperature = this.configManager.get<number>('llm.temperature', 0.1);
            args.push('--llm-temperature', temperature.toString());
        }
        
        // Add threshold
        const threshold = this.configManager.get<number>('threshold', 70);
        args.push('--threshold', threshold.toString());
        
        // Add language restrictions
        const languages = this.configManager.get<string[]>('languages', []);
        if (languages.length > 0) {
            args.push('--languages', languages.join(','));
        }
        
        // Add exclude patterns
        const excludePatterns = this.configManager.get<string[]>('excludePatterns', []);
        if (excludePatterns.length > 0) {
            for (const pattern of excludePatterns) {
                args.push('--exclude', pattern);
            }
        }
        
        return args;
    }

    private executeCodeGates(args: string[]): Promise<string> {
        return new Promise((resolve, reject) => {
            const command = this.buildCommand(args);
            
            exec(command, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
                if (error) {
                    reject(new Error(`CodeGates execution failed: ${error.message}\nStderr: ${stderr}`));
                    return;
                }
                
                if (stderr && stderr.trim()) {
                    console.warn('CodeGates stderr:', stderr);
                }
                
                resolve(stdout);
            });
        });
    }

    private buildCommand(args: string[]): string {
        if (this.codeGatesPath.endsWith('.py')) {
            return `${this.pythonPath} ${this.codeGatesPath} ${args.join(' ')}`;
        } else {
            return `${this.codeGatesPath} ${args.join(' ')}`;
        }
    }

    private async parseScanOutput(output: string, targetPath: string): Promise<ScanResult> {
        try {
            // Try to find JSON output in the command output
            const lines = output.split('\n');
            let jsonStart = -1;
            
            for (let i = lines.length - 1; i >= 0; i--) {
                if (lines[i].trim().startsWith('{')) {
                    jsonStart = i;
                    break;
                }
            }
            
            if (jsonStart === -1) {
                // If no JSON found, try to parse from report file
                return await this.parseFromReportFile(targetPath);
            }
            
            const jsonOutput = lines.slice(jsonStart).join('\n');
            const result = JSON.parse(jsonOutput);
            
            return this.transformResult(result);
            
        } catch (error) {
            // Fallback to parsing from report file
            try {
                return await this.parseFromReportFile(targetPath);
            } catch (fallbackError) {
                throw new Error(`Failed to parse CodeGates output: ${error}. Fallback also failed: ${fallbackError}`);
            }
        }
    }

    private async parseFromReportFile(targetPath: string): Promise<ScanResult> {
        const reportsDir = path.join(path.dirname(targetPath), 'reports');
        
        if (!fs.existsSync(reportsDir)) {
            throw new Error('No reports directory found');
        }
        
        const reportFiles = fs.readdirSync(reportsDir)
            .filter(file => file.startsWith('codegates_report_') && file.endsWith('.json'))
            .sort()
            .reverse();
        
        if (reportFiles.length === 0) {
            throw new Error('No JSON report files found');
        }
        
        const latestReport = path.join(reportsDir, reportFiles[0]);
        const reportContent = fs.readFileSync(latestReport, 'utf-8');
        const result = JSON.parse(reportContent);
        
        return this.transformResult(result);
    }

    private transformResult(rawResult: any): ScanResult {
        const gateScores: GateScore[] = [];
        const issues: Issue[] = [];
        
        if (rawResult.gate_scores) {
            for (const gate of rawResult.gate_scores) {
                const gateScore: GateScore = {
                    gate: gate.gate || 'unknown',
                    expected: gate.expected || 0,
                    found: gate.found || 0,
                    coverage: gate.coverage || 0,
                    score: gate.score || 0,
                    status: this.determineStatus(gate.score || 0),
                    details: gate.details || [],
                    recommendations: gate.recommendations || []
                };
                
                // Extract issues from gate details
                if (gate.issues) {
                    const gateIssues = gate.issues.map((issue: any) => ({
                        file: issue.file || '',
                        line: issue.line,
                        column: issue.column,
                        message: issue.message || '',
                        severity: this.determineSeverity(gateScore.status),
                        gate: gate.gate
                    }));
                    
                    gateScore.issues = gateIssues;
                    issues.push(...gateIssues);
                }
                
                gateScores.push(gateScore);
            }
        }
        
        return {
            overall_score: rawResult.overall_score || 0,
            gate_scores: gateScores,
            recommendations: rawResult.recommendations || [],
            issues: issues,
            project_name: rawResult.project_name || 'Unknown',
            scan_duration: rawResult.scan_duration || 0,
            languages: rawResult.languages || []
        };
    }

    private determineStatus(score: number): 'PASSED' | 'WARNING' | 'FAILED' {
        if (score >= 80) return 'PASSED';
        if (score >= 60) return 'WARNING';
        return 'FAILED';
    }

    private determineSeverity(status: 'PASSED' | 'WARNING' | 'FAILED'): 'error' | 'warning' | 'info' {
        switch (status) {
            case 'FAILED': return 'error';
            case 'WARNING': return 'warning';
            case 'PASSED': return 'info';
        }
    }

    async testConnection(): Promise<boolean> {
        try {
            const output = await this.executeCodeGates(['--help']);
            return output.includes('CodeGates');
        } catch (error) {
            return false;
        }
    }
} 