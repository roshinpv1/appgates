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
        
        return {
            "scan_id": scan_id,
            "total_interactions": len(logs),
            "total_prompt_tokens": total_prompt_tokens,
            "total_response_tokens": total_response_tokens,
            "total_duration": total_duration,
            "average_duration": total_duration / len(logs) if logs else 0,
            "errors": errors,
            "nodes": nodes,
            "log_file": str(self.log_dir / f"scan_{scan_id}_llm_log.jsonl")
        }
    
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
