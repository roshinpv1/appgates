"""
Scan flow nodes for the 10-step process
"""

import os
import json
import hashlib
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.base import AsyncNode, ScanContext
from models.scan_models import (
    RepositoryInfo, CodeChunk, Pattern, PatternMatch, GateResult, GateStatus,
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
        # Get commit hash from metadata if available
        commit_hash = None
        if context.metadata and "main_repo" in context.metadata:
            commit_hash = context.metadata["main_repo"].get("commit_hash")
        
        return {
            "repo_path": context.repo_path,
            "cd_repo_path": context.cd_repo_path,
            "scan_id": context.scan_id,
            "repo_url": context.repo_url,
            "branch": context.branch,
            "commit_hash": commit_hash,
            "metadata": context.metadata
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute vectorization step"""
        try:
            repo_path = prep_res["repo_path"]
            cd_repo_path = prep_res.get("cd_repo_path")
            scan_id = prep_res["scan_id"]
            repo_url = prep_res["repo_url"]
            branch = prep_res["branch"]
            commit_hash = prep_res["commit_hash"]
            
            print(f"🔍 Starting vectorization for scan: {scan_id}")
            print(f"📁 Main repo: {repo_path}")
            if cd_repo_path:
                print(f"📁 CD repo: {cd_repo_path}")
            
            # Generate collection name based on git hash for deduplication
            repo_hash = commit_hash  # Use the commit_hash from prep_res
            collection_name = self.vector_service._get_collection_name(scan_id, repo_hash)
            
            print(f"📊 Collection: {collection_name}")
            
            # Check if repository is already indexed
            if repo_hash and self.vector_service.is_repository_indexed(repo_hash):
                print(f"🔄 Repository already indexed (hash: {repo_hash}) - skipping vectorization")
                print(f"📋 Previous scans for this repo: {len(self.vector_service.get_scan_mappings_for_repo(repo_hash))}")
                
                # Store scan mapping for this scan
                self.vector_service._store_scan_mapping(
                    scan_id=scan_id,
                    repo_hash=repo_hash,
                    repo_url=repo_url,
                    branch=branch
                )
                
                # Store vector data in context
                if hasattr(self, 'context') and self.context is not None:
                    self.context.vector_data = {
                        "scan_id": scan_id,
                        "collection_name": collection_name,
                        "main_chunks_count": 0,
                        "cd_chunks_count": 0,
                        "total_vectors_stored": 0,
                        "repository_already_indexed": True,
                        "repo_hash": repo_hash
                    }
                
                return "success"
            
            if cd_repo_path:
                print(f"📁 Will include both main and CD repositories in single collection")
            
            # Process main repository
            print(f"🔍 Processing main repository files...")
            main_chunks = []
            
            # Get repository metadata
            main_repo_metadata = self._get_repo_metadata(repo_path, repo_url, branch, commit_hash, "main")
            
            for file_path in self._get_files_to_process(repo_path):
                try:
                    chunks = await self._process_file(file_path, repo_path, scan_id, "main", main_repo_metadata)
                    main_chunks.extend(chunks)
                except Exception as e:
                    print(f"⚠️ Failed to process file {file_path}: {e}")
                    continue
            
            print(f"✅ Main repository: {len(main_chunks)} chunks created")
            
            # Process CD repository if it exists
            cd_chunks = []
            if cd_repo_path:
                print(f"🔍 Processing CD repository files...")
                cd_repo_metadata = self._get_repo_metadata(cd_repo_path, repo_url, branch, commit_hash, "cd")
                
                for file_path in self._get_files_to_process(cd_repo_path):
                    try:
                        chunks = await self._process_file(file_path, cd_repo_path, scan_id, "cd", cd_repo_metadata)
                        cd_chunks.extend(chunks)
                    except Exception as e:
                        print(f"⚠️ Failed to process file {file_path}: {e}")
                        continue
                
                print(f"✅ CD repository: {len(cd_chunks)} chunks created")
            
            # Generate embeddings for all chunks
            print(f"🧠 Generating embeddings...")
            all_chunks = main_chunks + cd_chunks
            
            if not all_chunks:
                print("⚠️ No chunks to vectorize")
                return "error"
            
            # Generate embeddings in batches
            batch_size = 50
            all_embeddings = []
            
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]
                batch_texts = [chunk["content"] for chunk in batch]
                
                try:
                    batch_embeddings = self.embedding_service.embed_batch(batch_texts)
                    all_embeddings.extend(batch_embeddings)
                    print(f"✅ Generated embeddings for batch {i//batch_size + 1}/{(len(all_chunks) + batch_size - 1)//batch_size}")
                except Exception as e:
                    print(f"❌ Failed to generate embeddings for batch {i//batch_size + 1}: {e}")
                    # Continue with other batches
                    continue
            
            if len(all_embeddings) != len(all_chunks):
                print(f"⚠️ Embedding count mismatch: {len(all_embeddings)} vs {len(all_chunks)}")
                # Truncate to match
                all_chunks = all_chunks[:len(all_embeddings)]
            
            # Store vectors in database
            print(f"💾 Storing vectors in database...")
            
            # Prepare vectors for storage
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(all_chunks, all_embeddings)):
                if embedding is None:
                    continue
                    
                vector_data = {
                    "id": chunk["id"],
                    "vector": embedding,
                    "payload": chunk["metadata"]
                }
                vectors.append(vector_data)
            
            # Store all vectors in single collection
            if vectors:
                try:
                    print(f"🔍 About to store {len(vectors)} vectors in collection: {collection_name}")
                    success = self.vector_service.upsert_vectors(collection_name, vectors)
                    if success:
                        print(f"✅ Successfully stored {len(vectors)} vectors in collection: {collection_name}")
                        
                        # Verify storage by checking collection info
                        collection_info = self.vector_service.get_collection_info(collection_name)
                        if collection_info:
                            print(f"📊 Collection {collection_name} now has {collection_info.get('count', 0)} vectors")
                        else:
                            print(f"⚠️ Could not verify collection info for {collection_name}")
                    else:
                        print(f"❌ Failed to store vectors in {collection_name}")
                        return "error"
                except Exception as e:
                    print(f"❌ Failed to store vectors: {e}")
                    import traceback
                    traceback.print_exc()
                    return "error"
            
            # Store scan mapping for this scan (for new repositories)
            self.vector_service._store_scan_mapping(
                scan_id=scan_id,
                repo_hash=repo_hash,
                repo_url=repo_url,
                branch=branch
            )
            
            # Store vector data in context
            if hasattr(self, 'context') and self.context is not None:
                self.context.vector_data = {
                    "scan_id": scan_id,
                    "collection_name": collection_name,
                    "main_chunks_count": len(main_chunks),
                    "cd_chunks_count": len(cd_chunks),
                    "total_vectors_stored": len(vectors),
                    "repo_hash": repo_hash
                }
            
            print(f"✅ Vectorization completed successfully")
            print(f"📊 Total chunks processed: {len(all_chunks)}")
            print(f"📊 Total vectors stored: {len(vectors)}")
            
            return "success"
            
        except Exception as e:
            print(f"❌ Vectorization failed: {e}")
            import traceback
            traceback.print_exc()
            return "error"
    
    def _get_repo_metadata(self, repo_path: str, repo_url: str, branch: str, commit_hash: str, repo_type: str) -> Dict[str, Any]:
        """Helper to get repository metadata for vectorization"""
        return {
            "repo_path": repo_path,
            "repo_url": repo_url,
            "branch": branch,
            "commit_hash": commit_hash,
            "repo_type": repo_type,
            "total_files": 0, # Will be updated after processing
            "total_lines": 0, # Will be updated after processing
            "languages": [], # Will be updated after processing
            "dependencies": {}, # Will be updated after processing
            "build_files": [], # Will be updated after processing
            "config_files": [] # Will be updated after processing
        }
    
    def _get_files_to_process(self, repo_path: str) -> List[Path]:
        """Helper to get list of files to process, respecting ignore patterns"""
        repo_path_obj = Path(repo_path)
        files_to_process = []
        
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                files_to_process.append(file_path)
        
        return files_to_process
    
    async def _process_file(self, file_path: Path, repo_root: Path, scan_id: str, repo_type: str = "main", repo_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
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
                        # Generate a proper UUID for the chunk ID
                        import uuid
                        chunk_id = str(uuid.uuid4())
                        
                        # Create comprehensive metadata
                        chunk_metadata = {
                            "scan_id": scan_id,
                            "repo_type": repo_type,
                            "file_path": str(file_path.relative_to(repo_root)),
                            "filename": file_path.name,
                            "language": language,
                            "start_line": start_line,
                            "end_line": end_line,
                            "symbol_name": symbol_name,
                            "symbol_kind": "function" if "function" in symbol_name.lower() else "class",
                            "content_hash": hashlib.md5(symbol_content.encode()).hexdigest(),
                            "file_size": file_path.stat().st_size,
                            "total_lines": len(content.split('\n')),
                            "processing_timestamp": time.time()
                        }
                        
                        # Add repository metadata if available
                        if repo_metadata:
                            chunk_metadata.update({
                                "repo_url": repo_metadata.get("repo_url", ""),
                                "repo_branch": repo_metadata.get("branch", ""),
                                "repo_commit_hash": repo_metadata.get("commit_hash", ""),
                                "repo_total_files": repo_metadata.get("total_files", 0),
                                "repo_total_lines": repo_metadata.get("total_lines", 0),
                                "repo_languages": repo_metadata.get("languages", []),
                                "repo_dependencies": repo_metadata.get("dependencies", {}),
                                "repo_build_files": repo_metadata.get("build_files", []),
                                "repo_config_files": repo_metadata.get("config_files", [])
                            })
                        
                        chunks.append({
                            "id": chunk_id,
                            "content": symbol_content,
                            "metadata": chunk_metadata
                        })
            
            # If no symbols, create sliding window chunks
            if not chunks:
                chunks = self._create_sliding_chunks(content, file_path, repo_root, scan_id, language, repo_type, repo_metadata)
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ Failed to process file {file_path}: {e}")
            return []
    
    def _create_sliding_chunks(self, content: str, file_path: Path, repo_root: Path, 
                              scan_id: str, language: str, repo_type: str = "main", repo_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create sliding window chunks"""
        chunks = []
        lines = content.split('\n')
        chunk_size = 50  # lines per chunk
        overlap = 10     # overlapping lines
        
        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            
            if len(chunk_content.strip()) >= 10:
                # Generate a proper UUID for the chunk ID
                import uuid
                chunk_id = str(uuid.uuid4())
                
                # Create comprehensive metadata
                chunk_metadata = {
                    "scan_id": scan_id,
                    "repo_type": repo_type,
                    "file_path": str(file_path.relative_to(repo_root)),
                    "filename": file_path.name,
                    "language": language,
                    "start_line": i + 1,
                    "end_line": min(i + chunk_size, len(lines)),
                    "content_hash": hashlib.md5(chunk_content.encode()).hexdigest(),
                    "file_size": file_path.stat().st_size,
                    "total_lines": len(content.split('\n')),
                    "processing_timestamp": time.time()
                }
                
                # Add repository metadata if available
                if repo_metadata:
                    chunk_metadata.update({
                        "repo_url": repo_metadata.get("repo_url", ""),
                        "repo_branch": repo_metadata.get("branch", ""),
                        "repo_commit_hash": repo_metadata.get("commit_hash", ""),
                        "repo_total_files": repo_metadata.get("total_files", 0),
                        "repo_total_lines": repo_metadata.get("total_lines", 0),
                        "repo_languages": repo_metadata.get("languages", []),
                        "repo_dependencies": repo_metadata.get("dependencies", {}),
                        "repo_build_files": repo_metadata.get("build_files", []),
                        "repo_config_files": repo_metadata.get("config_files", [])
                    })
                
                chunks.append({
                    "id": chunk_id,
                    "content": chunk_content,
                    "metadata": chunk_metadata
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
        """Check if file should be ignored using enhanced filtering"""
        try:
            # Load file filtering configuration
            import json
            import os
            
            config_path = os.path.join(os.path.dirname(__file__), "..", "data", "file_filtering_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                filtering_config = config.get("file_filtering", {})
                ignore_patterns = filtering_config.get("ignore_patterns", [])
                binary_extensions = set(filtering_config.get("binary_extensions", []))
                size_limits = filtering_config.get("size_limits", {})
            else:
                # Fallback to default patterns
                ignore_patterns = [
                    '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
                    '.pytest_cache', 'target', 'build', 'dist', 'out',
                    '.idea', '.vscode', '.vs', '.DS_Store'
                ]
                binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
                                   '.mp4', '.avi', '.mov', '.mp3', '.wav',
                                   '.zip', '.tar', '.gz', '.rar', '.7z',
                                   '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                                   '.exe', '.dll', '.so', '.dylib',
                                   '.jar', '.war', '.ear', '.class'}
                size_limits = {"max_file_size_mb": 10, "skip_large_files": True}
            
            # Check ignore patterns
            file_path_str = str(file_path)
            for pattern in ignore_patterns:
                if pattern in file_path_str:
                    return True
            
            # Check binary extensions
            if file_path.suffix.lower() in binary_extensions:
                return True
            
            # Check file size limits
            if size_limits.get("skip_large_files", False):
                try:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    max_size_mb = size_limits.get("max_file_size_mb", 10)
                    if file_size_mb > max_size_mb:
                        return True
                except (OSError, AttributeError):
                    pass
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error in file filtering: {e}")
            # Fallback to basic filtering
            basic_patterns = ['.git', '.svn', '.hg', 'node_modules', '__pycache__']
            return any(pattern in str(file_path) for pattern in basic_patterns)
    
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
            
            # Analyze project structure for expected counts
            print("   🔍 Analyzing project structure for expected counts...")
            try:
                expected_counts_analysis = self._analyze_project_structure_for_expected_counts(metadata)
            except AttributeError:
                print("   ⚠️ Project structure analysis not available, using fallback")
                expected_counts_analysis = {}
            
            # Create prompt for LLM with expected counts analysis
            prompt = self._create_pre_analysis_prompt(project_summary, build_configs, expected_counts_analysis)
            
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
            
            # Store expected counts analysis for later use
            if expected_counts_analysis:
                self.context.expected_counts_analysis = expected_counts_analysis
                print(f"📊 Stored expected counts analysis for {len(expected_counts_analysis)} gates")
            
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
    
    def _create_pre_analysis_prompt(self, project_summary: str, build_configs: str, expected_counts_analysis: Dict[str, Dict[str, Any]] = None) -> str:
        """Create prompt for LLM pre-analysis with extracted code snippets and expected counts analysis"""
        from services.prompt_service import PromptService
        
        prompt_service = PromptService()
        
        # Extract relevant code snippets from vector database
        extracted_code = self._extract_relevant_code_snippets()
        
        # Format expected counts analysis for the prompt
        expected_counts_text = ""
        if expected_counts_analysis:
            expected_counts_text = "\n\nEXPECTED COUNTS ANALYSIS:\n"
            for gate_id, analysis in expected_counts_analysis.items():
                expected_counts_text += f"- Gate {gate_id}: Expected {analysis.get('expected_count', 1)} implementations\n"
                expected_counts_text += f"  Reason: {analysis.get('reason', 'Based on project structure analysis')}\n"
        
        return prompt_service.format_prompt(
            "llm_pre_analysis",
            code_structure=project_summary,
            config_files=build_configs,
            available_gates=self._get_available_gates_summary(),
            extracted_code=extracted_code,
            expected_counts=expected_counts_text
        ) or f"""
CRITICAL: You must respond with ONLY valid JSON. No explanations, no markdown, no other text.

Analyze the repository for hard gate compliance:

Repository Structure: {project_summary}
Key Config Files: {build_configs}

Available Gates:
{self._get_available_gates_summary()}

Extracts From the Code:
{extracted_code}

Expected Counts Analysis:
{expected_counts_text}

Generate regex patterns for applicable gates. 
CRITICAL RULES for patterns:
- Use ONLY simple Python regex patterns with basic syntax
- Allowed: word1.*word2|word3.*word4
- Forbidden: lookbehind (?<=...), lookahead (?=...), (?i) flags, complex assertions

For each gate, determine:
1. Whether the gate is APPLICABLE (true/false) based on the repository structure and config files
2. The REASON for applicability/non-applicability
3. If applicable, generate a regex pattern and supporting examples
4. If not applicable, leave pattern/examples empty

CRITICAL JSON FORMATTING RULES:
- Use ONLY double quotes for strings: "value" not 'value'
- Use proper JSON syntax: "key": "value" not "key". "value"
- Ensure all property names are quoted: "gate_id": "1.1"
- Use proper boolean values: true or false (not "true" or "false")
- No trailing commas before closing braces or brackets

Respond with ONLY this exact JSON structure:

{{
    "patterns": [
        {{
            "gate_id": "1.1",
            "name": "Log system errors",
            "description": "Log system errors for troubleshooting",
            "applicable": true,
            "reason": "Repository contains multiple logging utility files with error handling code",
            "pattern": "error.*log|system.*error|exception.*log",
            "severity": "HIGH",
            "category": "ERROR_HANDLING",
            "examples": ["error logging", "system error handling"]
        }},
        {{
            "gate_id": "1.3",
            "name": "Use HTTP standard error codes",
            "description": "All APIs must return standardized HTTP status codes",
            "applicable": false,
            "reason": "No API-related files or HTTP handlers found in repository",
            "pattern": "",
            "severity": "HIGH",
            "category": "ERROR_HANDLING",
            "examples": []
        }}
    ]
}}

Generate 5–10 specific entries. Focus ONLY on the actual gates in scope. Use simple regex patterns ONLY.
"""
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract patterns"""
        try:
            # Debug: Show response preview
            print(f"🔍 LLM Response preview: {response[:300]}...")
            
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                
                print(f"🔍 Extracted JSON string: {json_str[:200]}...")
                
                # Clean up common JSON issues
                json_str = json_str.replace("```json", "").replace("```", "")  # Remove markdown code blocks
                json_str = json_str.strip()
                
                # Try multiple parsing strategies
                parsing_strategies = [
                    # Strategy 1: Direct parsing
                    lambda: json.loads(json_str),
                    # Strategy 2: Fix common trailing commas
                    lambda: json.loads(json_str.replace(",\n}", "\n}").replace(",\n]", "\n]")),
                    # Strategy 3: Fix unquoted property names
                    lambda: json.loads(re.sub(r'(\w+):', r'"\1":', json_str)),
                    # Strategy 4: Fix single quotes
                    lambda: json.loads(json_str.replace("'", '"')),
                    # Strategy 5: Fix missing quotes around string values
                    lambda: json.loads(re.sub(r':\s*([^",\{\}\[\]\d][^,\{\}\[\]]*[^",\{\}\[\]\s])', r': "\1"', json_str)),
                    # Strategy 6: Try to fix common JSON issues manually
                    lambda: self._manual_json_fix(json_str)
                ]
                
                for i, strategy in enumerate(parsing_strategies):
                    try:
                        data = strategy()
                        patterns = data.get("patterns", [])
                        
                        if patterns:
                            print(f"✅ Successfully parsed {len(patterns)} patterns from LLM response (strategy {i+1})")
                            return patterns
                        else:
                            print(f"⚠️ No patterns found in LLM response (strategy {i+1})")
                            continue
                    except Exception as e:
                        print(f"⚠️ Strategy {i+1} failed: {e}")
                        continue
                
                print("⚠️ All JSON parsing strategies failed")
                return self._create_fallback_patterns()
            else:
                print("⚠️ No JSON structure found in LLM response")
                print(f"🔍 Response contains '{{': {'{' in response}, '}}': {'}' in response}")
                return self._create_fallback_patterns()
                
        except Exception as e:
            print(f"⚠️ Failed to parse LLM response: {e}")
            return self._create_fallback_patterns()
    
    def _manual_json_fix(self, json_str: str) -> Dict[str, Any]:
        """Manually fix common JSON issues"""
        try:
            # Fix the specific issue: "name". "value" -> "name": "value"
            json_str = re.sub(r'"(\w+)"\.\s*"([^"]*)"', r'"\1": "\2"', json_str)
            
            # Fix missing quotes around property names
            json_str = re.sub(r'(\w+):\s*"([^"]*)"', r'"\1": "\2"', json_str)
            
            # Fix missing quotes around string values
            json_str = re.sub(r':\s*([^",\{\}\[\]\d][^,\{\}\[\]]*[^",\{\}\[\]\s])(?=\s*[,}\]])', r': "\1"', json_str)
            
            # Remove any trailing commas before closing braces/brackets
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # Fix single quotes to double quotes
            json_str = json_str.replace("'", '"')
            
            # Fix common issues with boolean values
            json_str = re.sub(r':\s*(true|false)(?=\s*[,}\]])', r': \1', json_str)
            
            # Try to parse the fixed JSON
            return json.loads(json_str)
        except Exception as e:
            print(f"⚠️ Manual JSON fix failed: {e}")
            # If manual fix fails, try to extract just the patterns array
            try:
                # Find the patterns array and try to parse it manually
                pattern_match = re.search(r'"patterns"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                if pattern_match:
                    patterns_str = pattern_match.group(1)
                    # Try to extract individual pattern objects
                    pattern_objects = re.findall(r'\{[^{}]*\}', patterns_str)
                    patterns = []
                    
                    for pattern_obj in pattern_objects:
                        try:
                            # Clean up the pattern object
                            clean_obj = pattern_obj.strip()
                            # Fix common issues in the object
                            clean_obj = re.sub(r'"(\w+)"\.\s*"([^"]*)"', r'"\1": "\2"', clean_obj)
                            clean_obj = re.sub(r'(\w+):\s*"([^"]*)"', r'"\1": "\2"', clean_obj)
                            clean_obj = re.sub(r':\s*([^",\{\}\[\]\d][^,\{\}\[\]]*[^",\{\}\[\]\s])(?=\s*[,}\]])', r': "\1"', clean_obj)
                            
                            # Try to parse the individual pattern
                            pattern_data = json.loads(clean_obj)
                            patterns.append(pattern_data)
                        except Exception:
                            continue
                    
                    if patterns:
                        return {"patterns": patterns}
            except Exception:
                pass
            
            raise ValueError("Manual JSON fix failed")
    
    def _extract_relevant_code_snippets(self) -> str:
        """Extract relevant code snippets from vector database for each gate"""
        try:
            # Get vector service from context
            vector_service = getattr(self.context, 'vector_service', None)
            scan_id = getattr(self.context, 'scan_id', 'unknown')
            
            if not vector_service:
                return "No vector service available for code extraction"
            
            # Get collection name based on git hash
            repo_hash = getattr(self.context, 'metadata', {}).get("main_repo", {}).get("commit_hash")
            collection_name = vector_service._get_collection_name(scan_id, repo_hash)
            
            # Define search queries for each gate category
            gate_queries = {
                "auditability": ["logging", "log", "audit", "tracking", "monitoring"],
                "error_handling": ["error", "exception", "try catch", "throw", "handle"],
                "availability": ["timeout", "retry", "throttling", "circuit breaker", "health check"],
                "security": ["authentication", "authorization", "security", "encrypt", "hash"],
                "testing": ["test", "unit test", "integration test", "mock", "assert"]
            }
            
            extracted_snippets = []
            
            for category, queries in gate_queries.items():
                category_snippets = []
                for query in queries:
                    try:
                        results = vector_service.search(
                            collection_name=collection_name,
                            query=query,
                            limit=3,
                            score_threshold=0.3
                        )
                        
                        for result in results:
                            if result.payload and result.payload.get("content"):
                                content = result.payload["content"][:200]  # Truncate for context
                                file_path = result.payload.get("file_path", "Unknown")
                                category_snippets.append(f"File: {file_path}\nContent: {content}")
                    except Exception as e:
                        print(f"⚠️ Error extracting code for query '{query}': {e}")
                        continue
                
                if category_snippets:
                    extracted_snippets.append(f"\n=== {category.upper()} RELATED CODE ===\n")
                    extracted_snippets.extend(category_snippets[:5])  # Limit to 5 snippets per category
            
            if extracted_snippets:
                return "\n".join(extracted_snippets)
            else:
                return "No relevant code snippets found in vector database"
                
        except Exception as e:
            print(f"⚠️ Error extracting code snippets: {e}")
            return "Error extracting code snippets from vector database"
    
    def _get_available_gates_summary(self) -> str:
        """Get summary of available gates for the prompt"""
        try:
            # Load gates from pattern library
            import json
            import os
            
            pattern_library_path = os.path.join(os.path.dirname(__file__), "..", "data", "enhanced_pattern_library.json")
            if os.path.exists(pattern_library_path):
                with open(pattern_library_path, 'r') as f:
                    pattern_library = json.load(f)
                
                gates_summary = []
                gates = pattern_library.get("gates", {})
                
                # Handle the enhanced pattern library structure
                for gate_id, gate_data in gates.items():
                    if isinstance(gate_data, dict):
                        name = gate_data.get("display_name", gate_id)
                        category = gate_data.get("category", "Unknown")
                        priority = gate_data.get("priority", "Medium")
                        
                        gates_summary.append(f"- {gate_id}: {name} ({category}, {priority})")
                
                if not gates_summary:
                    # Fallback to basic gates if enhanced structure doesn't work
                    gates_summary = [
                        "- 1.1: Logs Searchable/Available (Auditability, High)",
                        "- 1.3: Audit Trail (Auditability, High)",
                        "- 1.5: Implement tracking ID for log messages (Auditability, Medium)",
                        "- 1.6: Log API Calls (Auditability, High)",
                        "- 1.8: Log Application Messages (Auditability, High)",
                        "- 1.10: Avoid Logging Sensitive Data (Security, Critical)",
                        "- 2.7: UI Error Handling (Auditability, Medium)",
                        "- 2.4: Include Client error tracking (Error Handling, Medium)",
                        "- 1.12: Retry Logic (Availability, High)",
                        "- 3.6: Throttling, drop request (Availability, Medium)",
                        "- 3.9: Circuit Breaker (Availability, High)",
                        "- 3.18: Health Checks (Availability, Medium)"
                    ]
                
                return "\n".join(gates_summary)
            else:
                return "Gates information not available"
                
        except Exception as e:
            print(f"⚠️ Error getting available gates summary: {e}")
            return "Error loading gates information"
    
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
            {
                "gate_id": "2.7",
                "name": "UI Error Handling",
                "description": "Critical and error log messages from client devices",
                "pattern": r"ui.*error|client.*error|browser.*error|mobile.*error|frontend.*error",
                "severity": "MEDIUM",
                "category": "AUDITABILITY",
                "examples": ["UI error handling", "client error logging", "browser error tracking"]
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
            {
                "gate_id": "2.4",
                "name": "Include Client error tracking",
                "description": "Include client error tracking for monitoring",
                "pattern": r"client.*error|error.*tracking|client.*tracking|error.*monitoring",
                "severity": "MEDIUM",
                "category": "ERROR_HANDLING",
                "examples": ["client error tracking", "error monitoring", "client tracking"]
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
    
    def _analyze_project_structure_for_expected_counts(self, metadata: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze project structure to calculate expected counts for each gate
        based on actual codebase structure, dependencies, and configuration
        """
        try:
            main_repo = metadata.get('main_repo', {})
            repo_path = main_repo.get('local_path')
            
            if not repo_path:
                print("⚠️ No repository path available for structure analysis")
                return {}
            
            expected_counts = {}
            
            # Analyze project structure
            project_structure = self._analyze_project_structure(repo_path)
            
            # Analyze dependencies and libraries
            dependencies = self._analyze_dependencies(repo_path, main_repo)
            
            # Analyze configuration files
            config_analysis = self._analyze_configuration_files(repo_path, main_repo)
            
            # Calculate expected counts for each gate category
            expected_counts.update(self._calculate_auditability_expected_counts(project_structure, dependencies, config_analysis))
            expected_counts.update(self._calculate_error_handling_expected_counts(project_structure, dependencies, config_analysis))
            expected_counts.update(self._calculate_availability_expected_counts(project_structure, dependencies, config_analysis))
            expected_counts.update(self._calculate_testing_expected_counts(project_structure, dependencies, config_analysis))
            expected_counts.update(self._calculate_security_expected_counts(project_structure, dependencies, config_analysis))
            
            print(f"✅ Project structure analysis completed: {len(expected_counts)} gate expected counts calculated")
            return expected_counts
            
        except Exception as e:
            print(f"❌ Project structure analysis failed: {e}")
            return {}
    
    def _analyze_project_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze the project structure and file organization"""
        try:
            structure = {
                "total_files": 0,
                "java_files": 0,
                "test_files": 0,
                "config_files": 0,
                "controller_files": 0,
                "service_files": 0,
                "repository_files": 0,
                "model_files": 0,
                "util_files": 0,
                "main_packages": [],
                "test_packages": [],
                "has_web_layer": False,
                "has_data_layer": False,
                "has_service_layer": False,
                "framework_indicators": []
            }
            
            repo_path_obj = Path(repo_path)
            
            for file_path in repo_path_obj.rglob("*"):
                if file_path.is_file():
                    structure["total_files"] += 1
                    file_name = file_path.name.lower()
                    file_path_str = str(file_path)
                    
                    # Count file types
                    if file_path.suffix == '.java':
                        structure["java_files"] += 1
                        
                        # Analyze Java file structure
                        if 'test' in file_path_str.lower():
                            structure["test_files"] += 1
                        elif 'controller' in file_path_str.lower():
                            structure["controller_files"] += 1
                        elif 'service' in file_path_str.lower():
                            structure["service_files"] += 1
                        elif 'repository' in file_path_str.lower():
                            structure["repository_files"] += 1
                        elif 'model' in file_path_str.lower() or 'entity' in file_path_str.lower():
                            structure["model_files"] += 1
                        elif 'util' in file_path_str.lower():
                            structure["util_files"] += 1
                    
                    # Detect framework indicators
                    if any(indicator in file_name for indicator in ['spring', 'boot', 'application']):
                        structure["framework_indicators"].append('spring_boot')
                    if any(indicator in file_name for indicator in ['pom.xml', 'build.gradle']):
                        structure["framework_indicators"].append('maven_or_gradle')
                    if any(indicator in file_name for indicator in ['web.xml', 'servlet']):
                        structure["framework_indicators"].append('servlet')
                    
                    # Detect layers
                    if any(layer in file_path_str.lower() for layer in ['controller', 'web', 'rest']):
                        structure["has_web_layer"] = True
                    if any(layer in file_path_str.lower() for layer in ['repository', 'dao', 'jpa']):
                        structure["has_data_layer"] = True
                    if any(layer in file_path_str.lower() for layer in ['service', 'business']):
                        structure["has_service_layer"] = True
                    
                    # Count config files
                    if any(config_ext in file_name for config_ext in ['.properties', '.yml', '.yaml', '.xml', '.json']):
                        structure["config_files"] += 1
            
            # Remove duplicates from framework indicators
            structure["framework_indicators"] = list(set(structure["framework_indicators"]))
            
            return structure
            
        except Exception as e:
            print(f"⚠️ Error analyzing project structure: {e}")
            return {}
    
    def _analyze_dependencies(self, repo_path: str, main_repo: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project dependencies and libraries"""
        try:
            dependencies = {
                "logging_frameworks": [],
                "testing_frameworks": [],
                "web_frameworks": [],
                "database_frameworks": [],
                "security_frameworks": [],
                "monitoring_frameworks": [],
                "build_tools": []
            }
            
            # Check build files for dependencies
            build_files = main_repo.get('build_files', [])
            for build_file in build_files:
                file_path = os.path.join(repo_path, build_file)
                content = self._read_file_content(file_path, max_lines=200)
                
                if content:
                    content_lower = content.lower()
                    
                    # Detect logging frameworks
                    if any(logger in content_lower for logger in ['logback', 'log4j', 'slf4j', 'logging']):
                        dependencies["logging_frameworks"].extend(['logback', 'log4j', 'slf4j'])
                    
                    # Detect testing frameworks
                    if any(test in content_lower for test in ['junit', 'testng', 'mockito', 'spring-test']):
                        dependencies["testing_frameworks"].extend(['junit', 'mockito', 'spring-test'])
                    
                    # Detect web frameworks
                    if any(web in content_lower for web in ['spring-web', 'spring-boot-starter-web', 'servlet']):
                        dependencies["web_frameworks"].extend(['spring-web', 'servlet'])
                    
                    # Detect database frameworks
                    if any(db in content_lower for db in ['spring-data', 'jpa', 'hibernate', 'jdbc']):
                        dependencies["database_frameworks"].extend(['spring-data', 'jpa', 'hibernate'])
                    
                    # Detect security frameworks
                    if any(sec in content_lower for sec in ['spring-security', 'oauth', 'jwt']):
                        dependencies["security_frameworks"].extend(['spring-security', 'oauth'])
                    
                    # Detect monitoring frameworks
                    if any(mon in content_lower for mon in ['actuator', 'micrometer', 'prometheus']):
                        dependencies["monitoring_frameworks"].extend(['actuator', 'micrometer'])
                    
                    # Detect build tools
                    if 'maven' in content_lower or 'pom.xml' in build_file:
                        dependencies["build_tools"].append('maven')
                    if 'gradle' in content_lower or 'build.gradle' in build_file:
                        dependencies["build_tools"].append('gradle')
            
            # Remove duplicates
            for key in dependencies:
                dependencies[key] = list(set(dependencies[key]))
            
            return dependencies
            
        except Exception as e:
            print(f"⚠️ Error analyzing dependencies: {e}")
            return {}
    
    def _analyze_configuration_files(self, repo_path: str, main_repo: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze configuration files for patterns and settings"""
        try:
            config_analysis = {
                "logging_config": False,
                "security_config": False,
                "database_config": False,
                "monitoring_config": False,
                "error_handling_config": False,
                "timeout_config": False,
                "retry_config": False,
                "throttling_config": False,
                "circuit_breaker_config": False,
                "health_check_config": False
            }
            
            config_files = main_repo.get('config_files', [])
            for config_file in config_files:
                file_path = os.path.join(repo_path, config_file)
                content = self._read_file_content(file_path, max_lines=100)
                
                if content:
                    content_lower = content.lower()
                    
                    # Detect logging configuration
                    if any(log in content_lower for log in ['logging', 'logback', 'log4j', 'slf4j']):
                        config_analysis["logging_config"] = True
                    
                    # Detect security configuration
                    if any(sec in content_lower for sec in ['security', 'authentication', 'authorization', 'oauth']):
                        config_analysis["security_config"] = True
                    
                    # Detect database configuration
                    if any(db in content_lower for db in ['datasource', 'jpa', 'hibernate', 'database']):
                        config_analysis["database_config"] = True
                    
                    # Detect monitoring configuration
                    if any(mon in content_lower for mon in ['actuator', 'management', 'endpoints', 'health']):
                        config_analysis["monitoring_config"] = True
                    
                    # Detect error handling configuration
                    if any(err in content_lower for err in ['error', 'exception', 'handling']):
                        config_analysis["error_handling_config"] = True
                    
                    # Detect timeout configuration
                    if any(timeout in content_lower for timeout in ['timeout', 'connection-timeout', 'read-timeout']):
                        config_analysis["timeout_config"] = True
                    
                    # Detect retry configuration
                    if any(retry in content_lower for retry in ['retry', 'retryable', 'backoff']):
                        config_analysis["retry_config"] = True
                    
                    # Detect throttling configuration
                    if any(throttle in content_lower for throttle in ['throttle', 'rate-limit', 'throttling']):
                        config_analysis["throttling_config"] = True
                    
                    # Detect circuit breaker configuration
                    if any(cb in content_lower for cb in ['circuit-breaker', 'resilience4j', 'hystrix']):
                        config_analysis["circuit_breaker_config"] = True
                    
                    # Detect health check configuration
                    if any(health in content_lower for health in ['health', 'liveness', 'readiness']):
                        config_analysis["health_check_config"] = True
            
            return config_analysis
            
        except Exception as e:
            print(f"⚠️ Error analyzing configuration files: {e}")
            return {}
    
    def _calculate_auditability_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for auditability gates"""
        expected_counts = {}
        
        # Gate 1.1: Logs Searchable/Available
        logging_count = 0
        if dependencies.get("logging_frameworks"):
            logging_count += len(dependencies["logging_frameworks"])
        if config.get("logging_config"):
            logging_count += 1
        if structure.get("java_files", 0) > 0:
            logging_count += max(1, structure["java_files"] // 50)  # At least 1 logger per 50 Java files
        expected_counts["1.1"] = {
            "expected_count": max(1, logging_count),
            "reason": f"Based on {len(dependencies.get('logging_frameworks', []))} logging frameworks, {structure.get('java_files', 0)} Java files, and logging config: {config.get('logging_config', False)}"
        }
        
        # Gate 1.3: Audit Trail
        audit_count = 0
        if structure.get("has_web_layer"):
            audit_count += 1  # Web layer should have audit trails
        if structure.get("has_data_layer"):
            audit_count += 1  # Data layer should have audit trails
        if config.get("security_config"):
            audit_count += 1  # Security config indicates audit needs
        expected_counts["1.3"] = {
            "expected_count": max(1, audit_count),
            "reason": f"Based on web layer: {structure.get('has_web_layer', False)}, data layer: {structure.get('has_data_layer', False)}, security config: {config.get('security_config', False)}"
        }
        
        # Gate 1.5: Implement tracking ID for log messages
        tracking_count = 0
        if structure.get("controller_files", 0) > 0:
            tracking_count += structure["controller_files"]  # Each controller should have tracking
        if structure.get("service_files", 0) > 0:
            tracking_count += max(1, structure["service_files"] // 2)  # Every other service should have tracking
        expected_counts["1.5"] = {
            "expected_count": max(1, tracking_count),
            "reason": f"Based on {structure.get('controller_files', 0)} controllers and {structure.get('service_files', 0)} services"
        }
        
        # Gate 1.6: Log API Calls
        api_logging_count = 0
        if structure.get("controller_files", 0) > 0:
            api_logging_count += structure["controller_files"]  # Each controller should log API calls
        if structure.get("has_web_layer"):
            api_logging_count += 1  # Web layer should have API logging
        expected_counts["1.6"] = {
            "expected_count": max(1, api_logging_count),
            "reason": f"Based on {structure.get('controller_files', 0)} controllers and web layer: {structure.get('has_web_layer', False)}"
        }
        
        # Gate 1.8: Log Application Messages
        app_logging_count = 0
        if structure.get("service_files", 0) > 0:
            app_logging_count += structure["service_files"]  # Each service should log application messages
        if structure.get("util_files", 0) > 0:
            app_logging_count += max(1, structure["util_files"] // 2)  # Every other util should log
        expected_counts["1.8"] = {
            "expected_count": max(1, app_logging_count),
            "reason": f"Based on {structure.get('service_files', 0)} services and {structure.get('util_files', 0)} utility files"
        }
        
        # Gate 1.10: Avoid Logging Sensitive Data
        sensitive_logging_count = 0
        if config.get("security_config"):
            sensitive_logging_count += 1  # Security config indicates sensitive data handling
        if structure.get("has_web_layer"):
            sensitive_logging_count += 1  # Web layer handles sensitive data
        if structure.get("has_data_layer"):
            sensitive_logging_count += 1  # Data layer handles sensitive data
        expected_counts["1.10"] = {
            "expected_count": max(1, sensitive_logging_count),
            "reason": f"Based on security config: {config.get('security_config', False)}, web layer: {structure.get('has_web_layer', False)}, data layer: {structure.get('has_data_layer', False)}"
        }
        
        return expected_counts
    
    def _calculate_error_handling_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for error handling gates"""
        expected_counts = {}
        
        # Gate 2.4: Include Client error tracking
        client_error_count = 0
        if structure.get("controller_files", 0) > 0:
            client_error_count += structure["controller_files"]  # Each controller should handle client errors
        if structure.get("has_web_layer"):
            client_error_count += 1  # Web layer should have client error handling
        expected_counts["2.4"] = {
            "expected_count": max(1, client_error_count),
            "reason": f"Based on {structure.get('controller_files', 0)} controllers and web layer: {structure.get('has_web_layer', False)}"
        }
        
        # Gate 2.7: UI Error Handling
        ui_error_count = 0
        if structure.get("controller_files", 0) > 0:
            ui_error_count += structure["controller_files"]  # Each controller should handle UI errors
        if structure.get("has_web_layer"):
            ui_error_count += 1  # Web layer should have UI error handling
        expected_counts["2.7"] = {
            "expected_count": max(1, ui_error_count),
            "reason": f"Based on {structure.get('controller_files', 0)} controllers and web layer: {structure.get('has_web_layer', False)}"
        }
        
        return expected_counts
    
    def _calculate_availability_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for availability gates"""
        expected_counts = {}
        
        # Gate 1.12: Retry Logic
        retry_count = 0
        if config.get("retry_config"):
            retry_count += 1  # Retry configuration indicates retry logic
        if structure.get("service_files", 0) > 0:
            retry_count += max(1, structure["service_files"] // 3)  # Every third service should have retry logic
        if dependencies.get("database_frameworks"):
            retry_count += 1  # Database operations should have retry logic
        expected_counts["1.12"] = {
            "expected_count": max(1, retry_count),
            "reason": f"Based on retry config: {config.get('retry_config', False)}, {structure.get('service_files', 0)} services, and database frameworks: {dependencies.get('database_frameworks', [])}"
        }
        
        # Gate 3.6: Throttling, drop request
        throttling_count = 0
        if config.get("throttling_config"):
            throttling_count += 1  # Throttling configuration indicates throttling logic
        if structure.get("controller_files", 0) > 0:
            throttling_count += max(1, structure["controller_files"] // 2)  # Every other controller should have throttling
        expected_counts["3.6"] = {
            "expected_count": max(1, throttling_count),
            "reason": f"Based on throttling config: {config.get('throttling_config', False)} and {structure.get('controller_files', 0)} controllers"
        }
        
        # Gate 3.9: Circuit Breaker
        circuit_breaker_count = 0
        if config.get("circuit_breaker_config"):
            circuit_breaker_count += 1  # Circuit breaker configuration indicates circuit breaker logic
        if structure.get("service_files", 0) > 0:
            circuit_breaker_count += max(1, structure["service_files"] // 4)  # Every fourth service should have circuit breaker
        expected_counts["3.9"] = {
            "expected_count": max(1, circuit_breaker_count),
            "reason": f"Based on circuit breaker config: {config.get('circuit_breaker_config', False)} and {structure.get('service_files', 0)} services"
        }
        
        # Gate 3.18: Health Checks
        health_check_count = 0
        if config.get("health_check_config"):
            health_check_count += 1  # Health check configuration indicates health checks
        if dependencies.get("monitoring_frameworks"):
            health_check_count += len(dependencies["monitoring_frameworks"])  # Each monitoring framework should have health checks
        if structure.get("has_web_layer"):
            health_check_count += 1  # Web layer should have health checks
        expected_counts["3.18"] = {
            "expected_count": max(1, health_check_count),
            "reason": f"Based on health check config: {config.get('health_check_config', False)}, monitoring frameworks: {dependencies.get('monitoring_frameworks', [])}, and web layer: {structure.get('has_web_layer', False)}"
        }
        
        return expected_counts
    
    def _calculate_testing_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for testing gates"""
        expected_counts = {}
        
        # Gate 2: Testing (general)
        testing_count = 0
        if structure.get("test_files", 0) > 0:
            testing_count += structure["test_files"]  # Each test file indicates testing
        if dependencies.get("testing_frameworks"):
            testing_count += len(dependencies["testing_frameworks"])  # Each testing framework indicates testing
        if structure.get("java_files", 0) > 0:
            testing_count += max(1, structure["java_files"] // 10)  # At least 1 test per 10 Java files
        expected_counts["2"] = {
            "expected_count": max(1, testing_count),
            "reason": f"Based on {structure.get('test_files', 0)} test files, testing frameworks: {dependencies.get('testing_frameworks', [])}, and {structure.get('java_files', 0)} Java files"
        }
        
        return expected_counts
    
    def _calculate_security_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for security gates"""
        expected_counts = {}
        
        # Security gates would be calculated here based on security frameworks and configurations
        # For now, return empty dict as security gates are not in the main scope
        
        return expected_counts
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-analysis processing"""
        if exec_res == "success":
            context.patterns = self.context.patterns
        return exec_res


class PatternConsolidationNode(AsyncNode):
    """Step 4: Pattern Consolidation"""
    
    def __init__(self, pattern_library_service=None):
        super().__init__()
        self.pattern_library_service = pattern_library_service
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
            
            # Add enhanced pattern library patterns if available
            if self.pattern_library_service:
                # Map enhanced pattern library gate IDs to expected numeric gate IDs
                gate_id_mapping = {
                    "STRUCTURED_LOGS": "1.1",           # Logs Searchable/Available
                    "AVOID_LOGGING_SECRETS": "1.10",    # Avoid Logging Sensitive Data
                    "TESTING_INFRASTRUCTURE": "2",      # Automated Regression Testing
                    "DOCUMENTATION_AVAILABLE": "1.3",   # Audit Trail (closest match)
                    "CONTAINERIZATION_READY": "3.18",   # Health Checks (closest match)
                    "ERROR_HANDLING": "2.4",            # Include Client error tracking
                    "INPUT_VALIDATION": "2.7"           # UI Error Handling
                }
                
                for enhanced_gate_id, pattern_info in self.pattern_library_service.patterns.items():
                    # Map to expected gate ID
                    expected_gate_id = gate_id_mapping.get(enhanced_gate_id, enhanced_gate_id)
                    
                    for pattern in pattern_info.patterns:
                        consolidated.append({
                            "source": "enhanced_library",
                            "gate_id": expected_gate_id,  # Use mapped gate ID
                            "name": pattern_info.display_name,
                            "pattern": pattern,
                            "description": pattern_info.description,
                            "severity": pattern_info.priority.upper(),
                            "category": pattern_info.category
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
        # Comprehensive static patterns for all hard gates
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
            {
                "gate_id": "2.7",
                "name": "UI Error Handling",
                "description": "Critical and error log messages from client devices",
                "pattern": r"ui.*error|client.*error|browser.*error|mobile.*error|frontend.*error",
                "severity": "MEDIUM",
                "category": "AUDITABILITY",
                "examples": ["UI error handling", "client error logging", "browser error tracking"]
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
            {
                "gate_id": "2.4",
                "name": "Include Client error tracking",
                "description": "Include client error tracking for monitoring",
                "pattern": r"client.*error|error.*tracking|client.*tracking|error.*monitoring",
                "severity": "MEDIUM",
                "category": "ERROR_HANDLING",
                "examples": ["client error tracking", "error monitoring", "client tracking"]
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
            "patterns": context.patterns,
            "expected_counts_analysis": getattr(context, 'expected_counts_analysis', {})
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute expected implementation calculation for both repositories"""
        try:
            print("🔍 Step 5: Expected Implementation Calculation (including CD repos)")
            
            vector_data = prep_res["vector_data"]
            patterns = prep_res["patterns"]
            expected_counts_analysis = prep_res.get("expected_counts_analysis", {})
            
            scan_id = vector_data["scan_id"]
            collection_name = vector_data["collection_name"]
            consolidated_patterns = patterns["consolidated"]
            
            expected_implementations = {}
            
            # Define all hard gates from the prompt library
            hard_gates = {
                # Auditability gates
                '1.1', '1.3', '1.5', '1.6', '1.8', '1.10', '2.7',
                # Error Handling gates
                '1.1', '1.3', '2.4',
                # Availability gates
                '1.5', '1.12', '3.6', '3.9', '3.18',
                # Testing gates
                '2'
            }
            
            # For each pattern, find expected implementations using semantic search
            for pattern in consolidated_patterns:
                # Only process hard gates
                if pattern.get("gate_id") not in hard_gates:
                    continue
                pattern_name = pattern["name"]
                pattern_description = pattern["description"]
                
                # Create semantic query
                query = f"implementation of {pattern_name}: {pattern_description}"
                query_embedding = self.embedding_service.embed_single(query)
                
                if query_embedding:
                    # Check if collection exists before searching
                    if not self.vector_service.collection_exists(collection_name):
                        print(f"⚠️ Collection {collection_name} does not exist, using project structure analysis for {pattern_name}")
                        
                        # Use project structure analysis if available
                        gate_id = pattern["gate_id"]
                        if gate_id in expected_counts_analysis:
                            analysis = expected_counts_analysis[gate_id]
                            expected_count = analysis.get("expected_count", 1)
                            reason = analysis.get("reason", "Based on project structure analysis")
                            print(f"📊 Using project structure analysis for {gate_id}: {expected_count} expected ({reason})")
                        else:
                            expected_count = 1
                            reason = "Default fallback (no project structure analysis available)"
                        
                        expected_implementations[gate_id] = {
                            "pattern": pattern,
                            "expected_count": expected_count,
                            "main_implementations": 0,
                            "cd_implementations": 0,
                            "similar_implementations": [],
                            "calculation_method": "project_structure_analysis",
                            "reason": reason
                        }
                        continue
                    
                    # Search single collection for both main and CD repositories
                    all_results = self.vector_service.search_similar(
                        collection_name=collection_name,
                        query_vector=query_embedding,
                        limit=20,  # Increased limit to get both main and CD results
                        score_threshold=0.5
                    )
                else:
                    # Fallback when embedding generation fails
                    print(f"⚠️ Failed to generate embedding for query: {query}")
                    
                    # Use project structure analysis if available
                    gate_id = pattern["gate_id"]
                    if gate_id in expected_counts_analysis:
                        analysis = expected_counts_analysis[gate_id]
                        expected_count = analysis.get("expected_count", 1)
                        reason = analysis.get("reason", "Based on project structure analysis")
                        print(f"📊 Using project structure analysis for {gate_id}: {expected_count} expected ({reason})")
                    else:
                        expected_count = 1
                        reason = "Default fallback (embedding generation failed)"
                    
                    expected_implementations[gate_id] = {
                        "pattern": pattern,
                        "expected_count": expected_count,
                        "main_implementations": 0,
                        "cd_implementations": 0,
                        "similar_implementations": [],
                        "calculation_method": "project_structure_analysis_fallback",
                        "reason": reason
                    }
                    continue
                    
                    # Process results and separate by repo_type
                    main_results = []
                    cd_results = []
                    
                    for result in all_results:
                        repo_type = result.payload.get("repo_type", "main")
                        result_data = {
                            "content": result.payload.get("content", ""),
                            "file_path": result.payload.get("file_path", ""),
                            "repo_type": repo_type,
                            "score": result.score
                        }
                        
                        if repo_type == "main":
                            main_results.append(result_data)
                        elif repo_type == "cd":
                            cd_results.append(result_data)
                    
                    # Combine and sort by score
                    combined_results = main_results + cd_results
                    combined_results.sort(key=lambda x: x["score"], reverse=True)
                    
                    # Use vector search results, but enhance with project structure analysis if available
                    gate_id = pattern["gate_id"]
                    vector_based_count = len(combined_results)
                    
                    # Check if we have project structure analysis for this gate
                    if gate_id in expected_counts_analysis:
                        analysis = expected_counts_analysis[gate_id]
                        project_based_count = analysis.get("expected_count", vector_based_count)
                        reason = analysis.get("reason", "Based on project structure analysis")
                        
                        # Use the higher of the two counts, or vector-based if project analysis is not available
                        final_expected_count = max(vector_based_count, project_based_count)
                        
                        print(f"📊 Gate {gate_id}: Vector search found {vector_based_count}, project analysis suggests {project_based_count}, using {final_expected_count}")
                        
                        expected_implementations[gate_id] = {
                            "pattern": pattern,
                            "expected_count": final_expected_count,
                            "main_implementations": len(main_results),
                            "cd_implementations": len(cd_results),
                            "similar_implementations": combined_results[:15],  # Top 15 combined results
                            "calculation_method": "vector_search_enhanced_with_project_analysis",
                            "vector_based_count": vector_based_count,
                            "project_based_count": project_based_count,
                            "reason": reason
                        }
                    else:
                        # Use vector search results only
                        expected_implementations[gate_id] = {
                            "pattern": pattern,
                            "expected_count": vector_based_count,
                            "main_implementations": len(main_results),
                            "cd_implementations": len(cd_results),
                            "similar_implementations": combined_results[:15],  # Top 15 combined results
                            "calculation_method": "vector_search_only"
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
            
            # Define all hard gates from the prompt library
            hard_gates = {
                # Auditability gates
                '1.1', '1.3', '1.5', '1.6', '1.8', '1.10', '2.7',
                # Error Handling gates
                '1.1', '1.3', '2.4',
                # Availability gates
                '1.5', '1.12', '3.6', '3.9', '3.18',
                # Testing gates
                '2'
            }
            
            # Filter patterns to only include hard gates
            hard_gate_patterns = [p for p in consolidated_patterns if p.get("gate_id") in hard_gates]
            
            # Scan main repository files for each pattern
            print(f"🔍 Scanning main repository: {repo_path}")
            for pattern in hard_gate_patterns:
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
                for pattern in hard_gate_patterns:
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
        """Scan for specific pattern in repository with gate-specific file filtering"""
        import re
        
        matches = []
        repo_path_obj = Path(repo_path)
        
        try:
            pattern = re.compile(pattern_regex, re.IGNORECASE)
        except re.error:
            print(f"⚠️ Invalid regex pattern for gate {gate_id}: {pattern_regex}")
            return matches
        
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file_for_gate(file_path, gate_id):
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
    
    def _should_ignore_file_for_gate(self, file_path: Path, gate_id: str) -> bool:
        """Check if file should be ignored for specific gate based on gate category"""
        try:
            # First apply general file filtering
            if self._should_ignore_file(file_path):
                return True
            
            # Define allowed source code and build file extensions for hard gate validation
            allowed_source_extensions = {
                # Source code files
                '.java', '.py', '.js', '.ts', '.jsx', '.tsx', '.cs', '.cpp', '.c', '.h', '.hpp',
                '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.clj', '.hs', '.ml',
                '.sql', '.r', '.m', '.mm', '.pl', '.sh', '.bash', '.zsh', '.fish',
                
                # Configuration and build files
                '.xml', '.properties', '.yml', '.yaml', '.json', '.toml', '.ini', '.cfg',
                '.gradle', '.gradle.kts', 'pom.xml', 'build.gradle', 'package.json',
                'requirements.txt', 'setup.py', 'pyproject.toml', 'Cargo.toml', 'go.mod',
                'composer.json', 'Gemfile', 'Podfile', 'Dockerfile', 'docker-compose.yml',
                '.dockerignore', '.gitignore', '.env', '.env.example',
                
                # Documentation files (excluded from hard gate analysis)
                # '.md', '.txt', '.rst', '.adoc'  # Commented out to exclude documentation
            }
            
            # Define test file extensions
            test_extensions = {
                '.test.java', '.test.py', '.test.js', '.test.ts', '.spec.java', '.spec.py',
                '.spec.js', '.spec.ts', '_test.java', '_test.py', '_test.js', '_test.ts',
                '_spec.java', '_spec.py', '_spec.js', '_spec.ts'
            }
            
            # Define gate categories and their file restrictions
            gate_categories = {
                # Testing gates - only consider test files
                "2": "TESTING",
                
                # All other gates - only consider source code and build files
                "1.1": "SOURCE_CODE",
                "1.3": "SOURCE_CODE", 
                "1.5": "SOURCE_CODE",
                "1.6": "SOURCE_CODE",
                "1.8": "SOURCE_CODE",
                "1.10": "SOURCE_CODE",
                "2.4": "SOURCE_CODE",
                "2.7": "SOURCE_CODE",
                "1.12": "SOURCE_CODE",
                "3.6": "SOURCE_CODE",
                "3.9": "SOURCE_CODE",
                "3.18": "SOURCE_CODE"
            }
            
            gate_category = gate_categories.get(gate_id, "SOURCE_CODE")
            file_path_str = str(file_path).lower()
            file_extension = file_path.suffix.lower()
            
            # Define test file patterns
            test_patterns = [
                'test/', 'tests/', 'testing/', 'spec/', 'specs/',
                '.test.', '.spec.', '_test.', '_spec.',
                'test_', 'spec_', 'test.', 'spec.',
                'jmeter/', 'jmx', '.jmx',
                'cypress/', 'playwright/', 'selenium/',
                'e2e/', 'integration/', 'unit/',
                'testdata/', 'fixtures/', 'mocks/'
            ]
            
            # Check if file is a test file
            is_test_file = any(pattern in file_path_str for pattern in test_patterns) or file_extension in test_extensions
            
            # Apply category-specific filtering
            if gate_category == "TESTING":
                # For testing gates, only include test files
                return not is_test_file
            elif gate_category == "SOURCE_CODE":
                # For source code gates, only include source code and build files, exclude test files
                if is_test_file:
                    return True
                
                # Check if file has an allowed extension
                has_allowed_extension = file_extension in allowed_source_extensions
                
                # Special handling for files without extensions (like Dockerfile, Makefile)
                if not has_allowed_extension:
                    # Check if filename is in allowed list
                    filename = file_path.name.lower()
                    allowed_filenames = [
                        'dockerfile', 'makefile',
                        'pom.xml', 'build.gradle', 'package.json', 'requirements.txt',
                        'setup.py', 'pyproject.toml', 'cargo.toml', 'go.mod',
                        'composer.json', 'gemfile', 'podfile', '.gitignore', '.env'
                    ]
                    has_allowed_extension = filename in allowed_filenames
                
                return not has_allowed_extension
            
            return True  # Default to ignoring unknown categories
            
        except Exception as e:
            print(f"⚠️ Error in gate-specific file filtering: {e}")
            # Fallback to general filtering
            return self._should_ignore_file(file_path)
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored using enhanced filtering"""
        try:
            # Load file filtering configuration
            import json
            import os
            
            config_path = os.path.join(os.path.dirname(__file__), "..", "data", "file_filtering_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                filtering_config = config.get("file_filtering", {})
                ignore_patterns = filtering_config.get("ignore_patterns", [])
            else:
                # Fallback to default patterns
                ignore_patterns = [
                    '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
                    '.pytest_cache', 'target', 'build', 'dist', 'out',
                    '.idea', '.vscode', '.vs', '.DS_Store'
                ]
            
            # Check ignore patterns
            file_path_str = str(file_path)
            for pattern in ignore_patterns:
                if pattern in file_path_str:
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error in file filtering: {e}")
            # Fallback to basic filtering
            basic_patterns = ['.git', '.svn', '.hg', 'node_modules', '__pycache__']
            return any(pattern in str(file_path) for pattern in basic_patterns)
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-scanning processing"""
        if exec_res == "success":
            context.scan_results = self.context.scan_results
        return exec_res


class GateEvaluationNode(AsyncNode):
    """Step 7: Gate Evaluation & Threshold Checking"""
    
    def __init__(self):
        super().__init__()
    
    def _should_skip_gate(self, gate_id: str, pattern: Dict[str, Any], 
                         metadata: Dict[str, Any], scan_results: Dict[str, Any]) -> bool:
        """Determine if a gate should be skipped based on technology and codebase analysis"""
        try:
            # Get technology stack from metadata
            tech_stack = metadata.get("tech_stack", {})
            file_types = metadata.get("file_types", {})
            
            # Technology-specific gate skipping rules
            skip_rules = {
                # Java-specific gates that should be skipped for non-Java projects
                "1.1": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.3": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.5": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.6": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.8": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.10": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "2.7": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                
                # Python-specific gates
                "2.4": lambda tech, files: tech.get("python", 0) == 0 and tech.get("django", 0) == 0 and tech.get("flask", 0) == 0,
                
                # JavaScript-specific gates
                "1.12": lambda tech, files: tech.get("javascript", 0) == 0 and tech.get("node", 0) == 0,
                "3.6": lambda tech, files: tech.get("javascript", 0) == 0 and tech.get("node", 0) == 0,
                "3.9": lambda tech, files: tech.get("javascript", 0) == 0 and tech.get("node", 0) == 0,
                "3.18": lambda tech, files: tech.get("javascript", 0) == 0 and tech.get("node", 0) == 0,
            }
            
            # Check if this gate should be skipped
            skip_rule = skip_rules.get(gate_id)
            if skip_rule and skip_rule(tech_stack, file_types):
                print(f"   ⏭️ Skipping gate {gate_id} - not applicable for current technology stack")
                return True
            
            # Check if no relevant files exist for this gate
            pattern_category = pattern.get("category", "").lower()
            if "security" in pattern_category and not any([
                file_types.get("java", 0) > 0,
                file_types.get("py", 0) > 0,
                file_types.get("js", 0) > 0,
                file_types.get("ts", 0) > 0
            ]):
                print(f"   ⏭️ Skipping gate {gate_id} - no relevant source files found")
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking if gate {gate_id} should be skipped: {e}")
            return False
    
    def _calculate_intelligent_expected_count(self, gate_id: str, pattern: Dict[str, Any], 
                                            metadata: Dict[str, Any], scan_results: Dict[str, Any]) -> int:
        """Calculate intelligent expected count based on technology stack and codebase analysis"""
        try:
            # Get technology stack from metadata
            tech_stack = metadata.get("tech_stack", {})
            file_types = metadata.get("file_types", {})
            total_files = metadata.get("total_files", 0)
            
            # Base expected counts by technology and gate category
            base_expected_counts = {
                # Security gates
                "1.1": {"java": 3, "python": 2, "javascript": 2, "default": 1},  # Authentication
                "1.3": {"java": 5, "python": 3, "javascript": 3, "default": 2},  # Authorization
                "1.5": {"java": 4, "python": 2, "javascript": 2, "default": 1},  # Input validation
                "1.6": {"java": 3, "python": 2, "javascript": 2, "default": 1},  # Output encoding
                "1.8": {"java": 2, "python": 1, "javascript": 1, "default": 1},  # Session management
                "1.10": {"java": 3, "python": 2, "javascript": 2, "default": 1}, # Error handling
                "2.7": {"java": 2, "python": 1, "javascript": 1, "default": 1},  # Logging
                
                # Error Handling gates
                "2.4": {"java": 4, "python": 3, "javascript": 3, "default": 2},  # Exception handling
                
                # Availability gates
                "1.12": {"java": 3, "python": 2, "javascript": 2, "default": 1}, # Timeouts
                "3.6": {"java": 2, "python": 1, "javascript": 1, "default": 1},  # Circuit breakers
                "3.9": {"java": 3, "python": 2, "javascript": 2, "default": 1},  # Retry logic
                "3.18": {"java": 2, "python": 1, "javascript": 1, "default": 1}, # Health checks
                
                # Testing gates
                "2": {"java": 5, "python": 4, "javascript": 4, "default": 3},     # Unit tests
            }
            
            # Determine primary technology
            primary_tech = "default"
            if tech_stack.get("java", 0) > 0:
                primary_tech = "java"
            elif tech_stack.get("python", 0) > 0:
                primary_tech = "python"
            elif tech_stack.get("javascript", 0) > 0:
                primary_tech = "javascript"
            
            # Get base expected count for this gate and technology
            gate_expected = base_expected_counts.get(gate_id, {"default": 1})
            base_count = gate_expected.get(primary_tech, gate_expected.get("default", 1))
            
            # Adjust based on codebase size
            size_multiplier = 1.0
            if total_files > 100:
                size_multiplier = 1.5
            elif total_files > 50:
                size_multiplier = 1.2
            elif total_files < 10:
                size_multiplier = 0.5
            
            # Adjust based on specific file types present
            file_type_multiplier = 1.0
            
            # For Java projects, check for specific file types
            if primary_tech == "java":
                if file_types.get("java", 0) > 0:
                    file_type_multiplier = 1.2
                if file_types.get("xml", 0) > 0:  # Spring configs
                    file_type_multiplier += 0.3
                if file_types.get("properties", 0) > 0:  # Properties files
                    file_type_multiplier += 0.2
                    
            # For Python projects
            elif primary_tech == "python":
                if file_types.get("py", 0) > 0:
                    file_type_multiplier = 1.2
                if file_types.get("requirements", 0) > 0 or file_types.get("txt", 0) > 0:
                    file_type_multiplier += 0.2
                    
            # For JavaScript projects
            elif primary_tech == "javascript":
                if file_types.get("js", 0) > 0 or file_types.get("ts", 0) > 0:
                    file_type_multiplier = 1.2
                if file_types.get("json", 0) > 0:
                    file_type_multiplier += 0.2
                if file_types.get("package", 0) > 0:
                    file_type_multiplier += 0.3
            
            # Calculate final expected count
            final_expected = max(1, int(base_count * size_multiplier * file_type_multiplier))
            
            # Special adjustments for specific gates based on actual codebase
            if gate_id == "2":  # Testing gate
                # Check if test files exist
                test_files = sum([
                    file_types.get("test", 0),
                    file_types.get("spec", 0),
                    file_types.get("specs", 0)
                ])
                if test_files == 0:
                    final_expected = max(1, final_expected // 2)  # Reduce expectation if no test files
            
            print(f"   📊 Gate {gate_id} expected count: {final_expected} (tech: {primary_tech}, files: {total_files}, multiplier: {size_multiplier:.1f}x{file_type_multiplier:.1f})")
            
            return final_expected
            
        except Exception as e:
            print(f"⚠️ Error calculating expected count for gate {gate_id}: {e}")
            return 1  # Default fallback
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare gate evaluation"""
        return {
            "scan_results": context.scan_results,
            "expected_implementations": context.expected_implementations,
            "metadata": context.metadata
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute gate evaluation for both repositories"""
        try:
            print("⚖️ Step 7: Gate Evaluation & Threshold Checking (including CD repos)")
            
            scan_results = prep_res["scan_results"]
            expected_implementations = prep_res["expected_implementations"]
            metadata = prep_res.get("metadata", {})
            
            # Handle case where scan_results is None
            if not scan_results:
                print("❌ No scan results available for gate evaluation")
                return "error"
            
            # Handle case where expected_implementations is None
            if not expected_implementations:
                print("⚠️ No expected implementations available, using defaults")
                expected_implementations = {}
            
            gate_results = []
            
            # Define all hard gates from the prompt library
            hard_gates = {
                # Auditability gates
                '1.1', '1.3', '1.5', '1.6', '1.8', '1.10', '2.7',
                # Error Handling gates
                '2.4',
                # Availability gates
                '1.12', '3.6', '3.9', '3.18',
                # Testing gates
                '2'
            }
            
            for gate_id, scan_result in scan_results.items():
                # Only process hard gates
                if gate_id not in hard_gates:
                    continue
                pattern = scan_result["pattern"]
                main_matches = scan_result.get("main_matches", [])
                cd_matches = scan_result.get("cd_matches", [])
                total_matches = scan_result.get("total_matches", 0)
                
                # Temporarily disable gate skipping to ensure all gates are evaluated
                # if self._should_skip_gate(gate_id, pattern, metadata, scan_results):
                #     continue
                
                # Calculate intelligent expected count based on technology and codebase
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from flow.expected_count_calculator import ExpectedCountCalculator
                calculator = ExpectedCountCalculator()
                expected_count = calculator.calculate_expected_count(gate_id, metadata)
                
                # Determine threshold (simplified logic)
                threshold = self._calculate_threshold(pattern, expected_count)
                
                # Evaluate gate status
                status = self._evaluate_gate_status(total_matches, expected_count, threshold)
                
                # Convert scan results to PatternMatch objects
                detailed_matches = []
                for match in main_matches + cd_matches:
                    detailed_matches.append(PatternMatch(
                        file_path=match["file_path"],
                        line_number=match["line_number"],
                        match_text=match["match_text"],
                        repo_type=match["repo_type"],
                        start_pos=match["start_pos"],
                        end_pos=match["end_pos"],
                        pattern=pattern["pattern"]
                    ))
                
                # Generate base reasoning and recommendations
                base_reasoning = self._generate_reasoning(status, pattern, total_matches, expected_count, len(main_matches), len(cd_matches))
                base_recommendations = self._generate_recommendations(status, pattern, total_matches, expected_count)
                
                # Create gate result with enhanced reasoning and recommendations
                gate_result = GateResult(
                    gate_id=gate_id,
                    gate_name=pattern["name"],
                    status=status,
                    expected_count=expected_count,
                    actual_count=total_matches,
                    threshold=threshold,
                    patterns_found=[match["match_text"] for match in (main_matches + cd_matches)[:5]],  # Top 5 matches
                    detailed_matches=detailed_matches,
                    recommendations=base_recommendations,
                    confidence_score=self._calculate_confidence(total_matches, expected_count),
                    reasoning=base_reasoning
                )
                
                # Enhance reasoning and recommendations with vector context and LLM (async)
                try:
                    # Get vector service and LLM service from context
                    vector_service = getattr(self.context, 'vector_service', None)
                    llm_service = getattr(self.context, 'llm_service', None)
                    scan_id = getattr(self.context, 'scan_id', 'unknown')
                    
                    if vector_service:
                        # Enhance reasoning with vector context
                        enhanced_reasoning = await self._generate_enhanced_reasoning_with_vector_context(
                            gate_result, vector_service, scan_id
                        )
                        gate_result.reasoning = enhanced_reasoning
                    
                    if llm_service and vector_service:
                        # Generate contextual recommendations with LLM
                        contextual_recommendations = await self._generate_contextual_recommendations_with_llm(
                            gate_result, vector_service, scan_id, llm_service
                        )
                        gate_result.recommendations = contextual_recommendations
                        
                except Exception as e:
                    print(f"⚠️ Failed to enhance gate {gate_id} with vector/LLM context: {e}")
                    # Keep base reasoning and recommendations if enhancement fails
                
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
        """Evaluate gate status with improved logic"""
        # If expected count is 0 or very low, this gate might not be applicable
        if expected_count <= 0:
            return GateStatus.SKIPPED
        
        # If we found implementations, evaluate based on expected count
        if actual_count >= expected_count:
            return GateStatus.PASS
        elif actual_count >= threshold:
            return GateStatus.PARTIAL
        elif actual_count > 0:
            return GateStatus.FAIL
        else:
            # Only mark as SKIPPED if we have a reasonable expected count but found nothing
            # This indicates the gate is applicable but not implemented
            if expected_count >= 2:
                return GateStatus.FAIL  # Should have implementations but doesn't
            else:
                return GateStatus.SKIPPED  # Low expectation, might not be applicable
    
    def _generate_recommendations(self, status: GateStatus, pattern: Dict[str, Any], 
                                actual_count: int, expected_count: int) -> List[str]:
        """Generate enhanced recommendations based on gate status and context"""
        recommendations = []
        
        if status == GateStatus.FAIL:
            # Enhanced failure recommendations
            if "security" in pattern.get('category', '').lower():
                recommendations.append(f"🔒 CRITICAL: Implement {pattern['name']} immediately to address security vulnerabilities")
                recommendations.append(f"💡 Consider implementing {pattern['name']} using industry best practices and security frameworks")
            elif "auditability" in pattern.get('category', '').lower():
                recommendations.append(f"📊 HIGH PRIORITY: Implement {pattern['name']} for compliance and audit requirements")
                recommendations.append(f"🔍 Add comprehensive logging and monitoring for {pattern['name']}")
            elif "error_handling" in pattern.get('category', '').lower():
                recommendations.append(f"⚠️ MEDIUM PRIORITY: Implement robust {pattern['name']} to improve system reliability")
                recommendations.append(f"🛠️ Add proper error handling, logging, and user feedback for {pattern['name']}")
            elif "availability" in pattern.get('category', '').lower():
                recommendations.append(f"⚡ MEDIUM PRIORITY: Implement {pattern['name']} to enhance system availability")
                recommendations.append(f"🔄 Add retry logic, timeouts, and circuit breakers for {pattern['name']}")
            else:
                recommendations.append(f"📋 Implement {pattern['name']} to improve {pattern.get('category', 'quality').lower()}")
            
            # Add specific implementation guidance
            if actual_count == 0:
                recommendations.append(f"🚀 Start with basic implementation of {pattern['name']} and gradually enhance")
            else:
                recommendations.append(f"📈 Enhance existing {pattern['name']} implementation for better coverage")
                
        elif status == GateStatus.PARTIAL:
            recommendations.append(f"📊 Enhance {pattern['name']} implementation for better coverage")
            recommendations.append(f"🎯 Focus on areas with missing {pattern['name']} implementations")
            if actual_count < expected_count:
                recommendations.append(f"📝 Review and expand {pattern['name']} coverage across all relevant components")
        elif status == GateStatus.PASS:
            recommendations.append(f"✅ Good implementation of {pattern['name']}")
            recommendations.append(f"🔄 Continue monitoring and maintaining {pattern['name']} standards")
        elif status == GateStatus.SKIPPED:
            # Provide context for why gate was skipped
            if expected_count <= 0:
                recommendations.append(f"ℹ️ Gate {pattern['name']} not applicable to current technology stack")
                recommendations.append(f"📋 This gate is designed for different technology frameworks")
            else:
                recommendations.append(f"ℹ️ Gate {pattern['name']} has low applicability to current codebase")
                recommendations.append(f"📋 Consider implementing if project scope expands")
        else:
            recommendations.append(f"❓ Review {pattern['name']} requirements and implementation strategy")
        
        return recommendations
    
    def _calculate_confidence(self, actual_count: int, expected_count: int) -> float:
        """Calculate enhanced confidence score"""
        if expected_count == 0:
            return 0.5
        
        ratio = actual_count / expected_count
        # Enhanced confidence calculation with better granularity
        if ratio >= 1.0:
            return 1.0  # Full compliance
        elif ratio >= 0.8:
            return 0.9  # Near compliance
        elif ratio >= 0.6:
            return 0.7  # Good progress
        elif ratio >= 0.4:
            return 0.5  # Moderate progress
        elif ratio >= 0.2:
            return 0.3  # Limited progress
        else:
            return 0.1  # Minimal progress
    
    def _generate_reasoning(self, status: GateStatus, pattern: Dict[str, Any], 
                          actual_count: int, expected_count: int, main_count: int, cd_count: int) -> str:
        """Generate enhanced reasoning for gate evaluation with context"""
        category = pattern.get('category', 'quality').lower()
        severity = pattern.get('severity', 'medium').lower()
        
        # Base reasoning with enhanced context
        if status == GateStatus.PASS:
            base_reason = f"✅ PASS: Found {actual_count} implementations, meeting expected {expected_count}"
            if cd_count > 0:
                base_reason += f" (Main: {main_count}, CD: {cd_count})"
            
            # Add category-specific context
            if "security" in category:
                base_reason += f" - Security requirements satisfied"
            elif "auditability" in category:
                base_reason += f" - Audit trail requirements met"
            elif "error_handling" in category:
                base_reason += f" - Error handling properly implemented"
            elif "availability" in category:
                base_reason += f" - Availability requirements fulfilled"
                
        elif status == GateStatus.PARTIAL:
            base_reason = f"⚠️ PARTIAL: Found {actual_count} implementations, partially meeting expected {expected_count}"
            if cd_count > 0:
                base_reason += f" (Main: {main_count}, CD: {cd_count})"
            
            # Add improvement guidance
            if actual_count < expected_count:
                base_reason += f" - Need {expected_count - actual_count} more implementations"
            base_reason += f" - {severity.upper()} priority improvement required"
            
        elif status == GateStatus.FAIL:
            base_reason = f"❌ FAIL: Found {actual_count} implementations, below expected {expected_count}"
            if cd_count > 0:
                base_reason += f" (Main: {main_count}, CD: {cd_count})"
            
            # Add severity-based context
            if severity == "critical":
                base_reason += f" - CRITICAL: Immediate action required"
            elif severity == "high":
                base_reason += f" - HIGH: Priority remediation needed"
            else:
                base_reason += f" - {severity.upper()}: Improvement recommended"
                
        elif status == GateStatus.SKIPPED:
            if expected_count <= 0:
                base_reason = f"ℹ️ NOT APPLICABLE: {pattern['name']} not applicable to current technology stack"
                base_reason += f" - Expected count: {expected_count} (technology mismatch)"
            else:
                base_reason = f"ℹ️ NOT APPLICABLE: {pattern['name']} has low applicability to current codebase"
                base_reason += f" - Found {actual_count} implementations, expected {expected_count}"
            if cd_count > 0:
                base_reason += f" (Main: {main_count}, CD: {cd_count})"
        else:
            base_reason = f"❓ UNKNOWN: No implementations found for {pattern['name']}"
            if cd_count > 0:
                base_reason += f" (Main: {main_count}, CD: {cd_count})"
            base_reason += f" - Implementation status unclear"
        
        return base_reason

    async def _generate_enhanced_reasoning_with_vector_context(self, gate_result: GateResult, 
                                                              vector_service, scan_id: str) -> str:
        """Generate enhanced reasoning using vector database context and LLM"""
        try:
            # Search for relevant code patterns in vector database
            repo_hash = getattr(self.context, 'metadata', {}).get("main_repo", {}).get("commit_hash")
            collection_name = vector_service._get_collection_name(scan_id, repo_hash)
            
            # Create search queries based on gate context
            search_queries = [
                f"{gate_result.gate_name} implementation",
                f"{gate_result.gate_name} pattern",
                f"{gate_result.gate_name} code",
                f"{gate_result.gate_name} example"
            ]
            
            relevant_contexts = []
            for query in search_queries:
                results = vector_service.search(
                    collection_name=collection_name,
                    query=query,
                    limit=5,
                    score_threshold=0.3
                )
                
                for result in results:
                    if result.payload and result.payload.get("content"):
                        relevant_contexts.append({
                            "content": result.payload["content"][:200],  # Truncate for context
                            "file_path": result.payload.get("file_path", "Unknown"),
                            "score": result.score
                        })
            
            # Generate enhanced reasoning with context
            if relevant_contexts:
                context_summary = " | ".join([ctx["content"] for ctx in relevant_contexts[:3]])
                enhanced_reasoning = f"{gate_result.reasoning} | Context: {context_summary}"
                return enhanced_reasoning
            else:
                return gate_result.reasoning
                
        except Exception as e:
            print(f"⚠️ Failed to generate enhanced reasoning with vector context: {e}")
            return gate_result.reasoning

    def _extract_gate_category(self, gate_name: str) -> str:
        """Extract gate category from gate name"""
        gate_name_lower = gate_name.lower()
        
        if any(keyword in gate_name_lower for keyword in ['log', 'audit', 'tracking']):
            return "Auditability"
        elif any(keyword in gate_name_lower for keyword in ['error', 'exception', 'handling']):
            return "Error Handling"
        elif any(keyword in gate_name_lower for keyword in ['timeout', 'retry', 'throttling', 'availability']):
            return "Availability"
        elif any(keyword in gate_name_lower for keyword in ['test', 'testing', 'validation']):
            return "Testing"
        elif any(keyword in gate_name_lower for keyword in ['security', 'authentication', 'authorization']):
            return "Security"
        else:
            return "Quality"

    def _extract_gate_severity(self, gate_name: str) -> str:
        """Extract gate severity from gate name"""
        gate_name_lower = gate_name.lower()
        
        if any(keyword in gate_name_lower for keyword in ['critical', 'security', 'authentication']):
            return "critical"
        elif any(keyword in gate_name_lower for keyword in ['high', 'error', 'timeout', 'retry']):
            return "high"
        elif any(keyword in gate_name_lower for keyword in ['medium', 'log', 'audit']):
            return "medium"
        else:
            return "medium"

    def _remove_markdown_formatting(self, text: str) -> str:
        """Remove markdown formatting from text"""
        import re
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Inline code
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Code blocks
        text = re.sub(r'__(.*?)__', r'\1', text)      # Bold (alternative)
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
        text = re.sub(r'#{1,6}\s*', '', text)         # Headers
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
        text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)  # Images
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    async def _get_detailed_code_context(self, vector_service, scan_id: str, gate_name: str, detailed_matches: List[PatternMatch]) -> str:
        """Get detailed code context for recommendations"""
        try:
            repo_hash = getattr(self.context, 'metadata', {}).get("main_repo", {}).get("commit_hash")
            collection_name = vector_service._get_collection_name(scan_id, repo_hash)
            
            # Get technology stack and project structure
            tech_context = await self._get_technology_context(vector_service, collection_name)
            
            # Get specific implementation patterns
            implementation_context = self._get_implementation_context(detailed_matches)
            
            # Get related code patterns
            related_patterns = await self._get_related_patterns(vector_service, collection_name, gate_name)
            
            context_parts = []
            
            if tech_context:
                context_parts.append(f"Technology Stack: {tech_context}")
            
            if implementation_context:
                context_parts.append(f"Current Implementations: {implementation_context}")
            
            if related_patterns:
                context_parts.append(f"Related Patterns: {related_patterns}")
            
            return "\n\n".join(context_parts) if context_parts else "No detailed context available"
            
        except Exception as e:
            print(f"⚠️ Failed to get detailed code context: {e}")
            return "No detailed context available"

    async def _get_technology_context(self, vector_service, collection_name: str) -> str:
        """Get technology stack context"""
        try:
            # Search for technology indicators
            tech_queries = [
                "spring framework",
                "java application",
                "maven gradle",
                "database configuration",
                "logging framework",
                "testing framework"
            ]
            
            tech_info = []
            for query in tech_queries:
                results = vector_service.search(collection_name, query, limit=3, score_threshold=0.3)
                for result in results:
                    if result.payload and result.payload.get("content"):
                        content = result.payload["content"][:200]
                        file_path = result.payload.get("file_path", "Unknown")
                        tech_info.append(f"{query}: {content} (in {file_path})")
            
            return "; ".join(tech_info[:5]) if tech_info else "Technology stack not clearly identified"
            
        except Exception as e:
            print(f"⚠️ Failed to get technology context: {e}")
            return "Technology stack not clearly identified"

    def _get_implementation_context(self, detailed_matches: List[PatternMatch]) -> str:
        """Get context about current implementations"""
        if not detailed_matches:
            return "No implementations found"
        
        # Group by file type and analyze patterns
        file_types = {}
        for match in detailed_matches:
            file_ext = match.file_path.split('.')[-1] if '.' in match.file_path else 'unknown'
            if file_ext not in file_types:
                file_types[file_ext] = []
            file_types[file_ext].append(match)
        
        context_parts = []
        for file_ext, matches in file_types.items():
            files = list(set([m.file_path for m in matches]))
            context_parts.append(f"{file_ext.upper()} files ({len(files)}): {', '.join(files[:3])}")
        
        return "; ".join(context_parts)

    async def _get_related_patterns(self, vector_service, collection_name: str, gate_name: str) -> str:
        """Get related code patterns"""
        try:
            # Search for related patterns
            related_queries = [
                f"{gate_name} implementation",
                f"{gate_name} configuration",
                f"{gate_name} setup",
                f"{gate_name} examples"
            ]
            
            related_info = []
            for query in related_queries:
                results = vector_service.search(collection_name, query, limit=2, score_threshold=0.2)
                for result in results:
                    if result.payload and result.payload.get("content"):
                        content = result.payload["content"][:150]
                        file_path = result.payload.get("file_path", "Unknown")
                        related_info.append(f"{content} (in {file_path})")
            
            return "; ".join(related_info[:3]) if related_info else "No related patterns found"
            
        except Exception as e:
            print(f"⚠️ Failed to get related patterns: {e}")
            return "No related patterns found"

    def _get_implementation_files(self, detailed_matches: List[PatternMatch]) -> str:
        """Get list of files with implementations"""
        if not detailed_matches:
            return "None"
        
        files = list(set([match.file_path for match in detailed_matches]))
        return ", ".join(files[:5]) + ("..." if len(files) > 5 else "")

    def _get_pattern_summary(self, detailed_matches: List[PatternMatch]) -> str:
        """Get summary of pattern matches"""
        if not detailed_matches:
            return "None"
        
        patterns = list(set([match.pattern for match in detailed_matches]))
        return ", ".join(patterns[:3]) + ("..." if len(patterns) > 3 else "")

    async def _generate_contextual_recommendations_with_llm(self, gate_result: GateResult, 
                                                          vector_service, scan_id: str,
                                                          llm_service) -> List[str]:
        """Generate contextual recommendations using LLM and vector data"""
        try:
            # Get relevant code context from vector database
            repo_hash = getattr(self.context, 'metadata', {}).get("main_repo", {}).get("commit_hash")
            collection_name = vector_service._get_collection_name(scan_id, repo_hash)
            
            # Search for similar implementations
            similar_results = vector_service.search(
                collection_name=collection_name,
                query=f"{gate_result.gate_name} implementation examples",
                limit=10,
                score_threshold=0.2
            )
            
            # Extract relevant code examples
            code_examples = []
            for result in similar_results:
                if result.payload and result.payload.get("content"):
                    code_examples.append(result.payload["content"][:300])
            
            # Create LLM prompt for contextual recommendations using prompt library
            from services.prompt_service import PromptService
            prompt_service = PromptService()
            
            # Extract gate category and severity from the gate name
            gate_category = self._extract_gate_category(gate_result.gate_name)
            gate_severity = self._extract_gate_severity(gate_result.gate_name)
            
            # Get detailed code context from vector database
            detailed_context = await self._get_detailed_code_context(
                vector_service, scan_id, gate_result.gate_name, gate_result.detailed_matches
            )
            
            # Format the prompt using the prompt library
            prompt = prompt_service.format_prompt(
                "contextual_recommendations",
                gate_name=gate_result.gate_name,
                gate_status=gate_result.status.value,
                expected_count=gate_result.expected_count,
                actual_count=gate_result.actual_count,
                gate_category=gate_category,
                gate_severity=gate_severity,
                current_reasoning=gate_result.reasoning,
                code_context=detailed_context
            ) or f"""
Generate specific, actionable recommendations for improving the implementation of gate: {gate_result.gate_name}

Gate Details:
- Gate Name: {gate_result.gate_name}
- Status: {gate_result.status.value}
- Expected Count: {gate_result.expected_count}
- Actual Count: {gate_result.actual_count}
- Category: {gate_category}
- Severity: {gate_severity}
- Current Reasoning: {gate_result.reasoning}

Codebase Analysis:
{detailed_context}

Current Implementation Status:
- Found {gate_result.actual_count} implementations out of {gate_result.expected_count} expected
- Files with implementations: {self._get_implementation_files(gate_result.detailed_matches)}
- Pattern matches: {self._get_pattern_summary(gate_result.detailed_matches)}

Generate 3-5 specific, actionable recommendations that:
1. Are specifically tailored to the {gate_result.gate_name} gate and this codebase
2. Reference specific files, components, or patterns found in the codebase
3. Provide concrete implementation guidance based on the actual code structure
4. Address the specific gap (expected vs actual count) with codebase-specific solutions
5. Consider the technology stack and patterns used in this project
6. Suggest immediate fixes and long-term improvements based on the current implementation

IMPORTANT: 
- Make recommendations specific to {gate_result.gate_name} and this codebase
- Reference specific files, classes, or methods when relevant
- Consider the technology stack (Java, Spring, etc.) and project structure
- Do not use markdown formatting (no **, ##, etc.)
- Use clear, actionable language with specific implementation details

Format as a numbered list of specific recommendations without any markdown formatting.
"""
            
            # Call LLM for contextual recommendations
            response = await llm_service.generate(
                prompt,
                scan_id=scan_id,
                node_name="GateEvaluationNode",
                metadata={
                    "gate_name": gate_result.gate_name,
                    "gate_status": gate_result.status.value,
                    "context_examples_count": len(code_examples)
                }
            )
            
            # Parse LLM response into recommendations
            if response and len(response.strip()) > 0:
                # Extract numbered recommendations
                lines = response.strip().split('\n')
                recommendations = []
                
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                        # Clean up the recommendation
                        clean_rec = line.lstrip('0123456789.-• ').strip()
                        if clean_rec and len(clean_rec) > 10:
                            # Remove markdown formatting
                            clean_rec = self._remove_markdown_formatting(clean_rec)
                            recommendations.append(clean_rec)
                
                # If LLM didn't provide structured recommendations, create fallback
                if not recommendations:
                    recommendations = self._generate_recommendations(
                        gate_result.status, 
                        {"name": gate_result.gate_name, "category": "quality"}, 
                        gate_result.actual_count, 
                        gate_result.expected_count
                    )
                
                return recommendations[:5]  # Limit to 5 recommendations
            else:
                # Fallback to basic recommendations
                return self._generate_recommendations(
                    gate_result.status, 
                    {"name": gate_result.gate_name, "category": "quality"}, 
                    gate_result.actual_count, 
                    gate_result.expected_count
                )
                
        except Exception as e:
            print(f"⚠️ Failed to generate contextual recommendations with LLM: {e}")
            # Fallback to basic recommendations
            return self._generate_recommendations(
                gate_result.status, 
                {"name": gate_result.gate_name, "category": "quality"}, 
                gate_result.actual_count, 
                gate_result.expected_count
            )
    
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
            
            # Generate LLM-based project summary
            from services.vector_service import VectorService
            from services.project_summary_service import ProjectSummaryService
            from services.embedding_service import EmbeddingService
            from services.llm_service import LLMService
            
            # Initialize services
            vector_service = VectorService(vector_config)
            embedding_service = EmbeddingService(vector_config)
            
            # Initialize LLM service for project summary
            llm_config = {
                "provider": "local",
                "model": "llama3.2:3b",
                "timeout": 300,
                "temperature": 0.3,
                "max_tokens": 2000
            }
            llm_service = LLMService(llm_config)
            
            project_summary_service = ProjectSummaryService(vector_service, llm_service, embedding_service)
            
            # Generate intelligent project summary
            project_info = await project_summary_service.generate_llm_project_summary(
                repo_url=metadata.get("main_repo", {}).get("repo_url", "Unknown"),
                scan_id=scan_id,
                metadata=metadata
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

    def _calculate_intelligent_expected_count(self, gate_id: str, pattern: Dict[str, Any], 
                                            metadata: Dict[str, Any], scan_results: Dict[str, Any]) -> int:
        """Calculate intelligent expected count based on technology stack and codebase analysis"""
        try:
            # Get technology stack from metadata
            tech_stack = metadata.get("tech_stack", {})
            file_types = metadata.get("file_types", {})
            total_files = metadata.get("total_files", 0)
            
            # Base expected counts by technology and gate category
            base_expected_counts = {
                # Security gates
                "1.1": {"java": 3, "python": 2, "javascript": 2, "default": 1},  # Authentication
                "1.3": {"java": 5, "python": 3, "javascript": 3, "default": 2},  # Authorization
                "1.5": {"java": 4, "python": 2, "javascript": 2, "default": 1},  # Input validation
                "1.6": {"java": 3, "python": 2, "javascript": 2, "default": 1},  # Output encoding
                "1.8": {"java": 2, "python": 1, "javascript": 1, "default": 1},  # Session management
                "1.10": {"java": 3, "python": 2, "javascript": 2, "default": 1}, # Error handling
                "2.7": {"java": 2, "python": 1, "javascript": 1, "default": 1},  # Logging
                
                # Error Handling gates
                "2.4": {"java": 4, "python": 3, "javascript": 3, "default": 2},  # Exception handling
                
                # Availability gates
                "1.12": {"java": 3, "python": 2, "javascript": 2, "default": 1}, # Timeouts
                "3.6": {"java": 2, "python": 1, "javascript": 1, "default": 1},  # Circuit breakers
                "3.9": {"java": 3, "python": 2, "javascript": 2, "default": 1},  # Retry logic
                "3.18": {"java": 2, "python": 1, "javascript": 1, "default": 1}, # Health checks
                
                # Testing gates
                "2": {"java": 5, "python": 4, "javascript": 4, "default": 3},     # Unit tests
            }
            
            # Determine primary technology
            primary_tech = "default"
            if tech_stack.get("java", 0) > 0:
                primary_tech = "java"
            elif tech_stack.get("python", 0) > 0:
                primary_tech = "python"
            elif tech_stack.get("javascript", 0) > 0:
                primary_tech = "javascript"
            
            # Get base expected count for this gate and technology
            gate_expected = base_expected_counts.get(gate_id, {"default": 1})
            base_count = gate_expected.get(primary_tech, gate_expected.get("default", 1))
            
            # Adjust based on codebase size
            size_multiplier = 1.0
            if total_files > 100:
                size_multiplier = 1.5
            elif total_files > 50:
                size_multiplier = 1.2
            elif total_files < 10:
                size_multiplier = 0.5
            
            # Adjust based on specific file types present
            file_type_multiplier = 1.0
            
            # For Java projects, check for specific file types
            if primary_tech == "java":
                if file_types.get("java", 0) > 0:
                    file_type_multiplier = 1.2
                if file_types.get("xml", 0) > 0:  # Spring configs
                    file_type_multiplier += 0.3
                if file_types.get("properties", 0) > 0:  # Properties files
                    file_type_multiplier += 0.2
                    
            # For Python projects
            elif primary_tech == "python":
                if file_types.get("py", 0) > 0:
                    file_type_multiplier = 1.2
                if file_types.get("requirements", 0) > 0 or file_types.get("txt", 0) > 0:
                    file_type_multiplier += 0.2
                    
            # For JavaScript projects
            elif primary_tech == "javascript":
                if file_types.get("js", 0) > 0 or file_types.get("ts", 0) > 0:
                    file_type_multiplier = 1.2
                if file_types.get("json", 0) > 0:
                    file_type_multiplier += 0.2
                if file_types.get("package", 0) > 0:
                    file_type_multiplier += 0.3
            
            # Calculate final expected count
            final_expected = max(1, int(base_count * size_multiplier * file_type_multiplier))
            
            # Special adjustments for specific gates based on actual codebase
            if gate_id == "2":  # Testing gate
                # Check if test files exist
                test_files = sum([
                    file_types.get("test", 0),
                    file_types.get("spec", 0),
                    file_types.get("specs", 0)
                ])
                if test_files == 0:
                    final_expected = max(1, final_expected // 2)  # Reduce expectation if no test files
            
            print(f"   📊 Gate {gate_id} expected count: {final_expected} (tech: {primary_tech}, files: {total_files}, multiplier: {size_multiplier:.1f}x{file_type_multiplier:.1f})")
            
            return final_expected
            
        except Exception as e:
            print(f"⚠️ Error calculating expected count for gate {gate_id}: {e}")
            return 1  # Default fallback
    
    def _should_skip_gate(self, gate_id: str, pattern: Dict[str, Any], 
                         metadata: Dict[str, Any], scan_results: Dict[str, Any]) -> bool:
        """Determine if a gate should be skipped based on technology and codebase analysis"""
        try:
            # Get technology stack
            tech_stack = metadata.get("tech_stack", {})
            file_types = metadata.get("file_types", {})
            
            # Technology-specific gate skipping rules
            skip_rules = {
                # Java-specific gates that should be skipped for non-Java projects
                "1.1": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.3": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.5": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.6": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.8": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "1.10": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                "2.7": lambda tech, files: tech.get("java", 0) == 0 and tech.get("spring", 0) == 0,
                
                # Python-specific gates
                "2.4": lambda tech, files: tech.get("python", 0) == 0 and tech.get("django", 0) == 0 and tech.get("flask", 0) == 0,
                
                # JavaScript-specific gates
                "1.12": lambda tech, files: tech.get("javascript", 0) == 0 and tech.get("node", 0) == 0,
                "3.6": lambda tech, files: tech.get("javascript", 0) == 0 and tech.get("node", 0) == 0,
                "3.9": lambda tech, files: tech.get("javascript", 0) == 0 and tech.get("node", 0) == 0,
                "3.18": lambda tech, files: tech.get("javascript", 0) == 0 and tech.get("node", 0) == 0,
            }
            
            # Check if this gate should be skipped
            skip_rule = skip_rules.get(gate_id)
            if skip_rule and skip_rule(tech_stack, file_types):
                print(f"   ⏭️ Skipping gate {gate_id} - not applicable for current technology stack")
                return True
            
            # Check if no relevant files exist for this gate
            pattern_category = pattern.get("category", "").lower()
            if "security" in pattern_category and not any([
                file_types.get("java", 0) > 0,
                file_types.get("py", 0) > 0,
                file_types.get("js", 0) > 0,
                file_types.get("ts", 0) > 0
            ]):
                print(f"   ⏭️ Skipping gate {gate_id} - no relevant source files found")
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking if gate {gate_id} should be skipped: {e}")
            return False

    def _analyze_project_structure_for_expected_counts(self, metadata: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze project structure to calculate expected counts for each gate
        based on actual codebase structure, dependencies, and configuration
        """
        try:
            main_repo = metadata.get('main_repo', {})
            repo_path = main_repo.get('local_path')
            
            if not repo_path:
                print("⚠️ No repository path available for structure analysis")
                return {}
            
            expected_counts = {}
            
            # Analyze project structure
            project_structure = self._analyze_project_structure(repo_path)
            
            # Analyze dependencies and libraries
            dependencies = self._analyze_dependencies(repo_path, main_repo)
            
            # Analyze configuration files
            config_analysis = self._analyze_configuration_files(repo_path, main_repo)
            
            # Calculate expected counts for each gate category
            expected_counts.update(self._calculate_auditability_expected_counts(project_structure, dependencies, config_analysis))
            expected_counts.update(self._calculate_error_handling_expected_counts(project_structure, dependencies, config_analysis))
            expected_counts.update(self._calculate_availability_expected_counts(project_structure, dependencies, config_analysis))
            expected_counts.update(self._calculate_testing_expected_counts(project_structure, dependencies, config_analysis))
            expected_counts.update(self._calculate_security_expected_counts(project_structure, dependencies, config_analysis))
            
            print(f"✅ Project structure analysis completed: {len(expected_counts)} gate expected counts calculated")
            return expected_counts
            
        except Exception as e:
            print(f"❌ Project structure analysis failed: {e}")
            return {}
    
    def _analyze_project_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze the project structure and file organization"""
        try:
            structure = {
                "total_files": 0,
                "java_files": 0,
                "test_files": 0,
                "config_files": 0,
                "controller_files": 0,
                "service_files": 0,
                "repository_files": 0,
                "model_files": 0,
                "util_files": 0,
                "main_packages": [],
                "test_packages": [],
                "has_web_layer": False,
                "has_data_layer": False,
                "has_service_layer": False,
                "framework_indicators": []
            }
            
            repo_path_obj = Path(repo_path)
            
            for file_path in repo_path_obj.rglob("*"):
                if file_path.is_file():
                    structure["total_files"] += 1
                    file_name = file_path.name.lower()
                    file_path_str = str(file_path)
                    
                    # Count file types
                    if file_path.suffix == '.java':
                        structure["java_files"] += 1
                        
                        # Analyze Java file structure
                        if 'test' in file_path_str.lower():
                            structure["test_files"] += 1
                        elif 'controller' in file_path_str.lower():
                            structure["controller_files"] += 1
                        elif 'service' in file_path_str.lower():
                            structure["service_files"] += 1
                        elif 'repository' in file_path_str.lower():
                            structure["repository_files"] += 1
                        elif 'model' in file_path_str.lower() or 'entity' in file_path_str.lower():
                            structure["model_files"] += 1
                        elif 'util' in file_path_str.lower():
                            structure["util_files"] += 1
                    
                    # Detect framework indicators
                    if any(indicator in file_name for indicator in ['spring', 'boot', 'application']):
                        structure["framework_indicators"].append('spring_boot')
                    if any(indicator in file_name for indicator in ['pom.xml', 'build.gradle']):
                        structure["framework_indicators"].append('maven_or_gradle')
                    if any(indicator in file_name for indicator in ['web.xml', 'servlet']):
                        structure["framework_indicators"].append('servlet')
                    
                    # Detect layers
                    if any(layer in file_path_str.lower() for layer in ['controller', 'web', 'rest']):
                        structure["has_web_layer"] = True
                    if any(layer in file_path_str.lower() for layer in ['repository', 'dao', 'jpa']):
                        structure["has_data_layer"] = True
                    if any(layer in file_path_str.lower() for layer in ['service', 'business']):
                        structure["has_service_layer"] = True
                    
                    # Count config files
                    if any(config_ext in file_name for config_ext in ['.properties', '.yml', '.yaml', '.xml', '.json']):
                        structure["config_files"] += 1
            
            # Remove duplicates from framework indicators
            structure["framework_indicators"] = list(set(structure["framework_indicators"]))
            
            return structure
            
        except Exception as e:
            print(f"⚠️ Error analyzing project structure: {e}")
            return {}
    
    def _analyze_dependencies(self, repo_path: str, main_repo: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project dependencies and libraries"""
        try:
            dependencies = {
                "logging_frameworks": [],
                "testing_frameworks": [],
                "web_frameworks": [],
                "database_frameworks": [],
                "security_frameworks": [],
                "monitoring_frameworks": [],
                "build_tools": []
            }
            
            # Check build files for dependencies
            build_files = main_repo.get('build_files', [])
            for build_file in build_files:
                file_path = os.path.join(repo_path, build_file)
                content = self._read_file_content(file_path, max_lines=200)
                
                if content:
                    content_lower = content.lower()
                    
                    # Detect logging frameworks
                    if any(logger in content_lower for logger in ['logback', 'log4j', 'slf4j', 'logging']):
                        dependencies["logging_frameworks"].extend(['logback', 'log4j', 'slf4j'])
                    
                    # Detect testing frameworks
                    if any(test in content_lower for test in ['junit', 'testng', 'mockito', 'spring-test']):
                        dependencies["testing_frameworks"].extend(['junit', 'mockito', 'spring-test'])
                    
                    # Detect web frameworks
                    if any(web in content_lower for web in ['spring-web', 'spring-boot-starter-web', 'servlet']):
                        dependencies["web_frameworks"].extend(['spring-web', 'servlet'])
                    
                    # Detect database frameworks
                    if any(db in content_lower for db in ['spring-data', 'jpa', 'hibernate', 'jdbc']):
                        dependencies["database_frameworks"].extend(['spring-data', 'jpa', 'hibernate'])
                    
                    # Detect security frameworks
                    if any(sec in content_lower for sec in ['spring-security', 'oauth', 'jwt']):
                        dependencies["security_frameworks"].extend(['spring-security', 'oauth'])
                    
                    # Detect monitoring frameworks
                    if any(mon in content_lower for mon in ['actuator', 'micrometer', 'prometheus']):
                        dependencies["monitoring_frameworks"].extend(['actuator', 'micrometer'])
                    
                    # Detect build tools
                    if 'maven' in content_lower or 'pom.xml' in build_file:
                        dependencies["build_tools"].append('maven')
                    if 'gradle' in content_lower or 'build.gradle' in build_file:
                        dependencies["build_tools"].append('gradle')
            
            # Remove duplicates
            for key in dependencies:
                dependencies[key] = list(set(dependencies[key]))
            
            return dependencies
            
        except Exception as e:
            print(f"⚠️ Error analyzing dependencies: {e}")
            return {}
    
    def _analyze_configuration_files(self, repo_path: str, main_repo: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze configuration files for patterns and settings"""
        try:
            config_analysis = {
                "logging_config": False,
                "security_config": False,
                "database_config": False,
                "monitoring_config": False,
                "error_handling_config": False,
                "timeout_config": False,
                "retry_config": False,
                "throttling_config": False,
                "circuit_breaker_config": False,
                "health_check_config": False
            }
            
            config_files = main_repo.get('config_files', [])
            for config_file in config_files:
                file_path = os.path.join(repo_path, config_file)
                content = self._read_file_content(file_path, max_lines=100)
                
                if content:
                    content_lower = content.lower()
                    
                    # Detect logging configuration
                    if any(log in content_lower for log in ['logging', 'logback', 'log4j', 'slf4j']):
                        config_analysis["logging_config"] = True
                    
                    # Detect security configuration
                    if any(sec in content_lower for sec in ['security', 'authentication', 'authorization', 'oauth']):
                        config_analysis["security_config"] = True
                    
                    # Detect database configuration
                    if any(db in content_lower for db in ['datasource', 'jpa', 'hibernate', 'database']):
                        config_analysis["database_config"] = True
                    
                    # Detect monitoring configuration
                    if any(mon in content_lower for mon in ['actuator', 'management', 'endpoints', 'health']):
                        config_analysis["monitoring_config"] = True
                    
                    # Detect error handling configuration
                    if any(err in content_lower for err in ['error', 'exception', 'handling']):
                        config_analysis["error_handling_config"] = True
                    
                    # Detect timeout configuration
                    if any(timeout in content_lower for timeout in ['timeout', 'connection-timeout', 'read-timeout']):
                        config_analysis["timeout_config"] = True
                    
                    # Detect retry configuration
                    if any(retry in content_lower for retry in ['retry', 'retryable', 'backoff']):
                        config_analysis["retry_config"] = True
                    
                    # Detect throttling configuration
                    if any(throttle in content_lower for throttle in ['throttle', 'rate-limit', 'throttling']):
                        config_analysis["throttling_config"] = True
                    
                    # Detect circuit breaker configuration
                    if any(cb in content_lower for cb in ['circuit-breaker', 'resilience4j', 'hystrix']):
                        config_analysis["circuit_breaker_config"] = True
                    
                    # Detect health check configuration
                    if any(health in content_lower for health in ['health', 'liveness', 'readiness']):
                        config_analysis["health_check_config"] = True
            
            return config_analysis
            
        except Exception as e:
            print(f"⚠️ Error analyzing configuration files: {e}")
            return {}
    
    def _calculate_auditability_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for auditability gates"""
        expected_counts = {}
        
        # Gate 1.1: Logs Searchable/Available
        logging_count = 0
        if dependencies.get("logging_frameworks"):
            logging_count += len(dependencies["logging_frameworks"])
        if config.get("logging_config"):
            logging_count += 1
        if structure.get("java_files", 0) > 0:
            logging_count += max(1, structure["java_files"] // 50)  # At least 1 logger per 50 Java files
        expected_counts["1.1"] = {
            "expected_count": max(1, logging_count),
            "reason": f"Based on {len(dependencies.get('logging_frameworks', []))} logging frameworks, {structure.get('java_files', 0)} Java files, and logging config: {config.get('logging_config', False)}"
        }
        
        # Gate 1.3: Audit Trail
        audit_count = 0
        if structure.get("has_web_layer"):
            audit_count += 1  # Web layer should have audit trails
        if structure.get("has_data_layer"):
            audit_count += 1  # Data layer should have audit trails
        if config.get("security_config"):
            audit_count += 1  # Security config indicates audit needs
        expected_counts["1.3"] = {
            "expected_count": max(1, audit_count),
            "reason": f"Based on web layer: {structure.get('has_web_layer', False)}, data layer: {structure.get('has_data_layer', False)}, security config: {config.get('security_config', False)}"
        }
        
        # Gate 1.5: Implement tracking ID for log messages
        tracking_count = 0
        if structure.get("controller_files", 0) > 0:
            tracking_count += structure["controller_files"]  # Each controller should have tracking
        if structure.get("service_files", 0) > 0:
            tracking_count += max(1, structure["service_files"] // 2)  # Every other service should have tracking
        expected_counts["1.5"] = {
            "expected_count": max(1, tracking_count),
            "reason": f"Based on {structure.get('controller_files', 0)} controllers and {structure.get('service_files', 0)} services"
        }
        
        # Gate 1.6: Log API Calls
        api_logging_count = 0
        if structure.get("controller_files", 0) > 0:
            api_logging_count += structure["controller_files"]  # Each controller should log API calls
        if structure.get("has_web_layer"):
            api_logging_count += 1  # Web layer should have API logging
        expected_counts["1.6"] = {
            "expected_count": max(1, api_logging_count),
            "reason": f"Based on {structure.get('controller_files', 0)} controllers and web layer: {structure.get('has_web_layer', False)}"
        }
        
        # Gate 1.8: Log Application Messages
        app_logging_count = 0
        if structure.get("service_files", 0) > 0:
            app_logging_count += structure["service_files"]  # Each service should log application messages
        if structure.get("util_files", 0) > 0:
            app_logging_count += max(1, structure["util_files"] // 2)  # Every other util should log
        expected_counts["1.8"] = {
            "expected_count": max(1, app_logging_count),
            "reason": f"Based on {structure.get('service_files', 0)} services and {structure.get('util_files', 0)} utility files"
        }
        
        # Gate 1.10: Avoid Logging Sensitive Data
        sensitive_logging_count = 0
        if config.get("security_config"):
            sensitive_logging_count += 1  # Security config indicates sensitive data handling
        if structure.get("has_web_layer"):
            sensitive_logging_count += 1  # Web layer handles sensitive data
        if structure.get("has_data_layer"):
            sensitive_logging_count += 1  # Data layer handles sensitive data
        expected_counts["1.10"] = {
            "expected_count": max(1, sensitive_logging_count),
            "reason": f"Based on security config: {config.get('security_config', False)}, web layer: {structure.get('has_web_layer', False)}, data layer: {structure.get('has_data_layer', False)}"
        }
        
        return expected_counts
    
    def _calculate_error_handling_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for error handling gates"""
        expected_counts = {}
        
        # Gate 2.4: Include Client error tracking
        client_error_count = 0
        if structure.get("controller_files", 0) > 0:
            client_error_count += structure["controller_files"]  # Each controller should handle client errors
        if structure.get("has_web_layer"):
            client_error_count += 1  # Web layer should have client error handling
        expected_counts["2.4"] = {
            "expected_count": max(1, client_error_count),
            "reason": f"Based on {structure.get('controller_files', 0)} controllers and web layer: {structure.get('has_web_layer', False)}"
        }
        
        # Gate 2.7: UI Error Handling
        ui_error_count = 0
        if structure.get("controller_files", 0) > 0:
            ui_error_count += structure["controller_files"]  # Each controller should handle UI errors
        if structure.get("has_web_layer"):
            ui_error_count += 1  # Web layer should have UI error handling
        expected_counts["2.7"] = {
            "expected_count": max(1, ui_error_count),
            "reason": f"Based on {structure.get('controller_files', 0)} controllers and web layer: {structure.get('has_web_layer', False)}"
        }
        
        return expected_counts
    
    def _calculate_availability_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for availability gates"""
        expected_counts = {}
        
        # Gate 1.12: Retry Logic
        retry_count = 0
        if config.get("retry_config"):
            retry_count += 1  # Retry configuration indicates retry logic
        if structure.get("service_files", 0) > 0:
            retry_count += max(1, structure["service_files"] // 3)  # Every third service should have retry logic
        if dependencies.get("database_frameworks"):
            retry_count += 1  # Database operations should have retry logic
        expected_counts["1.12"] = {
            "expected_count": max(1, retry_count),
            "reason": f"Based on retry config: {config.get('retry_config', False)}, {structure.get('service_files', 0)} services, and database frameworks: {dependencies.get('database_frameworks', [])}"
        }
        
        # Gate 3.6: Throttling, drop request
        throttling_count = 0
        if config.get("throttling_config"):
            throttling_count += 1  # Throttling configuration indicates throttling logic
        if structure.get("controller_files", 0) > 0:
            throttling_count += max(1, structure["controller_files"] // 2)  # Every other controller should have throttling
        expected_counts["3.6"] = {
            "expected_count": max(1, throttling_count),
            "reason": f"Based on throttling config: {config.get('throttling_config', False)} and {structure.get('controller_files', 0)} controllers"
        }
        
        # Gate 3.9: Circuit Breaker
        circuit_breaker_count = 0
        if config.get("circuit_breaker_config"):
            circuit_breaker_count += 1  # Circuit breaker configuration indicates circuit breaker logic
        if structure.get("service_files", 0) > 0:
            circuit_breaker_count += max(1, structure["service_files"] // 4)  # Every fourth service should have circuit breaker
        expected_counts["3.9"] = {
            "expected_count": max(1, circuit_breaker_count),
            "reason": f"Based on circuit breaker config: {config.get('circuit_breaker_config', False)} and {structure.get('service_files', 0)} services"
        }
        
        # Gate 3.18: Health Checks
        health_check_count = 0
        if config.get("health_check_config"):
            health_check_count += 1  # Health check configuration indicates health checks
        if dependencies.get("monitoring_frameworks"):
            health_check_count += len(dependencies["monitoring_frameworks"])  # Each monitoring framework should have health checks
        if structure.get("has_web_layer"):
            health_check_count += 1  # Web layer should have health checks
        expected_counts["3.18"] = {
            "expected_count": max(1, health_check_count),
            "reason": f"Based on health check config: {config.get('health_check_config', False)}, monitoring frameworks: {dependencies.get('monitoring_frameworks', [])}, and web layer: {structure.get('has_web_layer', False)}"
        }
        
        return expected_counts
    
    def _calculate_testing_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for testing gates"""
        expected_counts = {}
        
        # Gate 2: Testing (general)
        testing_count = 0
        if structure.get("test_files", 0) > 0:
            testing_count += structure["test_files"]  # Each test file indicates testing
        if dependencies.get("testing_frameworks"):
            testing_count += len(dependencies["testing_frameworks"])  # Each testing framework indicates testing
        if structure.get("java_files", 0) > 0:
            testing_count += max(1, structure["java_files"] // 10)  # At least 1 test per 10 Java files
        expected_counts["2"] = {
            "expected_count": max(1, testing_count),
            "reason": f"Based on {structure.get('test_files', 0)} test files, testing frameworks: {dependencies.get('testing_frameworks', [])}, and {structure.get('java_files', 0)} Java files"
        }
        
        return expected_counts
    
    def _calculate_security_expected_counts(self, structure: Dict[str, Any], dependencies: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate expected counts for security gates"""
        expected_counts = {}
        
        # Security gates would be calculated here based on security frameworks and configurations
        # For now, return empty dict as security gates are not in the main scope
        
        return expected_counts
