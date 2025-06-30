"""
LLM Optimizer - Handles timeout issues and improves LLM processing performance
"""

import asyncio
import time
import json
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from ..models import Language, GateType


@dataclass
class LLMBatch:
    """Represents a batch of LLM requests"""
    gate_name: str
    code_samples: List[str]
    language: Language
    technologies: Dict[str, List[str]]
    priority: int = 1  # Higher priority = processed first


class LLMOptimizer:
    """Optimizes LLM processing to prevent timeouts and improve performance"""
    
    def __init__(self, llm_analyzer, max_batch_size: int = 3, timeout_per_request: int = 30):
        self.llm_analyzer = llm_analyzer
        self.max_batch_size = max_batch_size
        self.timeout_per_request = timeout_per_request
        self.max_code_samples_per_gate = 5  # Limit code samples to prevent large prompts
        self.max_prompt_size = 15000  # Characters limit for prompts
        
    def optimize_gate_analysis(self, 
                             gate_name: str,
                             code_samples: List[str],
                             language: Language,
                             technologies: Dict[str, List[str]]) -> Dict[str, Any]:
        """Optimize LLM analysis for a single gate with timeout handling"""
        
        print(f"🔧 Optimizing LLM analysis for {gate_name}")
        
        # Step 1: Filter and limit code samples
        optimized_samples = self._optimize_code_samples(code_samples, gate_name)
        
        # Step 2: Check if we should skip LLM for this gate
        if self._should_skip_llm_analysis(gate_name, optimized_samples):
            print(f"⚡ Skipping LLM for {gate_name} (low priority or no samples)")
            return self._get_fallback_analysis(gate_name)
        
        # Step 3: Try LLM analysis with timeout
        try:
            print(f"🤖 Starting LLM analysis for {gate_name} with {len(optimized_samples)} samples")
            start_time = time.time()
            
            # Use ThreadPoolExecutor for timeout handling
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.llm_analyzer.analyze_gate_implementation,
                    gate_name,
                    optimized_samples,
                    language,
                    technologies
                )
                
                try:
                    result = future.result(timeout=self.timeout_per_request)
                    elapsed = time.time() - start_time
                    print(f"✅ LLM analysis completed for {gate_name} in {elapsed:.1f}s")
                    
                    # Convert to expected format
                    return {
                        'enhanced_quality_score': result.quality_score,
                        'llm_recommendations': result.recommendations[:3],  # Limit recommendations
                        'code_examples': [],  # Skip code examples to save time
                        'security_insights': result.security_issues[:2],  # Limit insights
                        'technology_insights': result.technology_insights,
                        'patterns_found': result.patterns_found[:3],
                        'code_smells': result.code_smells[:2],
                        'best_practices': result.best_practices[:2]
                    }
                    
                except FutureTimeoutError:
                    print(f"⏰ LLM analysis timeout for {gate_name} after {self.timeout_per_request}s")
                    future.cancel()
                    return self._get_fallback_analysis(gate_name)
                    
        except Exception as e:
            print(f"❌ LLM analysis failed for {gate_name}: {str(e)[:100]}...")
            return self._get_fallback_analysis(gate_name)
    
    def _optimize_code_samples(self, code_samples: List[str], gate_name: str) -> List[str]:
        """Optimize code samples to prevent large prompts"""
        
        if not code_samples:
            return []
        
        # Filter relevant samples based on gate type
        filtered_samples = self._filter_relevant_samples(code_samples, gate_name)
        
        # Limit number of samples
        limited_samples = filtered_samples[:self.max_code_samples_per_gate]
        
        # Truncate long samples
        optimized_samples = []
        total_chars = 0
        
        for sample in limited_samples:
            # Truncate individual samples if too long
            if len(sample) > 2000:  # Max 2000 chars per sample
                sample = sample[:2000] + "... [truncated]"
            
            # Check total prompt size
            if total_chars + len(sample) > self.max_prompt_size:
                break
                
            optimized_samples.append(sample)
            total_chars += len(sample)
        
        print(f"📊 Optimized {len(code_samples)} → {len(optimized_samples)} samples for {gate_name}")
        return optimized_samples
    
    def _filter_relevant_samples(self, code_samples: List[str], gate_name: str) -> List[str]:
        """Filter code samples to keep only relevant ones for the gate"""
        
        # Define relevance keywords for each gate type
        relevance_keywords = {
            'structured_logs': ['log', 'logger', 'logging', 'json', 'structured', 'extra', 'format'],
            'avoid_logging_secrets': ['password', 'token', 'secret', 'api_key', 'log', 'credential', 'auth'],
            'audit_trail': ['audit', 'log', 'track', 'history', 'event', 'record'],
            'correlation_id': ['correlation', 'request_id', 'trace_id', 'uuid', 'x-correlation'],
            'error_logs': ['error', 'exception', 'log', 'catch', 'try', 'except', 'raise'],
            'retry_logic': ['retry', 'attempt', 'backoff', 'exponential', 'sleep', 'time.sleep'],
            'timeouts': ['timeout', 'deadline', 'duration', 'time', 'sleep', 'wait'],
            'circuit_breakers': ['circuit', 'breaker', 'fallback', 'threshold', 'failure'],
            'throttling': ['throttle', 'rate', 'limit', 'quota', 'sleep', 'delay'],
            'automated_tests': ['test', 'assert', 'mock', 'spec', 'it(', 'describe(', 'unittest', 'pytest'],
            'http_codes': ['status', 'code', 'http', '200', '404', '500', 'response', 'status_code'],
            'log_api_calls': ['api', 'endpoint', 'request', 'response', 'log', 'method'],
            'ui_errors': ['error', 'exception', 'alert', 'message', 'ui', 'user'],
        }
        
        keywords = relevance_keywords.get(gate_name.lower(), [])
        if not keywords:
            # If no keywords defined, return all samples (don't filter)
            print(f"📊 No keywords defined for {gate_name}, keeping all {len(code_samples)} samples")
            return code_samples[:self.max_code_samples_per_gate]
        
        # Score samples by relevance
        scored_samples = []
        for sample in code_samples:
            sample_lower = sample.lower()
            score = sum(1 for keyword in keywords if keyword in sample_lower)
            # Keep samples with at least one relevant keyword OR if it's a short sample (likely important)
            if score > 0 or len(sample.split()) < 10:
                scored_samples.append((score, sample))
        
        # If no samples match keywords, keep the original samples (less aggressive filtering)
        if not scored_samples:
            print(f"📊 No keyword matches for {gate_name}, keeping original {len(code_samples)} samples")
            return code_samples[:self.max_code_samples_per_gate]
        
        # Sort by relevance score (descending)
        scored_samples.sort(key=lambda x: x[0], reverse=True)
        
        filtered_samples = [sample for _, sample in scored_samples[:self.max_code_samples_per_gate]]
        print(f"📊 Filtered {len(code_samples)} → {len(filtered_samples)} samples for {gate_name} (keyword matching)")
        
        # Return top samples
        return filtered_samples
    
    def _should_skip_llm_analysis(self, gate_name: str, code_samples: List[str]) -> bool:
        """Determine if LLM analysis should be skipped for performance"""
        
        # Skip if no code samples
        if not code_samples:
            print(f"⚡ Skipping LLM for {gate_name} (no code samples)")
            return True
        
        # Define low-priority gates that can be skipped if needed (reduced list)
        low_priority_gates = [
            'ui_error_tools',  # Only keep truly low-priority gates
            'log_background_jobs'
            # Removed 'http_codes' to allow LLM analysis
        ]
        
        # Skip low-priority gates with minimal samples (lowered threshold)
        if gate_name.lower() in low_priority_gates and len(code_samples) < 1:  # Changed from < 2 to < 1
            print(f"⚡ Skipping LLM for {gate_name} (low priority with {len(code_samples)} samples)")
            return True
        
        print(f"✅ LLM analysis approved for {gate_name} ({len(code_samples)} samples)")
        return False
    
    def _get_fallback_analysis(self, gate_name: str) -> Dict[str, Any]:
        """Get fallback analysis when LLM is not available or times out"""
        
        fallback_recommendations = {
            'structured_logs': [
                "Implement structured logging with JSON format",
                "Add consistent log fields across services",
                "Use correlation IDs in all log messages"
            ],
            'avoid_logging_secrets': [
                "Review all logging statements for sensitive data",
                "Implement log sanitization filters",
                "Use environment variables for secrets"
            ],
            'error_logs': [
                "Log all exceptions with context",
                "Include error codes and user actions",
                "Set up error alerting for critical issues"
            ],
            'retry_logic': [
                "Implement exponential backoff for retries",
                "Add circuit breakers for external services",
                "Set maximum retry limits"
            ],
            'timeouts': [
                "Configure timeouts for all I/O operations",
                "Use appropriate timeout values for different operations",
                "Implement timeout monitoring"
            ]
        }
        
        return {
            'enhanced_quality_score': None,  # Use pattern-based score
            'llm_recommendations': fallback_recommendations.get(gate_name.lower(), [
                f"Implement best practices for {gate_name}",
                "Add comprehensive monitoring",
                "Follow industry standards"
            ]),
            'code_examples': [],
            'security_insights': [],
            'technology_insights': {},
            'patterns_found': [],
            'code_smells': [],
            'best_practices': []
        }
    
    def batch_analyze_gates(self, gate_batches: List[LLMBatch]) -> Dict[str, Dict[str, Any]]:
        """Analyze multiple gates in optimized batches"""
        
        print(f"🚀 Starting batch LLM analysis for {len(gate_batches)} gates")
        
        results = {}
        
        # Sort batches by priority
        sorted_batches = sorted(gate_batches, key=lambda x: x.priority, reverse=True)
        
        # Process high-priority gates first
        high_priority = [b for b in sorted_batches if b.priority >= 3]
        medium_priority = [b for b in sorted_batches if b.priority == 2]
        low_priority = [b for b in sorted_batches if b.priority == 1]
        
        total_processed = 0
        start_time = time.time()
        
        # Process in order of priority with time limits
        for batch_group, time_limit in [(high_priority, 60), (medium_priority, 45), (low_priority, 30)]:
            if time.time() - start_time > 180:  # Total timeout: 3 minutes
                print("⏰ Batch processing timeout reached, using fallback for remaining gates")
                break
                
            for batch in batch_group:
                if time.time() - start_time > time_limit:
                    print(f"⏰ Time limit reached for priority group, skipping remaining")
                    break
                
                results[batch.gate_name] = self.optimize_gate_analysis(
                    batch.gate_name,
                    batch.code_samples,
                    batch.language,
                    batch.technologies
                )
                total_processed += 1
        
        # Fill in fallback results for any missing gates
        for batch in sorted_batches:
            if batch.gate_name not in results:
                results[batch.gate_name] = self._get_fallback_analysis(batch.gate_name)
        
        elapsed = time.time() - start_time
        print(f"✅ Batch analysis completed: {total_processed}/{len(gate_batches)} with LLM in {elapsed:.1f}s")
        
        return results
    
    def get_gate_priority(self, gate_name: str) -> int:
        """Get priority level for a gate (1=low, 2=medium, 3=high)"""
        
        high_priority_gates = [
            'structured_logs',
            'avoid_logging_secrets',
            'error_logs',
            'audit_trail'
        ]
        
        medium_priority_gates = [
            'correlation_id',
            'retry_logic',
            'timeouts',
            'circuit_breakers',
            'automated_tests'
        ]
        
        if gate_name.lower() in high_priority_gates:
            return 3
        elif gate_name.lower() in medium_priority_gates:
            return 2
        else:
            return 1


