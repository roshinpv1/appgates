"""
Main scan flow orchestrator
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.base import AsyncFlow, ScanContext
from utils.git_utils import GitUtils
from services.cocoindex_service import CocoIndexService
from services.prompt_service import PromptService
from services.pattern_library_service import PatternLibraryService
from services.llm_service import LLMService


class ScanFlow(AsyncFlow):
    """Main scan flow orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize scan flow"""
        super().__init__()
        
        # Initialize services
        self.cocoindex_service = CocoIndexService(config.get("cocoindex", {}))
        self.git_utils = GitUtils()
        
        # Initialize external libraries
        self.prompt_service = PromptService()
        self.pattern_library_service = PatternLibraryService()
        
        # Initialize LLM service
        self.llm_service = LLMService(config.get("llm", {}))
        
        # Build flow
        self._build_flow()
    
    def _build_flow(self):
        """Build the scan flow"""
        from .scan_nodes import (
            RepositoryCheckoutNode, VectorizationNode, LLMPreAnalysisNode,
            PatternConsolidationNode, ExpectedImplementationNode, FileScanningNode,
            GateEvaluationNode, LLMPostAnalysisNode, ReportGenerationNode,
            AgenticStorageNode
        )
        
        # Create nodes
        checkout_node = RepositoryCheckoutNode()
        vectorization_node = VectorizationNode(self.cocoindex_service)
        llm_pre_node = LLMPreAnalysisNode(self.llm_service)
        consolidation_node = PatternConsolidationNode(self.pattern_library_service)
        expected_impl_node = ExpectedImplementationNode(self.cocoindex_service)
        scanning_node = FileScanningNode()
        evaluation_node = GateEvaluationNode()
        llm_post_node = LLMPostAnalysisNode(self.llm_service, self.cocoindex_service)
        report_node = ReportGenerationNode()
        storage_node = AgenticStorageNode(self.cocoindex_service)
        
        # Build flow
        self.start(checkout_node)
        checkout_node - "success" >> vectorization_node
        vectorization_node - "success" >> llm_pre_node
        llm_pre_node - "success" >> consolidation_node
        consolidation_node - "success" >> expected_impl_node
        expected_impl_node - "success" >> scanning_node
        scanning_node - "success" >> evaluation_node
        evaluation_node - "success" >> llm_post_node
        llm_post_node - "success" >> report_node
        report_node - "success" >> storage_node
    
    async def run_scan(self, repo_url: str, branch: str = "main", 
                      git_token: Optional[str] = None, scan_id: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete scan process"""
        try:
            print("🚀 Starting CodeGates Scan Process")
            print(f"📁 Repository: {repo_url}")
            print(f"🌿 Branch: {branch}")
            
            # Create scan context
            context = ScanContext(
                repo_url=repo_url,
                branch=branch,
                git_token=git_token,
                scan_id=scan_id or f"scan_{int(datetime.now().timestamp())}"
            )
            
            # Add services to context for enhanced reasoning and recommendations
            context.cocoindex_service = self.cocoindex_service
            context.llm_service = self.llm_service
            
            # Run the flow
            result = await self.run_async(context)
            
            # Cleanup common folder
            if context.common_folder:
                self.git_utils.cleanup(context.common_folder)
            
            print("✅ Scan process completed successfully")
            
            return {
                "scan_id": context.scan_id,
                "status": "completed",
                "result": context.report_data.__dict__ if context.report_data else None,
                "metadata": context.metadata,
                "vector_data": context.vector_data
            }
            
        except Exception as e:
            print(f"❌ Scan process failed: {e}")
            
            # Cleanup common folder on error
            if context.common_folder:
                self.git_utils.cleanup(context.common_folder)
            
            return {
                "scan_id": scan_id,
                "status": "failed",
                "error": str(e)
            }
    
    def get_flow_status(self) -> Dict[str, Any]:
        """Get flow status and health"""
        return {
            "flow_type": "CodeGates Scan Flow",
            "steps": 10,
            "services": {
                "cocoindex_service": self.cocoindex_service.health_check()["status"] == "healthy"
            }
        }
