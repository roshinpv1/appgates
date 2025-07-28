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
exports.CodeGatesRunner = void 0;
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
class CodeGatesRunner {
    constructor(configManager, notificationManager) {
        this.configManager = configManager;
        this.notificationManager = notificationManager;
        this.pythonPath = this.configManager.get('pythonPath', 'python');
        this.codeGatesPath = this.configManager.get('codegatePath', '');
        if (!this.codeGatesPath) {
            this.codeGatesPath = this.detectCodeGatesPath();
        }
    }
    detectCodeGatesPath() {
        // Try to find CodeGates in common locations
        const possiblePaths = [
            path.join(process.cwd(), 'main.py'),
            path.join(process.cwd(), 'codegates', 'main.py'),
            path.join(process.cwd(), '..', 'main.py'),
            'codegates', // If installed globally
            'main.py' // If in current directory
        ];
        for (const possiblePath of possiblePaths) {
            if (fs.existsSync(possiblePath)) {
                return possiblePath;
            }
        }
        return 'python main.py'; // Default fallback
    }
    async scanWorkspace(workspacePath) {
        const args = this.buildScanArgs(workspacePath, false);
        try {
            const output = await this.executeCodeGates(args);
            return this.parseScanOutput(output, workspacePath);
        }
        catch (error) {
            throw new Error(`Failed to scan workspace: ${error}`);
        }
    }
    async scanFile(filePath) {
        const args = this.buildScanArgs(filePath, true);
        try {
            const output = await this.executeCodeGates(args);
            return this.parseScanOutput(output, filePath);
        }
        catch (error) {
            throw new Error(`Failed to scan file: ${error}`);
        }
    }
    buildScanArgs(targetPath, isFile) {
        const args = ['scan', targetPath];
        // Add format for JSON output
        args.push('--format', 'json');
        // Add LLM options if enabled
        if (this.configManager.get('llm.enabled', false)) {
            args.push('--enable-llm');
            const provider = this.configManager.get('llm.provider', 'openai');
            args.push('--llm-provider', provider);
            const model = this.configManager.get('llm.model', 'gpt-4');
            if (model) {
                args.push('--llm-model', model);
            }
            const temperature = this.configManager.get('llm.temperature', 0.1);
            args.push('--llm-temperature', temperature.toString());
        }
        // Add threshold
        const threshold = this.configManager.get('threshold', 70);
        args.push('--threshold', threshold.toString());
        // Add language restrictions
        const languages = this.configManager.get('languages', []);
        if (languages.length > 0) {
            args.push('--languages', languages.join(','));
        }
        // Add exclude patterns
        const excludePatterns = this.configManager.get('excludePatterns', []);
        if (excludePatterns.length > 0) {
            for (const pattern of excludePatterns) {
                args.push('--exclude', pattern);
            }
        }
        return args;
    }
    executeCodeGates(args) {
        return new Promise((resolve, reject) => {
            const command = this.buildCommand(args);
            (0, child_process_1.exec)(command, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
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
    buildCommand(args) {
        if (this.codeGatesPath.endsWith('.py')) {
            return `${this.pythonPath} ${this.codeGatesPath} ${args.join(' ')}`;
        }
        else {
            return `${this.codeGatesPath} ${args.join(' ')}`;
        }
    }
    async parseScanOutput(output, targetPath) {
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
        }
        catch (error) {
            // Fallback to parsing from report file
            try {
                return await this.parseFromReportFile(targetPath);
            }
            catch (fallbackError) {
                throw new Error(`Failed to parse CodeGates output: ${error}. Fallback also failed: ${fallbackError}`);
            }
        }
    }
    async parseFromReportFile(targetPath) {
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
    transformResult(rawResult) {
        const gateScores = [];
        const issues = [];
        if (rawResult.gate_scores) {
            for (const gate of rawResult.gate_scores) {
                const gateScore = {
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
                    const gateIssues = gate.issues.map((issue) => ({
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
    determineStatus(score) {
        const excellentThreshold = this.configManager.get('excellentThreshold', 80);
        const goodThreshold = this.configManager.get('goodThreshold', 60);
        if (score >= excellentThreshold)
            return 'PASSED';
        if (score >= goodThreshold)
            return 'WARNING';
        return 'FAILED';
    }
    determineSeverity(status) {
        switch (status) {
            case 'FAILED': return 'error';
            case 'WARNING': return 'warning';
            case 'PASSED': return 'info';
        }
    }
    async testConnection() {
        try {
            const output = await this.executeCodeGates(['--help']);
            return output.includes('CodeGates');
        }
        catch (error) {
            return false;
        }
    }
}
exports.CodeGatesRunner = CodeGatesRunner;
//# sourceMappingURL=codeGatesRunner.js.map