class FastLLMIntegrationManager:
    """Fast LLM Integration Manager with timeout optimization"""
    
    def __init__(self, llm_integration_manager):
        self.original_manager = llm_integration_manager
        self.optimizer = LLMOptimizer(
            llm_integration_manager.analyzer if llm_integration_manager else None
        ) if llm_integration_manager else None
        
    def is_enabled(self) -> bool:
        """Check if LLM integration is enabled"""
        return self.original_manager and self.original_manager.is_enabled()
    
    def enhance_gate_validation(self, 
                              gate_name: str,
                              matches: List[Dict[str, Any]],
                              language: Language,
                              detected_technologies: Dict[str, List[str]],
                              base_recommendations: List[str]) -> Dict[str, Any]:
        """Enhanced gate validation with timeout optimization"""
        
        if not self.is_enabled():
            return {
                'enhanced_quality_score': None,
                'llm_recommendations': base_recommendations,
                'code_examples': [],
                'security_insights': [],
                'technology_insights': {}
            }
        
        # Extract code samples from matches - FIX: Use correct field names
        code_samples = []
        for match in matches[:10]:  # Limit to 10 matches
            # Try multiple field names for code content
            code_text = (
                match.get('matched_text', '') or 
                match.get('match', '') or 
                match.get('full_line', '') or 
                str(match.get('pattern', ''))
            )
            if code_text and code_text.strip():
                code_samples.append(code_text.strip())
        
        print(f"🔧 Extracted {len(code_samples)} code samples from {len(matches)} matches for {gate_name}")
        
        # Use optimizer for fast analysis
        return self.optimizer.optimize_gate_analysis(
            gate_name, code_samples, language, detected_technologies
        ) 