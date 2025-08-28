"""
LLM-Based Project Summary Service

This service provides intelligent project analysis by:
1. Searching vector database for relevant code snippets
2. Using LLM to analyze the codebase and generate insights
3. Providing structured, contextual project summaries
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from services.vector_service import VectorService
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService


class ProjectSummaryService:
    """LLM-based project summary service for intelligent codebase analysis"""
    
    def __init__(self, vector_service: VectorService, llm_service: LLMService, embedding_service: EmbeddingService):
        self.vector_service = vector_service
        self.llm_service = llm_service
        self.embedding_service = embedding_service
    
    async def generate_llm_project_summary(self, repo_url: str, scan_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent project summary using LLM analysis"""
        try:
            print(f"🤖 Generating LLM-based project summary for {repo_url}")
            
            # Step 1: Extract comprehensive context from vector database
            vector_context = await self._extract_vector_context(scan_id, repo_url)
            
            # Step 2: Build comprehensive project context
            project_context = self._build_project_context(metadata, vector_context)
            
            # Step 3: Generate LLM-based summary
            llm_summary = await self._generate_llm_summary(project_context)
            
            # Step 4: Parse and structure the LLM response
            structured_summary = self._parse_llm_summary(llm_summary, vector_context)
            
            print(f"✅ LLM project summary generated successfully")
            return structured_summary
            
        except Exception as e:
            print(f"❌ Failed to generate LLM project summary: {e}")
            return self._get_fallback_summary(repo_url, metadata)
    
    async def _extract_vector_context(self, scan_id: str, repo_url: str) -> Dict[str, Any]:
        """Extract comprehensive context from vector database"""
        try:
            # Get the git hash from scan mapping or use scan_id as fallback
            repo_hash = None
            try:
                scan_mapping = self.vector_service._get_scan_mapping(scan_id)
                if scan_mapping:
                    repo_hash = scan_mapping.get("repo_hash")
            except Exception:
                pass
            
            # Use git hash-based collection naming if available, otherwise fallback to scan_id
            if repo_hash:
                collection = self.vector_service._get_collection_name(scan_id, repo_hash)
            else:
                collection = f"repo_{scan_id}"
            
            # Enhanced queries for comprehensive analysis
            analysis_queries = [
                # Architecture and Structure
                "main application class entry point startup configuration",
                "controller service repository layer architecture",
                "database configuration connection pool datasource",
                "security configuration authentication authorization",
                "logging configuration logback log4j slf4j",
                "testing framework junit mockito test configuration",
                "build configuration maven gradle dependencies",
                "deployment configuration docker kubernetes",
                "monitoring health check actuator metrics",
                "api rest controller endpoint mapping",
                "entity model data structure domain objects",
                "exception handling error management",
                "configuration properties application.yml",
                "development tools setup environment",
                "production deployment infrastructure",
                "microservices architecture patterns",
                "caching configuration redis memcached",
                "message queue configuration kafka rabbitmq",
                "database migration schema versioning",
                "performance optimization configuration"
            ]
            
            all_results = []
            
            for query in analysis_queries:
                try:
                    # Generate embedding for the query
                    query_embedding = self.embedding_service.embed_single(query)
                    
                    if not query_embedding:
                        continue
                    
                    # Search in collection
                    results = self.vector_service.search_similar(
                        collection_name=collection,
                        query_vector=query_embedding,
                        limit=20,
                        score_threshold=0.05
                    )
                    
                    all_results.extend(results)
                    
                except Exception as e:
                    print(f"⚠️ Query '{query}' failed: {e}")
                    continue
            
            # Remove duplicates and organize by file type
            unique_results = self._deduplicate_results(all_results)
            organized_context = self._organize_context_by_type(unique_results)
            
            return organized_context
            
        except Exception as e:
            print(f"❌ Failed to extract vector context: {e}")
            return {}
    
    def _deduplicate_results(self, results: List[Any]) -> List[Any]:
        """Remove duplicate results based on content hash"""
        seen_hashes = set()
        unique_results = []
        
        for result in results:
            content_hash = result.payload.get("content_hash", "")
            if content_hash and content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _organize_context_by_type(self, results: List[Any]) -> Dict[str, Any]:
        """Organize search results by file type and content"""
        organized = {
            "java_files": [],
            "config_files": [],
            "build_files": [],
            "test_files": [],
            "deployment_files": [],
            "documentation_files": [],
            "other_files": []
        }
        
        for result in results:
            file_path = result.payload.get("file_path", "").lower()
            content = result.payload.get("content", "")
            
            if file_path.endswith(".java"):
                organized["java_files"].append({
                    "file_path": result.payload.get("file_path", ""),
                    "content": content[:1000],  # Limit content length
                    "score": result.score
                })
            elif any(ext in file_path for ext in [".properties", ".yml", ".yaml", ".xml"]):
                organized["config_files"].append({
                    "file_path": result.payload.get("file_path", ""),
                    "content": content[:1000],
                    "score": result.score
                })
            elif any(ext in file_path for ext in ["pom.xml", "build.gradle", "package.json"]):
                organized["build_files"].append({
                    "file_path": result.payload.get("file_path", ""),
                    "content": content[:1000],
                    "score": result.score
                })
            elif any(ext in file_path for ext in ["test", "spec", ".test."]):
                organized["test_files"].append({
                    "file_path": result.payload.get("file_path", ""),
                    "content": content[:1000],
                    "score": result.score
                })
            elif any(ext in file_path for ext in ["dockerfile", "docker-compose", "kubernetes", "helm"]):
                organized["deployment_files"].append({
                    "file_path": result.payload.get("file_path", ""),
                    "content": content[:1000],
                    "score": result.score
                })
            elif any(ext in file_path for ext in ["readme", ".md", ".txt"]):
                organized["documentation_files"].append({
                    "file_path": result.payload.get("file_path", ""),
                    "content": content[:1000],
                    "score": result.score
                })
            else:
                organized["other_files"].append({
                    "file_path": result.payload.get("file_path", ""),
                    "content": content[:1000],
                    "score": result.score
                })
        
        return organized
    
    def _build_project_context(self, metadata: Dict[str, Any], vector_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive project context for LLM analysis"""
        main_repo = metadata.get("main_repo", {})
        
        context = {
            "repository_info": {
                "url": main_repo.get("repo_url", ""),
                "branch": main_repo.get("branch", ""),
                "total_files": main_repo.get("total_files", 0),
                "total_lines": main_repo.get("total_lines", 0),
                "languages": main_repo.get("languages", []),
                "commit_hash": main_repo.get("commit_hash", "")
            },
            "file_analysis": {
                "java_files_count": len(vector_context.get("java_files", [])),
                "config_files_count": len(vector_context.get("config_files", [])),
                "build_files_count": len(vector_context.get("build_files", [])),
                "test_files_count": len(vector_context.get("test_files", [])),
                "deployment_files_count": len(vector_context.get("deployment_files", [])),
                "documentation_files_count": len(vector_context.get("documentation_files", []))
            },
            "code_samples": {
                "java_samples": vector_context.get("java_files", [])[:5],  # Top 5 Java files
                "config_samples": vector_context.get("config_files", [])[:3],  # Top 3 config files
                "build_samples": vector_context.get("build_files", [])[:2],  # Top 2 build files
                "deployment_samples": vector_context.get("deployment_files", [])[:2]  # Top 2 deployment files
            },
            "metadata": metadata
        }
        
        return context
    
    async def _generate_llm_summary(self, project_context: Dict[str, Any]) -> str:
        """Generate LLM-based project summary"""
        try:
            # Create comprehensive prompt for LLM analysis
            prompt = self._create_project_analysis_prompt(project_context)
            
            # Call LLM service
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000,
                scan_id="project_summary",
                node_name="ProjectSummaryService"
            )
            
            return response
            
        except Exception as e:
            print(f"❌ LLM summary generation failed: {e}")
            return ""
    
    def _create_project_analysis_prompt(self, project_context: Dict[str, Any]) -> str:
        """Create comprehensive prompt for project analysis"""
        
        repo_info = project_context["repository_info"]
        file_analysis = project_context["file_analysis"]
        code_samples = project_context["code_samples"]
        
        # Build code samples text
        java_samples_text = ""
        for sample in code_samples["java_samples"]:
            java_samples_text += f"\nFile: {sample['file_path']}\nContent: {sample['content'][:500]}...\n"
        
        config_samples_text = ""
        for sample in code_samples["config_samples"]:
            config_samples_text += f"\nFile: {sample['file_path']}\nContent: {sample['content'][:500]}...\n"
        
        build_samples_text = ""
        for sample in code_samples["build_samples"]:
            build_samples_text += f"\nFile: {sample['file_path']}\nContent: {sample['content'][:500]}...\n"
        
        prompt = f"""
You are an expert software architect and code analyst. Analyze the following project and provide a comprehensive, intelligent summary.

CRITICAL: You must respond with ONLY valid JSON. No explanations, no markdown, no other text.

## PROJECT INFORMATION
- Repository: {repo_info['url']}
- Branch: {repo_info['branch']}
- Total Files: {repo_info['total_files']}
- Total Lines: {repo_info['total_lines']}
- Languages: {', '.join(repo_info['languages'])}

## FILE ANALYSIS
- Java Files: {file_analysis['java_files_count']}
- Configuration Files: {file_analysis['config_files_count']}
- Build Files: {file_analysis['build_files_count']}
- Test Files: {file_analysis['test_files_count']}
- Deployment Files: {file_analysis['deployment_files_count']}
- Documentation Files: {file_analysis['documentation_files_count']}

## CODE SAMPLES

### Java Files:
{java_samples_text}

### Configuration Files:
{config_samples_text}

### Build Files:
{build_samples_text}

## ANALYSIS TASK

Based on the code extracts and project structure, provide a comprehensive analysis that includes:

1. **Technology Stack**: Identify the main technologies, frameworks, and tools used
2. **Architecture Patterns**: Analyze the architectural patterns and design principles
3. **Application Type**: Determine if it's a web app, microservice, library, etc.
4. **Key Features**: Identify main functionality and business domain
5. **Development Practices**: Assess testing, logging, security, and deployment practices
6. **Code Quality**: Evaluate code organization, patterns, and maintainability
7. **Infrastructure**: Analyze deployment and infrastructure setup
8. **Dependencies**: Identify key external dependencies and libraries

## OUTPUT FORMAT

Respond with ONLY this JSON structure (no other text):

{{
    "summary": "A comprehensive 2-3 paragraph summary of the project",
    "technology_stack": {{
        "primary_language": "Main programming language",
        "frameworks": ["List of main frameworks"],
        "build_tools": ["Build tools used"],
        "databases": ["Database technologies"],
        "testing_frameworks": ["Testing tools"],
        "deployment_tools": ["Deployment technologies"]
    }},
    "architecture": {{
        "pattern": "Main architectural pattern (MVC, Microservices, etc.)",
        "layers": ["Application layers identified"],
        "design_principles": ["Design principles observed"]
    }},
    "application_type": "Type of application (Web App, API, Library, etc.)",
    "key_features": ["Main features and functionality"],
    "development_practices": {{
        "testing": "Testing approach and coverage",
        "logging": "Logging strategy",
        "security": "Security measures",
        "documentation": "Documentation quality"
    }},
    "code_quality": {{
        "organization": "Code organization assessment",
        "patterns": "Design patterns used",
        "maintainability": "Maintainability assessment"
    }},
    "infrastructure": {{
        "deployment": "Deployment strategy",
        "monitoring": "Monitoring and observability",
        "scalability": "Scalability considerations"
    }},
    "dependencies": {{
        "external": ["Key external dependencies"],
        "internal": ["Internal project structure"]
    }},
    "recommendations": ["3-5 specific recommendations for improvement"]
}}

Provide a detailed, insightful analysis based on the code samples provided. Focus on practical insights that would be valuable for understanding the project's architecture, technology choices, and development practices.

REMEMBER: Respond with ONLY valid JSON. No markdown, no explanations, no other text.
"""
        
        return prompt
    
    def _parse_llm_summary(self, llm_response: str, vector_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure the LLM response"""
        try:
            # Try to parse JSON response
            if llm_response.strip().startswith('{'):
                parsed_response = json.loads(llm_response)
            else:
                # If not JSON, create a structured response from the text
                parsed_response = self._parse_text_response(llm_response)
            
            # Add vector context metadata
            parsed_response["vector_analysis"] = {
                "total_files_analyzed": sum(len(files) for files in vector_context.values()),
                "java_files_analyzed": len(vector_context.get("java_files", [])),
                "config_files_analyzed": len(vector_context.get("config_files", [])),
                "build_files_analyzed": len(vector_context.get("build_files", [])),
                "test_files_analyzed": len(vector_context.get("test_files", [])),
                "deployment_files_analyzed": len(vector_context.get("deployment_files", [])),
                "documentation_files_analyzed": len(vector_context.get("documentation_files", []))
            }
            
            # Add timestamp
            parsed_response["analysis_timestamp"] = datetime.now().isoformat()
            
            return parsed_response
            
        except Exception as e:
            print(f"❌ Failed to parse LLM response: {e}")
            return self._get_fallback_summary("", {})
    
    def _parse_text_response(self, text_response: str) -> Dict[str, Any]:
        """Parse text response into structured format"""
        return {
            "summary": text_response[:1000] + "..." if len(text_response) > 1000 else text_response,
            "technology_stack": {
                "primary_language": "Unknown",
                "frameworks": [],
                "build_tools": [],
                "databases": [],
                "testing_frameworks": [],
                "deployment_tools": []
            },
            "architecture": {
                "pattern": "Unknown",
                "layers": [],
                "design_principles": []
            },
            "application_type": "Unknown",
            "key_features": [],
            "development_practices": {
                "testing": "Unknown",
                "logging": "Unknown",
                "security": "Unknown",
                "documentation": "Unknown"
            },
            "code_quality": {
                "organization": "Unknown",
                "patterns": "Unknown",
                "maintainability": "Unknown"
            },
            "infrastructure": {
                "deployment": "Unknown",
                "monitoring": "Unknown",
                "scalability": "Unknown"
            },
            "dependencies": {
                "external": [],
                "internal": []
            },
            "recommendations": []
        }
    
    def _get_fallback_summary(self, repo_url: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback summary when LLM analysis fails"""
        return {
            "summary": f"Project analysis for {repo_url}. The codebase has been analyzed for compliance with hard gates across auditability, error handling, availability, and testing categories. Detailed analysis results are provided in the gate evaluation sections below.",
            "technology_stack": {
                "primary_language": "Unknown",
                "frameworks": [],
                "build_tools": [],
                "databases": [],
                "testing_frameworks": [],
                "deployment_tools": []
            },
            "architecture": {
                "pattern": "Unknown",
                "layers": [],
                "design_principles": []
            },
            "application_type": "Unknown",
            "key_features": [],
            "development_practices": {
                "testing": "Unknown",
                "logging": "Unknown",
                "security": "Unknown",
                "documentation": "Unknown"
            },
            "code_quality": {
                "organization": "Unknown",
                "patterns": "Unknown",
                "maintainability": "Unknown"
            },
            "infrastructure": {
                "deployment": "Unknown",
                "monitoring": "Unknown",
                "scalability": "Unknown"
            },
            "dependencies": {
                "external": [],
                "internal": []
            },
            "recommendations": [],
            "vector_analysis": {
                "total_files_analyzed": 0,
                "java_files_analyzed": 0,
                "config_files_analyzed": 0,
                "build_files_analyzed": 0,
                "test_files_analyzed": 0,
                "deployment_files_analyzed": 0,
                "documentation_files_analyzed": 0
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
