"""
Scan flow nodes for the 10-step process
"""

import os
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.base import AsyncNode, ScanContext
from models.scan_models import (
    RepositoryInfo, CodeChunk, Pattern, GateResult, GateStatus,
    ContextualRecommendation, RecommendationType, ScanResult
)
from utils.git_utils import GitUtils
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService
from services.ast_parser_service import ASTParserService


class RepositoryCheckoutNode(AsyncNode):
    """Step 1: Repository Checkout and extract metadata (including CD repos)"""
    
    def __init__(self):
        super().__init__()
        self.git_utils = GitUtils()
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare repository checkout"""
        return {
            "repo_url": context.repo_url,
            "branch": context.branch,
            "git_token": context.git_token
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute repository checkout including CD repository"""
        try:
            print("📥 Step 1: Repository Checkout and extract metadata (including CD repos)")
            
            repo_url = prep_res["repo_url"]
            branch = prep_res["branch"]
            git_token = prep_res["git_token"]
            
            # Clone main repository
            main_repo_path = await self.git_utils.clone_repository(
                repo_url, branch, git_token
            )
            
            # Extract main repository information
            main_repo_info = await self.git_utils.get_repository_info(main_repo_path)
            
            # Try to clone CD repository
            cd_repo_path = None
            cd_repo_info = None
            
            try:
                cd_repo_url = self._get_cd_repo_url(repo_url)
                print(f"🔍 Attempting to clone CD repository: {cd_repo_url}")
                
                cd_repo_path = await self.git_utils.clone_repository(
                    cd_repo_url, branch, git_token
                )
                
                cd_repo_info = await self.git_utils.get_repository_info(cd_repo_path)
                print(f"✅ CD repository checked out: {cd_repo_path}")
                print(f"📊 CD repository info: {cd_repo_info.total_files} files, {cd_repo_info.total_lines} lines")
                
            except Exception as e:
                print(f"⚠️ CD repository not found or failed to clone: {e}")
                cd_repo_path = None
                cd_repo_info = None
            
            # Store in context
            self.context.repo_path = main_repo_path
            self.context.cd_repo_path = cd_repo_path
            self.context.metadata = {
                "main_repo": main_repo_info.__dict__,
                "cd_repo": cd_repo_info.__dict__ if cd_repo_info else None,
                "has_cd_repo": cd_repo_info is not None
            }
            
            print(f"✅ Main repository checked out: {main_repo_path}")
            print(f"📊 Main repository info: {main_repo_info.total_files} files, {main_repo_info.total_lines} lines")
            
            if cd_repo_info:
                print(f"🔄 CD repository included in analysis")
            
            return "success"
            
        except Exception as e:
            print(f"❌ Repository checkout failed: {e}")
            return "error"
    
    def _get_cd_repo_url(self, repo_url: str) -> str:
        """Generate CD repository URL by adding '-cd' suffix"""
        # Handle different repository URL formats
        if repo_url.endswith('.git'):
            base_url = repo_url[:-4]  # Remove .git
            return f"{base_url}-cd.git"
        else:
            return f"{repo_url}-cd"
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-checkout processing"""
        if exec_res == "success":
            context.repo_path = self.context.repo_path
            context.cd_repo_path = self.context.cd_repo_path
            context.metadata = self.context.metadata
        return exec_res


class VectorizationNode(AsyncNode):
    """Step 2: Vectorization & Storage"""
    
    def __init__(self, vector_service: VectorService, embedding_service: EmbeddingService, 
                 ast_parser_service: ASTParserService):
        super().__init__()
        self.vector_service = vector_service
        self.embedding_service = embedding_service
        self.ast_parser_service = ast_parser_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare vectorization"""
        return {
            "repo_path": context.repo_path,
            "cd_repo_path": context.cd_repo_path,
            "metadata": context.metadata
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute vectorization for both main and CD repositories"""
        try:
            import time
            start_time = time.time()
            print("🧠 Step 2: Vectorization & Storage (including CD repos)")
            
            repo_path = prep_res["repo_path"]
            cd_repo_path = prep_res["cd_repo_path"]
            metadata = prep_res["metadata"]
            
            # Handle case where metadata is None
            if not metadata:
                print("❌ No metadata available for vectorization")
                return "error"
            
            main_repo_metadata = metadata.get("main_repo")
            cd_repo_metadata = metadata.get("cd_repo")
            
            if not main_repo_metadata:
                print("❌ No main repository metadata available")
                return "error"
            
            # Create collection for main repository
            main_repo_id = hashlib.md5(f"{main_repo_metadata['repo_url']}_{main_repo_metadata['commit_hash']}".encode()).hexdigest()[:16]
            main_collection_name = f"repo_{main_repo_id}"
            
            if not self.vector_service.collection_exists(main_collection_name):
                self.vector_service.create_collection(main_collection_name)
            
            # Process main repository
            main_vectors = []
            main_chunks = []
            
            print(f"📁 Processing main repository: {repo_path}")
            
            # Limit files for large repositories to improve performance
            max_files = 1000  # Process max 1000 files for performance
            processed_files = 0
            
            for file_path in Path(repo_path).rglob("*"):
                if processed_files >= max_files:
                    print(f"⚠️ Reached file limit ({max_files}), skipping remaining files")
                    break
                    
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    try:
                        file_chunks = await self._process_file(file_path, repo_path, main_repo_id, "main")
                        main_chunks.extend(file_chunks)
                        
                        # Create embeddings for chunks
                        for chunk in file_chunks:
                            embedding = self.embedding_service.embed_single(chunk["content"])
                            if embedding:
                                main_vectors.append({
                                    "id": chunk["id"],
                                    "vector": embedding,
                                    "payload": chunk["metadata"]
                                })
                        
                        processed_files += 1
                        
                        # Progress indicator for large repositories
                        if processed_files % 100 == 0:
                            print(f"   📊 Processed {processed_files} files...")
                    
                    except Exception as e:
                        print(f"⚠️ Failed to process file {file_path}: {e}")
                        continue
            
            # Process CD repository if available
            cd_vectors = []
            cd_chunks = []
            cd_collection_name = None
            
            if cd_repo_path and cd_repo_metadata:
                cd_repo_id = hashlib.md5(f"{cd_repo_metadata['repo_url']}_{cd_repo_metadata['commit_hash']}".encode()).hexdigest()[:16]
                cd_collection_name = f"repo_{cd_repo_id}_cd"
                
                if not self.vector_service.collection_exists(cd_collection_name):
                    self.vector_service.create_collection(cd_collection_name)
                
                print(f"📁 Processing CD repository: {cd_repo_path}")
                for file_path in Path(cd_repo_path).rglob("*"):
                    if file_path.is_file() and not self._should_ignore_file(file_path):
                        try:
                            file_chunks = await self._process_file(file_path, cd_repo_path, cd_repo_id, "cd")
                            cd_chunks.extend(file_chunks)
                            
                            # Create embeddings for chunks
                            for chunk in file_chunks:
                                embedding = self.embedding_service.embed_single(chunk["content"])
                                if embedding:
                                    cd_vectors.append({
                                        "id": chunk["id"],
                                        "vector": embedding,
                                        "payload": chunk["metadata"]
                                    })
                        
                        except Exception as e:
                            print(f"⚠️ Failed to process CD file {file_path}: {e}")
                            continue
            
            # Store main repository vectors
            if main_vectors:
                self.vector_service.upsert_vectors(main_collection_name, main_vectors)
                print(f"✅ Stored {len(main_vectors)} vectors in main collection {main_collection_name}")
            
            # Store CD repository vectors
            if cd_vectors:
                self.vector_service.upsert_vectors(cd_collection_name, cd_vectors)
                print(f"✅ Stored {len(cd_vectors)} vectors in CD collection {cd_collection_name}")
            
            # Store in context
            self.context.vector_data = {
                "main_repo_id": main_repo_id,
                "main_collection_name": main_collection_name,
                "main_vectors_count": len(main_vectors),
                "main_chunks_count": len(main_chunks),
                "cd_repo_id": cd_repo_id if cd_repo_path else None,
                "cd_collection_name": cd_collection_name,
                "cd_vectors_count": len(cd_vectors),
                "cd_chunks_count": len(cd_chunks),
                "total_vectors_count": len(main_vectors) + len(cd_vectors),
                "total_chunks_count": len(main_chunks) + len(cd_chunks),
                "has_cd_repo": cd_repo_path is not None
            }
            
            elapsed_time = time.time() - start_time
            print(f"✅ Vectorization completed (took {elapsed_time:.2f}s)")
            
            return "success"
            
        except Exception as e:
            print(f"❌ Vectorization failed: {e}")
            return "error"
    
    async def _process_file(self, file_path: Path, repo_root: Path, repo_id: str, repo_type: str = "main") -> List[Dict[str, Any]]:
        """Process individual file"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Determine language
            language = self._detect_language(file_path)
            
            # Parse with AST if supported
            ast_result = self.ast_parser_service.parse_file(content, language)
            
            # Create chunks
            chunks = []
            
            if ast_result.get("symbols"):
                # Create symbol-based chunks
                for symbol in ast_result["symbols"]:
                    if isinstance(symbol, dict):
                        symbol_name = symbol.get("name", "unknown")
                        start_line = symbol.get("start_line", 0)
                        end_line = symbol.get("end_line", 0)
                    else:
                        symbol_name = symbol.name
                        start_line = symbol.start_line
                        end_line = symbol.end_line
                    
                    # Extract symbol content
                    lines = content.split('\n')
                    symbol_lines = lines[start_line-1:end_line] if start_line > 0 else []
                    symbol_content = '\n'.join(symbol_lines)
                    
                    if len(symbol_content.strip()) >= 10:
                        chunk_id = f"{repo_id}_{file_path.name}_{symbol_name}_{start_line}"
                        chunks.append({
                            "id": chunk_id,
                            "content": symbol_content,
                            "metadata": {
                                "repo_id": repo_id,
                                "repo_type": repo_type,
                                "file_path": str(file_path.relative_to(repo_root)),
                                "filename": file_path.name,
                                "language": language,
                                "start_line": start_line,
                                "end_line": end_line,
                                "symbol_name": symbol_name,
                                "symbol_kind": "function" if "function" in symbol_name.lower() else "class",
                                "content_hash": hashlib.md5(symbol_content.encode()).hexdigest()
                            }
                        })
            
            # If no symbols, create sliding window chunks
            if not chunks:
                chunks = self._create_sliding_chunks(content, file_path, repo_root, repo_id, language, repo_type)
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ Failed to process file {file_path}: {e}")
            return []
    
    def _create_sliding_chunks(self, content: str, file_path: Path, repo_root: Path, 
                              repo_id: str, language: str, repo_type: str = "main") -> List[Dict[str, Any]]:
        """Create sliding window chunks"""
        chunks = []
        lines = content.split('\n')
        chunk_size = 50  # lines per chunk
        overlap = 10     # overlapping lines
        
        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            
            if len(chunk_content.strip()) >= 10:
                chunk_id = f"{repo_id}_{file_path.name}_chunk_{i}"
                chunks.append({
                    "id": chunk_id,
                    "content": chunk_content,
                    "metadata": {
                        "repo_id": repo_id,
                        "repo_type": repo_type,
                        "file_path": str(file_path.relative_to(repo_root)),
                        "filename": file_path.name,
                        "language": language,
                        "start_line": i + 1,
                        "end_line": min(i + chunk_size, len(lines)),
                        "content_hash": hashlib.md5(chunk_content.encode()).hexdigest()
                    }
                })
        
        return chunks
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp'
        }
        return language_map.get(ext, 'text')
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
            '.pytest_cache', 'target', 'build', 'dist', 'out',
            '.idea', '.vscode', '.vs', '.DS_Store'
        ]
        
        for pattern in ignore_patterns:
            if pattern in str(file_path):
                return True
        
        # Ignore binary files
        binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
                           '.mp4', '.avi', '.mov', '.mp3', '.wav',
                           '.zip', '.tar', '.gz', '.rar', '.7z',
                           '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                           '.exe', '.dll', '.so', '.dylib',
                           '.jar', '.war', '.ear', '.class'}
        
        if file_path.suffix.lower() in binary_extensions:
            return True
        
        return False
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-vectorization processing"""
        if exec_res == "success":
            context.vector_data = self.context.vector_data
        return exec_res


class LLMPreAnalysisNode(AsyncNode):
    """Step 3: LLM Pre-Analysis (Dynamic Patterns)"""
    
    def __init__(self, llm_service):
        super().__init__()
        self.llm_service = llm_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare LLM pre-analysis"""
        return {
            "metadata": context.metadata,
            "vector_data": context.vector_data
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute LLM pre-analysis"""
        try:
            import time
            start_time = time.time()
            print("🤖 Step 3: LLM Pre-Analysis (Dynamic Patterns)")
            
            metadata = prep_res["metadata"]
            vector_data = prep_res["vector_data"]
            
            # Handle case where metadata is None
            if not metadata:
                print("❌ No metadata available for LLM pre-analysis")
                return "error"
            
            # Build project structure summary
            project_summary = self._build_project_summary(metadata)
            
            # Get build configuration content
            build_configs = self._get_build_configs(metadata)
            
            # Create prompt for LLM
            prompt = self._create_pre_analysis_prompt(project_summary, build_configs)
            
            # Call LLM for dynamic patterns
            print("   📞 Calling LLM service...")
            response = await self.llm_service.generate(
                prompt,
                scan_id=self.context.scan_id,
                node_name="LLMPreAnalysisNode",
                metadata={
                    "project_summary": project_summary,
                    "build_configs": build_configs,
                    "vector_data": vector_data
                }
            )
            print(f"   📝 LLM response received ({len(response)} chars)")
            
            # Parse response to extract patterns
            print("   🔍 Parsing LLM response...")
            dynamic_patterns = self._parse_llm_response(response)
            
            # Store in context
            self.context.patterns = {
                "dynamic": dynamic_patterns,
                "static": []  # Will be populated in next step
            }
            
            elapsed_time = time.time() - start_time
            print(f"✅ Generated {len(dynamic_patterns)} dynamic patterns (took {elapsed_time:.2f}s)")
            
            return "success"
            
        except Exception as e:
            print(f"❌ LLM pre-analysis failed: {e}")
            return "error"
    
    def _build_project_summary(self, metadata: Dict[str, Any]) -> str:
        """Build project structure summary"""
        # Handle the nested metadata structure
        main_repo = metadata.get('main_repo', {})
        cd_repo = metadata.get('cd_repo')
        
        summary = f"""
Project Summary:
- Repository: {main_repo.get('repo_url', 'Unknown')}
- Branch: {main_repo.get('branch', 'Unknown')}
- Total Files: {main_repo.get('total_files', 0)}
- Total Lines: {main_repo.get('total_lines', 0)}
- Languages: {', '.join(main_repo.get('languages', []))}
- Dependencies: {main_repo.get('dependencies', {})}
- Build Files: {', '.join(main_repo.get('build_files', []))}
- Config Files: {', '.join(main_repo.get('config_files', []))}
"""
        
        if cd_repo:
            summary += f"""
CD Repository:
- Repository: {cd_repo.get('repo_url', 'Unknown')}
- Total Files: {cd_repo.get('total_files', 0)}
- Total Lines: {cd_repo.get('total_lines', 0)}
"""
        
        return summary
    
    def _get_build_configs(self, metadata: Dict[str, Any]) -> str:
        """Get build configuration content"""
        try:
            main_repo = metadata.get('main_repo', {})
            repo_path = main_repo.get('local_path')
            
            if not repo_path:
                return "No repository path available for build config extraction."
            
            build_files = main_repo.get('build_files', [])
            config_files = main_repo.get('config_files', [])
            
            if not build_files and not config_files:
                return "No build or config files detected in the repository."
            
            config_content = []
            
            # Extract build files content
            if build_files:
                config_content.append("BUILD FILES:")
                for build_file in build_files[:5]:  # Limit to first 5 files
                    file_path = os.path.join(repo_path, build_file)
                    content = self._read_file_content(file_path, max_lines=50)
                    if content:
                        config_content.append(f"\n{build_file}:")
                        config_content.append(content)
                    else:
                        config_content.append(f"\n{build_file}: (file not found or empty)")
            
            # Extract config files content
            if config_files:
                config_content.append("\nCONFIG FILES:")
                for config_file in config_files[:5]:  # Limit to first 5 files
                    file_path = os.path.join(repo_path, config_file)
                    content = self._read_file_content(file_path, max_lines=50)
                    if content:
                        config_content.append(f"\n{config_file}:")
                        config_content.append(content)
                    else:
                        config_content.append(f"\n{config_file}: (file not found or empty)")
            
            # Add summary
            total_files = len(build_files) + len(config_files)
            if total_files > 10:
                config_content.append(f"\nNote: Showing content for first 10 files out of {total_files} total build/config files.")
            
            return "\n".join(config_content)
            
        except Exception as e:
            print(f"⚠️ Error extracting build configs: {e}")
            return f"Error extracting build configuration content: {str(e)}"
    
    def _read_file_content(self, file_path: str, max_lines: int = 50) -> str:
        """Read file content with line limit"""
        try:
            if not os.path.exists(file_path):
                return ""
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"... (truncated at {max_lines} lines)")
                        break
                    lines.append(line.rstrip())
                
                content = "\n".join(lines)
                
                # Truncate if too long
                if len(content) > 2000:
                    content = content[:2000] + "\n... (content truncated)"
                
                return content
                
        except Exception as e:
            print(f"⚠️ Error reading file {file_path}: {e}")
            return f"Error reading file: {str(e)}"
    
    def _create_pre_analysis_prompt(self, project_summary: str, build_configs: str) -> str:
        """Create prompt for LLM pre-analysis"""
        from services.prompt_service import PromptService
        
        prompt_service = PromptService()
        
        return prompt_service.format_prompt(
            "llm_pre_analysis",
            code_structure=project_summary,
            config_files=build_configs,
            hard_gate_summary="Project analysis for hard gate compliance"
        ) or f"""
Analyze the following project and generate applicable security, performance, and quality patterns:

{project_summary}

Build Configurations:
{build_configs}

Please generate patterns in the following JSON format:
{{
    "patterns": [
        {{
            "gate_id": "unique_id",
            "name": "Pattern Name",
            "description": "Pattern description",
            "pattern": "regex_pattern",
            "severity": "HIGH|MEDIUM|LOW",
            "category": "SECURITY|PERFORMANCE|QUALITY|OBSERVABILITY",
            "examples": ["example1", "example2"]
        }}
    ]
}}

Focus on patterns relevant to the project's technology stack and domain.
"""
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract patterns"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                
                # Clean up common JSON issues
                json_str = json_str.replace("\\n", "\\n")  # Fix newlines
                json_str = json_str.replace("\\t", "\\t")  # Fix tabs
                
                # Try to parse the JSON
                data = json.loads(json_str)
                patterns = data.get("patterns", [])
                
                if patterns:
                    return patterns
                else:
                    print("⚠️ No patterns found in LLM response")
                    return self._create_fallback_patterns()
            else:
                print("⚠️ No JSON structure found in LLM response")
                return self._create_fallback_patterns()
                
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed: {e}")
            print(f"Response preview: {response[:200]}...")
            return self._create_fallback_patterns()
        except Exception as e:
            print(f"⚠️ Failed to parse LLM response: {e}")
            return self._create_fallback_patterns()
    
    def _create_fallback_patterns(self) -> List[Dict[str, Any]]:
        """Create fallback patterns focused on hard gates when LLM response parsing fails"""
        return [
            # Auditability Hard Gates
            {
                "gate_id": "1.1",
                "name": "Logs Searchable/Available",
                "description": "Logs are searchable and available for both the platform and development team",
                "pattern": r"log|logger|logging|syslog|centralized.*log",
                "severity": "HIGH",
                "category": "AUDITABILITY",
                "examples": ["logging configuration", "centralized logging", "log aggregation"]
            },
            {
                "gate_id": "1.3",
                "name": "Audit Trail",
                "description": "Maintain logs of user and system activity",
                "pattern": r"audit|audit.*trail|user.*activity|system.*activity",
                "severity": "HIGH",
                "category": "AUDITABILITY",
                "examples": ["audit trail", "user activity logging", "system audit"]
            },
            {
                "gate_id": "1.5",
                "name": "Implement tracking ID for log messages",
                "description": "Log messages include a tracking ID where possible",
                "pattern": r"tracking.*id|request.*id|correlation.*id|trace.*id",
                "severity": "MEDIUM",
                "category": "AUDITABILITY",
                "examples": ["request tracking", "correlation ID", "trace ID"]
            },
            {
                "gate_id": "1.6",
                "name": "Log API Calls",
                "description": "Log REST API calls to capture external component interaction",
                "pattern": r"api.*log|rest.*log|http.*log|request.*log",
                "severity": "HIGH",
                "category": "AUDITABILITY",
                "examples": ["API logging", "REST call logging", "HTTP request logging"]
            },
            {
                "gate_id": "1.8",
                "name": "Log Application Messages",
                "description": "Log application messages with standard log libraries",
                "pattern": r"log.*library|logging.*framework|app.*log|application.*log",
                "severity": "HIGH",
                "category": "AUDITABILITY",
                "examples": ["logging library", "application logging", "log framework"]
            },
            {
                "gate_id": "1.10",
                "name": "Avoid Logging Sensitive Data",
                "description": "Prevent logging confidential and/or restricted data",
                "pattern": r"mask.*log|redact.*log|sensitive.*data|password.*log|token.*log",
                "severity": "CRITICAL",
                "category": "AUDITABILITY",
                "examples": ["log masking", "sensitive data redaction", "password masking"]
            },
            # Error Handling Hard Gates
            {
                "gate_id": "1.1",
                "name": "Log system errors",
                "description": "Log system errors for troubleshooting",
                "pattern": r"error.*log|system.*error|exception.*log|crash.*log",
                "severity": "HIGH",
                "category": "ERROR_HANDLING",
                "examples": ["error logging", "system error handling", "exception logging"]
            },
            {
                "gate_id": "1.3",
                "name": "Use HTTP standard error codes",
                "description": "All APIs must return standardized HTTP status codes",
                "pattern": r"http.*status|status.*code|error.*code|response.*code",
                "severity": "HIGH",
                "category": "ERROR_HANDLING",
                "examples": ["HTTP status codes", "error response codes", "status code handling"]
            },
            # Availability Hard Gates
            {
                "gate_id": "1.5",
                "name": "Timeouts",
                "description": "Set timeouts on I/O operations to prevent waiting",
                "pattern": r"timeout|time.*out|connection.*timeout|request.*timeout",
                "severity": "HIGH",
                "category": "AVAILABILITY",
                "examples": ["connection timeout", "request timeout", "I/O timeout"]
            },
            {
                "gate_id": "1.12",
                "name": "Retry Logic",
                "description": "Use retry logic to handle system failures",
                "pattern": r"retry|retry.*logic|retry.*mechanism|retry.*policy",
                "severity": "HIGH",
                "category": "AVAILABILITY",
                "examples": ["retry logic", "retry mechanism", "retry policy"]
            },
            {
                "gate_id": "3.6",
                "name": "Throttling, drop request",
                "description": "Throttling requests when capacity limit is reached",
                "pattern": r"throttle|throttling|rate.*limit|request.*limit",
                "severity": "MEDIUM",
                "category": "AVAILABILITY",
                "examples": ["request throttling", "rate limiting", "throttle mechanism"]
            },
            {
                "gate_id": "3.9",
                "name": "Set circuit breakers on outgoing requests",
                "description": "Circuit breaker to detect failures and prevent reoccurring",
                "pattern": r"circuit.*breaker|circuit.*break|breaker.*pattern",
                "severity": "HIGH",
                "category": "AVAILABILITY",
                "examples": ["circuit breaker", "circuit break pattern", "breaker implementation"]
            },
            {
                "gate_id": "3.18",
                "name": "Auto Scale",
                "description": "System can automatically scale based on usage telemetry",
                "pattern": r"auto.*scale|auto.*scaling|scale.*up|scale.*down",
                "severity": "MEDIUM",
                "category": "AVAILABILITY",
                "examples": ["auto scaling", "scale up/down", "automatic scaling"]
            },
            # Testing Hard Gates
            {
                "gate_id": "2",
                "name": "Automated Regression Testing",
                "description": "Regression test cases must cover all critical areas",
                "pattern": r"regression.*test|automated.*test|test.*suite|test.*coverage",
                "severity": "HIGH",
                "category": "TESTING",
                "examples": ["regression testing", "automated tests", "test coverage"]
            }
        ]
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-analysis processing"""
        if exec_res == "success":
            context.patterns = self.context.patterns
        return exec_res


class PatternConsolidationNode(AsyncNode):
    """Step 4: Pattern Consolidation"""
    
    def __init__(self):
        super().__init__()
        # Load static patterns
        self.static_patterns = self._load_static_patterns()
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare pattern consolidation"""
        return {
            "patterns": context.patterns
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute pattern consolidation"""
        try:
            print("🔧 Step 4: Pattern Consolidation")
            
            patterns = prep_res["patterns"]
            dynamic_patterns = patterns.get("dynamic", [])
            
            # Consolidate static and dynamic patterns
            consolidated = []
            
            # Add dynamic patterns
            for pattern in dynamic_patterns:
                consolidated.append({
                    "source": "dynamic",
                    "gate_id": pattern.get("gate_id", "unknown"),
                    "name": pattern.get("name", "Unknown Pattern"),
                    "pattern": pattern.get("pattern", ""),
                    "description": pattern.get("description", ""),
                    "severity": pattern.get("severity", "medium")
                })
            
            # Add static patterns
            for pattern in self.static_patterns:
                consolidated.append({
                    "source": "static",
                    "gate_id": pattern.get("gate_id", "unknown"),
                    "name": pattern.get("name", "Unknown Pattern"),
                    "pattern": pattern.get("pattern", ""),
                    "description": pattern.get("description", ""),
                    "severity": pattern.get("severity", "medium")
                })
            
            # Store consolidated patterns
            self.context.patterns = {
                "consolidated": consolidated,
                "dynamic": dynamic_patterns,
                "static": self.static_patterns
            }
            
            print(f"✅ Pattern consolidation completed: {len(consolidated)} patterns")
            
            return "success"
            
        except Exception as e:
            print(f"❌ Pattern consolidation failed: {e}")
            return "error"
    
    def _load_static_patterns(self) -> List[Dict[str, Any]]:
        """Load static patterns from library"""
        # Simplified static patterns - in real implementation, load from file
        return [
            {
                "gate_id": "security_auth",
                "name": "Authentication Check",
                "description": "Check for proper authentication implementation",
                "pattern": r"(?:auth|login|authenticate|verify)",
                "severity": "HIGH",
                "category": "SECURITY"
            },
            {
                "gate_id": "security_password",
                "name": "Password Security",
                "description": "Check for secure password handling",
                "pattern": r"password\s*=\s*['\"][^'\"]*['\"]",
                "severity": "HIGH",
                "category": "SECURITY"
            },
            {
                "gate_id": "performance_cache",
                "name": "Caching Implementation",
                "description": "Check for caching mechanisms",
                "pattern": r"(?:cache|redis|memcached)",
                "severity": "MEDIUM",
                "category": "PERFORMANCE"
            },
            {
                "gate_id": "quality_logging",
                "name": "Logging Implementation",
                "description": "Check for proper logging",
                "pattern": r"(?:log|logger|logging)",
                "severity": "MEDIUM",
                "category": "OBSERVABILITY"
            }
        ]
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-consolidation processing"""
        if exec_res == "success":
            context.patterns = self.context.patterns
        return exec_res


class ExpectedImplementationNode(AsyncNode):
    """Step 5: Expected Implementation Calculation"""
    
    def __init__(self, vector_service: VectorService, embedding_service: EmbeddingService):
        super().__init__()
        self.vector_service = vector_service
        self.embedding_service = embedding_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare expected implementation calculation"""
        return {
            "vector_data": context.vector_data,
            "patterns": context.patterns
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute expected implementation calculation for both repositories"""
        try:
            print("🔍 Step 5: Expected Implementation Calculation (including CD repos)")
            
            vector_data = prep_res["vector_data"]
            patterns = prep_res["patterns"]
            
            main_repo_id = vector_data["main_repo_id"]
            main_collection_name = vector_data["main_collection_name"]
            cd_repo_id = vector_data.get("cd_repo_id")
            cd_collection_name = vector_data.get("cd_collection_name")
            consolidated_patterns = patterns["consolidated"]
            
            expected_implementations = {}
            
            # For each pattern, find expected implementations using semantic search
            for pattern in consolidated_patterns:
                pattern_name = pattern["name"]
                pattern_description = pattern["description"]
                
                # Create semantic query
                query = f"implementation of {pattern_name}: {pattern_description}"
                query_embedding = self.embedding_service.embed_single(query)
                
                if query_embedding:
                    # Search main repository
                    main_results = self.vector_service.search_similar(
                        collection_name=main_collection_name,
                        query_vector=query_embedding,
                        limit=10,
                        score_threshold=0.5
                    )
                    
                    # Search CD repository if available
                    cd_results = []
                    if cd_collection_name:
                        cd_results = self.vector_service.search_similar(
                            collection_name=cd_collection_name,
                            query_vector=query_embedding,
                            limit=10,
                            score_threshold=0.5
                        )
                    
                    # Combine results
                    all_results = []
                    
                    # Add main repository results
                    for result in main_results:
                        all_results.append({
                            "content": result.payload.get("content", ""),
                            "file_path": result.payload.get("file_path", ""),
                            "repo_type": "main",
                            "score": result.score
                        })
                    
                    # Add CD repository results
                    for result in cd_results:
                        all_results.append({
                            "content": result.payload.get("content", ""),
                            "file_path": result.payload.get("file_path", ""),
                            "repo_type": "cd",
                            "score": result.score
                        })
                    
                    # Sort by score
                    all_results.sort(key=lambda x: x["score"], reverse=True)
                    
                    expected_implementations[pattern["gate_id"]] = {
                        "pattern": pattern,
                        "expected_count": len(all_results),
                        "main_implementations": len(main_results),
                        "cd_implementations": len(cd_results),
                        "similar_implementations": all_results[:15]  # Top 15 combined results
                    }
            
            # Store expected implementations
            self.context.expected_implementations = expected_implementations
            
            total_patterns = len(expected_implementations)
            total_implementations = sum(impl["expected_count"] for impl in expected_implementations.values())
            print(f"✅ Expected implementations calculated for {total_patterns} patterns ({total_implementations} total implementations)")
            
            return "success"
            
        except Exception as e:
            print(f"❌ Expected implementation calculation failed: {e}")
            return "error"
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-calculation processing"""
        if exec_res == "success":
            context.expected_implementations = self.context.expected_implementations
        return exec_res


class FileScanningNode(AsyncNode):
    """Step 6: File Scanning & Pattern & AST parser based Matching"""
    
    def __init__(self, ast_parser_service: ASTParserService):
        super().__init__()
        self.ast_parser_service = ast_parser_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare file scanning"""
        return {
            "repo_path": context.repo_path,
            "cd_repo_path": context.cd_repo_path,
            "patterns": context.patterns,
            "expected_implementations": context.expected_implementations
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute file scanning for both main and CD repositories"""
        try:
            print("📁 Step 6: File Scanning & Pattern & AST parser based Matching (including CD repos)")
            
            repo_path = prep_res["repo_path"]
            cd_repo_path = prep_res["cd_repo_path"]
            patterns = prep_res["patterns"]
            expected_implementations = prep_res["expected_implementations"]
            
            consolidated_patterns = patterns["consolidated"]
            scan_results = {}
            
            # Scan main repository files for each pattern
            print(f"🔍 Scanning main repository: {repo_path}")
            for pattern in consolidated_patterns:
                gate_id = pattern["gate_id"]
                pattern_regex = pattern["pattern"]
                
                main_matches = await self._scan_for_pattern(repo_path, pattern_regex, gate_id, "main")
                
                scan_results[gate_id] = {
                    "pattern": pattern,
                    "main_matches": main_matches,
                    "main_match_count": len(main_matches),
                    "cd_matches": [],
                    "cd_match_count": 0,
                    "total_matches": len(main_matches)
                }
            
            # Scan CD repository files for each pattern
            if cd_repo_path:
                print(f"🔍 Scanning CD repository: {cd_repo_path}")
                for pattern in consolidated_patterns:
                    gate_id = pattern["gate_id"]
                    pattern_regex = pattern["pattern"]
                    
                    cd_matches = await self._scan_for_pattern(cd_repo_path, pattern_regex, gate_id, "cd")
                    
                    if gate_id in scan_results:
                        scan_results[gate_id]["cd_matches"] = cd_matches
                        scan_results[gate_id]["cd_match_count"] = len(cd_matches)
                        scan_results[gate_id]["total_matches"] += len(cd_matches)
                    else:
                        scan_results[gate_id] = {
                            "pattern": pattern,
                            "main_matches": [],
                            "main_match_count": 0,
                            "cd_matches": cd_matches,
                            "cd_match_count": len(cd_matches),
                            "total_matches": len(cd_matches)
                        }
            
            # Store scan results
            self.context.scan_results = scan_results
            
            total_patterns = len(scan_results)
            total_matches = sum(result["total_matches"] for result in scan_results.values())
            print(f"✅ File scanning completed: {total_patterns} patterns scanned, {total_matches} total matches")
            
            return "success"
            
        except Exception as e:
            print(f"❌ File scanning failed: {e}")
            return "error"
    
    async def _scan_for_pattern(self, repo_path: str, pattern_regex: str, gate_id: str, repo_type: str = "main") -> List[Dict[str, Any]]:
        """Scan for specific pattern in repository"""
        import re
        
        matches = []
        repo_path_obj = Path(repo_path)
        
        try:
            pattern = re.compile(pattern_regex, re.IGNORECASE)
        except re.error:
            print(f"⚠️ Invalid regex pattern for gate {gate_id}: {pattern_regex}")
            return matches
        
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Find matches
                    for match in pattern.finditer(content):
                        line_number = content[:match.start()].count('\n') + 1
                        
                        matches.append({
                            "repo_type": repo_type,
                            "file_path": str(file_path.relative_to(repo_path_obj)),
                            "line_number": line_number,
                            "match_text": match.group(0),
                            "start_pos": match.start(),
                            "end_pos": match.end()
                        })
                
                except Exception as e:
                    print(f"⚠️ Failed to scan file {file_path}: {e}")
                    continue
        
        return matches
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
            '.pytest_cache', 'target', 'build', 'dist', 'out',
            '.idea', '.vscode', '.vs', '.DS_Store'
        ]
        
        for pattern in ignore_patterns:
            if pattern in str(file_path):
                return True
        
        return False
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-scanning processing"""
        if exec_res == "success":
            context.scan_results = self.context.scan_results
        return exec_res


class GateEvaluationNode(AsyncNode):
    """Step 7: Gate Evaluation & Threshold Checking"""
    
    def __init__(self):
        super().__init__()
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare gate evaluation"""
        return {
            "scan_results": context.scan_results,
            "expected_implementations": context.expected_implementations
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute gate evaluation for both repositories"""
        try:
            print("⚖️ Step 7: Gate Evaluation & Threshold Checking (including CD repos)")
            
            scan_results = prep_res["scan_results"]
            expected_implementations = prep_res["expected_implementations"]
            
            # Handle case where scan_results is None
            if not scan_results:
                print("❌ No scan results available for gate evaluation")
                return "error"
            
            # Handle case where expected_implementations is None
            if not expected_implementations:
                print("⚠️ No expected implementations available, using defaults")
                expected_implementations = {}
            
            gate_results = []
            
            for gate_id, scan_result in scan_results.items():
                pattern = scan_result["pattern"]
                main_matches = scan_result.get("main_matches", [])
                cd_matches = scan_result.get("cd_matches", [])
                total_matches = scan_result.get("total_matches", 0)
                
                # Get expected implementation
                expected = expected_implementations.get(gate_id, {})
                expected_count = expected.get("expected_count", 0)
                
                # Determine threshold (simplified logic)
                threshold = self._calculate_threshold(pattern, expected_count)
                
                # Evaluate gate status
                status = self._evaluate_gate_status(total_matches, expected_count, threshold)
                
                # Create gate result
                gate_result = GateResult(
                    gate_id=gate_id,
                    gate_name=pattern["name"],
                    status=status,
                    expected_count=expected_count,
                    actual_count=total_matches,
                    threshold=threshold,
                    patterns_found=[match["match_text"] for match in (main_matches + cd_matches)[:5]],  # Top 5 matches
                    recommendations=self._generate_recommendations(status, pattern, total_matches, expected_count),
                    confidence_score=self._calculate_confidence(total_matches, expected_count),
                    reasoning=self._generate_reasoning(status, pattern, total_matches, expected_count, len(main_matches), len(cd_matches))
                )
                
                gate_results.append(gate_result)
            
            # Store gate results
            self.context.gate_results = gate_results
            
            total_gates = len(gate_results)
            passed_gates = len([g for g in gate_results if g.status == GateStatus.PASS])
            failed_gates = len([g for g in gate_results if g.status == GateStatus.FAIL])
            
            print(f"✅ Gate evaluation completed: {total_gates} gates evaluated ({passed_gates} passed, {failed_gates} failed)")
            
            return "success"
            
        except Exception as e:
            print(f"❌ Gate evaluation failed: {e}")
            return "error"
    
    def _calculate_threshold(self, pattern: Dict[str, Any], expected_count: int) -> int:
        """Calculate threshold for gate evaluation"""
        severity = pattern.get("severity", "MEDIUM")
        
        if severity == "HIGH":
            return max(1, expected_count // 2)
        elif severity == "MEDIUM":
            return max(1, expected_count // 3)
        else:
            return max(1, expected_count // 4)
    
    def _evaluate_gate_status(self, actual_count: int, expected_count: int, threshold: int) -> GateStatus:
        """Evaluate gate status"""
        if actual_count >= expected_count:
            return GateStatus.PASS
        elif actual_count >= threshold:
            return GateStatus.PARTIAL
        elif actual_count > 0:
            return GateStatus.FAIL
        else:
            return GateStatus.SKIPPED
    
    def _generate_recommendations(self, status: GateStatus, pattern: Dict[str, Any], 
                                actual_count: int, expected_count: int) -> List[str]:
        """Generate recommendations based on gate status"""
        recommendations = []
        
        if status == GateStatus.FAIL:
            recommendations.append(f"Implement {pattern['name']} to improve {pattern.get('category', 'quality').lower()}")
        elif status == GateStatus.PARTIAL:
            recommendations.append(f"Enhance {pattern['name']} implementation for better coverage")
        elif status == GateStatus.PASS:
            recommendations.append(f"Good implementation of {pattern['name']}")
        
        return recommendations
    
    def _calculate_confidence(self, actual_count: int, expected_count: int) -> float:
        """Calculate confidence score"""
        if expected_count == 0:
            return 0.5
        
        ratio = actual_count / expected_count
        return min(1.0, max(0.0, ratio))
    
    def _generate_reasoning(self, status: GateStatus, pattern: Dict[str, Any], 
                          actual_count: int, expected_count: int, main_count: int, cd_count: int) -> str:
        """Generate reasoning for gate evaluation"""
        if status == GateStatus.PASS:
            base_reason = f"Found {actual_count} implementations, meeting expected {expected_count}"
            if cd_count > 0:
                return f"{base_reason} (Main: {main_count}, CD: {cd_count})"
            return base_reason
        elif status == GateStatus.PARTIAL:
            base_reason = f"Found {actual_count} implementations, partially meeting expected {expected_count}"
            if cd_count > 0:
                return f"{base_reason} (Main: {main_count}, CD: {cd_count})"
            return base_reason
        elif status == GateStatus.FAIL:
            base_reason = f"Found {actual_count} implementations, below expected {expected_count}"
            if cd_count > 0:
                return f"{base_reason} (Main: {main_count}, CD: {cd_count})"
            return base_reason
        else:
            base_reason = f"No implementations found for {pattern['name']}"
            if cd_count > 0:
                return f"{base_reason} (Main: {main_count}, CD: {cd_count})"
            return base_reason
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-evaluation processing"""
        if exec_res == "success":
            context.gate_results = self.context.gate_results
        return exec_res


class LLMPostAnalysisNode(AsyncNode):
    """Step 8: LLM Post-Analysis with Contextual Recommendations"""
    
    def __init__(self, llm_service, vector_service: VectorService, embedding_service: EmbeddingService):
        super().__init__()
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.embedding_service = embedding_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare LLM post-analysis"""
        return {
            "gate_results": context.gate_results,
            "metadata": context.metadata,
            "vector_data": context.vector_data
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute LLM post-analysis"""
        try:
            print("🧠 Step 8: LLM Post-Analysis with Contextual Recommendations")
            
            gate_results = prep_res["gate_results"]
            metadata = prep_res["metadata"]
            vector_data = prep_res["vector_data"]
            
            # Handle case where gate_results is None
            if not gate_results:
                print("❌ No gate results available for LLM post-analysis")
                return "error"
            
            # Generate contextual recommendations
            recommendations = await self._generate_contextual_recommendations(
                gate_results, metadata, vector_data
            )
            
            # Generate LLM analysis
            llm_analysis = await self._generate_llm_analysis(gate_results, metadata)
            
            # Store results
            self.context.post_analysis = {
                "recommendations": recommendations,
                "llm_analysis": llm_analysis
            }
            
            print(f"✅ LLM post-analysis completed: {len(recommendations)} recommendations generated")
            
            return "success"
            
        except Exception as e:
            print(f"❌ LLM post-analysis failed: {e}")
            return "error"
    
    async def _generate_contextual_recommendations(self, gate_results: List[GateResult], 
                                                 metadata: Dict[str, Any], 
                                                 vector_data: Dict[str, Any]) -> List[ContextualRecommendation]:
        """Generate contextual recommendations"""
        recommendations = []
        
        # Analyze failed gates for recommendations
        failed_gates = [gate for gate in gate_results if gate.status == GateStatus.FAIL]
        
        for gate in failed_gates:
            # Create recommendation based on gate failure
            recommendation = ContextualRecommendation(
                title=f"Improve {gate.gate_name}",
                description=f"Implement {gate.gate_name} to address {gate.gate_name.lower()} concerns",
                recommendation_type=RecommendationType.SECURITY if "security" in gate.gate_name.lower() else RecommendationType.BEST_PRACTICES,
                confidence_score=gate.confidence_score,
                code_examples=gate.patterns_found,
                pattern_references=[gate.gate_name],
                similar_implementations=[],
                reasoning=gate.reasoning,
                priority="HIGH" if gate.gate_name.lower().startswith("security") else "MEDIUM",
                impact="High impact on code quality and security"
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_llm_analysis(self, gate_results: List[GateResult], 
                                   metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate LLM analysis of scan results"""
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(gate_results, metadata)
            
            # Call LLM
            response = await self.llm_service.generate(
                prompt,
                scan_id=self.context.scan_id,
                node_name="LLMPostAnalysisNode",
                metadata={
                    "gate_results_count": len(gate_results),
                    "failed_gates_count": len([g for g in gate_results if g.status == GateStatus.FAIL]),
                    "metadata": metadata
                }
            )
            
            # Parse response
            analysis = {
                "summary": response,
                "total_gates": len(gate_results),
                "passed_gates": len([g for g in gate_results if g.status == GateStatus.PASS]),
                "failed_gates": len([g for g in gate_results if g.status == GateStatus.FAIL]),
                "partial_gates": len([g for g in gate_results if g.status == GateStatus.PARTIAL]),
                "skipped_gates": len([g for g in gate_results if g.status == GateStatus.SKIPPED])
            }
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ LLM analysis failed: {e}")
            return {
                "summary": "Analysis failed",
                "total_gates": len(gate_results),
                "passed_gates": 0,
                "failed_gates": 0,
                "partial_gates": 0,
                "skipped_gates": 0
            }
    
    def _create_analysis_prompt(self, gate_results: List[GateResult], 
                              metadata: Dict[str, Any]) -> str:
        """Create prompt for LLM analysis"""
        from services.prompt_service import PromptService
        
        prompt_service = PromptService()
        
        # Format gate results
        gate_results_text = "\n".join([
            f"- {gate.gate_name}: {gate.status.value} ({gate.actual_count}/{gate.expected_count})" 
            for gate in gate_results
        ])
        
        return prompt_service.format_prompt(
            "llm_post_analysis",
            scan_results=f"Project: {metadata.get('repo_url', 'Unknown')}",
            pattern_matches="Pattern analysis results",
            gate_evaluations=gate_results_text,
            repo_context=f"Languages: {', '.join(metadata.get('languages', []))}"
        ) or f"""
Analyze the following code scan results and provide insights:

Project: {metadata.get('repo_url', 'Unknown')}
Languages: {', '.join(metadata.get('languages', []))}

Gate Results:
{gate_results_text}

Provide a comprehensive analysis including:
1. Overall code quality assessment
2. Key areas for improvement
3. Security and performance insights
4. Recommendations for next steps
"""
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-analysis processing"""
        if exec_res == "success":
            context.post_analysis = self.context.post_analysis
        return exec_res


class ReportGenerationNode(AsyncNode):
    """Step 9: Report Generation"""
    
    def __init__(self):
        super().__init__()
        from services.html_report_service import HTMLReportService
        self.html_service = HTMLReportService()
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare report generation"""
        return {
            "gate_results": context.gate_results,
            "post_analysis": context.post_analysis,
            "metadata": context.metadata,
            "scan_id": context.scan_id
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute report generation"""
        try:
            print("📊 Step 9: Report Generation")
            
            gate_results = prep_res["gate_results"]
            post_analysis = prep_res["post_analysis"]
            metadata = prep_res["metadata"]
            scan_id = prep_res["scan_id"]
            
            # Handle case where gate_results is None
            if not gate_results:
                print("❌ No gate results available for report generation")
                return "error"
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(gate_results)
            
            # Add vector configuration to metadata for project summary generation
            # Use the same configuration as the scan flow to access the same vector data
            vector_config = {
                "vector_size": 768,
                "distance_metric": "cosine",
                "use_qdrant": self.vector_service.use_qdrant if hasattr(self, 'vector_service') else True,
                "qdrant_path": "./qdrant_data"
            }
            
            # Generate project summary from vector database
            from services.vector_service import VectorService
            vector_service = VectorService(vector_config)
            
            project_info = vector_service.generate_project_summary(
                repo_url=metadata.get("main_repo", {}).get("repo_url", "Unknown"),
                scan_id=scan_id
            )
            
            # Update metadata with vector config and project info
            metadata_with_vector = metadata.copy()
            metadata_with_vector["vector_config"] = vector_config
            metadata_with_vector["project_summary"] = project_info
            
            # Create scan result object
            scan_result = ScanResult(
                scan_id=scan_id or f"scan_{int(time.time())}",
                repo_url=metadata.get("main_repo", {}).get("repo_url", "Unknown"),
                branch=metadata.get("main_repo", {}).get("branch", "Unknown"),
                scan_timestamp=datetime.now(),
                total_gates=len(gate_results),
                passed_gates=len([g for g in gate_results if g.status == GateStatus.PASS]),
                failed_gates=len([g for g in gate_results if g.status == GateStatus.FAIL]),
                partial_gates=len([g for g in gate_results if g.status == GateStatus.PARTIAL]),
                skipped_gates=len([g for g in gate_results if g.status == GateStatus.SKIPPED]),
                gate_results=gate_results,
                recommendations=self._convert_recommendations_to_strings(post_analysis.get("recommendations", []) if post_analysis else []),
                risk_score=risk_score,
                scan_duration=0.0,  # Would be calculated from start time
                metadata=metadata_with_vector
            )
            
            # Generate HTML report
            html_report = self.html_service.generate_html_report(scan_result)
            
            # Store reports to filesystem
            report_paths = self._save_reports_to_filesystem(scan_result, html_report, scan_id)
            
            # Store scan result and HTML report
            self.context.scan_result = scan_result
            self.context.html_report = html_report
            self.context.report_paths = report_paths
            
            print(f"✅ Report generated: {scan_result.passed_gates}/{scan_result.total_gates} gates passed")
            print(f"📄 HTML report generated ({len(html_report)} characters)")
            print(f"💾 Reports saved to: {report_paths}")
            
            return "success"
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return "error"
    
    def _calculate_risk_score(self, gate_results: List[GateResult]) -> float:
        """Calculate overall risk score"""
        if not gate_results:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for gate in gate_results:
            # Weight based on severity
            weight = 1.0
            if "HIGH" in gate.gate_name.upper() or "SECURITY" in gate.gate_name.upper():
                weight = 3.0
            elif "MEDIUM" in gate.gate_name.upper():
                weight = 2.0
            
            # Score based on status
            if gate.status == GateStatus.FAIL:
                score = 1.0
            elif gate.status == GateStatus.PARTIAL:
                score = 0.5
            elif gate.status == GateStatus.PASS:
                score = 0.0
            else:
                score = 0.0
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _convert_recommendations_to_strings(self, recommendations: List[Any]) -> List[str]:
        """Convert recommendations to strings for JSON serialization"""
        if not recommendations:
            return []
        
        converted = []
        for rec in recommendations:
            if isinstance(rec, str):
                converted.append(rec)
            elif hasattr(rec, 'title') and hasattr(rec, 'description'):
                # ContextualRecommendation object
                converted.append(f"{rec.title}: {rec.description}")
            elif isinstance(rec, dict):
                # Dictionary recommendation
                title = rec.get('title', '')
                description = rec.get('description', '')
                converted.append(f"{title}: {description}")
            else:
                # Fallback
                converted.append(str(rec))
        
        return converted
    
    def _save_reports_to_filesystem(self, scan_result: ScanResult, html_report: str, scan_id: str) -> Dict[str, str]:
        """Save HTML and JSON reports to filesystem with scan ID subfolder"""
        try:
            # Create reports directory structure
            reports_dir = "reports"
            scan_dir = os.path.join(reports_dir, scan_id)
            
            # Ensure directories exist
            os.makedirs(reports_dir, exist_ok=True)
            os.makedirs(scan_dir, exist_ok=True)
            
            report_paths = {}
            
            # Save HTML report
            html_filename = f"codegates_report_{scan_id}.html"
            html_path = os.path.join(scan_dir, html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            report_paths["html"] = html_path
            print(f"💾 HTML report saved: {html_path}")
            
            # Save JSON report
            json_filename = f"codegates_report_{scan_id}.json"
            json_path = os.path.join(scan_dir, json_filename)
            
            # Convert ScanResult to JSON-serializable dict
            json_data = {
                "scan_id": scan_result.scan_id,
                "repo_url": scan_result.repo_url,
                "branch": scan_result.branch,
                "scan_timestamp": scan_result.scan_timestamp.isoformat(),
                "total_gates": scan_result.total_gates,
                "passed_gates": scan_result.passed_gates,
                "failed_gates": scan_result.failed_gates,
                "partial_gates": scan_result.partial_gates,
                "skipped_gates": scan_result.skipped_gates,
                "risk_score": scan_result.risk_score,
                "scan_duration": scan_result.scan_duration,
                "gate_results": [
                    {
                        "gate_id": gate.gate_id,
                        "gate_name": gate.gate_name,
                        "status": gate.status.value,
                        "expected_count": gate.expected_count,
                        "actual_count": gate.actual_count,
                        "threshold": gate.threshold,
                        "patterns_found": gate.patterns_found,
                        "recommendations": gate.recommendations,
                        "confidence_score": gate.confidence_score,
                        "reasoning": gate.reasoning
                    }
                    for gate in scan_result.gate_results
                ],
                "recommendations": scan_result.recommendations,
                "metadata": scan_result.metadata
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            report_paths["json"] = json_path
            print(f"💾 JSON report saved: {json_path}")
            
            # Create a summary file with report locations
            summary_filename = f"report_summary_{scan_id}.txt"
            summary_path = os.path.join(scan_dir, summary_filename)
            
            summary_content = f"""
CodeGates Scan Report Summary
============================

Scan ID: {scan_id}
Repository: {scan_result.repo_url}
Branch: {scan_result.branch}
Scan Timestamp: {scan_result.scan_timestamp}

Results Summary:
- Total Gates: {scan_result.total_gates}
- Passed: {scan_result.passed_gates}
- Failed: {scan_result.failed_gates}
- Partial: {scan_result.partial_gates}
- Skipped: {scan_result.skipped_gates}
- Risk Score: {scan_result.risk_score:.2f}

Report Files:
- HTML Report: {html_filename}
- JSON Report: {json_filename}
- Summary: {summary_filename}

Report Directory: {scan_dir}

Generated on: {datetime.now().isoformat()}
"""
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            report_paths["summary"] = summary_path
            print(f"💾 Summary file saved: {summary_path}")
            
            return report_paths
            
        except Exception as e:
            print(f"❌ Failed to save reports to filesystem: {e}")
            return {}
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-report generation processing"""
        if exec_res == "success":
            context.report_data = self.context.scan_result
        return exec_res


class AgenticStorageNode(AsyncNode):
    """Step 10: Agentic Storage for Future Use"""
    
    def __init__(self, vector_service: VectorService, embedding_service: EmbeddingService):
        super().__init__()
        self.vector_service = vector_service
        self.embedding_service = embedding_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare agentic storage"""
        return {
            "scan_result": context.report_data,
            "vector_data": context.vector_data
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute agentic storage"""
        try:
            print("💾 Step 10: Agentic Storage for Future Use")
            
            scan_result = prep_res["scan_result"]
            vector_data = prep_res["vector_data"]
            
            # Handle case where scan_result is None
            if not scan_result:
                print("❌ No scan result available for agentic storage")
                return "error"
            
            # Create scan summary for storage
            scan_summary = {
                "scan_id": scan_result.scan_id,
                "repo_url": scan_result.repo_url,
                "branch": scan_result.branch,
                "scan_timestamp": scan_result.scan_timestamp.isoformat(),
                "total_gates": scan_result.total_gates,
                "passed_gates": scan_result.passed_gates,
                "failed_gates": scan_result.failed_gates,
                "risk_score": scan_result.risk_score,
                "summary": f"Scan completed with {scan_result.passed_gates}/{scan_result.total_gates} gates passed"
            }
            
            # Generate embedding for scan summary
            summary_text = json.dumps(scan_summary, indent=2)
            embedding = self.embedding_service.embed_single(summary_text)
            
            if embedding:
                # Store in vector database
                vector_id = f"scan_{scan_result.scan_id}"
                vector_data = {
                    "id": vector_id,
                    "vector": embedding,
                    "payload": {
                        "type": "scan_result",
                        "scan_id": scan_result.scan_id,
                        "content": summary_text,
                        "metadata": scan_summary
                    }
                }
                
                # Store in scan results collection
                self.vector_service.upsert_vectors("scan_results", [vector_data])
                
                print(f"✅ Scan result stored in vector database: {vector_id}")
            
            # Store detailed results (simplified - in real implementation, store in database)
            self.context.stored_result = {
                "scan_id": scan_result.scan_id,
                "vector_id": vector_id if embedding else None,
                "stored_at": datetime.now().isoformat()
            }
            
            return "success"
            
        except Exception as e:
            print(f"❌ Agentic storage failed: {e}")
            return "error"
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-storage processing"""
        if exec_res == "success":
            context.stored_result = self.context.stored_result
        return exec_res
