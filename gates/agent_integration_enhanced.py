"""
Enhanced CodeGates Agent Integration Module
Bridges existing CodeGates functionality with Google ADK agent capabilities
Includes advanced code analysis and question answering features
"""

import os
import sys
import asyncio
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add agent directory to path for imports
agent_dir = Path(__file__).parent.parent / "agent"
if agent_dir.exists():
    sys.path.insert(0, str(agent_dir))

try:
    from google.adk.agents import Agent
    from google.adk.tools.base_tool import BaseTool
    from google.adk.tools.function_tool import FunctionTool
    from google.adk.tools.agent_tool import AgentTool
    from google.adk.runners import InMemoryRunner
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    logger.warning("Google ADK not available. Install with: pip install google-adk")

# Import existing CodeGates functionality
try:
    from .utils.hard_gates import HARD_GATES, get_gate_number
    from .utils.git_operations import clone_repository, cleanup_repository
    from .utils.file_scanner import scan_directory
    from .criteria_evaluator import EnhancedGateEvaluator
    from .utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig
    from .advanced_llm.core import AdvancedLLMService
    
    # Optional integrations
    try:
        from .utils.splunk_integration import execute_splunk_query
    except ImportError:
        execute_splunk_query = None
        
    try:
        from .utils.appdynamics_integration import analyze_appdynamics_coverage
    except ImportError:
        analyze_appdynamics_coverage = None
        
    try:
        from .utils.playwright_integration import collect_web_portal_evidence
    except ImportError:
        collect_web_portal_evidence = None
    
    CODEGATES_AVAILABLE = True
except ImportError as e:
    CODEGATES_AVAILABLE = False
    logger.warning(f"CodeGates functionality not available: {e}")

# Import agent functionality
AGENT_AVAILABLE = False
try:
    # Only try to import if the agent directory exists and has the required files
    agent_dir = Path(__file__).parent.parent / "agent"
    if agent_dir.exists() and (agent_dir / "codegates_agent.py").exists():
        from agent.codegates_agent import create_codegates_runner, root_agent
        from agent.litellm_config import setup_litellm_environment, LiteLLMConfig
        AGENT_AVAILABLE = True
        logger.info("✅ Agent functionality imported successfully")
    else:
        logger.info("ℹ️ Agent directory or files not found - agent functionality disabled")
except ImportError as e:
    logger.warning(f"Agent functionality not available: {e}")
except Exception as e:
    logger.warning(f"Unexpected error importing agent functionality: {e}")


# =============================================================================
# ENHANCED AGENT TOOLS FOR CODE ANALYSIS AND QUESTION ANSWERING
# =============================================================================

