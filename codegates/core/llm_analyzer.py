"""
LLM Analyzer - Intelligent code analysis using Large Language Models
Enhanced with enterprise support and token management
"""

import json
import re
import os
import uuid
import requests
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from ..models import Language, FileAnalysis
from ..utils.env_loader import EnvironmentLoader
from .analysis_result import CodeAnalysisResult


# Ensure environment is loaded when module is imported
EnvironmentLoader.load_environment()


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    LOCAL = "local"
    ENTERPRISE = "enterprise"


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 8000

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback"""
        return getattr(self, key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Support dictionary-like access"""
        return getattr(self, key)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator"""
        return hasattr(self, key)


@dataclass
class TokenInfo:
    """Token information with expiry tracking"""
    token: str
    expires_at: datetime
    refresh_token: Optional[str] = None


class EnterpriseTokenManager:
    """Manages enterprise LLM tokens with automatic refresh"""
    
    def __init__(self):
        self.token_info: Optional[TokenInfo] = None
        self.refresh_url = os.getenv("ENTERPRISE_LLM_REFRESH_URL")
        self.client_id = os.getenv("ENTERPRISE_LLM_CLIENT_ID")
        self.client_secret = os.getenv("ENTERPRISE_LLM_CLIENT_SECRET")
        self.refresh_token = os.getenv("ENTERPRISE_LLM_REFRESH_TOKEN")
        self.token_lock = threading.Lock()
        
        # Load initial token if provided
        initial_token = os.getenv("ENTERPRISE_LLM_TOKEN")
        if initial_token:
            # Default to 24 hours expiry if not specified
            expires_in_hours = int(os.getenv("ENTERPRISE_LLM_TOKEN_EXPIRY_HOURS", "24"))
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            self.token_info = TokenInfo(
                token=initial_token,
                expires_at=expires_at,
                refresh_token=self.refresh_token
            )
    
    def get_valid_token(self) -> str:
        """Get a valid token, refreshing if necessary"""
        with self.token_lock:
            if not self.token_info:
                raise ValueError("No enterprise token configured. Set ENTERPRISE_LLM_TOKEN in .env file")
            
            # Check if token is expired or will expire in the next 5 minutes
            if datetime.now() >= (self.token_info.expires_at - timedelta(minutes=5)):
                print("🔄 Enterprise token expired or expiring soon, refreshing...")
                self._refresh_token()
            
            return self.token_info.token
    
    def _refresh_token(self):
        """Refresh the enterprise token"""
        if not self.refresh_url:
            raise ValueError("No refresh URL configured. Set ENTERPRISE_LLM_REFRESH_URL in .env file")
        
        if not self.refresh_token and not (self.client_id and self.client_secret):
            raise ValueError("No refresh credentials configured. Set either ENTERPRISE_LLM_REFRESH_TOKEN or both ENTERPRISE_LLM_CLIENT_ID and ENTERPRISE_LLM_CLIENT_SECRET in .env file")
        
        try:
            # Prepare refresh request
            headers = {"Content-Type": "application/json"}
            
            if self.refresh_token:
                # Use refresh token flow
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token
                }
            else:
                # Use client credentials flow
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            
            # Add any additional refresh headers from .env
            refresh_headers_str = os.getenv("ENTERPRISE_LLM_REFRESH_HEADERS", "{}")
            try:
                additional_headers = json.loads(refresh_headers_str)
                headers.update(additional_headers)
            except json.JSONDecodeError:
                print("⚠️ Warning: Invalid ENTERPRISE_LLM_REFRESH_HEADERS format, ignoring")
            
            # Configure proxy if specified
            proxies = self._get_proxy_config()
            
            print(f"🔄 Refreshing token from {self.refresh_url}")
            response = requests.post(
                self.refresh_url,
                headers=headers,
                json=data,
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Token refresh failed with status {response.status_code}: {response.text}")
            
            token_data = response.json()
            
            # Extract new token and expiry
            new_token = token_data.get("access_token") or token_data.get("token")
            if not new_token:
                raise Exception(f"No access token in refresh response: {token_data}")
            
            # Calculate expiry time
            expires_in = token_data.get("expires_in", 24 * 3600)  # Default to 24 hours
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Update refresh token if provided
            new_refresh_token = token_data.get("refresh_token", self.refresh_token)
            
            # Update token info
            self.token_info = TokenInfo(
                token=new_token,
                expires_at=expires_at,
                refresh_token=new_refresh_token
            )
            
            print(f"✅ Token refreshed successfully, expires at {expires_at}")
            
        except Exception as e:
            print(f"❌ Token refresh failed: {str(e)}")
            raise Exception(f"Failed to refresh enterprise token: {str(e)}")

    def _get_proxy_config(self) -> Dict[str, str]:
        """Get proxy configuration from environment variables"""
        proxy = os.getenv("ENTERPRISE_LLM_PROXY")
        
        if proxy:
            # Use the same proxy for both HTTP and HTTPS
            return {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            
        return {}


class LLMAnalyzer:
    """Enhanced LLM-powered code analyzer with enterprise support"""
    
    def __init__(self, model_config: Optional[LLMConfig] = None):
        if model_config is None:
            # Create a default mock config
            self.model_config = LLMConfig(
                provider=LLMProvider.LOCAL,
                model="mock",
                temperature=0.1
            )
        else:
            self.model_config = model_config
        self.chunk_size = 4000  # Maximum size for each chunk
    
    def analyze_gate_implementation(self, gate_name: str, code_samples: List[str], 
                                  language: Language, technologies: Dict[str, List[str]]) -> CodeAnalysisResult:
        """Analyze gate implementation using code samples"""
        
        if not code_samples:
            return self._provide_general_gate_recommendations(gate_name, language, technologies)
        
        # Prepare enhanced context
        enhanced_context = {
            'gate_name': gate_name,
            'language': language,
            'technologies': technologies,
            'code_samples': code_samples,
            'total_matches': len(code_samples),
            'high_priority_issues': [],  # Will be populated during analysis
            'severity_distribution': {}  # Will be populated during analysis
        }
        
        # Use enhanced metadata analysis
        return self.analyze_gate_with_enhanced_metadata(enhanced_context)
    
    def analyze_validation_results(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze gate validation results and generate recommendations
        
        Args:
            validation_results: Dictionary containing gate validation results
                {
                    'gate_name': str,
                    'quality_score': float,
                    'coverage_score': float,
                    'found_patterns': int,
                    'expected_patterns': int,
                    'severity_distribution': Dict[str, int],
                    'implementation_details': List[str]
                }
        
        Returns:
            Dict containing analysis results and recommendations
        """
        try:
            # Split large results into manageable chunks
            chunks = self._split_into_chunks(validation_results)
            
            # Process each chunk and combine results
            combined_analysis = {
                'recommendations': [],
                'quality_insights': [],
                'improvement_areas': []
            }
            
            for chunk in chunks:
                chunk_result = self._analyze_chunk(chunk)
                self._merge_analysis_results(combined_analysis, chunk_result)
            
            return combined_analysis
            
        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            return self._fallback_analysis(validation_results)
    
    def _split_into_chunks(self, validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split large validation results into manageable chunks"""
        chunks = []
        current_chunk = {
            'gate_name': validation_results['gate_name'],
            'quality_score': validation_results['quality_score'],
            'coverage_score': validation_results['coverage_score'],
            'implementation_details': []
        }
        
        current_size = 0
        for detail in validation_results.get('implementation_details', []):
            detail_size = len(str(detail))
            if current_size + detail_size > self.chunk_size:
                # Start new chunk
                chunks.append(current_chunk)
                current_chunk = {
                    'gate_name': validation_results['gate_name'],
                    'quality_score': validation_results['quality_score'],
                    'coverage_score': validation_results['coverage_score'],
                    'implementation_details': []
                }
                current_size = 0
            
            current_chunk['implementation_details'].append(detail)
            current_size += detail_size
        
        if current_chunk['implementation_details']:
            chunks.append(current_chunk)
        
        return chunks
    
    def _analyze_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single chunk of validation results"""
        prompt = self._create_analysis_prompt(chunk)
        
        try:
            # Call LLM with the prompt
            response = self._call_llm(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            print(f"Error analyzing chunk: {e}")
            return self._fallback_chunk_analysis(chunk)
    
    def _create_analysis_prompt(self, chunk: Dict[str, Any]) -> str:
        """Create prompt for LLM analysis"""
        return f"""
Analyze the following code quality gate results and provide specific recommendations:

Gate: {chunk['gate_name']}
Quality Score: {chunk['quality_score']}
Coverage Score: {chunk['coverage_score']}

Implementation Details:
{self._format_details(chunk['implementation_details'])}

Please provide:
1. 2-3 specific recommendations for improvement
2. Quality insights based on the scores
3. Key improvement areas needing attention

Format your response as JSON:
{{
    "recommendations": ["rec1", "rec2", "rec3"],
    "quality_insights": ["insight1", "insight2"],
    "improvement_areas": ["area1", "area2"]
}}
"""
    
    def _format_details(self, details: List[str]) -> str:
        """Format implementation details for prompt"""
        formatted = []
        total_length = 0
        
        for detail in details:
            if total_length + len(detail) + 1 > 1900:  # Leave room for truncation message
                formatted.append("... (additional details omitted)")
                break
            formatted.append(detail)
            total_length += len(detail) + 1  # +1 for newline
        
        return "\n".join(formatted)
    
    def _merge_analysis_results(self, combined: Dict[str, Any], chunk_result: Dict[str, Any]):
        """Merge chunk analysis results into combined results"""
        # Merge recommendations (avoid duplicates)
        existing_recs = set(combined['recommendations'])
        for rec in chunk_result.get('recommendations', []):
            if rec not in existing_recs:
                combined['recommendations'].append(rec)
                existing_recs.add(rec)
        
        # Merge insights
        combined['quality_insights'].extend(chunk_result.get('quality_insights', []))
        
        # Merge improvement areas (avoid duplicates)
        existing_areas = set(combined['improvement_areas'])
        for area in chunk_result.get('improvement_areas', []):
            if area not in existing_areas:
                combined['improvement_areas'].append(area)
                existing_areas.add(area)
    
    def _fallback_analysis(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when LLM is unavailable"""
        gate_name = validation_results['gate_name']
        quality_score = validation_results['quality_score']
        
        # Basic recommendations based on scores
        recommendations = []
        if quality_score < 50:
            recommendations.extend([
                f"Improve {gate_name} implementation - current quality score is low",
                "Review and implement missing patterns",
                "Add proper error handling and logging"
            ])
        elif quality_score < 80:
            recommendations.extend([
                "Enhance existing implementations with better practices",
                "Add more comprehensive error handling",
                "Improve logging coverage"
            ])
        else:
            recommendations.extend([
                "Maintain current good practices",
                "Consider adding advanced features",
                "Regular review and updates"
            ])
        
        return {
            'recommendations': recommendations,
            'quality_insights': [
                f"Current quality score: {quality_score}",
                "Generated by fallback analysis"
            ],
            'improvement_areas': [
                "Implementation coverage",
                "Code quality",
                "Best practices"
            ]
        }
    
    def _fallback_chunk_analysis(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis for individual chunks"""
        return {
            'recommendations': [
                f"Review {chunk['gate_name']} implementation",
                "Ensure proper error handling",
                "Add comprehensive logging"
            ],
            'quality_insights': [
                f"Chunk quality score: {chunk['quality_score']}"
            ],
            'improvement_areas': [
                "Implementation details",
                "Code quality"
            ]
        }
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt and return response"""
        if not self.model_config:
            raise Exception("LLM not configured")
            
        # Mock implementation for testing
        if self.model_config.get('mock', False):
            return '{"recommendations": ["Test"], "quality_insights": ["Test"], "improvement_areas": ["Test"]}'
        
        # Get provider-specific configuration
        provider = self.model_config.provider
        model = self.model_config.model
        api_key = self.model_config.api_key
        base_url = self.model_config.base_url
        temperature = self.model_config.temperature
        max_tokens = self.model_config.max_tokens
        
        try:
            if provider == LLMProvider.OPENAI:
                import openai
                openai.api_key = api_key
                if base_url:
                    openai.api_base = base_url
                
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            
            elif provider == LLMProvider.ANTHROPIC:
                import anthropic
                client = anthropic.Client(api_key=api_key)
                if base_url:
                    client.base_url = base_url
                
                response = client.messages.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.content[0].text
            
            elif provider == LLMProvider.GEMINI:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                if base_url:
                    genai.configure(api_base=base_url)
                
                model = genai.GenerativeModel(model)
                response = model.generate_content(prompt)
                return response.text
            
            elif provider == LLMProvider.OLLAMA:
                import ollama
                if base_url:
                    ollama.base_url = base_url
                
                response = ollama.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature
                )
                return response.message.content
            
            elif provider == LLMProvider.ENTERPRISE:
                # Get enterprise token
                token_manager = EnterpriseTokenManager()
                token = token_manager.get_valid_token()
                
                # Configure enterprise API endpoint
                enterprise_url = base_url or os.getenv("ENTERPRISE_LLM_URL")
                if not enterprise_url:
                    raise ValueError("Enterprise LLM URL not configured")
                
                # Make API request
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                response = requests.post(
                    enterprise_url,
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code != 200:
                    raise Exception(f"Enterprise LLM request failed: {response.text}")
                
                return response.json()["response"]
            
            elif provider == LLMProvider.LOCAL:
                # Local LLM implementation using OpenAI-compatible API
                if not base_url:
                    raise ValueError("Local LLM URL not configured")
                
                headers = {"Content-Type": "application/json"}
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                response = requests.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code != 200:
                    raise Exception(f"Local LLM request failed: {response.text}")
                
                try:
                    return response.json()["choices"][0]["message"]["content"]
                except (KeyError, json.JSONDecodeError) as e:
                    print(f"⚠️ Error parsing LLM response: {e}")
                    print(f"Response content: {response.text[:200]}...")
                    raise Exception("Failed to parse LLM response")
            
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        
        except Exception as e:
            print(f"⚠️ LLM call failed: {str(e)}")
            raise Exception(f"LLM call failed: {str(e)}")
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print("Error parsing LLM response")
            return {
                'recommendations': [],
                'quality_insights': [],
                'improvement_areas': []
            }
    
    def enhance_recommendations(self, 
                              base_recommendations: List[str],
                              gate_name: str,
                              language: Language,
                              detected_technologies: Dict[str, List[str]]) -> List[str]:
        """Enhance basic recommendations with LLM insights"""
        
        if not self.model_config:
            return base_recommendations
        
        prompt = f"""
Given these basic recommendations for {gate_name} in {language.value}:
{chr(10).join(f"- {rec}" for rec in base_recommendations)}

Technologies detected: {detected_technologies}

Please enhance these recommendations with:
1. Specific code examples
2. Technology-specific best practices
3. Implementation steps
4. Potential pitfalls to avoid

Provide 3-5 enhanced, actionable recommendations in a simple list format.
"""
        
        try:
            response = self._call_llm(prompt)
            
            # Extract recommendations from response
            enhanced_recs = []
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    enhanced_recs.append(line.lstrip('-•0123456789. '))
            
            return enhanced_recs[:5] if enhanced_recs else base_recommendations
        
        except Exception:
            return base_recommendations
    
    def generate_code_examples(self, 
                             gate_name: str,
                             language: Language,
                             detected_technologies: Dict[str, List[str]]) -> List[str]:
        """Generate code examples for implementing the gate"""
        
        if not self.model_config:
            return []
        
        tech_context = ""
        if detected_technologies:
            main_techs = []
            for category, techs in detected_technologies.items():
                main_techs.extend(techs[:2])  # Top 2 from each category
            tech_context = f"using {', '.join(main_techs[:3])}"
        
        prompt = f"""
Generate 2-3 practical code examples for implementing {gate_name} in {language.value} {tech_context}.

Examples should be:
1. Production-ready
2. Following best practices
3. Technology-specific
4. Well-commented
5. Realistic (not toy examples)

Format each example with a brief description followed by the code.
"""
        
        try:
            response = self._call_llm(prompt)
            
            # Parse code examples from response
            examples = []
            code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', response, re.DOTALL)
            for i, code in enumerate(code_blocks[:3]):
                examples.append(f"Example {i+1}:\n```{language.value}\n{code.strip()}\n```")
            
            return examples
        
        except Exception:
            return []
    
    def _provide_general_gate_recommendations(self, 
                                            gate_name: str,
                                            language: Language,
                                            detected_technologies: Dict[str, List[str]]) -> CodeAnalysisResult:
        """Provide general recommendations for a gate when no code samples are found"""
        
        # Technology-specific recommendations
        tech_recommendations = []
        
        if language == Language.PYTHON:
            if gate_name == "structured_logs":
                tech_recommendations = [
                    "Use Python's logging module with structured formatters",
                    "Consider using structlog for better structured logging",
                    "Add JSON formatting to your log handlers"
                ]
            elif gate_name == "error_logs":
                tech_recommendations = [
                    "Use try-except blocks with proper logging",
                    "Log exceptions with traceback information",
                    "Include context information in error logs"
                ]
        
        return CodeAnalysisResult(
            quality_score=50.0,  # Neutral score for general recommendations
            patterns_found=[],
            security_issues=[],
            recommendations=tech_recommendations,
            technology_insights={"general": f"No specific {gate_name} patterns found for {language.value}"},
            code_smells=[],
            best_practices=tech_recommendations
        )
    
    def analyze_gate_with_enhanced_metadata(self, enhanced_context: Dict[str, Any]) -> CodeAnalysisResult:
        """Analyze gate implementation using enhanced metadata"""
        
        try:
            # Create comprehensive prompt using enhanced metadata
            prompt = self._build_enhanced_analysis_prompt(enhanced_context)
            
            # Call LLM with enhanced context
            response = self._call_llm(prompt)
            
            # Parse the enhanced response
            analysis = self._parse_enhanced_analysis_response(response, enhanced_context)
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Enhanced LLM analysis failed: {e}")
            # Fallback to basic analysis
            return self._fallback_enhanced_analysis(enhanced_context)
    
    def _build_enhanced_analysis_prompt(self, enhanced_context: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt using enhanced metadata"""
        
        gate_name = enhanced_context['gate_name']
        language = enhanced_context['language']
        total_matches = enhanced_context['total_matches']
        severity_dist = enhanced_context.get('severity_distribution', {})
        pattern_types = enhanced_context.get('pattern_types', {})  # Use get() with default
        technologies = enhanced_context.get('detected_technologies', {})
        high_priority = enhanced_context.get('high_priority_issues', [])
        enhanced_samples = enhanced_context.get('enhanced_samples', [])
        coverage_stats = enhanced_context.get('coverage_stats', {})
        
        # Build technology context
        tech_context = ""
        if technologies:
            tech_list = []
            for category, techs in technologies.items():
                if techs:
                    tech_list.append(f"  {category}: {', '.join(techs)}")
            if tech_list:
                tech_context = f"\n\nDetected Technologies:\n" + "\n".join(tech_list)
        
        # Build severity analysis
        severity_context = ""
        if severity_dist:
            severity_context = f"\n\nSeverity Analysis:\n"
            for severity, count in severity_dist.items():
                severity_context += f"  {severity}: {count} issues\n"
        
        # Build pattern types context
        pattern_context = ""
        if pattern_types:
            pattern_context = f"\n\nPattern Types:\n"
            for pattern, count in pattern_types.items():
                pattern_context += f"  {pattern}: {count} occurrences\n"
        
        # Build high priority issues context
        priority_context = ""
        if high_priority:
            priority_context = f"\n\nHigh Priority Issues ({len(high_priority)}):\n"
            for issue in high_priority[:5]:  # Limit to top 5
                priority_context += f"  {issue['file']}:{issue['line']} - {issue['severity']} (Priority: {issue['priority']})\n"
                priority_context += f"    Code: {issue['code'][:100]}...\n"
                if issue.get('suggested_fix'):
                    priority_context += f"    Suggested Fix: {issue['suggested_fix']}\n"
        
        # Build enhanced samples context
        samples_context = ""
        if enhanced_samples:
            samples_context = f"\n\nCode Analysis Samples:\n"
            for i, sample in enumerate(enhanced_samples[:5], 1):
                samples_context += f"{i}. {sample['file']}:{sample['line']} ({sample['severity']})\n"
                samples_context += f"   Code: {sample['code']}\n"
                samples_context += f"   Context: {sample.get('full_line', '')}\n"
                samples_context += f"   Pattern: {sample['pattern_type']}, Category: {sample['category']}\n"
                if sample.get('function_context'):
                    func_name = sample['function_context'].get('function_name', 'unknown')
                    samples_context += f"   Function: {func_name}\n"
                if sample.get('suggested_fix'):
                    samples_context += f"   Suggested Fix: {sample['suggested_fix']}\n"
                samples_context += "\n"
        
        prompt = f"""
You are a senior software architect and code quality expert. Analyze the following comprehensive code quality gate results and provide detailed insights.

## Gate Analysis: {gate_name}
- **Language**: {language}
- **Total Issues Found**: {total_matches}
- **Files Affected**: {coverage_stats.get('total_files', 0)}
- **Functions Affected**: {coverage_stats.get('functions_affected', 0)}
- **Security Issues**: {coverage_stats.get('security_issues', 0)}

{tech_context}
{severity_context}
{pattern_context}
{priority_context}
{samples_context}

## Coverage Statistics
- High Severity: {coverage_stats.get('high_severity_count', 0)} issues
- Medium Severity: {coverage_stats.get('medium_severity_count', 0)} issues  
- Low Severity: {coverage_stats.get('low_severity_count', 0)} issues

## Analysis Required
Based on this comprehensive analysis, provide:

1. **Quality Score** (0-100): Overall implementation quality
2. **Security Issues**: Critical security concerns identified
3. **Patterns Found**: Key implementation patterns detected
4. **Technology Insights**: Technology-specific observations
5. **Code Smells**: Problematic code patterns
6. **Best Practices**: Recommended practices for this gate
7. **Code Examples**: Improved code examples for the language/framework

## Response Format
Provide your analysis as a JSON object:
{{
    "quality_score": <number>,
    "security_issues": [
        "Critical security issue 1",
        "Security concern 2"
    ],
    "patterns_found": [
        "Pattern 1 description",
        "Pattern 2 description"
    ],
    "technology_insights": {{
        "framework": "Framework-specific insights",
        "language": "Language-specific observations",
        "libraries": "Library usage analysis"
    }},
    "code_smells": [
        "Code smell 1 with location",
        "Code smell 2 with impact"
    ],
    "best_practices": [
        "Best practice 1 for {gate_name}",
        "Best practice 2 for {language}"
    ],
    "code_examples": [
        "Example 1: Improved implementation",
        "Example 2: Better pattern usage"
    ]
}}

Focus on actionable insights based on the actual code patterns and metadata provided.
"""
        
        return prompt.strip()
    
    def _parse_enhanced_analysis_response(self, response: str, enhanced_context: Dict[str, Any]) -> CodeAnalysisResult:
        """Parse enhanced LLM analysis response"""
        
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                data = json.loads(response)
                
                return CodeAnalysisResult(
                    quality_score=float(data.get('quality_score', 50.0)),
                    patterns_found=data.get('patterns_found', []),
                    security_issues=data.get('security_issues', []),
                    recommendations=data.get('best_practices', []),
                    technology_insights=data.get('technology_insights', {}),
                    code_smells=data.get('code_smells', []),
                    best_practices=data.get('best_practices', [])
                )
            else:
                # Parse as text response
                return self._parse_enhanced_text_response(response, enhanced_context)
                
        except Exception as e:
            print(f"⚠️ Failed to parse enhanced LLM response: {e}")
            return self._fallback_enhanced_analysis(enhanced_context)
    
    def _parse_enhanced_text_response(self, response: str, enhanced_context: Dict[str, Any]) -> CodeAnalysisResult:
        """Parse text-based enhanced analysis response"""
        
        # Extract quality score
        quality_score = 50.0
        score_match = re.search(r'quality[:\s]*(\d+(?:\.\d+)?)', response, re.IGNORECASE)
        if score_match:
            quality_score = float(score_match.group(1))
        
        # Extract sections
        security_issues = re.findall(r'security[:\s]*(.+?)(?=\n\n|\n[A-Z]|$)', response, re.IGNORECASE | re.DOTALL)
        patterns_found = re.findall(r'pattern[s]?[:\s]*(.+?)(?=\n\n|\n[A-Z]|$)', response, re.IGNORECASE | re.DOTALL)
        recommendations = re.findall(r'recommend[ation]*[s]?[:\s]*(.+?)(?=\n\n|\n[A-Z]|$)', response, re.IGNORECASE | re.DOTALL)
        
        return CodeAnalysisResult(
            quality_score=quality_score,
            patterns_found=[p.strip() for p in patterns_found if p.strip()],
            security_issues=[s.strip() for s in security_issues if s.strip()],
            recommendations=[r.strip() for r in recommendations if r.strip()],
            technology_insights={"analysis": "Enhanced text-based analysis"},
            code_smells=[],
            best_practices=[r.strip() for r in recommendations if r.strip()]
        )
    
    def _fallback_enhanced_analysis(self, enhanced_context: Dict[str, Any]) -> CodeAnalysisResult:
        """Fallback analysis when LLM fails"""
        
        gate_name = enhanced_context['gate_name']
        severity_dist = enhanced_context['severity_distribution']
        high_priority = enhanced_context['high_priority_issues']
        
        # Calculate quality score based on severity distribution
        total_issues = sum(severity_dist.values()) if severity_dist else 0
        high_severity = severity_dist.get('HIGH', 0)
        
        if total_issues == 0:
            quality_score = 90.0
        elif high_severity > 5:
            quality_score = 30.0
        elif high_severity > 0:
            quality_score = 50.0
        else:
            quality_score = 70.0
        
        # Generate basic recommendations
        recommendations = []
        if high_priority:
            recommendations.append(f"Address {len(high_priority)} high-priority issues immediately")
        if high_severity > 0:
            recommendations.append(f"Fix {high_severity} high-severity issues in {gate_name}")
        
        return CodeAnalysisResult(
            quality_score=quality_score,
            patterns_found=[f"Found {total_issues} {gate_name} patterns"],
            security_issues=[f"High-priority security issues detected: {len(high_priority)}"] if high_priority else [],
            recommendations=recommendations,
            technology_insights={"fallback": "Basic analysis due to LLM unavailability"},
            code_smells=[],
            best_practices=recommendations
        )
    
    def generate_enhanced_recommendations(self, enhanced_context: Dict[str, Any], 
                                        base_recommendations: List[str]) -> List[str]:
        """Generate enhanced recommendations using rich metadata"""
        
        try:
            # Create recommendation prompt using enhanced context
            prompt = self._build_enhanced_recommendation_prompt(enhanced_context, base_recommendations)
            
            # Call LLM
            response = self._call_llm(prompt)
            
            # Parse recommendations
            enhanced_recs = self._parse_recommendation_response(response)
            
            if enhanced_recs:
                return enhanced_recs
            else:
                return base_recommendations
                
        except Exception as e:
            print(f"⚠️ Enhanced recommendation generation failed: {e}")
            return base_recommendations
    
    def _build_enhanced_recommendation_prompt(self, enhanced_context: Dict[str, Any], 
                                            base_recommendations: List[str]) -> str:
        """Build enhanced recommendation prompt"""
        
        gate_name = enhanced_context['gate_name']
        language = enhanced_context['language']
        severity_dist = enhanced_context['severity_distribution']
        high_priority = enhanced_context['high_priority_issues']
        technologies = enhanced_context['detected_technologies']
        
        # Build context summary
        context_summary = f"""
Gate: {gate_name}
Language: {language}
High Priority Issues: {len(high_priority)}
Severity Distribution: {severity_dist}
Technologies: {technologies}
"""
        
        # Build high priority issues context
        priority_context = ""
        if high_priority:
            priority_context = "\n\nHigh Priority Issues:\n"
            for issue in high_priority[:3]:
                priority_context += f"- {issue['file']}:{issue['line']} - {issue['code'][:50]}...\n"
                priority_context += f"  Severity: {issue['severity']}, Fix: {issue['suggested_fix']}\n"
        
        prompt = f"""
You are a senior software architect. Based on the following code analysis, provide specific, actionable recommendations.

{context_summary}
{priority_context}

Current Basic Recommendations:
{chr(10).join(f"- {rec}" for rec in base_recommendations)}

## Task
Enhance these recommendations with:
1. **Immediate Actions**: Critical fixes needed now
2. **Technology-Specific**: Recommendations for the detected technologies
3. **Implementation Strategy**: Step-by-step improvement plan
4. **Monitoring**: How to prevent future issues

Provide 3-5 enhanced, specific recommendations as a JSON array:
{{
    "recommendations": [
        "Specific recommendation 1 with concrete steps",
        "Technology-specific recommendation 2",
        "Implementation strategy recommendation 3",
        "Monitoring recommendation 4"
    ]
}}
"""
        
        return prompt.strip()
    
    def _parse_recommendation_response(self, response: str) -> List[str]:
        """Parse LLM recommendation response"""
        
        try:
            # Try JSON parsing first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return data.get('recommendations', [])
            
            # Parse as text with bullet points
            lines = response.split('\n')
            recommendations = []
            
            for line in lines:
                line = line.strip()
                # Remove bullet points and numbering
                line = re.sub(r'^[-*•]\s*', '', line)
                line = re.sub(r'^\d+\.\s*', '', line)
                
                if line and len(line) > 20:  # Filter out short lines
                    recommendations.append(line)
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            print(f"⚠️ Failed to parse recommendation response: {e}")
            return []


class LLMIntegrationManager:
    """Manages LLM integration for the gate validation system"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or self._get_default_config()
        self.analyzer = LLMAnalyzer(self.config) if config else None
        self.enabled = config is not None
        
        # Pass manager reference to analyzer for error verification
        if self.analyzer:
            self.analyzer.manager = self
        
        # Cache for availability check
        self._availability_cache = None
        self._last_availability_check = None
        self._availability_cache_duration = 300  # 5 minutes in seconds
    
    def _get_default_config(self) -> LLMConfig:
        """Get default LLM configuration"""
        return LLMConfig(
            provider=LLMProvider.LOCAL,
            model="mock",
            temperature=0.1
        )
    
    def _should_check_availability(self) -> bool:
        """Check if we need to perform availability check"""
        if self._last_availability_check is None:
            return True
        
        from datetime import datetime, timedelta
        now = datetime.now()
        cache_expiry = self._last_availability_check + timedelta(seconds=self._availability_cache_duration)
        
        return now > cache_expiry
    
    def is_enabled(self) -> bool:
        """Check if LLM integration is properly enabled and accessible"""
        if not self.config:
            return False
        
        # Use cached result if available and not expired
        if not self._should_check_availability() and self._availability_cache is not None:
            return self._availability_cache
        
        # For cloud providers, just check if we have the required config (no HTTP call)
        if self.config.provider != LLMProvider.LOCAL:
            is_available = bool(self.config.api_key and self.config.model)
            self._availability_cache = is_available
            self._last_availability_check = datetime.now()
            return is_available
        
        # For local LLM, assume it's working unless we've had a recent failure
        # Only do the HTTP check if this is the first time or if cache expired
        if self._last_availability_check is None:
            # First time - do a quick check
            try:
                import requests
                from datetime import datetime
                
                response = requests.get(
                    f"{self.config.base_url.rstrip('/')}/models",
                    timeout=2  # Very quick timeout
                )
                
                if response.status_code == 200:
                    models = response.json()
                    print(f"🤖 LLM service available at: {self.config.base_url}")
                    
                    # Check if our model is available
                    if isinstance(models, dict) and 'data' in models:
                        available_models = [model.get('id', '') for model in models['data']]
                    else:
                        available_models = []
                    
                    is_available = self.config.model in available_models
                    
                    if is_available:
                        print(f"✅ Model {self.config.model} confirmed available")
                    else:
                        print(f"⚠️ Model {self.config.model} not found, but will try to use it anyway")
                        print(f"   Available models: {available_models}")
                        # Still return True - let the actual LLM call fail if model is wrong
                        is_available = True
                    
                    self._availability_cache = is_available
                    self._last_availability_check = datetime.now()
                    return is_available
                else:
                    print(f"⚠️ LLM service check failed with status {response.status_code}, assuming available")
                    # Assume it's working - let LLM calls handle the errors
                    self._availability_cache = True
                    self._last_availability_check = datetime.now()
                    return True
                    
            except Exception as e:
                print(f"⚠️ LLM service check failed: {e}, assuming available")
                # Assume it's working - let LLM calls handle the errors
                self._availability_cache = True
                self._last_availability_check = datetime.now()
                return True
        else:
            # Not first time and cache hasn't expired - assume it's working
            return self._availability_cache if self._availability_cache is not None else True
    
    def verify_model_availability_on_error(self, error_message: str) -> bool:
        """Verify model availability when an LLM call fails"""
        print(f"🔍 LLM call failed, verifying model availability...")
        print(f"   Error: {error_message}")
        
        if self.config.provider != LLMProvider.LOCAL:
            print("   Cloud provider - cannot verify model list")
            return False
        
        try:
            import requests
            from datetime import datetime
            
            response = requests.get(
                f"{self.config.base_url.rstrip('/')}/models",
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json()
                print(f"🤖 Checking available models at: {self.config.base_url}")
                
                if isinstance(models, dict) and 'data' in models:
                    available_models = [model.get('id', '') for model in models['data']]
                else:
                    available_models = []
                
                if self.config.model in available_models:
                    print(f"✅ Model {self.config.model} is available - error might be temporary")
                    return True
                else:
                    print(f"❌ Model {self.config.model} not found in LLM service")
                    print(f"   Available models: {available_models}")
                    print(f"   Please update your model name or load the correct model")
                    
                    # Update cache to reflect the issue
                    self._availability_cache = False
                    self._last_availability_check = datetime.now()
                    return False
            else:
                print(f"⚠️ LLM service returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ Failed to verify model availability: {e}")
            return False
    
    def set_availability_cache_duration(self, seconds: int):
        """Set the duration for caching availability checks"""
        self._availability_cache_duration = seconds
    
    def get_availability_status(self) -> Dict[str, Any]:
        """Get detailed availability status including cache info"""
        from datetime import datetime, timedelta
        
        status = {
            'enabled': self.enabled,
            'cached_result': self._availability_cache,
            'cache_valid': False,
            'last_check': None,
            'next_check': None
        }
        
        if self._last_availability_check:
            status['last_check'] = self._last_availability_check.isoformat()
            cache_expiry = self._last_availability_check + timedelta(seconds=self._availability_cache_duration)
            status['cache_valid'] = datetime.now() < cache_expiry
            status['next_check'] = cache_expiry.isoformat()
        
        return status
    
    def force_availability_check(self) -> bool:
        """Force a fresh availability check, bypassing cache"""
        print("🔄 Forcing fresh LLM availability check...")
        self._last_availability_check = None
        self._availability_cache = None
        return self.is_enabled()
    
    def enhance_gate_validation(self, 
                              gate_name: str,
                              matches: List[Dict[str, Any]],
                              language: Language,
                              detected_technologies: Dict[str, List[str]],
                              base_recommendations: List[str]) -> Dict[str, Any]:
        """Enhance gate validation with LLM analysis using enhanced metadata"""
        
        print(f"🤖 LLM enhance_gate_validation called for {gate_name}")
        print(f"   - Matches received: {len(matches)}")
        print(f"   - Language: {language}")
        print(f"   - LLM enabled: {self.is_enabled()}")
        
        if not self.is_enabled():
            print(f"   - LLM not enabled, returning base recommendations")
            return {
                'enhanced_quality_score': None,
                'llm_recommendations': base_recommendations,
                'code_examples': [],
                'security_insights': [],
                'technology_insights': {}
            }
        
        # Debug: Show sample match structure
        if matches:
            sample_match = matches[0]
            print(f"   - Sample match keys: {list(sample_match.keys())}")
            print(f"   - Sample match content: {str(sample_match)[:200]}...")
        
        try:
            # Prepare enhanced context using rich metadata from matches
            enhanced_context = self._prepare_enhanced_context(
                gate_name, matches, language, detected_technologies
            )
            
            print(f"   - Enhanced context prepared with {enhanced_context['total_matches']} matches")
            print(f"   - High priority issues: {len(enhanced_context['high_priority_issues'])}")
            
            # Use enhanced metadata for comprehensive LLM analysis
            analysis_result = self.analyzer.analyze_gate_with_enhanced_metadata(enhanced_context)
            
            print(f"   - LLM analysis completed successfully")
            
            return {
                'enhanced_quality_score': analysis_result.quality_score,
                'llm_recommendations': analysis_result.recommendations,
                'code_examples': analysis_result.best_practices,
                'security_insights': analysis_result.security_issues,
                'technology_insights': analysis_result.technology_insights,
                'patterns_found': analysis_result.patterns_found,
                'code_smells': analysis_result.code_smells
            }
            
        except Exception as e:
            print(f"   - LLM analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback to base recommendations
            return {
                'enhanced_quality_score': None,
                'llm_recommendations': base_recommendations,
                'code_examples': [],
                'security_insights': [],
                'technology_insights': {}
            }
    
    def _prepare_enhanced_context(self, gate_name: str, matches: List[Dict[str, Any]], 
                                language: Language, detected_technologies: Dict[str, List[str]]) -> Dict[str, Any]:
        """Prepare enhanced context using rich metadata from matches"""
        
        # Extract key information from enhanced metadata
        files_analyzed = list(set(match.get('relative_path', match.get('file', 'unknown')) for match in matches))
        severity_counts = {}
        pattern_types = {}
        function_contexts = []
        high_priority_issues = []
        
        for match in matches:
            # Count severities
            severity = match.get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count pattern types
            pattern_type = match.get('pattern_type', 'unknown')
            pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
            
            # Collect function contexts
            func_context = match.get('function_context')
            if func_context and func_context.get('function_name'):
                function_contexts.append({
                    'function': func_context.get('function_name', 'unknown'),
                    'line': func_context.get('line_number', 0),
                    'signature': func_context.get('signature', ''),
                    'file': match.get('file_name', 'unknown')
                })
            
            # Collect high priority issues
            priority = match.get('priority', 0)
            if priority >= 8:  # High priority threshold
                high_priority_issues.append({
                    'file': match.get('file_name', 'unknown'),
                    'line': match.get('line_number', 0),
                    'code': match.get('matched_text', match.get('match', '')),
                    'severity': severity,
                    'priority': priority,
                    'category': match.get('category', 'unknown'),
                    'suggested_fix': match.get('suggested_fix', '')
                })
        
        # Get sample matches with enhanced details (limit to avoid token overflow)
        sample_matches = matches[:10] if len(matches) > 10 else matches
        
        # Prepare enhanced sample data
        enhanced_samples = []
        for match in sample_matches:
            enhanced_sample = {
                'file': match.get('file_name', 'unknown'),
                'relative_path': match.get('relative_path', 'unknown'),
                'line': match.get('line_number', 0),
                'column': match.get('column_start', 0),
                'code': match.get('matched_text', match.get('match', '')),
                'full_line': match.get('full_line', ''),
                'context_lines': match.get('context_lines', []),
                'severity': match.get('severity', 'UNKNOWN'),
                'priority': match.get('priority', 0),
                'category': match.get('category', 'unknown'),
                'pattern_type': match.get('pattern_type', 'unknown'),
                'language': match.get('language', language.value if language else 'unknown'),
                'function_context': match.get('function_context', {}),
                'suggested_fix': match.get('suggested_fix', ''),
                'documentation_link': match.get('documentation_link', ''),
                'is_comment': match.get('is_comment', False),
                'is_string_literal': match.get('is_string_literal', False)
            }
            enhanced_samples.append(enhanced_sample)
        
        enhanced_context = {
            'gate_name': gate_name,
            'language': language.value if language else 'unknown',
            'total_matches': len(matches),
            'files_analyzed': files_analyzed[:10],  # Limit for context
            'severity_distribution': severity_counts,
            'pattern_types': pattern_types,
            'detected_technologies': detected_technologies,
            'function_contexts': function_contexts[:5],  # Top 5 functions
            'high_priority_issues': high_priority_issues,
            'enhanced_samples': enhanced_samples,
            'coverage_stats': {
                'total_files': len(files_analyzed),
                'high_severity_count': severity_counts.get('HIGH', 0),
                'medium_severity_count': severity_counts.get('MEDIUM', 0),
                'low_severity_count': severity_counts.get('LOW', 0),
                'security_issues': len([m for m in matches if 'security' in m.get('category', '').lower()]),
                'functions_affected': len(function_contexts)
            }
        }
        
        return enhanced_context 