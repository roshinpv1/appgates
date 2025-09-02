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
            "git_token": context.git_token,
            "scan_id": context.scan_id
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute repository checkout including CD repository"""
        try:
            print("📥 Step 1: Repository Checkout and extract metadata (including CD repos)")
            
            repo_url = prep_res["repo_url"]
            branch = prep_res["branch"]
            git_token = prep_res["git_token"]
            scan_id = prep_res["scan_id"]
            
            # Create common folder structure based on scan_id and repo hash
            common_folder = self._create_common_folder_structure(scan_id, repo_url)
            print(f"📁 Created common folder structure: {common_folder}")
            
            # Clone main repository into common folder
            main_repo_name = self._extract_repo_name(repo_url)
            main_repo_path = os.path.join(common_folder, main_repo_name)
            
            main_repo_path = await self.git_utils.clone_repository_to_path(
                repo_url, branch, git_token, main_repo_path
            )
            
            # Extract main repository information
            main_repo_info = await self.git_utils.get_repository_info(main_repo_path)
            
            # Clone CD repository into common folder
            cd_repo_path = None
            cd_repo_info = None
            
            cd_repo_url = self._get_cd_repo_url(repo_url)
            cd_repo_name = self._extract_repo_name(cd_repo_url)
            cd_repo_path = os.path.join(common_folder, cd_repo_name)
            
            print(f"🔍 Attempting to clone CD repository: {cd_repo_url}")
            
            try:
                cd_repo_path = await self.git_utils.clone_repository_to_path(
                    cd_repo_url, branch, git_token, cd_repo_path
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
            self.context.common_folder = common_folder
            self.context.metadata = {
                "main_repo": main_repo_info.__dict__,
                "cd_repo": cd_repo_info.__dict__ if cd_repo_info else None,
                "has_cd_repo": cd_repo_info is not None,
                "common_folder": common_folder,
                "scan_id": scan_id
            }
            
            print(f"✅ Main repository checked out: {main_repo_path}")
            print(f"📊 Main repository info: {main_repo_info.total_files} files, {main_repo_info.total_lines} lines")
            print(f"📁 Common folder: {common_folder}")
            
            if cd_repo_info:
                print(f"🔄 CD repository included in analysis")
            
            return "success"
            
        except Exception as e:
            print(f"❌ Repository checkout failed: {e}")
            return "error"
    
    def _create_common_folder_structure(self, scan_id: str, repo_url: str) -> str:
        """Create common folder structure based on scan_id and repo hash"""
        import hashlib
        import tempfile
        from pathlib import Path
        
        # Generate repo hash from URL
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]
        
        # Create folder name: scan_{scan_id}_repo_{repo_hash}
        folder_name = f"scan_{scan_id}_repo_{repo_hash}"
        
        # Create path in temp directory
        temp_dir = Path(tempfile.gettempdir()) / "codegates_scan"
        temp_dir.mkdir(exist_ok=True)
        
        common_folder = temp_dir / folder_name
        common_folder.mkdir(exist_ok=True)
        
        return str(common_folder)
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL"""
        # Remove .git suffix if present
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        return repo_name
    
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
            context.common_folder = self.context.common_folder
            context.metadata = self.context.metadata
        return exec_res


