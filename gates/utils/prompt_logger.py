#!/usr/bin/env python3
"""
Prompt Logger Utility
Logs all LLM prompts to temporary files for debugging and analysis
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class PromptLogEntry:
    """Structure for logging prompt information"""
    timestamp: str
    gate_name: str
    prompt_type: str  # "explainability", "pattern_generation", "recommendation", etc.
    prompt_content: str
    context_data: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class ConversationLogEntry:
    """Structure for logging complete conversations"""
    timestamp: str
    gate_name: str
    conversation_type: str  # "explainability", "pattern_generation", "recommendation", etc.
    system_prompt: str
    user_prompt: str
    llm_response: Optional[str] = None
    context_data: Dict[str, Any] = None
    metadata: Dict[str, Any] = None


class PromptLogger:
    """Centralized prompt logging utility"""
    
    def __init__(self, log_dir: str = "./logs/prompts"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different prompt types
        self.explainability_dir = self.log_dir / "explainability"
        self.pattern_dir = self.log_dir / "patterns"
        self.recommendation_dir = self.log_dir / "recommendations"
        self.general_dir = self.log_dir / "general"
        self.conversations_dir = self.log_dir / "conversations"
        
        for directory in [self.explainability_dir, self.pattern_dir, self.recommendation_dir, self.general_dir, self.conversations_dir]:
            directory.mkdir(exist_ok=True)
    
    def log_explainability_prompt(self, gate_name: str, prompt: str, context: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log explainability prompt"""
        return self._log_prompt(
            gate_name=gate_name,
            prompt_type="explainability",
            prompt_content=prompt,
            context_data=context,
            metadata=metadata or {},
            log_dir=self.explainability_dir
        )
    
    def log_pattern_generation_prompt(self, gate_name: str, prompt: str, context: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log pattern generation prompt"""
        return self._log_prompt(
            gate_name=gate_name,
            prompt_type="pattern_generation",
            prompt_content=prompt,
            context_data=context,
            metadata=metadata or {},
            log_dir=self.pattern_dir
        )
    
    def log_recommendation_prompt(self, gate_name: str, prompt: str, context: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log recommendation prompt"""
        return self._log_prompt(
            gate_name=gate_name,
            prompt_type="recommendation",
            prompt_content=prompt,
            context_data=context,
            metadata=metadata or {},
            log_dir=self.recommendation_dir
        )
    
    def log_general_prompt(self, gate_name: str, prompt: str, context: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log general prompt"""
        return self._log_prompt(
            gate_name=gate_name,
            prompt_type="general",
            prompt_content=prompt,
            context_data=context,
            metadata=metadata or {},
            log_dir=self.general_dir
        )
    
    def log_complete_conversation(self, gate_name: str, conversation_type: str, system_prompt: str, 
                                user_prompt: str, llm_response: Optional[str] = None, 
                                context: Optional[Dict[str, Any]] = None, 
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log complete conversation including system prompt, user prompt, and LLM response"""
        timestamp = datetime.now().isoformat()
        
        # Create conversation log entry
        log_entry = ConversationLogEntry(
            timestamp=timestamp,
            gate_name=gate_name,
            conversation_type=conversation_type,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            llm_response=llm_response,
            context_data=context or {},
            metadata=metadata or {}
        )
        
        # Generate filename
        safe_gate_name = self._sanitize_filename(gate_name)
        filename = f"{timestamp.replace(':', '-')}_{safe_gate_name}_{conversation_type}_conversation.json"
        filepath = self.conversations_dir / filename
        
        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(log_entry), f, indent=2, ensure_ascii=False)
            
            print(f"💬 Logged complete {conversation_type} conversation for {gate_name} to {filepath}")
            
            # Also create a text file for easier reading
            txt_filename = f"{timestamp.replace(':', '-')}_{safe_gate_name}_{conversation_type}_prompt.txt"
            txt_filepath = self.conversations_dir / txt_filename
            self._save_prompt_as_text(txt_filepath, log_entry)
            
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Failed to log conversation: {e}")
            return ""
    
    def log_conversation_with_messages(self, gate_name: str, conversation_type: str, 
                                     messages: List[Dict[str, str]], llm_response: Optional[str] = None,
                                     context: Optional[Dict[str, Any]] = None, 
                                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log conversation using messages format (system, user, assistant)"""
        # Extract system and user prompts from messages
        system_prompt = ""
        user_prompt = ""
        
        for message in messages:
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                user_prompt = content
        
        return self.log_complete_conversation(
            gate_name=gate_name,
            conversation_type=conversation_type,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            llm_response=llm_response,
            context=context,
            metadata=metadata
        )
    
    def _save_prompt_as_text(self, filepath: Path, log_entry: ConversationLogEntry):
        """Save prompt as a readable text file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("CODEGATES LLM PROMPT LOG\n")
                f.write("=" * 80 + "\n")
                f.write(f"Timestamp: {log_entry.timestamp}\n")
                f.write(f"Gate Name: {log_entry.gate_name}\n")
                f.write(f"Conversation Type: {log_entry.conversation_type}\n")
                f.write(f"File: {filepath.name}\n")
                f.write("=" * 80 + "\n\n")
                
                # System Prompt
                if log_entry.system_prompt:
                    f.write("SYSTEM PROMPT:\n")
                    f.write("-" * 40 + "\n")
                    f.write(log_entry.system_prompt)
                    f.write("\n\n")
                
                # User Prompt
                f.write("USER PROMPT:\n")
                f.write("-" * 40 + "\n")
                f.write(log_entry.user_prompt)
                f.write("\n\n")
                
                # LLM Response
                if log_entry.llm_response:
                    f.write("LLM RESPONSE:\n")
                    f.write("-" * 40 + "\n")
                    f.write(log_entry.llm_response)
                    f.write("\n\n")
                
                # Context (if available)
                if log_entry.context_data:
                    f.write("CONTEXT DATA:\n")
                    f.write("-" * 40 + "\n")
                    f.write(json.dumps(log_entry.context_data, indent=2, ensure_ascii=False))
                    f.write("\n\n")
                
                # Metadata (if available)
                if log_entry.metadata:
                    f.write("METADATA:\n")
                    f.write("-" * 40 + "\n")
                    f.write(json.dumps(log_entry.metadata, indent=2, ensure_ascii=False))
                    f.write("\n\n")
                
                f.write("=" * 80 + "\n")
                f.write("END OF PROMPT LOG\n")
                f.write("=" * 80 + "\n")
            
            print(f"📝 Saved prompt text file: {filepath}")
            
        except Exception as e:
            print(f"❌ Failed to save prompt text file: {e}")
    
    def save_single_prompt_file(self, gate_name: str, conversation_type: str, 
                               system_prompt: str, user_prompt: str, 
                               llm_response: Optional[str] = None,
                               context: Optional[Dict[str, Any]] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save a single prompt as a text file (without JSON)"""
        timestamp = datetime.now().isoformat()
        safe_gate_name = self._sanitize_filename(gate_name)
        filename = f"{timestamp.replace(':', '-')}_{safe_gate_name}_{conversation_type}.txt"
        filepath = self.conversations_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("CODEGATES LLM PROMPT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Gate Name: {gate_name}\n")
                f.write(f"Type: {conversation_type}\n")
                f.write("=" * 80 + "\n\n")
                
                # System Prompt
                if system_prompt:
                    f.write("SYSTEM PROMPT:\n")
                    f.write("-" * 40 + "\n")
                    f.write(system_prompt)
                    f.write("\n\n")
                
                # User Prompt
                f.write("USER PROMPT:\n")
                f.write("-" * 40 + "\n")
                f.write(user_prompt)
                f.write("\n\n")
                
                # LLM Response
                if llm_response:
                    f.write("LLM RESPONSE:\n")
                    f.write("-" * 40 + "\n")
                    f.write(llm_response)
                    f.write("\n\n")
                
                # Context (if available)
                if context:
                    f.write("CONTEXT:\n")
                    f.write("-" * 40 + "\n")
                    f.write(json.dumps(context, indent=2, ensure_ascii=False))
                    f.write("\n\n")
                
                # Metadata (if available)
                if metadata:
                    f.write("METADATA:\n")
                    f.write("-" * 40 + "\n")
                    f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
                    f.write("\n\n")
                
                f.write("=" * 80 + "\n")
                f.write("END OF PROMPT\n")
                f.write("=" * 80 + "\n")
            
            print(f"📝 Saved single prompt file: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Failed to save single prompt file: {e}")
            return ""
    
    def _log_prompt(self, gate_name: str, prompt_type: str, prompt_content: str, 
                   context_data: Dict[str, Any], metadata: Dict[str, Any], log_dir: Path) -> str:
        """Internal method to log a prompt"""
        timestamp = datetime.now().isoformat()
        
        # Create log entry
        log_entry = PromptLogEntry(
            timestamp=timestamp,
            gate_name=gate_name,
            prompt_type=prompt_type,
            prompt_content=prompt_content,
            context_data=context_data,
            metadata=metadata
        )
        
        # Generate filename
        safe_gate_name = self._sanitize_filename(gate_name)
        filename = f"{timestamp.replace(':', '-')}_{safe_gate_name}_{prompt_type}.json"
        filepath = log_dir / filename
        
        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(log_entry), f, indent=2, ensure_ascii=False)
            
            print(f"📝 Logged {prompt_type} prompt for {gate_name} to {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Failed to log prompt: {e}")
            return ""
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        # Replace problematic characters
        sanitized = filename.replace('/', '_').replace('\\', '_').replace(':', '_')
        sanitized = sanitized.replace('*', '_').replace('?', '_').replace('"', '_')
        sanitized = sanitized.replace('<', '_').replace('>', '_').replace('|', '_')
        
        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized
    
    def get_prompt_summary(self) -> Dict[str, Any]:
        """Get summary of logged prompts"""
        summary = {
            "total_prompts": 0,
            "total_conversations": 0,
            "by_type": {},
            "by_gate": {},
            "recent_prompts": [],
            "recent_conversations": []
        }
        
        # Count prompts in each directory
        for prompt_type, directory in [
            ("explainability", self.explainability_dir),
            ("pattern_generation", self.pattern_dir),
            ("recommendation", self.recommendation_dir),
            ("general", self.general_dir)
        ]:
            if directory.exists():
                files = list(directory.glob("*.json"))
                summary["by_type"][prompt_type] = len(files)
                summary["total_prompts"] += len(files)
                
                # Get recent prompts
                for file in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            summary["recent_prompts"].append({
                                "timestamp": data.get("timestamp"),
                                "gate_name": data.get("gate_name"),
                                "prompt_type": data.get("prompt_type"),
                                "file": str(file)
                            })
                    except Exception:
                        continue
        
        # Count conversations
        if self.conversations_dir.exists():
            conversation_files = list(self.conversations_dir.glob("*.json"))
            summary["total_conversations"] = len(conversation_files)
            
            # Get recent conversations
            for file in sorted(conversation_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        summary["recent_conversations"].append({
                            "timestamp": data.get("timestamp"),
                            "gate_name": data.get("gate_name"),
                            "conversation_type": data.get("conversation_type"),
                            "file": str(file)
                        })
                except Exception:
                    continue
        
        return summary
    
    def cleanup_old_logs(self, days_to_keep: int = 7) -> int:
        """Clean up old log files"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for directory in [self.explainability_dir, self.pattern_dir, self.recommendation_dir, self.general_dir, self.conversations_dir]:
            if directory.exists():
                for file in directory.glob("*.json"):
                    try:
                        file_time = datetime.fromtimestamp(file.stat().st_mtime)
                        if file_time < cutoff_time:
                            file.unlink()
                            deleted_count += 1
                    except Exception:
                        continue
        
        print(f"🧹 Cleaned up {deleted_count} old prompt log files")
        return deleted_count


# Global instance for consistent logging
prompt_logger = PromptLogger() 