class CodeAnalysisTool(BaseTool):
    """Tool for analyzing code using advanced LLM service capabilities"""
    
    name = "analyze_code"
    description = "Analyze code using advanced indexing, metadata extraction, and context retrieval"
    
    def __init__(self, advanced_llm_service):
        super().__init__(name=self.name, description=self.description)
        self.advanced_llm_service = advanced_llm_service
    
    async def run_async(self, args: dict, tool_context) -> dict:
        """Analyze code using advanced capabilities"""
        try:
            repo_url = args["repo_url"]
            branch = args.get("branch", "main")
            github_token = args.get("github_token")
            
            print(f"🔍 Analyzing code for repository: {repo_url}")
            
            if not self.advanced_llm_service:
                return {
                    "status": "error",
                    "message": "Advanced LLM Service not available",
                    "data": None
                }
            
            # Index repository with enhanced metadata
            index_result = self.advanced_llm_service.index_repository(
                repo_url=repo_url,
                branch=branch,
                github_token=github_token
            )
            
            if index_result.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Failed to index repository: {index_result.get('error', 'Unknown error')}",
                    "data": None
                }
            
            repo_id = index_result["repo_id"]
            
            return {
                "status": "success",
                "repo_id": repo_id,
                "index_result": index_result,
                "message": f"Successfully indexed repository with enhanced metadata. Repo ID: {repo_id}",
                "capabilities": {
                    "context_retrieval": True,
                    "question_answering": True,
                    "enhanced_metadata": True,
                    "pattern_library": True
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing code: {str(e)}",
                "data": None
            }


class QuestionAnsweringTool(BaseTool):
    """Tool for asking questions about indexed repositories"""
    
    name = "ask_question"
    description = "Ask questions about indexed repositories using advanced context retrieval and LLM capabilities"
    
    def __init__(self, advanced_llm_service):
        super().__init__(name=self.name, description=self.description)
        self.advanced_llm_service = advanced_llm_service
    
    async def run_async(self, args: dict, tool_context) -> dict:
        """Ask questions about indexed repositories"""
        try:
            repo_id = args["repo_id"]
            question = args["question"]
            max_chunks = args.get("max_chunks", 8)
            cursor_context = args.get("cursor_context")
            
            print(f"❓ Asking question about repo {repo_id}: {question}")
            
            if not self.advanced_llm_service:
                return {
                    "status": "error",
                    "message": "Advanced LLM Service not available",
                    "data": None
                }
            
            # Get context for the question
            context_result = self.advanced_llm_service.get_context(
                repo_id=repo_id,
                query=question,
                cursor_context=cursor_context,
                max_chunks=max_chunks
            )
            
            # Generate answer using context
            answer_result = await self.advanced_llm_service.complete_with_context(
                repo_id=repo_id,
                instruction=question,
                context_result=context_result,
                mode="chat"
            )
            
            return {
                "status": "success",
                "question": question,
                "answer": answer_result.get("content", ""),
                "context_used": {
                    "chunks_retrieved": len(context_result.get("chunks", [])),
                    "retrieval_time_ms": context_result.get("retrieval_time_ms", 0),
                    "llm_time_ms": answer_result.get("llm_time_ms", 0),
                    "total_tokens": answer_result.get("total_tokens", 0)
                },
                "metadata": {
                    "repo_id": repo_id,
                    "provider": answer_result.get("provider", "unknown"),
                    "mode": answer_result.get("mode", "chat")
                },
                "message": f"Successfully answered question using {len(context_result.get('chunks', []))} context chunks"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error answering question: {str(e)}",
                "data": None
            }


class CodeSearchTool(BaseTool):
    """Tool for searching code using enhanced metadata and vector search"""
    
    name = "search_code"
    description = "Search code using semantic search, file metadata, and enhanced indexing capabilities"
    
    def __init__(self, advanced_llm_service):
        super().__init__(name=self.name, description=self.description)
        self.advanced_llm_service = advanced_llm_service
    
    async def run_async(self, args: dict, tool_context) -> dict:
        """Search code using advanced capabilities"""
        try:
            repo_id = args["repo_id"]
            search_query = args["search_query"]
            search_type = args.get("search_type", "semantic")  # semantic, keyword, metadata
            max_results = args.get("max_results", 10)
            file_types = args.get("file_types", [])  # Filter by file types
            min_score = args.get("min_score", 0.5)
            
            print(f"🔍 Searching code in repo {repo_id}: {search_query}")
            
            if not self.advanced_llm_service:
                return {
                    "status": "error",
                    "message": "Advanced LLM Service not available",
                    "data": None
                }
            
            # Get context with search parameters
            context_result = self.advanced_llm_service.get_context(
                repo_id=repo_id,
                query=search_query,
                max_chunks=max_results
            )
            
            # Filter results based on search criteria
            filtered_chunks = []
            for chunk in context_result.get("chunks", []):
                # Apply file type filter
                if file_types:
                    chunk_file_type = chunk.get("file_extension", "").lower()
                    if chunk_file_type not in [ft.lower() for ft in file_types]:
                        continue
                
                # Apply score filter
                if chunk.get("score", 0) < min_score:
                    continue
                
                filtered_chunks.append(chunk)
            
            # Extract metadata from chunks
            file_metadata = {}
            for chunk in filtered_chunks:
                file_path = chunk.get("file_path", "unknown")
                if file_path not in file_metadata:
                    file_metadata[file_path] = {
                        "filename": chunk.get("filename", "unknown"),
                        "relative_path": chunk.get("relative_path", "unknown"),
                        "file_extension": chunk.get("file_extension", "unknown"),
                        "file_size": chunk.get("file_size", 0),
                        "total_lines": chunk.get("total_lines", 0),
                        "is_binary": chunk.get("is_binary", False),
                        "file_type": chunk.get("file_type", "unknown"),
                        "encoding": chunk.get("encoding", "unknown"),
                        "git_status": chunk.get("git_status", "unknown"),
                        "complexity_score": chunk.get("complexity_score", 0),
                        "chunks": []
                    }
                file_metadata[file_path]["chunks"].append({
                    "content": chunk.get("content", ""),
                    "start_line": chunk.get("start_line", 0),
                    "end_line": chunk.get("end_line", 0),
                    "score": chunk.get("score", 0)
                })
            
            return {
                "status": "success",
                "search_query": search_query,
                "search_type": search_type,
                "results": {
                    "total_chunks": len(filtered_chunks),
                    "total_files": len(file_metadata),
                    "file_metadata": file_metadata,
                    "chunks": filtered_chunks
                },
                "search_metadata": {
                    "repo_id": repo_id,
                    "max_results": max_results,
                    "file_types_filter": file_types,
                    "min_score": min_score,
                    "retrieval_time_ms": context_result.get("retrieval_time_ms", 0)
                },
                "message": f"Found {len(filtered_chunks)} code chunks across {len(file_metadata)} files"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error searching code: {str(e)}",
                "data": None
            }


class PatternAnalysisTool(BaseTool):
    """Tool for analyzing code against pattern library and quality gates"""
    
    name = "analyze_patterns"
    description = "Analyze code against pattern library and identify quality issues"
    
    def __init__(self, advanced_llm_service):
        super().__init__(name=self.name, description=self.description)
        self.advanced_llm_service = advanced_llm_service
    
    async def run_async(self, args: dict, tool_context) -> dict:
        """Analyze code against patterns"""
        try:
            repo_id = args["repo_id"]
            analysis_type = args.get("analysis_type", "quality")  # quality, security, performance
            specific_patterns = args.get("patterns", [])  # Specific patterns to check
            
            print(f"🔍 Analyzing patterns for repo {repo_id}: {analysis_type}")
            
            if not self.advanced_llm_service:
                return {
                    "status": "error",
                    "message": "Advanced LLM Service not available",
                    "data": None
                }
            
            # Get relevant patterns for the analysis
            pattern_query = f"{analysis_type} code quality patterns"
            if specific_patterns:
                pattern_query = f"patterns: {', '.join(specific_patterns)}"
            
            # Get context with pattern analysis
            context_result = self.advanced_llm_service.get_context(
                repo_id=repo_id,
                query=pattern_query,
                max_chunks=12
            )
            
            # Generate pattern analysis
            analysis_result = await self.advanced_llm_service.complete_with_context(
                repo_id=repo_id,
                instruction=f"Analyze the code for {analysis_type} issues and provide specific recommendations based on code quality patterns. Identify potential problems and suggest improvements.",
                context_result=context_result,
                mode="chat"
            )
            
            return {
                "status": "success",
                "analysis_type": analysis_type,
                "analysis_result": analysis_result.get("content", ""),
                "patterns_used": {
                    "query": pattern_query,
                    "chunks_analyzed": len(context_result.get("chunks", [])),
                    "context_time_ms": context_result.get("retrieval_time_ms", 0),
                    "analysis_time_ms": analysis_result.get("llm_time_ms", 0)
                },
                "metadata": {
                    "repo_id": repo_id,
                    "specific_patterns": specific_patterns,
                    "total_tokens": analysis_result.get("total_tokens", 0)
                },
                "message": f"Successfully analyzed code for {analysis_type} patterns using {len(context_result.get('chunks', []))} context chunks"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing patterns: {str(e)}",
                "data": None
            }


class EnhancedCodeGatesAgentIntegration:
    """
    Enhanced integration layer between CodeGates and Google ADK agent functionality
    Includes advanced code analysis and question answering capabilities
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.advanced_llm_service = None
        self.agent_runner = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize CodeGates and Agent services"""
        try:
            # Initialize Advanced LLM Service if available
            if CODEGATES_AVAILABLE:
                try:
                    # Use a basic configuration for AdvancedLLMService
                    config = {
                        "retrieval": {"max_chunks": 8},
                        "indexing": {"chunk_size": 800},
                        "llm": {"provider": "local", "model": "llama2"},
                        "vector_store": {"use_qdrant": True, "vector_size": 768},
                        "embedding": {"provider": "local", "model": "text-embedding"},
                        "cache": {"use_redis": False, "max_size": 1000}
                    }
                    self.advanced_llm_service = AdvancedLLMService(config)
                    logger.info("✅ Advanced LLM Service initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Advanced LLM Service: {e}")
                    self.advanced_llm_service = None
            else:
                logger.info("ℹ️ CodeGates functionality not available - Advanced LLM Service disabled")
            
            # Initialize Agent Runner if available
            if AGENT_AVAILABLE and ADK_AVAILABLE:
                try:
                    self.agent_runner = create_codegates_runner()
                    logger.info("✅ Agent Runner initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Agent Runner: {e}")
                    self.agent_runner = None
            else:
                logger.info("ℹ️ Agent functionality not available - Agent Runner disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            # Ensure services are None on error
            self.advanced_llm_service = None
            self.agent_runner = None
    
    def get_enhanced_agent_tools(self) -> List[BaseTool]:
        """Get enhanced agent tools with code analysis capabilities"""
        tools = []
        
        if self.advanced_llm_service:
            tools.extend([
                CodeAnalysisTool(self.advanced_llm_service),
                QuestionAnsweringTool(self.advanced_llm_service),
                CodeSearchTool(self.advanced_llm_service),
                PatternAnalysisTool(self.advanced_llm_service)
            ])
            logger.info(f"✅ Added {len(tools)} enhanced code analysis tools")
        else:
            logger.info("ℹ️ Advanced LLM Service not available - enhanced tools disabled")
        
        return tools
    
    async def ask_question_about_repository(
        self,
        repo_url: str,
        question: str,
        branch: str = "main",
        github_token: Optional[str] = None,
        user_id: str = "default_user",
        session_id: str = "default_session"
    ) -> Dict[str, Any]:
        """
        Ask questions about a repository using enhanced code analysis
        """
        try:
            # First, ensure repository is indexed
            if not self.advanced_llm_service:
                return {
                    "status": "error",
                    "message": "Advanced LLM Service not available",
                    "data": None
                }
            
            # Index repository if not already indexed
            index_result = self.advanced_llm_service.index_repository(
                repo_url=repo_url,
                branch=branch,
                github_token=github_token
            )
            
            if index_result.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Failed to index repository: {index_result.get('error', 'Unknown error')}",
                    "data": None
                }
            
            repo_id = index_result["repo_id"]
            
            # Get context for the question
            context_result = self.advanced_llm_service.get_context(
                repo_id=repo_id,
                query=question,
                max_chunks=8
            )
            
            # Generate answer using context
            answer_result = await self.advanced_llm_service.complete_with_context(
                repo_id=repo_id,
                instruction=question,
                context_result=context_result,
                mode="chat"
            )
            
            # If agent is available, also get agent insights
            agent_insights = None
            if AGENT_AVAILABLE and self.agent_runner:
                try:
                    agent_message = {
                        "parts": [{
                            "text": f"Based on the question '{question}' about the repository at {repo_url}, provide additional insights and recommendations."
                        }]
                    }
                    
                    agent_events = []
                    async for event in self.agent_runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=agent_message
                    ):
                        agent_events.append({
                            "type": event.type,
                            "content": getattr(event, 'content', None),
                            "timestamp": getattr(event, 'timestamp', None)
                        })
                    
                    agent_insights = {
                        "events": agent_events,
                        "status": "completed"
                    }
                except Exception as e:
                    logger.warning(f"Agent insights failed: {e}")
                    agent_insights = {"error": str(e)}
            
            return {
                "status": "success",
                "question": question,
                "answer": answer_result.get("content", ""),
                "repo_id": repo_id,
                "context_used": {
                    "chunks_retrieved": len(context_result.get("chunks", [])),
                    "retrieval_time_ms": context_result.get("retrieval_time_ms", 0),
                    "llm_time_ms": answer_result.get("llm_time_ms", 0),
                    "total_tokens": answer_result.get("total_tokens", 0)
                },
                "agent_insights": agent_insights,
                "metadata": {
                    "repo_url": repo_url,
                    "branch": branch,
                    "provider": answer_result.get("provider", "unknown"),
                    "index_status": index_result.get("status", "unknown")
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error asking question: {str(e)}",
                "data": None
            }
    
    async def validate_repository_with_agent(
        self, 
        repo_url: str, 
        branch: str = "main",
        gates: Optional[List[str]] = None,
        user_id: str = "default_user",
        session_id: str = "default_session"
    ) -> Dict[str, Any]:
        """
        Validate repository using both CodeGates and Agent capabilities
        """
        results = {
            "codegates_results": None,
            "agent_results": None,
            "integration_results": None
        }
        
        # Run CodeGates validation (existing functionality)
        if CODEGATES_AVAILABLE and self.advanced_llm_service:
            try:
                results["codegates_results"] = await self._run_codegates_validation(
                    repo_url, branch, gates
                )
            except Exception as e:
                logger.error(f"CodeGates validation failed: {e}")
                results["codegates_results"] = {"error": str(e)}
        
        # Run Agent validation (new functionality)
        if AGENT_AVAILABLE and self.agent_runner:
            try:
                results["agent_results"] = await self._run_agent_validation(
                    repo_url, user_id, session_id
                )
            except Exception as e:
                logger.error(f"Agent validation failed: {e}")
                results["agent_results"] = {"error": str(e)}
        
        # Generate integrated results
        results["integration_results"] = self._integrate_results(
            results["codegates_results"], 
            results["agent_results"]
        )
        
        return results
    
    async def _run_codegates_validation(
        self, 
        repo_url: str, 
        branch: str, 
        gates: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Run validation using existing CodeGates functionality"""
        try:
            # Index repository
            index_result = self.advanced_llm_service.index_repository(repo_url, branch)
            
            if index_result.get("status") == "success":
                repo_id = index_result["repo_id"]
                
                # Run gate validation if gates specified
                gate_results = {}
                if gates:
                    for gate in gates:
                        gate_results[gate] = await self._validate_single_gate(repo_id, gate)
                
                return {
                    "repo_id": repo_id,
                    "index_status": "success",
                    "gate_results": gate_results,
                    "repository_info": index_result
                }
            else:
                return {
                    "index_status": "failed",
                    "error": index_result.get("error", "Unknown error")
                }
                
        except Exception as e:
            logger.error(f"CodeGates validation error: {e}")
            return {"error": str(e)}
    
    async def _run_agent_validation(
        self, 
        repo_url: str, 
        user_id: str, 
        session_id: str
    ) -> Dict[str, Any]:
        """Run validation using Google ADK agent"""
        try:
            user_message = {
                "parts": [{
                    "text": f"Validate the repository at {repo_url} with comprehensive analysis"
                }]
            }
            
            events = []
            async for event in self.agent_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message
            ):
                events.append({
                    "type": event.type,
                    "content": getattr(event, 'content', None),
                    "timestamp": getattr(event, 'timestamp', None)
                })
            
            return {
                "events": events,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Agent validation error: {e}")
            return {"error": str(e)}
    
    async def _validate_single_gate(self, repo_id: str, gate_name: str) -> Dict[str, Any]:
        """Validate a single gate using CodeGates functionality"""
        try:
            # Use existing gate validation logic
            evaluator = EnhancedGateEvaluator()
            result = evaluator.evaluate_gate(gate_name, repo_id)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _integrate_results(
        self, 
        codegates_results: Optional[Dict[str, Any]], 
        agent_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Integrate results from both systems"""
        integration = {
            "summary": {
                "codegates_available": codegates_results is not None,
                "agent_available": agent_results is not None,
                "total_gates_validated": 0,
                "overall_status": "unknown"
            },
            "recommendations": [],
            "combined_analysis": {}
        }
        
        # Process CodeGates results
        if codegates_results and "gate_results" in codegates_results:
            gate_count = len(codegates_results["gate_results"])
            integration["summary"]["total_gates_validated"] += gate_count
            integration["combined_analysis"]["codegates_gates"] = codegates_results["gate_results"]
        
        # Process Agent results
        if agent_results and "events" in agent_results:
            integration["combined_analysis"]["agent_events"] = agent_results["events"]
            
            # Extract recommendations from agent events
            for event in agent_results["events"]:
                if event.get("type") == "content" and event.get("content"):
                    content = event["content"]
                    if isinstance(content, str) and ("recommend" in content.lower() or "suggest" in content.lower()):
                        integration["recommendations"].append(content)
        
        # Determine overall status
        if integration["summary"]["codegates_available"] and integration["summary"]["agent_available"]:
            integration["summary"]["overall_status"] = "comprehensive"
        elif integration["summary"]["codegates_available"]:
            integration["summary"]["overall_status"] = "codegates_only"
        elif integration["summary"]["agent_available"]:
            integration["summary"]["overall_status"] = "agent_only"
        else:
            integration["summary"]["overall_status"] = "none_available"
        
        return integration
    
    def get_available_capabilities(self) -> Dict[str, bool]:
        """Get available capabilities"""
        return {
            "codegates_available": CODEGATES_AVAILABLE,
            "agent_available": AGENT_AVAILABLE,
            "adk_available": ADK_AVAILABLE,
            "advanced_llm_available": self.advanced_llm_service is not None,
            "agent_runner_available": self.agent_runner is not None,
            "enhanced_tools_available": self.advanced_llm_service is not None
        }
    
    async def run_comprehensive_analysis(
        self, 
        repo_url: str, 
        analysis_type: str = "full",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run comprehensive analysis using both systems
        
        Args:
            repo_url: Repository URL to analyze
            analysis_type: Type of analysis ("full", "codegates_only", "agent_only")
            **kwargs: Additional parameters
        """
        if analysis_type == "codegates_only":
            return await self._run_codegates_validation(
                repo_url, 
                kwargs.get("branch", "main"), 
                kwargs.get("gates")
            )
        elif analysis_type == "agent_only":
            return await self._run_agent_validation(
                repo_url,
                kwargs.get("user_id", "default_user"),
                kwargs.get("session_id", "default_session")
            )
        else:  # full
            return await self.validate_repository_with_agent(
                repo_url,
                kwargs.get("branch", "main"),
                kwargs.get("gates"),
                kwargs.get("user_id", "default_user"),
                kwargs.get("session_id", "default_session")
            )


# Convenience functions for easy integration
def create_enhanced_agent_integration(config: Optional[Dict[str, Any]] = None) -> EnhancedCodeGatesAgentIntegration:
    """Create a new enhanced agent integration instance"""
    return EnhancedCodeGatesAgentIntegration(config)


async def ask_question_about_repository(
    repo_url: str,
    question: str,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for asking questions about repositories"""
    integration = create_enhanced_agent_integration(config)
    return await integration.ask_question_about_repository(repo_url, question, **kwargs)


async def validate_repository_integrated(
    repo_url: str,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for repository validation"""
    integration = create_enhanced_agent_integration(config)
    return await integration.validate_repository_with_agent(repo_url, **kwargs)


def get_enhanced_integration_status() -> Dict[str, Any]:
    """Get status of all integration components"""
    integration = create_enhanced_agent_integration()
    return {
        "capabilities": integration.get_available_capabilities(),
        "services_initialized": {
            "advanced_llm": integration.advanced_llm_service is not None,
            "agent_runner": integration.agent_runner is not None
        },
        "enhanced_tools": len(integration.get_enhanced_agent_tools())
    }