class ProjectAnalysisNode(AsyncNode):
    """Step 2: Project Analysis (main + cd) to produce optimized structure JSON and LLM-ranked critical files"""
    
    def __init__(self, llm_service):
        super().__init__()
        self.llm_service = llm_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        return {
            "repo_path": context.repo_path,
            "cd_repo_path": context.cd_repo_path,
            "metadata": context.metadata,
            "scan_id": context.scan_id
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        try:
            print("🔎 Step 2: Project Analysis (structure + critical files)")
            repo_path = prep_res["repo_path"]
            cd_repo_path = prep_res.get("cd_repo_path")
            scan_id = prep_res.get("scan_id", "unknown")
            
            # Deterministic project structure (compact JSON) for main and cd
            main_summary = self._summarize_repository(repo_path)
            cd_summary = self._summarize_repository(cd_repo_path) if cd_repo_path else None

            # Build compact directory trees to avoid repeating path prefixes
            main_tree = self._build_directory_tree(repo_path)
            cd_tree = self._build_directory_tree(cd_repo_path) if cd_repo_path else None

            project_analysis = {
                "main": {"summary": main_summary, "tree": main_tree},
                "cd": {"summary": cd_summary, "tree": cd_tree} if cd_repo_path else None
            }

            # Ask LLM to identify critical files per gate, and configs/build/properties from structure only
            critical_files = await self._identify_critical_files_from_structure(project_analysis, scan_id)
            
            self.context.project_analysis = project_analysis
            self.context.critical_files = critical_files
            
            # Also reflect minimal pointers in metadata
            if isinstance(self.context.metadata, dict):
                self.context.metadata.setdefault("analysis", {})
                self.context.metadata["analysis"]["project_analysis_available"] = True
                self.context.metadata["analysis"]["critical_files_counts"] = {
                    k: {kk: len(vv) for kk, vv in (critical_files.get(k, {}) or {}).items()}
                    for k in ["main", "cd"] if critical_files.get(k)
                }
            
            print("✅ Project analysis completed")
            return "success"
        except Exception as e:
            print(f"❌ Project analysis failed: {e}")
            return "error"
    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        if exec_res == "success":
            context.project_analysis = self.context.project_analysis
            context.critical_files = self.context.critical_files
        return exec_res
    
    def _summarize_repository(self, repo_path: Optional[str]) -> Optional[Dict[str, Any]]:
        if not repo_path:
            return None
        summary: Dict[str, Any] = {
            "summary": {
                "languages": [],
                "file_types": {},
                "frameworks": [],
                "layers": {"web": False, "service": False, "data": False}
            },
            "structure": {
                "modules": [],
                "top_packages": []
            }
        }
        try:
            repo = Path(repo_path)
            file_types: Dict[str, int] = {}
            top_packages: Dict[str, int] = {}
            modules: List[Dict[str, Any]] = []
            seen_modules: set = set()
            
            from utils.file_filter import DEFAULT_FILE_FILTER
            for fp in DEFAULT_FILE_FILTER.iter_files(repo):
                ext = fp.suffix.lower().lstrip('.') or "_"
                file_types[ext] = file_types.get(ext, 0) + 1
                rel = str(fp.relative_to(repo))
                low = rel.lower()
                # layers
                if any(x in low for x in ["controller", "web", "rest"]):
                    summary["summary"]["layers"]["web"] = True
                if any(x in low for x in ["service", "business"]):
                    summary["summary"]["layers"]["service"] = True
                if any(x in low for x in ["repository", "dao", "jpa", "data/"]):
                    summary["summary"]["layers"]["data"] = True
                # top packages (java)
                parts = low.split('/')
                if len(parts) > 2:
                    pkg_key = '.'.join(parts[:3])
                    top_packages[pkg_key] = top_packages.get(pkg_key, 0) + 1
                # modules by top dir with src
                if len(parts) > 0:
                    mod = parts[0]
                    if mod not in seen_modules and (repo / mod / 'src').exists():
                        seen_modules.add(mod)
                        modules.append({"name": mod, "path": str((repo/mod).resolve())})
            
            # frameworks detection by files
            frameworks: List[str] = []
            if (repo / 'pom.xml').exists() or (repo / 'build.gradle').exists():
                frameworks.append('maven' if (repo / 'pom.xml').exists() else 'gradle')
            if any((repo / p).exists() for p in ['package.json']):
                frameworks.append('node')
            if any((repo / p).exists() for p in ['requirements.txt', 'pyproject.toml', 'setup.py']):
                frameworks.append('python')
            if (repo / 'Dockerfile').exists() or any('docker' in str(p).lower() for p in repo.rglob('docker*')):
                frameworks.append('docker')
            if any('k8s' in str(p).lower() or 'kubernetes' in str(p).lower() for p in repo.rglob('*')):
                frameworks.append('kubernetes')
            
            summary["summary"]["file_types"] = file_types
            # languages map
            ext_to_lang = {
                'py':'python','js':'javascript','ts':'typescript','java':'java','cs':'csharp','go':'go','rs':'rust','cpp':'cpp','c':'c','h':'c','hpp':'cpp','xml':'xml','yml':'yaml','yaml':'yaml','json':'json'
            }
            langs = set(ext_to_lang.get(k, None) for k in file_types.keys())
            summary["summary"]["languages"] = sorted([l for l in langs if l])
            summary["summary"]["frameworks"] = sorted(list(set(frameworks)))
            summary["structure"]["modules"] = modules
            summary["structure"]["top_packages"] = sorted([{ "name": k, "files": v } for k, v in top_packages.items()], key=lambda x: x["files"], reverse=True)[:15]
            return summary
        except Exception as e:
            print(f"⚠️ Failed summarizing repository {repo_path}: {e}")
            return summary
    
    def _list_repo_files(self, repo_path: Optional[str]) -> List[str]:
        if not repo_path:
            return []
        repo = Path(repo_path)
        files: List[str] = []
        try:
            from utils.file_filter import DEFAULT_FILE_FILTER
            for fp in DEFAULT_FILE_FILTER.iter_files(repo):
                files.append(str(fp.relative_to(repo)))
            # cap at a safe upper bound to keep prompt size reasonable
            return files[:5000]
        except Exception as e:
            print(f"⚠️ Failed listing repo files: {e}")
            return files

    def _build_directory_tree(self, repo_path: Optional[str]) -> Optional[Dict[str, Any]]:
        """Build a compact JSON directory tree to eliminate repeated prefixes.
        Shape (token-optimized): nested object where directories map to objects and files map to 1.
        Example: {"src": {"main": {"java": {"App.java": 1}}}, "README.md": 1}
        Only includes files that pass FileFilter.
        """
        if not repo_path:
            return None
        from utils.file_filter import DEFAULT_FILE_FILTER
        from pathlib import Path
        root = Path(repo_path)
        try:
            # Build a trie-like structure with minimal tokens
            tree: Dict[str, Any] = {}

            def insert(path: Path):
                rel = path.relative_to(root)
                parts = list(rel.parts)
                node = tree
                for i, part in enumerate(parts):
                    is_last = (i == len(parts) - 1)
                    if is_last:
                        node[part] = 1  # mark file
                    else:
                        if part not in node or not isinstance(node.get(part), dict):
                            node[part] = {}
                        node = node[part]

            for fp in DEFAULT_FILE_FILTER.iter_files(root):
                insert(fp)

            return tree
        except Exception as e:
            print(f"⚠️ Failed building directory tree: {e}")
            return None

    def _map_category_files_to_gates(self, repo_path: Optional[str], category_selection: Dict[str, List[str]]) -> Dict[str, Any]:
        """Map category-selected files to gate IDs using pattern library and gate registry."""
        result = {"gates": {}}
        if not repo_path:
            return result
        try:
            from models.gate_definitions import gate_registry
            from services.pattern_library_service import PatternLibraryService
            import re
            repo = Path(repo_path)
            pls = PatternLibraryService()
            # Build an index of all repo file paths for regex matching
            all_files = [str(p.relative_to(repo)) for p in repo.rglob('*') if p.is_file()]
            # Helper to extract file-pattern regexes from pattern library
            def file_regexes_for_gate(gid: str) -> List[str]:
                try:
                    gate_config = pls.get_gate_patterns(gid)
                    if not gate_config:
                        return []
                    criteria = gate_config.get("criteria", {})
                    patterns = []
                    for cond in criteria.get("conditions", []):
                        if cond.get("type") == "file_pattern":
                            for pc in cond.get("file_patterns", []):
                                pat = pc.get("pattern")
                                if isinstance(pat, str) and pat:
                                    patterns.append(pat)
                    return patterns
                except Exception:
                    return []
            # Convert category name
            def cat_key(g):
                c = g.category.value.lower() if hasattr(g, 'category') else str(g.category).lower()
                if "audit" in c: return "auditability"
                if "availability" in c: return "availability"
                if "test" in c: return "testing"
                if "security" in c: return "security"
                if "error" in c: return "auditability"  # map error handling to auditability bucket if needed
                return "auditability"
            for g in gate_registry.get_hard_gates():
                gid = g.gate_id
                bucket = category_selection.get(cat_key(g), [])
                picked: List[str] = []
                # 1) Use file pattern regexes
                regexes = file_regexes_for_gate(gid)
                for r in regexes[:10]:  # limit regex volume
                    try:
                        cre = re.compile(r, re.IGNORECASE)
                        for path in all_files:
                            if cre.search(path):
                                picked.append(path)
                    except re.error:
                        continue
                # 2) Add from category bucket
                picked.extend(bucket)
                # Deduplicate, limit
                seen = set()
                deduped = []
                for p in picked:
                    if p not in seen:
                        deduped.append(p)
                        seen.add(p)
                result["gates"][gid] = deduped[:30]
            return result
        except Exception as e:
            print(f"⚠️ Gate mapping failed: {e}")
            return result
    
    async def _identify_critical_files_from_structure(self, project_analysis: Dict[str, Any], scan_id: str) -> Dict[str, Any]:
        try:
            import json
            # Provide gate definitions (number | category | name | summary) and canonical gate IDs
            try:
                from models.gate_definitions import gate_registry
                available_gates_text = gate_registry.get_gates_for_llm_analysis()
                gate_ids = gate_registry.get_hard_gate_ids()
            except Exception:
                available_gates_text = ""
                gate_ids = []
            # Build instruction (shared across chunks)
            instruction = (
                "Given the repository structure (summary + directory tree), identify: \n"
                "1) critical files for each hard gate (keys are gate IDs as in the gate registry), \n"
                "2) overall project category files under: Build, Config, Properties, Infrastructure, Deployment. \n"
                "\nAVAILABLE GATES (number | category | name | summary):\n"
                f"{available_gates_text}\n\n"
                "Use ONLY these gate IDs as keys when returning results (do not invent):\n"
                f"{json.dumps(gate_ids)}\n\n"
                "Classification rules (use only provided file paths, no invention):\n"
                "- Build: Dockerfile, docker-compose*.yml|yaml, helm/**, k8s/**, pom.xml, build.gradle, gradle/**, .mvn/**\n"
                "- Config: *.yml, *.yaml, *.json, *.conf, *.ini, *.properties\n"
                "- Properties: *.properties, *.conf, *.ini\n"
                "- Infrastructure: terraform/**, infra/**, k8s/**, helm/**, cloudformation/**\n"
                "- Deployment: .github/workflows/**, pipeline/**, Jenkinsfile, .gitlab-ci.yml, ArgoCD/**\n"
                "- Deduplicate paths. Allow at least 20 items per list; cap at 100 if needed.\n"
                "- If a section has no items, return an empty array.\n"
                "- Always include both 'main' and 'cd'. If 'cd' is null in input, still return empty arrays for 'cd'.\n\n"
                "The input provides a compact JSON directory tree under each repo as 'tree' where directories map to objects and files map to 1 (no repeated prefixes). Reconstruct full relative paths when returning results.\n\n"
                "Return STRICT JSON only with this exact shape: {\n"
                "  \"main\": { \"gates\": { \"<gate_id>\": [\"path\", ...] }, \"categories\": {\n"
                "    \"Build\": [...], \"Config\": [...], \"Properties\": [...], \"Infrastructure\": [...], \"Deployment\": [...]\n"
                "  } },\n"
                "  \"cd\":   { \"gates\": { \"<gate_id>\": [\"path\", ...] }, \"categories\": {\n"
                "    \"Build\": [...], \"Config\": [...], \"Properties\": [...], \"Infrastructure\": [...], \"Deployment\": [...]\n"
                "  } }\n"
                "}\n\n"
            )

            # Helper: chunk trees by top-level directories to keep payload size under ~40k chars
            def build_chunks() -> list:
                chunks = []
                main_obj = project_analysis.get("main") or {}
                cd_obj = project_analysis.get("cd") or {}
                main_summary = main_obj.get("summary")
                cd_summary = cd_obj.get("summary")
                main_tree = main_obj.get("tree") or {}
                cd_tree = cd_obj.get("tree") or {}

                def pack_side(side_name: str, summary: dict, tree: dict) -> list:
                    keys = list(tree.keys())
                    if not keys:
                        payload = {"project": {"main": main_obj, "cd": cd_obj}}
                        return [payload]
                    batches = []
                    current = []
                    for k in sorted(keys):
                        current.append(k)
                        partial_tree = {kk: tree[kk] for kk in current}
                        tmp = {"project": {"main": {}, "cd": {}}}
                        tmp["project"][side_name] = {"summary": summary, "tree": partial_tree}
                        other = "cd" if side_name == "main" else "main"
                        tmp["project"][other] = {"summary": (cd_summary if side_name == "main" else main_summary), "tree": {}}
                        if len(json.dumps(tmp)) > 12000 and len(current) > 1:
                            last = current.pop()
                            batches.append(list(current))
                            current = [last]
                    if current:
                        batches.append(list(current))
                    res = []
                    for batch in batches:
                        partial_tree = {kk: tree[kk] for kk in batch}
                        payload = {"project": {"main": {}, "cd": {}}}
                        payload["project"][side_name] = {"summary": summary, "tree": partial_tree}
                        other = "cd" if side_name == "main" else "main"
                        payload["project"][other] = {"summary": (cd_summary if side_name == "main" else main_summary), "tree": {}}
                        res.append(payload)
                    return res

                chunks.extend(pack_side("main", main_summary, main_tree))
                if cd_obj:
                    chunks.extend(pack_side("cd", cd_summary, cd_tree))
                return chunks

            # Helper: merge results with dedupe
            def merge_results(target: dict, piece: dict):
                for side in ["main", "cd"]:
                    side_obj = piece.get(side) or {}
                    if side not in target:
                        target[side] = {"gates": {}, "categories": {}}
                    # gates
                    for gid, arr in (side_obj.get("gates") or {}).items():
                        target[side]["gates"].setdefault(gid, [])
                        seen = set(target[side]["gates"][gid])
                        for p in arr or []:
                            if p not in seen:
                                target[side]["gates"][gid].append(p)
                                seen.add(p)
                    # categories
                    for cname, arr in (side_obj.get("categories") or {}).items():
                        target[side]["categories"].setdefault(cname, [])
                        seen = set(target[side]["categories"][cname])
                        for p in arr or []:
                            if p not in seen:
                                target[side]["categories"][cname].append(p)
                                seen.add(p)

            combined = {"main": {"gates": {}, "categories": {}}, "cd": {"gates": {}, "categories": {}}}

            # Run chunked calls
            for idx, payload in enumerate(build_chunks()):
                base_prompt = instruction + f"INPUT:\n{json.dumps(payload)}"
                # first attempt (low temperature)
                resp = await self.llm_service.generate(
                    base_prompt,
                    scan_id=scan_id,
                    node_name="ProjectAnalysisNode",
                    metadata={"type": "critical_files_from_structure", "chunk_index": idx},
                    temperature=0.1,
                    timeout=300,
                    max_tokens=2000
                )
                parsed_ok = False
                for attempt in range(2):
                    try:
                        piece = json.loads(self._extract_json(resp))
                        # normalize minimal structure
                        for side in ["main", "cd"]:
                            if side in piece and isinstance(piece[side], dict):
                                piece[side].setdefault("gates", {})
                                piece[side].setdefault("categories", {})
                        merge_results(combined, piece)
                        parsed_ok = True
                        break
                    except Exception as e:
                        if attempt == 0:
                            # retry once with explicit JSON-only reminder
                            retry_prompt = base_prompt + "\n\nSTRICT: Respond with ONLY a single JSON object. Do not include code fences or any extra text."
                            resp = await self.llm_service.generate(
                                retry_prompt,
                                scan_id=scan_id,
                                node_name="ProjectAnalysisNode",
                                metadata={"type": "critical_files_from_structure", "chunk_index": idx, "retry": True},
                                temperature=0.0,
                                timeout=300,
                                max_tokens=2000
                            )
                            continue
                        else:
                            print(f"⚠️ Parsing critical chunk {idx} failed after retry: {e}")
                if not parsed_ok:
                    continue

            # Enforce caps
            for side in ["main", "cd"]:
                for gid, arr in list(combined[side]["gates"].items()):
                    combined[side]["gates"][gid] = (arr or [])[:100]
                for cname, arr in list(combined[side]["categories"].items()):
                    combined[side]["categories"][cname] = (arr or [])[:100]

            return combined
        except Exception as e:
            print(f"⚠️ LLM identify critical files failed: {e}")
            return {"main": {"gates": {}, "categories": {}}, "cd": {"gates": {}, "categories": {}}}
    
    def _extract_json(self, text: str) -> str:
        import re
        if not text:
            return text
        s = text.strip()
        # strip markdown code fences if present
        if s.startswith("```"):
            s = re.sub(r"^```[a-zA-Z0-9]*\n", "", s)
            s = re.sub(r"\n```$", "", s)
        # find first JSON object
        m = re.search(r"\{[\s\S]*\}$", s)
        if m:
            return m.group(0)
        # fallback: try to locate first '{' and last '}'
        start = s.find('{')
        end = s.rfind('}')
        if start != -1 and end != -1 and end > start:
            return s[start:end+1]
        return s

class VectorizationNode(AsyncNode):
    """Step 2: CocoIndex Vectorization & Storage"""
    
    def __init__(self, cocoindex_service):
        super().__init__()
        self.cocoindex_service = cocoindex_service
    
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
        """Execute CocoIndex vectorization step"""
        try:
            repo_path = prep_res["repo_path"]
            cd_repo_path = prep_res.get("cd_repo_path")
            scan_id = prep_res["scan_id"]
            repo_url = prep_res["repo_url"]
            branch = prep_res["branch"]
            commit_hash = prep_res["commit_hash"]
            
            print(f"🔍 Starting CocoIndex vectorization for scan: {scan_id}")
            print(f"📁 Main repo: {repo_path}")
            if cd_repo_path:
                print(f"📁 CD repo: {cd_repo_path}")
            
            # Index main repository using CocoIndex
            print(f"🔍 Indexing main repository with CocoIndex...")
            try:
                main_result = await self.cocoindex_service.index_repository(
                    repo_path=repo_path,
                    scan_id=scan_id,
                    repo_type="main"
                )
                
                if not main_result["indexing_successful"]:
                    print(f"❌ Main repository indexing failed: {main_result.get('error', 'Unknown error')}")
                    # Continue without vector data instead of failing completely
                    main_result = None
            except Exception as e:
                print(f"❌ Main repository indexing failed with exception: {e}")
                main_result = None
            
            # Index CD repository if it exists
            cd_result = None
            if cd_repo_path:
                print(f"🔍 Indexing CD repository with CocoIndex...")
                try:
                    cd_result = await self.cocoindex_service.index_repository(
                        repo_path=cd_repo_path,
                        scan_id=scan_id,
                        repo_type="cd"
                    )
                    
                    if not cd_result["indexing_successful"]:
                        print(f"⚠️ CD repository indexing failed: {cd_result.get('error', 'Unknown error')}")
                        # Continue with main repository only
                        cd_result = None
                except Exception as e:
                    print(f"⚠️ CD repository indexing failed with exception: {e}")
                    cd_result = None
            
            # Store vector data in context
            if hasattr(self, 'context') and self.context is not None:
                if main_result:
                    self.context.vector_data = {
                        "scan_id": scan_id,
                        "main_collection_name": main_result["collection_name"],
                        "cd_collection_name": cd_result["collection_name"] if cd_result else None,
                        "main_chunks_count": main_result["chunks_count"],
                        "cd_chunks_count": cd_result["chunks_count"] if cd_result else 0,
                        "total_chunks": main_result["chunks_count"] + (cd_result["chunks_count"] if cd_result else 0),
                        "repo_hash": commit_hash,
                        "cocoindex_used": True
                    }
                    
                    print(f"✅ CocoIndex vectorization completed successfully")
                    print(f"📊 Main repository chunks: {main_result['chunks_count']}")
                    if cd_result:
                        print(f"📊 CD repository chunks: {cd_result['chunks_count']}")
                    print(f"📊 Total chunks: {main_result['chunks_count'] + (cd_result['chunks_count'] if cd_result else 0)}")
                else:
                    # No vector data available
                    self.context.vector_data = None
                    print(f"⚠️ CocoIndex vectorization failed, continuing without vector data")
            
            return "success"
            
        except Exception as e:
            print(f"❌ CocoIndex vectorization failed: {e}")
            import traceback
            traceback.print_exc()
            return "error"
    

    
    async def post_async(self, context: ScanContext, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Post-vectorization processing"""
        if exec_res == "success":
            context.vector_data = self.context.vector_data
        return exec_res


class LLMPreAnalysisNode(AsyncNode):
    """Step 3: LLM Pre-Analysis using critical files (applicability + expected counts + dynamic patterns)"""
    
    def __init__(self, llm_service):
        super().__init__()
        self.llm_service = llm_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        return {
            "critical_files": context.critical_files,
            "repo_path": context.repo_path,
            "cd_repo_path": context.cd_repo_path,
            "metadata": context.metadata,
            "scan_id": context.scan_id
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        try:
            import time
            import json
            start_time = time.time()
            print("🤖 Step 3: LLM Pre-Analysis (critical files)")
            
            critical_files = prep_res.get("critical_files") or {}
            repo_path = prep_res.get("repo_path")
            cd_repo_path = prep_res.get("cd_repo_path")
            scan_id = prep_res.get("scan_id")
            metadata = prep_res.get("metadata") or {}
            
            # Prefer gate-mapped files if present
            main_gate_files = ((critical_files.get("main") or {}).get("gates") or {})
            cd_gate_files = ((critical_files.get("cd") or {}).get("gates") or {})
            # Fallback: categories
            main_cats = ((critical_files.get("main") or {}).get("categories") or {})
            cd_cats = ((critical_files.get("cd") or {}).get("categories") or {})
            
            # Read contents of critical files with truncation
            file_blobs = self._read_critical_files(repo_path, cd_repo_path, {
                "gates": {"main": main_gate_files, "cd": cd_gate_files},
                "categories": {"main": main_cats, "cd": cd_cats}
            })
            
            # Chunk into multiple LLM calls with overlap
            chunks = self._chunk_blobs(file_blobs, max_chars=12000, overlap_chars=1000)
            
            # Aggregate results
            aggregated_expected: Dict[str, Any] = {}
            aggregated_actual: Dict[str, Any] = {}
            aggregated_patterns: List[Dict[str, Any]] = []
            aggregated_insights: Dict[str, Any] = {"project_type": None, "functional_summary": "", "frameworks": [], "libraries": []}
            
            for idx, chunk in enumerate(chunks):
                prompt = self._build_preanalysis_prompt(chunk, metadata)
                resp = await self.llm_service.generate(
                prompt,
                    scan_id=scan_id,
                node_name="LLMPreAnalysisNode",
                    metadata={"chunk_index": idx, "total_chunks": len(chunks)}
                )
                parsed = self._parse_llm_preanalysis_response(resp)
                # merge expected counts
                for gid, obj in parsed.get("expected_counts", {}).items():
                    if gid not in aggregated_expected:
                        aggregated_expected[gid] = obj
                # merge actual counts
                for gid, obj in parsed.get("actual_counts", {}).items():
                    if gid not in aggregated_actual:
                        aggregated_actual[gid] = obj
                # dynamic patterns not needed; ignore
                # merge insights
                insights = parsed.get("insights") or {}
                if insights:
                    if not aggregated_insights.get("project_type") and insights.get("project_type"):
                        aggregated_insights["project_type"] = insights.get("project_type")
                    if insights.get("functional_summary"):
                        # keep the longest summary
                        cur = aggregated_insights.get("functional_summary") or ""
                        cand = insights.get("functional_summary") or ""
                        if len(cand) > len(cur):
                            aggregated_insights["functional_summary"] = cand
                    if isinstance(insights.get("frameworks"), list):
                        seen = set(aggregated_insights.get("frameworks") or [])
                        for x in insights.get("frameworks"):
                            if x not in seen:
                                aggregated_insights.setdefault("frameworks", []).append(x)
                                seen.add(x)
                    if isinstance(insights.get("libraries"), list):
                        seen = set(aggregated_insights.get("libraries") or [])
                        for x in insights.get("libraries"):
                            if x not in seen:
                                aggregated_insights.setdefault("libraries", []).append(x)
            
            # Store in context
            self.context.llm_expected_counts = aggregated_expected
            self.context.llm_actual_counts = aggregated_actual
            # Do not include dynamic patterns; keep only static placeholder for compatibility
            self.context.patterns = {"static": []}
            self.context.pre_analysis_insights = aggregated_insights
            
            print(f"✅ Pre-analysis completed: gates={len(aggregated_expected)}, patterns={len(aggregated_patterns)}")
            return "success"
        except Exception as e:
            print(f"❌ LLM pre-analysis failed: {e}")
            return "error"
    
    def _read_critical_files(self, repo_path: Optional[str], cd_repo_path: Optional[str], critical: Dict[str, Any]) -> List[Dict[str, str]]:
        blobs: List[Dict[str, str]] = []
        try:
            def read_paths(base: Optional[str], paths: List[str], side: str, tag: str):
                if not base or not paths:
                    return
                root = Path(base)
                for rel in paths:
                    p = root / rel
                    try:
                        if p.exists() and p.is_file():
                            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                                text = f.read()
                            blobs.append({
                                "repo": side,
                                "category": tag,
                                "path": rel,
                                "content": self._truncate(text, 100000)
                            })
                    except Exception:
                        continue
            # Read gate-specific first
            gates_main: Dict[str, List[str]] = (critical.get("gates") or {}).get("main") or {}
            for gid, files in gates_main.items():
                read_paths(repo_path, files[:100], "main", f"gate:{gid}")
            gates_cd: Dict[str, List[str]] = (critical.get("gates") or {}).get("cd") or {}
            for gid, files in gates_cd.items():
                read_paths(cd_repo_path, files[:100], "cd", f"gate:{gid}")
            # Then categories
            cats_main: Dict[str, List[str]] = (critical.get("categories") or {}).get("main") or {}
            for cat, files in cats_main.items():
                read_paths(repo_path, files[:100], "main", f"cat:{cat}")
            cats_cd: Dict[str, List[str]] = (critical.get("categories") or {}).get("cd") or {}
            for cat, files in cats_cd.items():
                read_paths(cd_repo_path, files[:100], "cd", f"cat:{cat}")
        except Exception as e:
            print(f"⚠️ Failed reading critical files: {e}")
        return blobs
    
    def _truncate(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        head = text[: max_chars // 2]
        tail = text[- max_chars // 2 :]
        return head + "\n\n... [content truncated] ...\n\n" + tail
    
    def _chunk_blobs(self, blobs: List[Dict[str, str]], max_chars: int, overlap_chars: int) -> List[str]:
        serialized: List[str] = []
        for b in blobs:
            serialized.append(f"[{b['repo']}]({b['category']}) {b['path']}\n" + b['content'] + "\n\n====\n\n")
        big = ''.join(serialized)
        chunks: List[str] = []
        i = 0
        while i < len(big):
            chunk = big[i:i+max_chars]
            chunks.append(chunk)
            if i + max_chars >= len(big):
                break
            i += max_chars - overlap_chars
        return chunks
    
    def _build_preanalysis_prompt(self, chunk: str, metadata: Dict[str, Any]) -> str:
        meta_compact = {
            "languages": (metadata.get("languages") if isinstance(metadata, dict) else None),
            "file_types": (metadata.get("file_types") if isinstance(metadata, dict) else None)
        }
        return (
            "Analyze the following selected critical files from a repository.\n"
            "For EACH hard-gate, provide BOTH: \n"
            "- expected_counts: { gate_id -> { applicable, expected_count, reasoning_expected } }\n"
            "- actual_counts: { gate_id -> { actual_count, reasoning_actual } }\n"
            "Additionally, include project insights: insights: { project_type, functional_summary, frameworks:[], libraries:[] }.\n"
            "Strictly return a single JSON object with keys: expected_counts, actual_counts, insights.\n\n"
            f"METADATA:\n{meta_compact}\n\nFILES:\n{chunk}"
        )
    
    def _parse_llm_preanalysis_response(self, text: str) -> Dict[str, Any]:
        import json, re
        try:
            m = re.search(r"\{[\s\S]*\}$", text.strip())
            payload = json.loads(m.group(0) if m else text)
            exp = payload.get("expected_counts") or {}
            act = payload.get("actual_counts") or {}
            ins = payload.get("insights") or {}
            # normalize
            if isinstance(exp, dict):
                for k,v in list(exp.items()):
                    if isinstance(v, dict):
                        v.setdefault("applicable", True)
                        if v.get("expected_count") is None:
                            v["expected_count"] = 1
                        v.setdefault("reasoning_expected", "")
            if isinstance(act, dict):
                for k,v in list(act.items()):
                    if isinstance(v, dict):
                        if v.get("actual_count") is None:
                            v["actual_count"] = 0
                        v.setdefault("reasoning_actual", "")
            # normalize insights
            if isinstance(ins, dict):
                if not isinstance(ins.get("frameworks"), list):
                    ins["frameworks"] = []
                if not isinstance(ins.get("libraries"), list):
                    ins["libraries"] = []
                ins.setdefault("project_type", None)
                ins.setdefault("functional_summary", "")
            return {"expected_counts": exp, "actual_counts": act, "insights": ins}
        except Exception:
            return {"expected_counts": {}, "actual_counts": {}, "insights": {}}
    
    # def _detect_frameworks(self, build_files: List[str], config_files: List[str]) -> List[str]:
        """Detect frameworks based on build and config files"""
        frameworks = []
        
        # Java frameworks
        if any('pom.xml' in f for f in build_files):
            frameworks.append('Maven')
        if any('build.gradle' in f for f in build_files):
            frameworks.append('Gradle')
        if any('spring' in f.lower() for f in build_files + config_files):
            frameworks.append('Spring Framework')
        if any('spring-boot' in f.lower() for f in build_files + config_files):
            frameworks.append('Spring Boot')
        if any('hibernate' in f.lower() for f in build_files + config_files):
            frameworks.append('Hibernate')
        
        # Python frameworks
        if any('requirements.txt' in f for f in build_files):
            frameworks.append('pip')
        if any('setup.py' in f for f in build_files):
            frameworks.append('setuptools')
        if any('django' in f.lower() for f in build_files + config_files):
            frameworks.append('Django')
        if any('flask' in f.lower() for f in build_files + config_files):
            frameworks.append('Flask')
        if any('fastapi' in f.lower() for f in build_files + config_files):
            frameworks.append('FastAPI')
        
        # Node.js frameworks
        if any('package.json' in f for f in build_files):
            frameworks.append('npm')
        if any('express' in f.lower() for f in build_files + config_files):
            frameworks.append('Express.js')
        if any('react' in f.lower() for f in build_files + config_files):
            frameworks.append('React')
        if any('angular' in f.lower() for f in build_files + config_files):
            frameworks.append('Angular')
        
        return list(set(frameworks))
    
    # def _detect_databases(self, build_files: List[str], config_files: List[str]) -> List[str]:
        """Detect database technologies"""
        databases = []
        
        # Check for database indicators
        db_indicators = {
            'mysql': ['mysql', 'mariadb'],
            'postgresql': ['postgresql', 'postgres', 'psql'],
            'mongodb': ['mongodb', 'mongo'],
            'redis': ['redis'],
            'h2': ['h2'],
            'sqlite': ['sqlite'],
            'oracle': ['oracle'],
            'sqlserver': ['sqlserver', 'mssql']
        }
        
        all_files = build_files + config_files
        for db_name, indicators in db_indicators.items():
            if any(indicator in ' '.join(all_files).lower() for indicator in indicators):
                databases.append(db_name.title())
        
        return list(set(databases))
    
    # def _detect_build_tools(self, build_files: List[str]) -> List[str]:
        """Detect build tools"""
        tools = []
        
        if any('pom.xml' in f for f in build_files):
            tools.append('Maven')
        if any('build.gradle' in f for f in build_files):
            tools.append('Gradle')
        if any('package.json' in f for f in build_files):
            tools.append('npm')
        if any('requirements.txt' in f for f in build_files):
            tools.append('pip')
        if any('setup.py' in f for f in build_files):
            tools.append('setuptools')
        if any('dockerfile' in f.lower() for f in build_files):
            tools.append('Docker')
        if any('docker-compose' in f.lower() for f in build_files):
            tools.append('Docker Compose')
        
        return list(set(tools))
    
    # def _detect_deployment_platforms(self, build_files: List[str], config_files: List[str]) -> List[str]:
        """Detect deployment platforms"""
        platforms = []
        
        if any('dockerfile' in f.lower() for f in build_files):
            platforms.append('Docker')
        if any('kubernetes' in f.lower() or 'k8s' in f.lower() for f in build_files + config_files):
            platforms.append('Kubernetes')
        if any('heroku' in f.lower() for f in build_files + config_files):
            platforms.append('Heroku')
        if any('aws' in f.lower() for f in build_files + config_files):
            platforms.append('AWS')
        if any('azure' in f.lower() for f in build_files + config_files):
            platforms.append('Azure')
        if any('gcp' in f.lower() or 'google' in f.lower() for f in build_files + config_files):
            platforms.append('Google Cloud')
        
        return list(set(platforms))
    
    # def _detect_integrations(self, build_files: List[str], config_files: List[str]) -> List[str]:
        """Detect external system integrations"""
        integrations = []
        
        # Message queues
        if any('kafka' in f.lower() for f in build_files + config_files):
            integrations.append('Apache Kafka')
        if any('rabbitmq' in f.lower() for f in build_files + config_files):
            integrations.append('RabbitMQ')
        
        # Monitoring
        if any('prometheus' in f.lower() for f in build_files + config_files):
            integrations.append('Prometheus')
        if any('grafana' in f.lower() for f in build_files + config_files):
            integrations.append('Grafana')
        if any('elk' in f.lower() or 'elasticsearch' in f.lower() for f in build_files + config_files):
            integrations.append('ELK Stack')
        
        # APIs
        if any('rest' in f.lower() for f in build_files + config_files):
            integrations.append('REST APIs')
        if any('graphql' in f.lower() for f in build_files + config_files):
            integrations.append('GraphQL')
        
        return list(set(integrations))
    
    # def _detect_security_frameworks(self, build_files: List[str], config_files: List[str]) -> List[str]:
        """Detect security frameworks"""
        security = []
        
        if any('spring-security' in f.lower() for f in build_files + config_files):
            security.append('Spring Security')
        if any('oauth' in f.lower() for f in build_files + config_files):
            security.append('OAuth')
        if any('jwt' in f.lower() for f in build_files + config_files):
            security.append('JWT')
        if any('ldap' in f.lower() for f in build_files + config_files):
            security.append('LDAP')
        if any('saml' in f.lower() for f in build_files + config_files):
            security.append('SAML')
        
        return list(set(security))
    
    # def _detect_monitoring_tools(self, build_files: List[str], config_files: List[str]) -> List[str]:
        """Detect monitoring and logging tools"""
        monitoring = []
        
        if any('logback' in f.lower() for f in build_files + config_files):
            monitoring.append('Logback')
        if any('log4j' in f.lower() for f in build_files + config_files):
            monitoring.append('Log4j')
        if any('slf4j' in f.lower() for f in build_files + config_files):
            monitoring.append('SLF4J')
        if any('actuator' in f.lower() for f in build_files + config_files):
            monitoring.append('Spring Boot Actuator')
        if any('sentry' in f.lower() for f in build_files + config_files):
            monitoring.append('Sentry')
        
        return list(set(monitoring))
    
    # def _detect_cicd_tools(self, build_files: List[str], config_files: List[str]) -> List[str]:
        """Detect CI/CD tools"""
        cicd = []
        
        if any('jenkins' in f.lower() for f in build_files + config_files):
            cicd.append('Jenkins')
        if any('github-actions' in f.lower() or '.github' in f.lower() for f in build_files + config_files):
            cicd.append('GitHub Actions')
        if any('gitlab-ci' in f.lower() for f in build_files + config_files):
            cicd.append('GitLab CI')
        if any('azure-pipelines' in f.lower() for f in build_files + config_files):
            cicd.append('Azure Pipelines')
        if any('circleci' in f.lower() for f in build_files + config_files):
            cicd.append('CircleCI')
        
        return list(set(cicd))
    
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
                    content = self._read_file_content(file_path, max_lines=5000)
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
                    content = self._read_file_content(file_path, max_lines=5000)
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
    
    def _read_file_content(self, file_path: str, max_lines: int = 5000) -> str:
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
                if len(content) > 40000:
                    content = content[:40000] + "\n... (content truncated)"
                
                return content
                
        except Exception as e:
            print(f"⚠️ Error reading file {file_path}: {e}")
            return f"Error reading file: {str(e)}"
    
    def _create_pre_analysis_prompt(self, build_configs: str, project_structure: str = None, extracted_code: str = None, available_gates: str = None) -> str:
        """Create prompt for LLM pre-analysis with extracted code snippets"""
        # Use provided components or extract them
        if project_structure is None:
            project_structure = self._get_project_structure_info()
        if extracted_code is None:
            extracted_code = self._extract_relevant_code_snippets()
        if available_gates is None:
            available_gates = self._get_available_gates_summary()
        
        # Create a concise but comprehensive prompt
        prompt = f"""Analyze this project and generate patterns for ALL 16 security gates.

PROJECT STRUCTURE:
{project_structure}

BUILD CONFIGURATIONS:
{build_configs}

CODE SNIPPETS:
{extracted_code}

AVAILABLE GATES:
{available_gates}

ANALYSIS REQUIREMENTS:
1. Project summary (type, functionality, architecture, tech stack)
2. Integration analysis (databases, APIs, auth, monitoring, CI/CD)
3. Framework analysis (web, ORM, testing, security, logging)
4. For each of 16 gates: applicability, reasoning, patterns, expected count with detailed reasoning

Return ONLY valid JSON with this structure:

Return ONLY valid JSON with this exact structure:

{{
  "project_summary": {{
    "project_type": "Type of application (e.g., Spring Boot Web Application)",
    "primary_functionality": "What the application does",
    "architecture_pattern": "MVC, Microservices, etc.",
    "technology_stack": ["Java", "Spring Boot", "Hibernate", "MySQL"]
  }},
  "integration_analysis": {{
    "database_systems": ["MySQL", "Redis"],
    "message_systems": ["Kafka"],
    "external_apis": ["REST APIs", "Payment Gateway"],
    "authentication_systems": ["OAuth2", "JWT"],
    "monitoring_systems": ["ELK Stack"],
    "ci_cd_systems": ["Jenkins"]
  }},
  "framework_analysis": {{
    "web_frameworks": ["Spring Boot"],
    "database_orms": ["Hibernate", "JPA"],
    "testing_frameworks": ["JUnit", "Mockito"],
    "security_libraries": ["Spring Security"],
    "logging_frameworks": ["Logback", "SLF4J"]
  }},
  "patterns": [
    {{
      "gate_id": "1.1",
      "name": "Logs Searchable/Available",
      "description": "Ensure logs are searchable and available for troubleshooting",
      "applicable": true,
      "reason": "Spring Boot web application requires comprehensive logging for monitoring and debugging",
      "pattern": ["logger.(info|debug|warn|error)", "logging.config", "logback.xml"],
      "expected_count": 8,
      "expected_count_reasoning": "Based on 3 controllers, 2 services, 1 repository, 1 configuration class, and 1 utility class that should implement logging. Spring Boot best practices require logging in all major components."
    }},
    {{
      "gate_id": "1.2",
      "name": "Log Application Messages",
      "description": "Log application messages for monitoring and debugging",
      "applicable": true,
      "reason": "Web application with user interactions requires application-level logging",
      "pattern": ["logger.info.*request", "logger.debug.*response", "application.*log"],
      "expected_count": 5,
      "expected_count_reasoning": "Based on 3 controllers handling HTTP requests/responses, 1 service layer for business logic, and 1 configuration for application logging setup."
    }}
  ]
}}

IMPORTANT:
- Use ONLY double quotes for strings
- Use proper JSON syntax: "key": "value"
- No trailing commas
- Include ALL 16 gates with comprehensive analysis
- Provide detailed reasoning for all decisions
- For regex patterns, use simple patterns without complex escaping (e.g., "logger.info" not "logger\\.info")
- Return ONLY the JSON, no other text"""
        
        # Remove newlines to compact the prompt for transport
        try:
            import re as _re
            compact = prompt.replace("\n", " ").replace("\\n", " ")
            compact = _re.sub(r"\s{2,}", " ", compact).strip()
            return compact
        except Exception:
            return prompt
    
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
                
                # Try multiple parsing strategies (simplified since we have a cleaner prompt)
                parsing_strategies = [
                    # Strategy 1: Direct parsing
                    lambda: json.loads(json_str),
                    # Strategy 2: Fix common trailing commas
                    lambda: json.loads(json_str.replace(",\n}", "\n}").replace(",\n]", "\n]")),
                    # Strategy 3: Fix single quotes
                    lambda: json.loads(json_str.replace("'", '"')),
                    # Strategy 4: Fix escaped regex patterns
                    lambda: self._fix_regex_escapes(json_str),
                    # Strategy 5: Extract patterns array only (fallback)
                    lambda: self._extract_patterns_only(json_str)
                ]
                
                for i, strategy in enumerate(parsing_strategies):
                    try:
                        data = strategy()
                        patterns = data.get("patterns", [])
                        project_summary = data.get("project_summary", {})
                        integration_analysis = data.get("integration_analysis", {})
                        framework_analysis = data.get("framework_analysis", {})
                        
                        if patterns:
                            print(f"✅ Successfully parsed {len(patterns)} patterns from LLM response (strategy {i+1})")
                            
                            # Map LLM gate_ids to internal canonical ids
                            try:
                                from models.gate_definitions import gate_registry
                                internal_ids = {g.gate_id for g in gate_registry.get_hard_gates()}
                                by_display = {}
                                by_name = {}
                                for g in gate_registry.get_hard_gates():
                                    by_display.setdefault(g.display_id, []).append(g)
                                    by_name[g.gate_name.strip().lower()] = g
                                mapped = 0
                                for p in patterns:
                                    rid = p.get("gate_id")
                                    rname = (p.get("name") or "").strip().lower()
                                    # Already internal
                                    if rid in internal_ids:
                                        continue
                                    # Match by display id + name
                                    if rid and rid in by_display:
                                        candidates = by_display[rid]
                                        chosen = None
                                        if rname and rname in by_name:
                                            chosen = by_name[rname]
                                        elif len(candidates) == 1:
                                            chosen = candidates[0]
                                        else:
                                            # try contains match
                                            for cg in candidates:
                                                if rname and (rname in cg.gate_name.lower() or cg.gate_name.lower() in rname):
                                                
                                                    chosen = cg
                                                    break
                                        if chosen:
                                            p["gate_id"] = chosen.gate_id
                                            mapped += 1
                                            continue
                                    # Match by name only
                                    if rname and rname in by_name:
                                        p["gate_id"] = by_name[rname].gate_id
                                        mapped += 1
                                if mapped:
                                    print(f"🔗 Normalized {mapped} LLM gate ids to internal ids")
                            except Exception as norm_e:
                                print(f"⚠️ Failed to normalize LLM gate ids: {norm_e}")

                            # Check if we got all required hard gates (exact canonical ids)
                            from models.gate_definitions import gate_registry
                            required_gate_ids = {g.gate_id for g in gate_registry.get_hard_gates()}
                            returned_gate_ids = set(p.get("gate_id") for p in patterns if p.get("gate_id"))
                            missing_ids = required_gate_ids - returned_gate_ids
                            extra_ids = returned_gate_ids - required_gate_ids
                            if missing_ids:
                                print(f"⚠️ Missing gates in LLM response: {sorted(list(missing_ids))}")
                            if extra_ids:
                                print(f"⚠️ Extra/unexpected gates in LLM response (will be ignored downstream): {sorted(list(extra_ids))}")
                            if not missing_ids:
                                print("✅ All required hard gates included in response")
                            
                            # Log comprehensive analysis results
                            if project_summary:
                                print(f"📊 Project Summary: {project_summary.get('project_type', 'Unknown')}")
                                print(f"📊 Architecture: {project_summary.get('architecture_pattern', 'Unknown')}")
                                print(f"📊 Technology Stack: {project_summary.get('technology_stack', [])}")
                            
                            if integration_analysis:
                                print(f"📊 Database Systems: {integration_analysis.get('database_systems', [])}")
                                print(f"📊 Message Systems: {integration_analysis.get('message_systems', [])}")
                                print(f"📊 External APIs: {integration_analysis.get('external_apis', [])}")
                            
                            if framework_analysis:
                                print(f"📊 Web Frameworks: {framework_analysis.get('web_frameworks', [])}")
                                print(f"📊 Testing Frameworks: {framework_analysis.get('testing_frameworks', [])}")
                                print(f"📊 Security Libraries: {framework_analysis.get('security_libraries', [])}")
                            
                            # Process and validate expected counts from LLM
                            llm_expected_counts = {}
                            for pattern in patterns:
                                gate_id = pattern.get("gate_id")
                                if gate_id:  # Store expected counts for all gates, regardless of applicability
                                    expected_count = pattern.get("expected_count")
                                    expected_count_reasoning = pattern.get("expected_count_reasoning", "")
                                    applicable = pattern.get("applicable", False)
                                    
                                    if expected_count is not None:
                                        llm_expected_counts[gate_id] = {
                                            "expected_count": expected_count,
                                            "reasoning": expected_count_reasoning,
                                            "applicable": applicable,
                                            "source": "llm_analysis"
                                        }
                                        print(f"📊 LLM expected count for {gate_id}: {expected_count} (applicable: {applicable}) ({expected_count_reasoning[:50]}...)")
                                    else:
                                        print(f"⚠️ No expected_count provided by LLM for gate {gate_id}")
                                        # Set a default expected count even if not provided
                                        llm_expected_counts[gate_id] = {
                                            "expected_count": 1,
                                            "reasoning": "Default expected count (LLM did not provide specific count)",
                                            "applicable": applicable,
                                            "source": "llm_analysis_default"
                                        }
                                        print(f"📊 Set default LLM expected count for {gate_id}: 1 (applicable: {applicable})")
                                else:
                                    print(f"⚠️ No gate_id found in pattern: {pattern}")
                            
                            # Store comprehensive analysis in context
                            if hasattr(self, 'context') and self.context is not None:
                                self.context.project_summary = project_summary
                                self.context.integration_analysis = integration_analysis
                                self.context.framework_analysis = framework_analysis
                                self.context.llm_expected_counts = llm_expected_counts
                                print(f"📊 Stored project summary: {len(project_summary)} fields")
                                print(f"📊 Stored integration analysis: {len(integration_analysis)} fields")
                                print(f"📊 Stored framework analysis: {len(framework_analysis)} fields")
                                print(f"📊 Stored LLM expected counts: {len(llm_expected_counts)} gates")
                                
                                # Ensure we have expected counts for all gates
                                from models.gate_definitions import gate_registry
                                all_gate_ids = [g.gate_id for g in gate_registry.get_hard_gates()]
                                missing_gates = [gate_id for gate_id in all_gate_ids if gate_id not in llm_expected_counts]
                                
                                if missing_gates:
                                    print(f"⚠️ Missing expected counts for gates: {missing_gates}")
                                    for gate_id in missing_gates:
                                        llm_expected_counts[gate_id] = {
                                            "expected_count": 1,
                                            "reasoning": "Fallback expected count (gate not covered by LLM analysis)",
                                            "applicable": False,
                                            "source": "llm_analysis_fallback"
                                        }
                                        print(f"📊 Added fallback expected count for {gate_id}: 1")
                                
                                # Update context with complete expected counts
                                self.context.llm_expected_counts = llm_expected_counts
                                print(f"📊 Final LLM expected counts: {len(llm_expected_counts)} gates")
                            
                            return patterns
                        else:
                            print(f"⚠️ No patterns found in LLM response (strategy {i+1})")
                            continue
                    except Exception as e:
                        print(f"⚠️ Strategy {i+1} failed: {e}")
                        continue
                
                print("⚠️ All JSON parsing strategies failed")
                print(f"🔍 Full LLM response for debugging:")
                print(response)
                
                # Check if response was truncated
                if len(response) < 2000 or "..." in response[-100:]:
                    print("⚠️ Response appears to be truncated, using fallback patterns")
                    return self._create_fallback_patterns()
                else:
                    print("⚠️ JSON parsing failed but response doesn't appear truncated")
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
    
    def _extract_patterns_only(self, json_str: str) -> Dict[str, Any]:
        """Extract only the patterns array from malformed JSON"""
        try:
            # Find the patterns array using regex
            pattern_match = re.search(r'"patterns"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
            if pattern_match:
                patterns_content = pattern_match.group(1)
                # Try to extract individual pattern objects
                pattern_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', patterns_content, re.DOTALL)
                patterns = []
                
                for pattern_obj in pattern_objects:
                    try:
                        # Clean up the pattern object
                        clean_obj = pattern_obj.strip()
                        # Fix common issues
                        clean_obj = re.sub(r'"(\w+)"\.\s*"([^"]*)"', r'"\1": "\2"', clean_obj)
                        clean_obj = re.sub(r'(\w+):\s*"([^"]*)"', r'"\1": "\2"', clean_obj)
                        clean_obj = re.sub(r':\s*([^",\{\}\[\]\d][^,\{\}\[\]]*[^",\{\}\[\]\s])(?=\s*[,}\]])', r': "\1"', clean_obj)
                        clean_obj = clean_obj.replace("'", '"')
                        
                        # Try to parse the individual pattern
                        pattern_data = json.loads(clean_obj)
                        patterns.append(pattern_data)
                    except Exception as e:
                        print(f"⚠️ Failed to parse individual pattern: {e}")
                        continue
                
                if patterns:
                    return {"patterns": patterns}
            
            raise ValueError("No patterns array found")
        except Exception as e:
            print(f"⚠️ Extract patterns only failed: {e}")
            raise
    
    def _extract_patterns_regex(self, json_str: str) -> Dict[str, Any]:
        """Use regex to extract patterns from completely malformed JSON"""
        try:
            patterns = []
            
            # Look for pattern-like structures in the text
            # Find objects that contain gate_id, name, description, etc.
            pattern_matches = re.findall(r'\{[^{}]*"gate_id"[^{}]*\}', json_str, re.DOTALL)
            
            for match in pattern_matches:
                try:
                    # Clean up the match
                    clean_match = match.strip()
                    # Fix common issues
                    clean_match = re.sub(r'"(\w+)"\.\s*"([^"]*)"', r'"\1": "\2"', clean_match)
                    clean_match = re.sub(r'(\w+):\s*"([^"]*)"', r'"\1": "\2"', clean_match)
                    clean_match = re.sub(r':\s*([^",\{\}\[\]\d][^,\{\}\[\]]*[^",\{\}\[\]\s])(?=\s*[,}\]])', r': "\1"', clean_match)
                    clean_match = clean_match.replace("'", '"')
                    
                    # Try to parse
                    pattern_data = json.loads(clean_match)
                    if "gate_id" in pattern_data:
                        patterns.append(pattern_data)
                except Exception:
                    continue
            
            if patterns:
                return {"patterns": patterns}
            
            raise ValueError("No valid patterns found")
        except Exception as e:
            print(f"⚠️ Extract patterns regex failed: {e}")
            raise
    
    def _fix_regex_escapes(self, json_str: str) -> Dict[str, Any]:
        """Fix escaped regex patterns in JSON"""
        try:
            # Fix escaped regex patterns - double escape backslashes in pattern arrays
            # This handles patterns like "alert\.(error|warning)" -> "alert\\.(error|warning)"
            
            # Find pattern arrays and fix escapes within them
            import re
            
            # Pattern to match "pattern": ["regex1", "regex2"] or "pattern": ["regex1"]
            pattern_regex = r'"pattern"\s*:\s*\[(.*?)\]'
            
            def fix_pattern_escapes(match):
                pattern_content = match.group(1)
                # Split by comma and fix each pattern
                patterns = re.split(r',\s*', pattern_content)
                fixed_patterns = []
                
                for pattern in patterns:
                    # Remove quotes and fix escapes
                    pattern = pattern.strip().strip('"\'')
                    # Double escape backslashes for JSON
                    pattern = pattern.replace('\\', '\\\\')
                    fixed_patterns.append(f'"{pattern}"')
                
                return f'"pattern": [{", ".join(fixed_patterns)}]'
            
            # Apply the fix
            fixed_json = re.sub(pattern_regex, fix_pattern_escapes, json_str, flags=re.DOTALL)
            
            # Try to parse the fixed JSON
            return json.loads(fixed_json)
        except Exception as e:
            print(f"⚠️ Fix regex escapes failed: {e}")
            raise
    
    def _fix_delimiter_issues(self, json_str: str) -> Dict[str, Any]:
        """Fix specific delimiter issues in JSON"""
        try:
            # Fix the specific issue: "Expecting ',' delimiter"
            # This often happens when there are missing commas between array elements or object properties
            
            # Fix missing commas between array elements
            json_str = re.sub(r'(\])\s*(\[)', r'\1,\2', json_str)
            
            # Fix missing commas between object properties
            json_str = re.sub(r'(")\s*(")', r'\1,\2', json_str)
            
            # Fix missing commas before closing braces/brackets
            json_str = re.sub(r'([^,{])\s*([}\]])', r'\1,\2', json_str)
            
            # Remove any double commas that might have been created
            json_str = re.sub(r',\s*,', ',', json_str)
            
            # Try to parse the fixed JSON
            return json.loads(json_str)
        except Exception as e:
            print(f"⚠️ Fix delimiter issues failed: {e}")
            raise
    
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
    
    def _get_project_structure_info(self) -> str:
        """Get comprehensive project structure information for the prompt"""
        try:
            metadata = getattr(self.context, 'metadata', {})
            main_repo = metadata.get('main_repo', {})
            cd_repo = metadata.get('cd_repo')
            
            structure_info = []
            
            # Main repository comprehensive info
            if main_repo:
                structure_info.append("=== MAIN REPOSITORY ANALYSIS ===")
                structure_info.append(f"Repository URL: {main_repo.get('repo_url', 'Unknown')}")
                structure_info.append(f"Branch: {main_repo.get('branch', 'Unknown')}")
                structure_info.append(f"Total Files: {main_repo.get('total_files', 0)}")
                structure_info.append(f"Total Lines: {main_repo.get('total_lines', 0)}")
                structure_info.append(f"Primary Languages: {', '.join(main_repo.get('languages', []))}")
                
                # Build and configuration files
                build_files = main_repo.get('build_files', [])
                if build_files:
                    structure_info.append(f"Build Files: {', '.join(build_files)}")
                
                config_files = main_repo.get('config_files', [])
                if config_files:
                    structure_info.append(f"Configuration Files: {', '.join(config_files)}")
                
                # Dependencies analysis
                dependencies = main_repo.get('dependencies', {})
                if dependencies:
                    structure_info.append("Dependencies Analysis:")
                    for dep_type, deps in dependencies.items():
                        if deps:
                            structure_info.append(f"  - {dep_type}: {', '.join(deps)}")
                
                # File structure analysis
                file_structure = main_repo.get('file_structure', {})
                if file_structure:
                    structure_info.append("File Structure Analysis:")
                    for file_type, count in file_structure.items():
                        if count > 0:
                            structure_info.append(f"  - {file_type}: {count} files")

                # JSON directory tree plus flat path list
                repo_path = main_repo.get('local_path') or getattr(self.context, 'repo_path', None)
                if repo_path:
                    from pathlib import Path
                    ignore_dirs_set = {'.git', '.svn', '.hg', 'node_modules', '__pycache__', 'build', 'dist', 'target', '.pytest_cache', '.tox'}
                    ignore_exts_set = {'.jar', '.class', '.png'}

                    def build_tree(path: Path):
                        node = {"name": path.name, "dirs": {}, "files": []}
                        try:
                            for entry in path.iterdir():
                                if entry.name in ignore_dirs_set:
                                    continue
                                if entry.is_dir():
                                    node["dirs"][entry.name] = build_tree(entry)
                                else:
                                    if entry.suffix.lower() in ignore_exts_set:
                                        continue
                                    node["files"].append(entry.name)
                        except Exception:
                            pass
                        return node

                    root = Path(repo_path)
                    tree = build_tree(root)
                    import json as _json
                    structure_info.append("\nFILE TREE (JSON):")
                    structure_info.append(_json.dumps(tree, ensure_ascii=False))

                    # Flat path list representation (compact, no repeated dir names)
                    prefix = root.name
                    flat_paths = []
                    try:
                        for fp in root.rglob('*'):
                            if fp.is_dir():
                                if any(seg in ignore_dirs_set for seg in fp.parts):
                                    continue
                                continue
                            if any(seg in ignore_dirs_set for seg in fp.parts):
                                continue
                            if fp.suffix.lower() in ignore_exts_set:
                                continue
                            rel = fp.relative_to(root).as_posix()
                            flat_paths.append(f"{prefix}/{rel}")
                    except Exception:
                        pass
                    if flat_paths:
                        structure_info.append("\nFILE LIST (paths):")
                        structure_info.append("\n".join(flat_paths))
            
            # CD/CI repository info
            if cd_repo:
                structure_info.append("\n=== CD/CI REPOSITORY ANALYSIS ===")
                structure_info.append(f"Repository URL: {cd_repo.get('repo_url', 'Unknown')}")
                structure_info.append(f"Total Files: {cd_repo.get('total_files', 0)}")
                structure_info.append(f"Total Lines: {cd_repo.get('total_lines', 0)}")
                
                cd_build_files = cd_repo.get('build_files', [])
                if cd_build_files:
                    structure_info.append(f"Build Files: {', '.join(cd_build_files)}")
                
                cd_config_files = cd_repo.get('config_files', [])
                if cd_config_files:
                    structure_info.append(f"Configuration Files: {', '.join(cd_config_files)}")
                
                # CD/CI specific analysis
                cd_dependencies = cd_repo.get('dependencies', {})
                if cd_dependencies:
                    structure_info.append("CD/CI Dependencies:")
                    for dep_type, deps in cd_dependencies.items():
                        if deps:
                            structure_info.append(f"  - {dep_type}: {', '.join(deps)}")
            
            if not structure_info:
                return "No project structure information available"
            
            return "\n".join(structure_info)
            
        except Exception as e:
            print(f"⚠️ Error getting project structure info: {e}")
            return "Error retrieving project structure information"

    def _get_available_gates_summary(self) -> str:
        """Get summary of available gates for the prompt"""
        try:
            # Always use centralized registry to avoid discrepancies
            from models.gate_definitions import gate_registry
            gates = sorted(
                gate_registry.get_hard_gates(),
                key=lambda g: [int(x) if x.isdigit() else x for x in g.display_id.split('.')]
            )
            lines = []
            for g in gates:
                category = g.category.value.title()
                severity = g.severity.value.title()
                lines.append(f"- {g.display_id}: {g.gate_name} ({category}, {severity})")
            return "\n".join(lines) if lines else "No gates defined"
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
                content = self._read_file_content(file_path, max_lines=5000)
                
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
                content = self._read_file_content(file_path, max_lines=5000)
                
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
                # Get all gate IDs from pattern library (now using gate numbers as keys)
                gate_ids = self.pattern_library_service.get_all_gate_names()
                
                for gate_id in gate_ids:
                    # Get gate config directly from pattern library
                    gate_config = self.pattern_library_service.get_gate_patterns(gate_id)
                    if not gate_config:
                        continue
                    
                    # Extract patterns from gate config
                    patterns = []
                    criteria = gate_config.get("criteria", {})
                    conditions = criteria.get("conditions", [])
                    
                    for condition in conditions:
                        if condition.get("type") == "pattern":
                            for pattern_config in condition.get("patterns", []):
                                patterns.append(pattern_config.get("pattern", ""))
                        elif condition.get("type") == "file_pattern":
                            for pattern_config in condition.get("file_patterns", []):
                                patterns.append(pattern_config.get("pattern", ""))
                    
                    for pattern in patterns:
                        consolidated.append({
                            "source": "enhanced_library",
                            "gate_id": gate_id,  # Use gate_id directly
                            "name": gate_config.get("display_name", gate_id),
                            "pattern": pattern,
                            "description": gate_config.get("description", ""),
                            "severity": gate_config.get("priority", "MEDIUM").upper(),
                            "category": gate_config.get("category", "Unknown")
                        })
            
            # Store consolidated patterns
            self.context.patterns = {
                "consolidated": consolidated,
                "dynamic": dynamic_patterns,
                "static": self.static_patterns
            }
            
            print(f"✅ Pattern consolidation completed: {len(consolidated)} patterns")
            print(f"   - Dynamic patterns: {len(dynamic_patterns)}")
            print(f"   - Static patterns: {len(self.static_patterns)}")
            print(f"   - Enhanced library patterns: {len([p for p in consolidated if p.get('source') == 'enhanced_library'])}")
            print(f"   - Total consolidated: {len(consolidated)}")
            
            # Debug: Show first few consolidated patterns
            if consolidated:
                print(f"   - Sample patterns:")
                for i, pattern in enumerate(consolidated[:3]):
                    print(f"     {i+1}. {pattern.get('gate_id')}: {pattern.get('name')} ({pattern.get('source')})")
            
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
    
    def __init__(self, cocoindex_service):
        super().__init__()
        self.cocoindex_service = cocoindex_service
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare expected implementation calculation"""
        return {
            "vector_data": context.vector_data,
            "patterns": context.patterns,
            "expected_counts_analysis": getattr(context, 'expected_counts_analysis', {}),
            "llm_expected_counts": getattr(context, 'llm_expected_counts', {})
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute expected implementation calculation for both repositories"""
        try:
            print("🔍 Step 5: Expected Implementation Calculation (including CD repos)")
            
            vector_data = prep_res["vector_data"]
            patterns = prep_res["patterns"]
            expected_counts_analysis = prep_res.get("expected_counts_analysis", {})
            llm_expected_counts = prep_res.get("llm_expected_counts", {})
            
            # Handle case where vector_data is None (CocoIndex indexing failed)
            if not vector_data:
                print("⚠️ No vector data available, using project structure analysis only")
                expected_implementations = {}
                
                # Use LLM expected counts first, then fall back to project structure analysis
                consolidated_patterns = patterns.get("consolidated", [])
                for pattern in consolidated_patterns:
                    gate_id = pattern.get("gate_id")
                    
                    # Check LLM expected counts first
                    if gate_id in llm_expected_counts:
                        llm_analysis = llm_expected_counts[gate_id]
                        expected_count = llm_analysis.get("expected_count", 1)
                        reason = llm_analysis.get("reasoning", "Based on LLM analysis")
                        print(f"📊 Using LLM expected count for {gate_id}: {expected_count} ({reason[:50]}...)")
                    elif gate_id in expected_counts_analysis:
                        analysis = expected_counts_analysis[gate_id]
                        expected_count = analysis.get("expected_count", 1)
                        reason = analysis.get("reason", "Based on project structure analysis")
                        print(f"📊 Using project structure expected count for {gate_id}: {expected_count} ({reason[:50]}...)")
                    else:
                        expected_count = 1
                        reason = "Default fallback (no vector data available)"
                        print(f"⚠️ No LLM expected count found for {gate_id}, using calculated fallback")
                    
                    expected_implementations[gate_id] = {
                        "pattern": pattern,
                        "expected_count": expected_count,
                        "main_implementations": 0,
                        "cd_implementations": 0,
                        "similar_implementations": [],
                        "calculation_method": "project_structure_analysis",
                        "reason": reason
                    }
                
                self.context.expected_implementations = expected_implementations
                print(f"✅ Expected implementations calculated using project structure analysis only")
                return "success"
            
            scan_id = vector_data["scan_id"]
            main_collection_name = vector_data["main_collection_name"]
            cd_collection_name = vector_data.get("cd_collection_name")
            consolidated_patterns = patterns.get("consolidated", [])
            if not consolidated_patterns:
                print("⚠️ No consolidated patterns found, using dynamic patterns as fallback")
                consolidated_patterns = patterns.get("dynamic", [])
            
            expected_implementations = {}
            
            # Get hard gates from centralized registry
            from models.gate_definitions import gate_registry
            hard_gates = {g.gate_id for g in gate_registry.get_hard_gates()}
            
            # For each pattern, find expected implementations using CocoIndex semantic search
            for pattern in consolidated_patterns:
                # Only process hard gates
                if pattern.get("gate_id") not in hard_gates:
                    continue
                pattern_name = pattern["name"]
                pattern_description = pattern["description"]
                
                # Create semantic query
                query = f"implementation of {pattern_name}: {pattern_description}"
                
                # Search main repository collection
                main_results = self.cocoindex_service.search_similar(
                    collection_name=main_collection_name,
                    query=query,
                    limit=10,
                    score_threshold=0.5
                )
                
                # Search CD repository collection if it exists
                cd_results = []
                if cd_collection_name:
                    cd_results = self.cocoindex_service.search_similar(
                        collection_name=cd_collection_name,
                        query=query,
                        limit=10,
                        score_threshold=0.5
                    )
                
                # Combine results
                all_results = main_results + cd_results
                
                if all_results:
                    # Calculate expected count based on similar implementations found
                    expected_count = len(all_results)
                    reason = f"Found {expected_count} similar implementations using CocoIndex semantic search"
                    
                    expected_implementations[pattern["gate_id"]] = {
                        "pattern": pattern,
                        "expected_count": expected_count,
                        "main_implementations": len(main_results),
                        "cd_implementations": len(cd_results),
                        "similar_implementations": all_results,
                        "calculation_method": "cocoindex_semantic_search",
                        "reason": reason
                    }
                else:
                    # Use LLM expected counts first, then fall back to project structure analysis
                    gate_id = pattern["gate_id"]
                    if gate_id in llm_expected_counts:
                        llm_analysis = llm_expected_counts[gate_id]
                        expected_count = llm_analysis.get("expected_count", 1)
                        reason = llm_analysis.get("reasoning", "Based on LLM analysis")
                        print(f"📊 Using LLM expected count for {gate_id}: {expected_count} expected ({reason[:50]}...)")
                    elif gate_id in expected_counts_analysis:
                        analysis = expected_counts_analysis[gate_id]
                        expected_count = analysis.get("expected_count", 1)
                        reason = analysis.get("reason", "Based on project structure analysis")
                        print(f"📊 Using project structure analysis for {gate_id}: {expected_count} expected ({reason})")
                    else:
                        expected_count = 1
                        reason = "Default fallback (no similar implementations found)"
                        print(f"⚠️ No LLM expected count found for {gate_id}, using calculated fallback")
                    
                    expected_implementations[gate_id] = {
                        "pattern": pattern,
                        "expected_count": expected_count,
                        "main_implementations": 0,
                        "cd_implementations": 0,
                        "similar_implementations": [],
                        "calculation_method": "project_structure_analysis",
                        "reason": reason
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
    
    def __init__(self):
        super().__init__()
    
    async def prep_async(self, context: ScanContext) -> Dict[str, Any]:
        """Prepare file scanning"""
        return {
            "repo_path": context.repo_path,
            "cd_repo_path": context.cd_repo_path,
            "patterns": context.patterns,
            "expected_implementations": context.expected_implementations
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute file scanning for both main and CD repositories with enhanced pattern library integration"""
        try:
            print("📁 Step 6: File Scanning & Pattern & AST parser based Matching (including CD repos)")
            
            repo_path = prep_res["repo_path"]
            cd_repo_path = prep_res["cd_repo_path"]
            patterns = prep_res["patterns"]
            expected_implementations = prep_res["expected_implementations"]
            
            consolidated_patterns = patterns.get("consolidated", [])
            if not consolidated_patterns:
                print("⚠️ No consolidated patterns found, using dynamic patterns as fallback")
                consolidated_patterns = patterns.get("dynamic", [])
            
            print(f"📊 FileScanningNode received {len(consolidated_patterns)} consolidated patterns")
            print(f"   - Patterns from context: {len(patterns.get('consolidated', []))}")
            print(f"   - Dynamic patterns: {len(patterns.get('dynamic', []))}")

            # Normalize all consolidated pattern gate_ids to internal ids
            try:
                from models.gate_definitions import gate_registry
                internal_ids = {g.gate_id for g in gate_registry.get_hard_gates()}
                by_display = {}
                by_name = {}
                for g in gate_registry.get_hard_gates():
                    by_display.setdefault(g.display_id, []).append(g)
                    by_name[g.gate_name.strip().lower()] = g
                normalized_count = 0
                for p in consolidated_patterns:
                    rid = p.get("gate_id")
                    rname = (p.get("name") or "").strip().lower()
                    if rid in internal_ids:
                        continue
                    if rid and rid in by_display:
                        candidates = by_display[rid]
                        chosen = None
                        if rname and rname in by_name:
                            chosen = by_name[rname]
                        elif len(candidates) == 1:
                            chosen = candidates[0]
                        else:
                            for cg in candidates:
                                if rname and (rname in cg.gate_name.lower() or cg.gate_name.lower() in rname):
                                    chosen = cg
                                    break
                        if chosen:
                            p["gate_id"] = chosen.gate_id
                            normalized_count += 1
                            continue
                    if rname and rname in by_name:
                        p["gate_id"] = by_name[rname].gate_id
                        normalized_count += 1
                if normalized_count:
                    print(f"🔗 Normalized {normalized_count} consolidated pattern ids to internal ids")
            except Exception as e_norm:
                print(f"⚠️ Failed to normalize consolidated pattern ids: {e_norm}")
            
            scan_results = {}
            
            # Get hard gates from centralized registry
            from models.gate_definitions import gate_registry
            hard_gates = {g.gate_id for g in gate_registry.get_hard_gates()}
            
            # Filter patterns to only include hard gates
            hard_gate_patterns = [p for p in consolidated_patterns if p.get("gate_id") in hard_gates]
            print(f"   - Hard gate patterns: {len(hard_gate_patterns)}")
            print(f"   - Hard gates available: {len(hard_gates)}")
            if hard_gate_patterns:
                print(f"   - Sample hard gate patterns:")
                for i, pattern in enumerate(hard_gate_patterns[:3]):
                    print(f"     {i+1}. {pattern.get('gate_id')}: {pattern.get('name')} ({pattern.get('source')})")
            
            # Initialize pattern library service
            try:
                from services.pattern_library_service import PatternLibraryService
                pattern_library_service = PatternLibraryService()
                print(f"📚 Pattern library service initialized with {len(pattern_library_service.get_all_gate_names())} gates")
            except Exception as e:
                print(f"⚠️ Pattern library service not available: {e}")
                pattern_library_service = None

            # Always use pattern library patterns as primary; LLM/dynamic as secondary
            # Combination happens per-gate below when preparing pattern_regex
            
            # Enhanced scanning with pattern library integration
            print(f"🔍 Enhanced scanning main repository: {repo_path}")
            for pattern in hard_gate_patterns:
                gate_id = pattern["gate_id"]
                # Combine library patterns (primary) and LLM/dynamic (secondary)
                lib_patterns = []
                if pattern_library_service:
                    try:
                        lib_patterns = pattern_library_service.get_patterns_for_gate(gate_id) or []
                    except Exception:
                        lib_patterns = []
                llm_patterns = pattern.get("pattern", [])
                if isinstance(llm_patterns, str):
                    llm_patterns = [llm_patterns] if llm_patterns.strip() else []
                llm_patterns = [p for p in llm_patterns if isinstance(p, str) and p.strip()]
                # de-duplicate while preserving order (library first)
                combined = []
                seen = set()
                for src in (lib_patterns, llm_patterns):
                    for pat in src:
                        key = pat
                        if key not in seen:
                            combined.append(pat)
                            seen.add(key)
                pattern_regex = combined
                
                # Traditional pattern matching
                main_matches = await self._scan_for_pattern(repo_path, pattern_regex, gate_id, "main")
                
                # Enhanced pattern library evaluation
                static_evaluation = None
                if pattern_library_service:
                    static_evaluation = await self._evaluate_with_pattern_library(
                        pattern_library_service, gate_id, repo_path, "main"
                    )
                
                scan_results[gate_id] = {
                    "pattern": pattern,
                    "main_matches": main_matches,
                    "main_match_count": len(main_matches),
                    "cd_matches": [],
                    "cd_match_count": 0,
                    "total_matches": len(main_matches),
                    "static_evaluation": static_evaluation
                }
            
            # Scan CD repository files for each pattern
            if cd_repo_path:
                print(f"🔍 Enhanced scanning CD repository: {cd_repo_path}")
                for pattern in hard_gate_patterns:
                    gate_id = pattern["gate_id"]
                    lib_patterns = []
                    if pattern_library_service:
                        try:
                            lib_patterns = pattern_library_service.get_patterns_for_gate(gate_id) or []
                        except Exception:
                            lib_patterns = []
                    llm_patterns = pattern.get("pattern", [])
                    if isinstance(llm_patterns, str):
                        llm_patterns = [llm_patterns] if llm_patterns.strip() else []
                    llm_patterns = [p for p in llm_patterns if isinstance(p, str) and p.strip()]
                    combined = []
                    seen = set()
                    for src in (lib_patterns, llm_patterns):
                        for pat in src:
                            key = pat
                            if key not in seen:
                                combined.append(pat)
                                seen.add(key)
                    pattern_regex = combined
                    
                    # Traditional pattern matching
                    cd_matches = await self._scan_for_pattern(cd_repo_path, pattern_regex, gate_id, "cd")
                    
                    # Enhanced pattern library evaluation
                    static_evaluation_cd = None
                    if pattern_library_service:
                        static_evaluation_cd = await self._evaluate_with_pattern_library(
                            pattern_library_service, gate_id, cd_repo_path, "cd"
                        )
                    
                    if gate_id in scan_results:
                        scan_results[gate_id]["cd_matches"] = cd_matches
                        scan_results[gate_id]["cd_match_count"] = len(cd_matches)
                        scan_results[gate_id]["total_matches"] += len(cd_matches)
                        scan_results[gate_id]["static_evaluation_cd"] = static_evaluation_cd
                    else:
                        scan_results[gate_id] = {
                            "pattern": pattern,
                            "main_matches": [],
                            "main_match_count": 0,
                            "cd_matches": cd_matches,
                            "cd_match_count": len(cd_matches),
                            "total_matches": len(cd_matches),
                            "static_evaluation": None,
                            "static_evaluation_cd": static_evaluation_cd
                        }
            
            # Store scan results
            self.context.scan_results = scan_results
            
            total_patterns = len(scan_results)
            total_matches = sum(result["total_matches"] for result in scan_results.values())
            static_evaluations = sum(1 for result in scan_results.values() 
                                   if result.get("static_evaluation") or result.get("static_evaluation_cd"))
            
            print(f"✅ Enhanced file scanning completed: {total_patterns} patterns scanned, {total_matches} total matches, {static_evaluations} static evaluations")
            
            return "success"
            
        except Exception as e:
            print(f"❌ File scanning failed: {e}")
            import traceback
            traceback.print_exc()
            return "error"
    
    async def _scan_for_pattern(self, repo_path: str, pattern_regex: Any, gate_id: str, repo_type: str = "main") -> List[Dict[str, Any]]:
        """Scan for specific pattern(s) in repository with gate-specific file filtering.
        pattern_regex may be a single regex string or a list/tuple of regex strings.
        """
        import re
        
        matches = []
        repo_path_obj = Path(repo_path)
        
        # Prepare compiled regex list
        compiled_patterns = []
        patterns_input = pattern_regex
        if isinstance(patterns_input, (list, tuple)):
            for idx, p in enumerate(patterns_input):
                if not isinstance(p, str):
                    print(f"⚠️ Skipping non-string regex at index {idx} for gate {gate_id}: {p}")
                    continue
                try:
                    compiled_patterns.append(re.compile(p, re.IGNORECASE))
                except re.error:
                    print(f"⚠️ Invalid regex pattern for gate {gate_id} at index {idx}: {p}")
        elif isinstance(patterns_input, str):
            try:
                compiled_patterns.append(re.compile(patterns_input, re.IGNORECASE))
            except re.error:
                print(f"⚠️ Invalid regex pattern for gate {gate_id}: {patterns_input}")
        else:
            print(f"⚠️ Unsupported pattern type for gate {gate_id}: {type(patterns_input)}")
        
        if not compiled_patterns:
            # No valid patterns to scan
            return matches
        
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file_for_gate(file_path, gate_id):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Find matches for each compiled pattern
                    for pattern in compiled_patterns:
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
    
    async def _evaluate_with_pattern_library(self, pattern_library_service, gate_id: str, repo_path: str, repo_type: str) -> Dict[str, Any]:
        """Evaluate a gate using the enhanced pattern library"""
        try:
            from pathlib import Path
            import asyncio
            
            repo_path_obj = Path(repo_path)
            evaluation_results = {
                "gate_id": gate_id,
                "repo_type": repo_type,
                "files_evaluated": 0,
                "files_passed": 0,
                "total_score": 0.0,
                "file_results": [],
                "overall_passed": False,
                "overall_score": 0.0
            }
            
            # Get all relevant files for evaluation
            relevant_files = []
            from utils.file_filter import DEFAULT_FILE_FILTER
            for file_path in DEFAULT_FILE_FILTER.iter_files(repo_path_obj):
                if not self._should_ignore_file_for_gate(file_path, gate_id):
                    relevant_files.append(file_path)
            
            evaluation_results["files_evaluated"] = len(relevant_files)
            
            if not relevant_files:
                return evaluation_results
            
            # Evaluate each file
            file_scores = []
            for file_path in relevant_files:
                try:
                    # Detect technology
                    technology = pattern_library_service.detect_technology(str(file_path))
                    
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Evaluate gate against file content
                    result = pattern_library_service.evaluate_gate(
                        gate_id, content, str(file_path), technology
                    )
                    
                    file_result = {
                        "file_path": str(file_path.relative_to(repo_path_obj)),
                        "technology": technology,
                        "passed": result.get("passed", False),
                        "score": result.get("score", 0.0),
                        "threshold": result.get("threshold", 20.0),
                        "category": result.get("category", "Unknown"),
                        "priority": result.get("priority", "Unknown")
                    }
                    
                    evaluation_results["file_results"].append(file_result)
                    file_scores.append(result.get("score", 0.0))
                    
                    if result.get("passed", False):
                        evaluation_results["files_passed"] += 1
                
                except Exception as e:
                    print(f"⚠️ Failed to evaluate file {file_path} for gate {gate_id}: {e}")
                    continue
            
            # Calculate overall results
            if file_scores:
                evaluation_results["overall_score"] = sum(file_scores) / len(file_scores)
                evaluation_results["total_score"] = sum(file_scores)
                
                # Determine overall pass based on coverage and score
                coverage_percentage = (evaluation_results["files_passed"] / evaluation_results["files_evaluated"]) * 100
                evaluation_results["overall_passed"] = (
                    evaluation_results["overall_score"] >= 50.0 and 
                    coverage_percentage >= 20.0
                )
            
            return evaluation_results
            
        except Exception as e:
            print(f"❌ Error evaluating gate {gate_id} with pattern library: {e}")
            return {
                "gate_id": gate_id,
                "repo_type": repo_type,
                "error": str(e),
                "files_evaluated": 0,
                "files_passed": 0,
                "overall_passed": False,
                "overall_score": 0.0
            }
    
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
                                            metadata: Dict[str, Any], scan_results: Dict[str, Any], 
                                            llm_expected_counts: Dict[str, Any] = None) -> int:
        """Calculate intelligent expected count based on technology stack and codebase analysis"""
        try:
            # First, check if LLM provided an expected count for this gate
            if llm_expected_counts and gate_id in llm_expected_counts:
                llm_count = llm_expected_counts[gate_id]
                expected_count = llm_count.get("expected_count")
                reasoning = llm_count.get("reasoning", "")
                
                if expected_count is not None and expected_count > 0:
                    print(f"   📊 Using LLM expected count for {gate_id}: {expected_count}")
                    print(f"   📝 LLM reasoning: {reasoning[:100]}...")
                    return expected_count
            
            # Fall back to calculated expected count if LLM didn't provide one
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
            
            scan_results = prep_res.get("scan_results") or {}
            expected_implementations = prep_res.get("expected_implementations") or {}
            metadata = prep_res.get("metadata", {})
            
            # If static scan missing, we will use LLM actual counts instead
            
            # Handle case where expected_implementations is None
            if not expected_implementations:
                print("⚠️ No expected implementations available, using defaults")
                expected_implementations = {}
            
            gate_results = []
            
            # Get canonical hard gates from centralized registry (internal ids)
            from models.gate_definitions import gate_registry
            canonical_gates = gate_registry.get_hard_gates()
            canonical_ids = [g.gate_id for g in canonical_gates]
            gate_def_by_id = {g.gate_id: g for g in canonical_gates}
            
            for gate_id in canonical_ids:
                scan_result = scan_results.get(gate_id, {})
                # Build a minimal pattern object if missing, from registry definition
                gate_def = gate_def_by_id.get(gate_id)
                default_pattern_obj = {
                    "name": gate_def.gate_name if gate_def else gate_id,
                    "severity": gate_def.severity.value.upper() if gate_def else "MEDIUM",
                    "category": gate_def.category.value.upper() if gate_def else "UNKNOWN",
                    "pattern": []
                }
                pattern = scan_result.get("pattern", default_pattern_obj)
                main_matches = scan_result.get("main_matches", [])
                cd_matches = scan_result.get("cd_matches", [])
                total_matches = scan_result.get("total_matches", 0)
                if total_matches == 0:
                    llm_actual_counts = getattr(self.context, 'llm_actual_counts', None)
                    if llm_actual_counts and gate_id in llm_actual_counts:
                        try:
                            total_matches = int(llm_actual_counts[gate_id].get("actual_count") or 0)
                        except Exception:
                            total_matches = total_matches
                
                # Check LLM applicability decision first
                llm_expected_counts = getattr(self.context, 'llm_expected_counts', None)
                if llm_expected_counts and gate_id in llm_expected_counts:
                    llm_count = llm_expected_counts[gate_id]
                    llm_applicable = llm_count.get("applicable", True)
                    
                    if not llm_applicable:
                        print(f"   ⏭️ Skipping gate {gate_id} - LLM marked as not applicable")
                        continue
                
                # Fall back to traditional gate skipping logic if no LLM decision
                if self._should_skip_gate(gate_id, pattern, metadata, scan_results):
                    print(f"   ⏭️ Skipping gate {gate_id} - traditional gate skipping logic")
                    continue
                
                # Special inverse gate handling: Avoid Logging Sensitive Data (gate_id '7')
                # For this gate, expected_count is 0; any non-zero match is a FAIL, zero matches is PASS.
                if gate_id == "7":
                    expected_count = 0
                    threshold = 0
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
                            pattern=pattern.get("pattern", [])
                        ))
                    status = GateStatus.PASS if total_matches == 0 else GateStatus.FAIL
                    base_reasoning = (
                        "No sensitive data logging detected." if status == GateStatus.PASS else
                        f"Detected {total_matches} potential sensitive-log occurrences; any occurrence fails this gate."
                    )
                    base_recommendations = [] if status == GateStatus.PASS else [
                        "Remove or mask sensitive fields (passwords, tokens, PII) before logging",
                        "Use structured logging with field-level redaction",
                        "Review logging configuration for filters/maskers"
                    ]
                    gate_result = GateResult(
                        gate_id=gate_id,
                        gate_name=pattern["name"],
                        status=status,
                        expected_count=expected_count,
                        actual_count=total_matches,
                        threshold=threshold,
                        patterns_found=[match["match_text"] for match in (main_matches + cd_matches)[:5]],
                        detailed_matches=detailed_matches,
                        recommendations=base_recommendations,
                        confidence_score=self._calculate_confidence(total_matches, max(1, expected_count)),
                        reasoning=base_reasoning
                    )
                    gate_results.append(gate_result)
                    continue

                # Get LLM expected counts from context if available
                llm_expected_counts = getattr(self.context, 'llm_expected_counts', None)
                
                # Calculate intelligent expected count based on technology and codebase
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from flow.expected_count_calculator import ExpectedCountCalculator
                calculator = ExpectedCountCalculator()
                
                # PRIMARY: Use LLM expected count from pre-analysis response
                if llm_expected_counts and gate_id in llm_expected_counts:
                    llm_count = llm_expected_counts[gate_id]
                    expected_count = llm_count.get("expected_count")
                    reasoning = llm_count.get("reasoning", "")
                    applicable = llm_count.get("applicable", False)
                    
                    if expected_count is not None:
                        print(f"   🎯 Using LLM expected count for {gate_id}: {expected_count} (applicable: {applicable})")
                        if reasoning:
                            print(f"   📝 LLM reasoning: {reasoning[:100]}...")
                    else:
                        print(f"   ⚠️ LLM provided no expected_count for {gate_id}, using calculated fallback")
                        expected_count = calculator.calculate_expected_count(gate_id, metadata)
                else:
                    print(f"   ⚠️ No LLM expected count found for {gate_id}, using calculated fallback")
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
                
                # Enhance reasoning with LLM expected count reasoning if available
                if llm_expected_counts and gate_id in llm_expected_counts:
                    llm_count = llm_expected_counts[gate_id]
                    llm_reasoning = llm_count.get("reasoning", "")
                    if llm_reasoning:
                        base_reasoning += f"\n\nLLM Expected Count Reasoning: {llm_reasoning}"
                
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
    
    def __init__(self, llm_service, cocoindex_service):
        super().__init__()
        self.llm_service = llm_service
        self.cocoindex_service = cocoindex_service
    
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
            gate_results=gate_results_text,
            project_summary=f"Project: {metadata.get('repo_url', 'Unknown')}",
            scan_metadata=f"Languages: {', '.join(metadata.get('languages', []))}"
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
            "vector_data": context.vector_data,
            "scan_id": context.scan_id
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        """Execute report generation"""
        try:
            print("📊 Step 9: Report Generation")
            
            gate_results = prep_res["gate_results"]
            post_analysis = prep_res["post_analysis"]
            metadata = prep_res["metadata"]
            vector_data = prep_res["vector_data"]
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
            
            # Update metadata with vector config, vector data, project info, and analysis extras
            metadata_with_vector = metadata.copy()
            metadata_with_vector["vector_config"] = vector_config
            if vector_data:
                metadata_with_vector["vector_data"] = vector_data
            metadata_with_vector["project_summary"] = project_info
            # attach critical files & expected counts if available
            if hasattr(self, 'context') and self.context is not None:
                if getattr(self.context, 'critical_files', None):
                    metadata_with_vector["critical_files"] = getattr(self.context, 'critical_files')
                if getattr(self.context, 'llm_expected_counts', None):
                    metadata_with_vector["llm_expected_counts"] = getattr(self.context, 'llm_expected_counts')
            
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
    
    def __init__(self, cocoindex_service):
        super().__init__()
        self.cocoindex_service = cocoindex_service
    
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
            
            # Generate embedding for scan summary using CocoIndex service
            summary_text = json.dumps(scan_summary, indent=2)
            
            # Use CocoIndex service to generate embedding and store
            try:
                # Create a temporary collection for scan results
                scan_collection_name = f"scan_results_{scan_result.scan_id}"
                
                # Generate embedding using the same method as CocoIndex service
                from services.embedding_service import EmbeddingService
                
                embedding_config = {
                    "provider": "local",
                    "model": "text-embedding-nomic-embed-text-v1.5-embedding",
                    "base_url": "http://localhost:1234",
                    "batch_size": 1,
                    "vector_size": 768,
                    "timeout": 30
                }
                
                embedding_service = EmbeddingService(embedding_config)
                embedding = embedding_service.embed_single(summary_text)
                
                if embedding:
                    # Store in Qdrant using CocoIndex service
                    import uuid
                    vector_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"scan_{scan_result.scan_id}"))
                    
                    # Create collection if it doesn't exist
                    self.cocoindex_service._create_collection(scan_collection_name)
                    
                    # Store the vector
                    from qdrant_client.models import PointStruct
                    point = PointStruct(
                        id=vector_id,
                        vector=embedding,
                        payload={
                            "type": "scan_result",
                            "scan_id": scan_result.scan_id,
                            "content": summary_text,
                            "metadata": scan_summary
                        }
                    )
                    
                    self.cocoindex_service.client.upsert(
                        collection_name=scan_collection_name,
                        points=[point]
                    )
                    
                    print(f"✅ Scan result stored in vector database: {vector_id}")
                else:
                    print("⚠️ Failed to generate embedding for scan summary")
                    
            except Exception as e:
                print(f"⚠️ Failed to store scan result in vector database: {e}")
            
            # Store detailed results (simplified - in real implementation, store in database)
            vector_id = None
            if 'embedding' in locals() and embedding:
                vector_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"scan_{scan_result.scan_id}"))
                
            self.context.stored_result = {
                "scan_id": scan_result.scan_id,
                "vector_id": vector_id,
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
                content = self._read_file_content(file_path, max_lines=5000)
                
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
                content = self._read_file_content(file_path, max_lines=5000)
                
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
