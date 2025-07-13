export interface ApiConfig {
    baseUrl: string;
    apiKey?: string;
    timeout: number;
    retries: number;
}

export interface ScanOptions {
    threshold?: number;
}

export interface ScanRequest {
    repository_url: string;
    branch?: string;
    github_token?: string;
    scan_options?: ScanOptions;
}

export interface GateResult {
    name: string;
    status: string;  // 'PASS' | 'FAIL' | 'WARNING'
    score: number;
    details: string[];
}

export interface ScanResult {
    scan_id: string;
    status: string;
    message?: string;
    repository_url?: string;
    score: number;
    gates: GateResult[];
    recommendations: string[];
    report_url?: string;
    progress: number;
    languages_detected: string[];
    current_step?: string;
    progress_percentage?: number;
    step_details?: string;
}

export interface ICodeGatesRunner {
    scanRepository(repoUrl: string, branch?: string, token?: string, options?: ScanOptions): Promise<ScanResult>;
    testConnection(): Promise<boolean>;
    dispose(): void;
} 