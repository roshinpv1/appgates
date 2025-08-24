"""
Hard Gate Analyzer Service
Orchestrates the complete hard gate analysis workflow
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

try:
    from .advanced_llm.core import AdvancedLLMService
    from .advanced_llm.vector_store import VectorStore
    from .advanced_llm.pattern_library import PatternLibraryService
    from .utils.git_operations import get_repository_info, clone_repository
    from .nodes import EnhancedGateEvaluator
except ImportError:
    from advanced_llm.core import AdvancedLLMService
    from advanced_llm.vector_store import VectorStore
    from advanced_llm.pattern_library import PatternLibraryService
    from utils.git_operations import get_repository_info, clone_repository
    from nodes import EnhancedGateEvaluator


class GateStatus(Enum):
    """Gate evaluation status"""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class GateResult:
    """Result of gate evaluation"""
    gate_id: str
    gate_name: str
    status: GateStatus
    expected_count: int
    actual_count: int
    threshold: int
    patterns_found: List[str]
    recommendations: List[str]
    confidence_score: float
    reasoning: str


@dataclass
class ScanRequest:
    """Scan request parameters"""
    repo_url: str
    branch: str
    git_token: Optional[str] = None
    app_id: Optional[str] = None
    scan_id: Optional[str] = None


@dataclass
class ScanResult:
    """Complete scan result"""
    scan_id: str
    app_id: str
    repo_url: str
    branch: str
    scan_timestamp: datetime
    total_gates: int
    passed_gates: int
    failed_gates: int
    partial_gates: int
    skipped_gates: int
    gate_results: List[GateResult]
    recommendations: List[str]
    risk_score: float
    scan_duration: float


class HardGateAnalyzer:
    """
    Main orchestrator for hard gate analysis workflow
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the hard gate analyzer"""
        self.config = config
        self.advanced_llm = None
        self.vector_store = None
        self.pattern_library = None
        self.gate_evaluator = None
        self.prompt_library = None
        
        # Initialize components
        self._initialize_components()
        
        # Load externalized libraries
        self._load_externalized_libraries()
        
        print("✅ Hard Gate Analyzer initialized")
    
    def _initialize_components(self):
        """Initialize all required components"""
        try:
            # Initialize Advanced LLM Service
            self.advanced_llm = AdvancedLLMService(self.config.get("advanced_llm", {}))
            
            # Initialize Vector Store
            vector_config = self.config.get("vector_store", {})
            self.vector_store = VectorStore(vector_config)
            
            # Initialize Pattern Library
            self.pattern_library = PatternLibraryService()
            
            # Initialize Gate Evaluator
            self.gate_evaluator = EnhancedGateEvaluator(codebase_files=[])
            
            print("✅ Core components initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            raise
    
    def _load_externalized_libraries(self):
        """Load externalized prompt and pattern libraries"""
        try:
            # Load Prompt Library
            prompt_library_path = self.config.get("prompt_library_path", "prompt_library.json")
            if os.path.exists(prompt_library_path):
                with open(prompt_library_path, 'r') as f:
                    self.prompt_library = json.load(f)
                print(f"✅ Loaded prompt library: {len(self.prompt_library)} prompts")
            else:
                print("⚠️ Prompt library not found, using defaults")
                self.prompt_library = self._get_default_prompts()
            
            # Pattern library is already loaded via PatternLibraryService
            print(f"✅ Pattern library loaded: {len(self.pattern_library.patterns)} patterns")
            
        except Exception as e:
            print(f"⚠️ Failed to load externalized libraries: {e}")
            self.prompt_library = self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """Get default prompt templates"""
        return {
            "llm_pre_analysis": {
                "use_case": "pre_analysis",
                "prompt_template": """
                Analyze the following repository for hard gate compliance:
                
                Repository Structure: {code_structure}
                Key Config Files: {config_files}
                Hard Gate Summary: {hard_gate_summary}
                
                Generate:
                1. Regex patterns for each applicable gate
                2. Gate applicability assessment
                3. Expected implementation patterns
                
                Format output as JSON with the following structure:
                {{
                    "patterns": [
                        {{
                            "gate_id": "gate_name",
                            "pattern": "regex_pattern",
                            "description": "pattern_description",
                            "severity": "high|medium|low",
                            "applicable": true|false
                        }}
                    ],
                    "gate_applicability": [
                        {{
                            "gate_id": "gate_name",
                            "applicable": true|false,
                            "reasoning": "why applicable or not"
                        }}
                    ]
                }}
                """,
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            },
            "llm_post_analysis": {
                "use_case": "post_analysis",
                "prompt_template": """
                Analyze the scan results and provide recommendations:
                
                Scan Results: {scan_results}
                Project Config: {project_config}
                Embedding Extracts: {embedding_extracts}
                
                Provide:
                1. Detailed recommendations for failed/partial gates
                2. Risk analysis and impact assessment
                3. Remediation steps and best practices
                
                Format as structured recommendations with priority levels.
                """,
                "parameters": {
                    "temperature": 0.4,
                    "max_tokens": 3000
                }
            }
        }
    
    async def analyze_repository(self, request: ScanRequest) -> ScanResult:
        """
        Main workflow: Analyze repository for hard gate compliance
        """
        start_time = datetime.now()
        scan_id = request.scan_id or f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            print(f"🚀 Starting hard gate analysis for {request.repo_url}")
            
            # Step 1: Repository Checkout
            print("📥 Step 1: Repository Checkout")
            repo_info = await self._checkout_repository(request)
            
            # Step 2: Vectorization & Storage
            print("🧠 Step 2: Vectorization & Storage")
            repo_id = await self._vectorize_repository(repo_info)
            
            # Step 3: LLM Pre-Analysis
            print("🤖 Step 3: LLM Pre-Analysis")
            llm_patterns = await self._llm_pre_analysis(repo_info, repo_id)
            
            # Step 4: Pattern Consolidation
            print("🔧 Step 4: Pattern Consolidation")
            consolidated_patterns = await self._consolidate_patterns(llm_patterns)
            
            # Step 5: Expected Implementations
            print("🔍 Step 5: Expected Implementations")
            expected_implementations = await self._get_expected_implementations(repo_id, consolidated_patterns)
            
            # Step 6: File Scanning
            print("📁 Step 6: File Scanning")
            scan_results = await self._scan_files(repo_info, consolidated_patterns)
            
            # Step 7: Threshold Check & Gate Evaluation
            print("⚖️ Step 7: Threshold Check & Gate Evaluation")
            gate_results = await self._evaluate_gates(scan_results, expected_implementations)
            
            # Step 8: LLM Post-Analysis
            print("🧠 Step 8: LLM Post-Analysis")
            recommendations = await self._llm_post_analysis(gate_results, repo_info, repo_id)
            
            # Step 9: Generate Final Result
            print("📊 Step 9: Generate Final Result")
            scan_result = self._generate_scan_result(
                scan_id, request, gate_results, recommendations, start_time
            )
            
            # Step 10: Store for Agentic Use
            print("💾 Step 10: Store for Agentic Use")
            await self._store_for_agentic_use(scan_result, repo_id)
            
            print(f"✅ Hard gate analysis completed in {scan_result.scan_duration:.2f} seconds")
            return scan_result
            
        except Exception as e:
            print(f"❌ Hard gate analysis failed: {e}")
            raise
    
    async def _checkout_repository(self, request: ScanRequest) -> Dict[str, Any]:
        """Step 1: Checkout repository"""
        try:
            # Clone repository
            repo_path = await clone_repository(
                request.repo_url, 
                request.branch, 
                request.git_token
            )
            
            # Get repository info
            repo_info = await get_repository_info(repo_path)
            repo_info['local_path'] = repo_path
            
            print(f"✅ Repository checked out: {repo_path}")
            return repo_info
            
        except Exception as e:
            print(f"❌ Repository checkout failed: {e}")
            raise
    
    async def _vectorize_repository(self, repo_info: Dict[str, Any]) -> str:
        """Step 2: Vectorize repository"""
        try:
            # Use existing Advanced LLM Service to index repository
            repo_id = await self.advanced_llm.index_repository(
                repo_info['local_path'],
                branch=repo_info.get('branch', 'main')
            )
            
            print(f"✅ Repository vectorized: {repo_id}")
            return repo_id
            
        except Exception as e:
            print(f"❌ Repository vectorization failed: {e}")
            raise
    
    async def _llm_pre_analysis(self, repo_info: Dict[str, Any], repo_id: str) -> Dict[str, Any]:
        """Step 3: LLM Pre-Analysis"""
        try:
            # Get code structure and config files
            code_structure = self._get_code_structure(repo_info['local_path'])
            config_files = self._get_config_files(repo_info['local_path'])
            hard_gate_summary = self._get_hard_gate_summary()
            
            # Build prompt
            prompt_template = self.prompt_library["llm_pre_analysis"]["prompt_template"]
            prompt = prompt_template.format(
                code_structure=code_structure,
                config_files=config_files,
                hard_gate_summary=hard_gate_summary
            )
            
            # Call LLM
            response = await self.advanced_llm.complete(prompt)
            
            # Parse response
            try:
                llm_output = json.loads(response.get('content', '{}'))
                print(f"✅ LLM pre-analysis completed: {len(llm_output.get('patterns', []))} patterns")
                return llm_output
            except json.JSONDecodeError:
                print("⚠️ LLM response not valid JSON, using fallback")
                return self._get_fallback_patterns()
                
        except Exception as e:
            print(f"❌ LLM pre-analysis failed: {e}")
            return self._get_fallback_patterns()
    
    async def _consolidate_patterns(self, llm_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Step 4: Pattern Consolidation"""
        try:
            consolidated = []
            
            # Add LLM-generated patterns
            for pattern in llm_patterns.get('patterns', []):
                if pattern.get('applicable', False):
                    consolidated.append({
                        'source': 'llm',
                        'gate_id': pattern['gate_id'],
                        'pattern': pattern['pattern'],
                        'description': pattern['description'],
                        'severity': pattern['severity']
                    })
            
            # Add static patterns from pattern library
            static_pattern_infos = list(self.pattern_library.patterns.values())
            for pattern_info in static_pattern_infos:
                # Get the first pattern from the patterns list, or use a default
                pattern_text = pattern_info.patterns[0] if pattern_info.patterns else ""
                consolidated.append({
                    'source': 'static',
                    'gate_id': pattern_info.gate_id,
                    'pattern': pattern_text,
                    'description': pattern_info.description,
                    'severity': pattern_info.priority
                })
            
            print(f"✅ Pattern consolidation completed: {len(consolidated)} patterns")
            return consolidated
            
        except Exception as e:
            print(f"❌ Pattern consolidation failed: {e}")
            return []
    
    async def _get_expected_implementations(self, repo_id: str, patterns: List[Dict[str, Any]]) -> Dict[str, int]:
        """Step 5: Expected Implementations"""
        try:
            expected_counts = {}
            
            for pattern in patterns:
                gate_id = pattern['gate_id']
                
                # Search embeddings for expected patterns
                query = f"Find implementations of {pattern['description']}"
                results = await self.vector_store.search(
                    query=query,
                    collection=repo_id,
                    limit=10
                )
                
                # Estimate expected count based on search results
                expected_count = len(results) if results else 1
                expected_counts[gate_id] = expected_count
            
            print(f"✅ Expected implementations calculated: {len(expected_counts)} gates")
            return expected_counts
            
        except Exception as e:
            print(f"❌ Expected implementations failed: {e}")
            return {}
    
    async def _scan_files(self, repo_info: Dict[str, Any], patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Step 6: File Scanning"""
        try:
            scan_results = {
                'files_scanned': 0,
                'patterns_found': {},
                'gate_results': {}
            }
            
            # Use existing gate evaluator for scanning
            for pattern in patterns:
                gate_id = pattern['gate_id']
                pattern_regex = pattern['pattern']
                
                # Scan for pattern occurrences
                matches = await self.gate_evaluator.scan_pattern(
                    repo_info['local_path'],
                    pattern_regex,
                    pattern['description']
                )
                
                scan_results['patterns_found'][gate_id] = matches
                scan_results['gate_results'][gate_id] = {
                    'pattern': pattern,
                    'matches': matches,
                    'count': len(matches)
                }
            
            scan_results['files_scanned'] = len(os.listdir(repo_info['local_path']))
            print(f"✅ File scanning completed: {scan_results['files_scanned']} files")
            return scan_results
            
        except Exception as e:
            print(f"❌ File scanning failed: {e}")
            return {'files_scanned': 0, 'patterns_found': {}, 'gate_results': {}}
    
    def _evaluate_gates(self, scan_results: Dict[str, Any], expected_implementations: Dict[str, int]) -> List[GateResult]:
        """Step 7: Threshold Check & Gate Evaluation"""
        try:
            gate_results = []
            
            for gate_id, gate_data in scan_results['gate_results'].items():
                pattern = gate_data['pattern']
                actual_count = gate_data['count']
                expected_count = expected_implementations.get(gate_id, 1)
                threshold = self._get_threshold_for_gate(gate_id)
                
                # Threshold check
                if actual_count >= threshold:
                    status = GateStatus.SKIPPED
                    reasoning = f"Threshold met ({actual_count} >= {threshold})"
                else:
                    # Gate evaluation
                    if actual_count >= expected_count:
                        status = GateStatus.PASS
                    elif actual_count > 0:
                        status = GateStatus.PARTIAL
                    else:
                        status = GateStatus.FAIL
                    
                    reasoning = f"Expected: {expected_count}, Actual: {actual_count}"
                
                gate_result = GateResult(
                    gate_id=gate_id,
                    gate_name=pattern.get('description', gate_id),
                    status=status,
                    expected_count=expected_count,
                    actual_count=actual_count,
                    threshold=threshold,
                    patterns_found=gate_data['matches'],
                    recommendations=[],
                    confidence_score=0.8,
                    reasoning=reasoning
                )
                
                gate_results.append(gate_result)
            
            print(f"✅ Gate evaluation completed: {len(gate_results)} gates")
            return gate_results
            
        except Exception as e:
            print(f"❌ Gate evaluation failed: {e}")
            return []
    
    async def _llm_post_analysis(self, gate_results: List[GateResult], repo_info: Dict[str, Any], repo_id: str) -> List[str]:
        """Step 8: LLM Post-Analysis"""
        try:
            # Prepare inputs for LLM
            scan_results = [asdict(result) for result in gate_results]
            project_config = self._get_project_config(repo_info['local_path'])
            embedding_extracts = await self._get_embedding_extracts(repo_id, gate_results)
            
            # Build prompt
            prompt_template = self.prompt_library["llm_post_analysis"]["prompt_template"]
            prompt = prompt_template.format(
                scan_results=json.dumps(scan_results, indent=2),
                project_config=json.dumps(project_config, indent=2),
                embedding_extracts=json.dumps(embedding_extracts, indent=2)
            )
            
            # Call LLM
            response = await self.advanced_llm.complete(prompt)
            recommendations = response.get('content', '').split('\n')
            
            print(f"✅ LLM post-analysis completed: {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            print(f"❌ LLM post-analysis failed: {e}")
            return ["Analysis failed - manual review required"]
    
    def _generate_scan_result(self, scan_id: str, request: ScanRequest, gate_results: List[GateResult], 
                            recommendations: List[str], start_time: datetime) -> ScanResult:
        """Step 9: Generate Final Result"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        total_gates = len(gate_results)
        passed_gates = len([g for g in gate_results if g.status == GateStatus.PASS])
        failed_gates = len([g for g in gate_results if g.status == GateStatus.FAIL])
        partial_gates = len([g for g in gate_results if g.status == GateStatus.PARTIAL])
        skipped_gates = len([g for g in gate_results if g.status == GateStatus.SKIPPED])
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(gate_results)
        
        return ScanResult(
            scan_id=scan_id,
            app_id=request.app_id or "unknown",
            repo_url=request.repo_url,
            branch=request.branch,
            scan_timestamp=end_time,
            total_gates=total_gates,
            passed_gates=passed_gates,
            failed_gates=failed_gates,
            partial_gates=partial_gates,
            skipped_gates=skipped_gates,
            gate_results=gate_results,
            recommendations=recommendations,
            risk_score=risk_score,
            scan_duration=duration
        )
    
    async def _store_for_agentic_use(self, scan_result: ScanResult, repo_id: str):
        """Step 10: Store for Agentic Use"""
        try:
            # Store scan result in vector database
            scan_data = asdict(scan_result)
            scan_data['scan_timestamp'] = scan_data['scan_timestamp'].isoformat()
            
            # Convert to embedding and store
            scan_text = json.dumps(scan_data, indent=2)
            embedding = await self.advanced_llm.embedding_service.embed_single(scan_text)
            
            if embedding:
                await self.vector_store.upsert_vectors(
                    collection_name=f"scan_results_{repo_id}",
                    vectors=[{
                        'id': scan_result.scan_id,
                        'vector': embedding,
                        'payload': scan_data
                    }]
                )
            
            print(f"✅ Scan result stored for agentic use: {scan_result.scan_id}")
            
        except Exception as e:
            print(f"⚠️ Failed to store for agentic use: {e}")
    
    # Helper methods
    def _get_code_structure(self, repo_path: str) -> str:
        """Get code structure summary"""
        try:
            # Simple file structure analysis
            files = []
            for root, dirs, filenames in os.walk(repo_path):
                for filename in filenames:
                    if filename.endswith(('.py', '.js', '.java', '.go', '.rs')):
                        rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                        files.append(rel_path)
            
            return f"Repository contains {len(files)} code files: {', '.join(files[:10])}..."
        except Exception:
            return "Code structure analysis failed"
    
    def _get_config_files(self, repo_path: str) -> Dict[str, str]:
        """Get key configuration files"""
        config_files = {}
        config_patterns = ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.cfg']
        
        try:
            for pattern in config_patterns:
                import glob
                matches = glob.glob(os.path.join(repo_path, '**', pattern), recursive=True)
                for match in matches[:5]:  # Limit to 5 files per pattern
                    rel_path = os.path.relpath(match, repo_path)
                    try:
                        with open(match, 'r') as f:
                            content = f.read()[:500]  # First 500 chars
                            config_files[rel_path] = content
                    except:
                        config_files[rel_path] = "[Unable to read file]"
            
            return config_files
        except Exception:
            return {"error": "Config file analysis failed"}
    
    def _get_hard_gate_summary(self) -> str:
        """Get hard gate summary"""
        return """
        Hard Gates Summary:
        1. Security Gates: Authentication, Authorization, Input Validation, Data Encryption
        2. Performance Gates: Caching, Database Optimization, Resource Management
        3. Quality Gates: Code Coverage, Static Analysis, Documentation
        4. Compliance Gates: Licensing, Privacy, Regulatory Requirements
        5. Architecture Gates: Design Patterns, Modularity, Scalability
        """
    
    def _get_fallback_patterns(self) -> Dict[str, Any]:
        """Get fallback patterns when LLM fails"""
        return {
            "patterns": [
                {
                    "gate_id": "security_auth",
                    "pattern": r"(auth|authentication|login)",
                    "description": "Authentication implementation",
                    "severity": "high",
                    "applicable": True
                }
            ],
            "gate_applicability": [
                {
                    "gate_id": "security_auth",
                    "applicable": True,
                    "reasoning": "Basic security gate always applicable"
                }
            ]
        }
    
    def _get_threshold_for_gate(self, gate_id: str) -> int:
        """Get threshold for a specific gate"""
        thresholds = {
            "security_auth": 1,
            "security_input_validation": 3,
            "performance_caching": 2,
            "quality_documentation": 5,
            "default": 1
        }
        return thresholds.get(gate_id, thresholds["default"])
    
    def _get_project_config(self, repo_path: str) -> Dict[str, Any]:
        """Get project configuration"""
        config_files = self._get_config_files(repo_path)
        return {
            "config_files": config_files,
            "repo_path": repo_path
        }
    
    async def _get_embedding_extracts(self, repo_id: str, gate_results: List[GateResult]) -> List[Dict[str, Any]]:
        """Get relevant embedding extracts"""
        try:
            extracts = []
            for result in gate_results:
                if result.status in [GateStatus.FAIL, GateStatus.PARTIAL]:
                    # Search for relevant code snippets
                    query = f"Find code related to {result.gate_name}"
                    results = await self.vector_store.search(
                        query=query,
                        collection=repo_id,
                        limit=3
                    )
                    
                    for res in results:
                        extracts.append({
                            'gate_id': result.gate_id,
                            'content': res.payload.get('content', ''),
                            'file_path': res.payload.get('file_path', ''),
                            'similarity': res.score
                        })
            
            return extracts
        except Exception:
            return []
    
    def _calculate_risk_score(self, gate_results: List[GateResult]) -> float:
        """Calculate overall risk score"""
        if not gate_results:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for result in gate_results:
            weight = 1.0
            if result.status == GateStatus.FAIL:
                score = 1.0
            elif result.status == GateStatus.PARTIAL:
                score = 0.5
            elif result.status == GateStatus.SKIPPED:
                score = 0.3
            else:  # PASS
                score = 0.0
            
            # Adjust weight based on severity
            if 'security' in result.gate_id.lower():
                weight = 2.0
            elif 'performance' in result.gate_id.lower():
                weight = 1.5
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
