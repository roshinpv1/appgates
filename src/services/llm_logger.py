#!/usr/bin/env python3
"""
LLM Logger Service for capturing prompts and responses
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class LLMLogger:
    """Service for logging LLM prompts and responses"""
    
    def __init__(self, log_dir: str = "logs/llm"):
        """Initialize the LLM logger"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_llm_interaction(
        self,
        scan_id: str,
        node_name: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None
    ) -> str:
        """
        Log an LLM interaction to a scan-specific file
        
        Args:
            scan_id: The scan ID
            node_name: Name of the node making the LLM call
            prompt: The prompt sent to the LLM
            response: The response from the LLM
            metadata: Additional metadata about the interaction
            error: Error message if the call failed
            duration: Time taken for the LLM call in seconds
            
        Returns:
            Path to the log file
        """
        # Create scan-specific log file
        log_file = self.log_dir / f"scan_{scan_id}_llm_log.jsonl"
        
        # Prepare log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "scan_id": scan_id,
            "node_name": node_name,
            "prompt": prompt,
            "response": response,
            "metadata": metadata or {},
            "error": error,
            "duration": duration,
            "prompt_length": len(prompt),
            "response_length": len(response)
        }
        
        # Write to log file (append mode)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        return str(log_file)
    
    def get_scan_logs(self, scan_id: str) -> list:
        """
        Get all LLM logs for a specific scan
        
        Args:
            scan_id: The scan ID
            
        Returns:
            List of log entries
        """
        log_file = self.log_dir / f"scan_{scan_id}_llm_log.jsonl"
        
        if not log_file.exists():
            return []
        
        logs = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        return logs
    
    def get_scan_summary(self, scan_id: str) -> Dict[str, Any]:
        """
        Get a summary of LLM interactions for a scan
        
        Args:
            scan_id: The scan ID
            
        Returns:
            Summary statistics
        """
        logs = self.get_scan_logs(scan_id)
        
        if not logs:
            return {
                "scan_id": scan_id,
                "total_interactions": 0,
                "total_prompt_tokens": 0,
                "total_response_tokens": 0,
                "total_duration": 0.0,
                "errors": 0,
                "nodes": []
            }
        
        total_duration = sum(log.get("duration", 0) for log in logs)
        total_prompt_tokens = sum(log.get("prompt_length", 0) for log in logs)
        total_response_tokens = sum(log.get("response_length", 0) for log in logs)
        errors = sum(1 for log in logs if log.get("error"))
        nodes = list(set(log.get("node_name") for log in logs))
        
        # Group by node for detailed analysis
        node_stats = {}
        for log in logs:
            node_name = log.get("node_name", "unknown")
            if node_name not in node_stats:
                node_stats[node_name] = {
                    "calls": 0,
                    "total_duration": 0.0,
                    "total_prompt_length": 0,
                    "total_response_length": 0,
                    "errors": 0
                }
            
            node_stats[node_name]["calls"] += 1
            node_stats[node_name]["total_duration"] += log.get("duration", 0)
            node_stats[node_name]["total_prompt_length"] += log.get("prompt_length", 0)
            node_stats[node_name]["total_response_length"] += log.get("response_length", 0)
            if log.get("error"):
                node_stats[node_name]["errors"] += 1
        
        return {
            "scan_id": scan_id,
            "total_interactions": len(logs),
            "total_prompt_tokens": total_prompt_tokens,
            "total_response_tokens": total_response_tokens,
            "total_duration": total_duration,
            "average_duration": total_duration / len(logs) if logs else 0,
            "errors": errors,
            "nodes": nodes,
            "node_statistics": node_stats,
            "log_file": str(self.log_dir / f"scan_{scan_id}_llm_log.jsonl")
        }
    
    def generate_scan_report(self, scan_id: str, output_dir: str = "reports") -> str:
        """
        Generate a comprehensive HTML report for a scan's LLM interactions
        
        Args:
            scan_id: The scan ID
            output_dir: Directory to save the report
            
        Returns:
            Path to the generated report
        """
        logs = self.get_scan_logs(scan_id)
        summary = self.get_scan_summary(scan_id)
        
        if not logs:
            return ""
        
        # Create output directory
        output_path = Path(output_dir) / scan_id
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate HTML report
        html_content = self._generate_html_report(scan_id, logs, summary)
        report_file = output_path / "llm_interactions_report.html"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Generate JSON summary
        json_file = output_path / "llm_interactions_summary.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return str(report_file)
    
    def _generate_html_report(self, scan_id: str, logs: list, summary: dict) -> str:
        """Generate HTML report content"""
        
        # Create node-wise breakdown
        node_breakdown = ""
        for node_name, stats in summary.get("node_statistics", {}).items():
            node_breakdown += f"""
            <div class="node-stats">
                <h3>{node_name}</h3>
                <ul>
                    <li>Calls: {stats['calls']}</li>
                    <li>Total Duration: {stats['total_duration']:.2f}s</li>
                    <li>Average Duration: {stats['total_duration']/stats['calls']:.2f}s</li>
                    <li>Total Prompt Length: {stats['total_prompt_length']:,} chars</li>
                    <li>Total Response Length: {stats['total_response_length']:,} chars</li>
                    <li>Errors: {stats['errors']}</li>
                </ul>
            </div>
            """
        
        # Create interaction details
        interaction_details = ""
        for i, log in enumerate(logs):
            interaction_details += f"""
            <div class="interaction">
                <h4>Interaction {i+1}: {log.get('node_name', 'Unknown')}</h4>
                <p><strong>Timestamp:</strong> {log.get('timestamp', 'Unknown')}</p>
                <p><strong>Duration:</strong> {log.get('duration', 0):.2f}s</p>
                <p><strong>Prompt Length:</strong> {log.get('prompt_length', 0):,} chars</p>
                <p><strong>Response Length:</strong> {log.get('response_length', 0):,} chars</p>
                {f'<p><strong>Error:</strong> <span class="error">{log.get("error")}</span></p>' if log.get('error') else ''}
                
                <details>
                    <summary>View Prompt</summary>
                    <pre class="prompt">{log.get('prompt', '')}</pre>
                </details>
                
                <details>
                    <summary>View Response</summary>
                    <pre class="response">{log.get('response', '')}</pre>
                </details>
            </div>
            """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LLM Interactions Report - Scan {scan_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .node-stats {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .interaction {{ border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .error {{ color: red; }}
                pre {{ background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
                details {{ margin: 10px 0; }}
                summary {{ cursor: pointer; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>LLM Interactions Report</h1>
                <p><strong>Scan ID:</strong> {scan_id}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <ul>
                    <li><strong>Total Interactions:</strong> {summary.get('total_interactions', 0)}</li>
                    <li><strong>Total Duration:</strong> {summary.get('total_duration', 0):.2f}s</li>
                    <li><strong>Average Duration:</strong> {summary.get('average_duration', 0):.2f}s</li>
                    <li><strong>Total Prompt Length:</strong> {summary.get('total_prompt_tokens', 0):,} chars</li>
                    <li><strong>Total Response Length:</strong> {summary.get('total_response_tokens', 0):,} chars</li>
                    <li><strong>Errors:</strong> {summary.get('errors', 0)}</li>
                    <li><strong>Nodes:</strong> {', '.join(summary.get('nodes', []))}</li>
                </ul>
            </div>
            
            <h2>Node Statistics</h2>
            {node_breakdown}
            
            <h2>Detailed Interactions</h2>
            {interaction_details}
        </body>
        </html>
        """
        
        return html_template
    
    def cleanup_old_logs(self, days_to_keep: int = 7) -> int:
        """
        Clean up old log files
        
        Args:
            days_to_keep: Number of days to keep logs
            
        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        for log_file in self.log_dir.glob("scan_*_llm_log.jsonl"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1
        
        return deleted_count
