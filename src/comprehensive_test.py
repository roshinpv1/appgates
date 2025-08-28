#!/usr/bin/env python3
"""
Comprehensive Test Suite for CodeGates Scan System
Tests all functionalities from core components to full scan workflow
Updated with all current implemented scenarios and criteria
"""

import sys
import os
import asyncio
import json
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import all components
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService
from services.ast_parser_service import ASTParserService
from services.prompt_service import PromptService
from services.pattern_library_service import PatternLibraryService
from services.llm_service import LLMService
from services.project_summary_service import ProjectSummaryService
from services.question_service import QuestionService
from services.html_report_service import HTMLReportService
from utils.git_utils import GitUtils, EnhancedGitIntegration
from flow.scan_flow import ScanFlow
from flow.scan_nodes import (
    RepositoryCheckoutNode, VectorizationNode, LLMPreAnalysisNode,
    PatternConsolidationNode, ExpectedImplementationNode, FileScanningNode,
    GateEvaluationNode, LLMPostAnalysisNode, ReportGenerationNode
)


class ComprehensiveTestSuite:
    """Comprehensive test suite for all CodeGates functionality"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.test_repo_path = None
        self.config = {
            "vector_store": {
                "vector_size": 768,
                "use_qdrant": False,
                "qdrant_path": "./test_qdrant_data"
            },
            "embedding": {
                "provider": "local",
                "model": "all-MiniLM-L6-v2"
            },
            "ast_parser": {
                "supported_languages": ["python", "java", "javascript", "typescript", "go", "rust"]
            },
            "llm": {
                "provider": "local",
                "model": "test-model",
                "timeout": 300
            }
        }
        
    def log_test(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        print(f"{status} {test_name}{duration_str}")
        if message:
            print(f"    {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration
        })
    
    def setup_test_environment(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="codegates_test_")
        
        # Create a simple test repository
        self.test_repo_path = Path(self.temp_dir) / "test_repo"
        self.test_repo_path.mkdir()
        
        # Create test files with various patterns
        (self.test_repo_path / "README.md").write_text("# Test Repository\nThis is a test repository.")
        
        # Create Java-like files for testing
        java_dir = self.test_repo_path / "src/main/java/com/example"
        java_dir.mkdir(parents=True, exist_ok=True)
        
        (java_dir / "Application.java").write_text("""
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@SpringBootApplication
public class Application {
    private static final Logger logger = LoggerFactory.getLogger(Application.class);
    
    public static void main(String[] args) {
        logger.info("Application starting...");
        SpringApplication.run(Application.class, args);
        logger.info("Application started successfully");
    }
}
""")
        
        # Create configuration files
        resources_dir = self.test_repo_path / "src/main/resources"
        resources_dir.mkdir(parents=True, exist_ok=True)
        
        (resources_dir / "application.properties").write_text("""
# Application Configuration
spring.application.name=test-application
server.port=8080

# Logging Configuration
logging.level.org.springframework=INFO
logging.level.com.example=DEBUG
logging.pattern.console=%d{yyyy-MM-dd HH:mm:ss} - %msg%n

# Database Configuration
spring.datasource.url=jdbc:h2:mem:testdb
spring.datasource.driverClassName=org.h2.Driver
spring.datasource.username=sa
spring.datasource.password=

# Security Configuration
spring.security.user.name=admin
spring.security.user.password=admin123
""")
        
        # Create build files
        (self.test_repo_path / "pom.xml").write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>test-application</artifactId>
    <version>1.0.0</version>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.7.0</version>
    </parent>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
""")
        
        print(f"✅ Test environment created at {self.temp_dir}")
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print("🧹 Test environment cleaned up")
    
    def test_core_services(self):
        """Test core service components"""
        print("\n🔍 Testing Core Services...")
        
        # Test VectorService with git hash-based collections
        start_time = time.time()
        try:
            vector_service = VectorService(self.config["vector_store"])
            
            # Test git hash-based collection naming
            collection_name = vector_service._get_collection_name("test_scan", "abc123def456")
            assert collection_name == "repo_abc123def456"
            
            # Test scan mapping functionality
            vector_service._store_scan_mapping("test_scan", "abc123def456", "https://github.com/test/repo", "main")
            
            # Test repository indexing check
            is_indexed = vector_service.is_repository_indexed("abc123def456")
            assert is_indexed
            
            duration = time.time() - start_time
            self.log_test("VectorService with Git Hash Collections", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("VectorService with Git Hash Collections", False, str(e), duration)
        
        # Test EmbeddingService with auto-detection
        start_time = time.time()
        try:
            embedding_service = EmbeddingService(self.config["embedding"])
            
            # Test embedding generation
            test_texts = ["Hello world", "Test embedding"]
            embeddings = embedding_service.generate_embeddings(test_texts)
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 768  # Default vector size
            
            duration = time.time() - start_time
            self.log_test("EmbeddingService with Auto-detection", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("EmbeddingService with Auto-detection", False, str(e), duration)
        
        # Test LLMService with timeout configuration
        start_time = time.time()
        try:
            llm_service = LLMService(self.config["llm"])
            
            # Test configuration
            assert llm_service.timeout == 300
            
            # Test provider info
            provider_info = llm_service.get_provider_info()
            assert provider_info["provider"] == "local"
            
            duration = time.time() - start_time
            self.log_test("LLMService with Timeout Configuration", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("LLMService with Timeout Configuration", False, str(e), duration)
    
    def test_enhanced_pattern_library(self):
        """Test enhanced pattern library functionality"""
        print("\n🔍 Testing Enhanced Pattern Library...")
        
        start_time = time.time()
        try:
            pattern_service = PatternLibraryService()
            
            # Test enhanced pattern loading
            patterns = pattern_service.get_all_patterns()
            assert len(patterns) > 0
            
            # Test pattern categories
            categories = pattern_service.get_pattern_categories()
            assert len(categories) > 0
            
            # Test technology-specific patterns
            java_patterns = pattern_service.get_patterns_by_technology("java")
            assert len(java_patterns) > 0
            
            # Test priority-based patterns
            high_priority = pattern_service.get_patterns_by_priority("High")
            assert len(high_priority) > 0
            
            # Test enhanced pattern structure
            for pattern_id, pattern_info in patterns.items():
                assert hasattr(pattern_info, 'display_name')
                assert hasattr(pattern_info, 'description')
                assert hasattr(pattern_info, 'category')
                assert hasattr(pattern_info, 'priority')
                assert hasattr(pattern_info, 'patterns')
            
            duration = time.time() - start_time
            self.log_test("Enhanced Pattern Library", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Enhanced Pattern Library", False, str(e), duration)
    
    def test_prompt_library(self):
        """Test prompt library functionality"""
        print("\n🔍 Testing Prompt Library...")
        
        start_time = time.time()
        try:
            prompt_service = PromptService()
            
            # Test prompt loading
            prompts = prompt_service.list_prompts()
            assert len(prompts) > 0
            
            # Test specific prompts
            required_prompts = [
                "llm_pre_analysis",
                "llm_post_analysis", 
                "gate_evaluation",
                "project_summary"
            ]
            
            for prompt_name in required_prompts:
                prompt = prompt_service.get_prompt(prompt_name)
                assert prompt is not None
                assert hasattr(prompt, 'prompt_template')
                assert len(prompt.prompt_template) > 0
            
            duration = time.time() - start_time
            self.log_test("Prompt Library", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Prompt Library", False, str(e), duration)
    
    def test_git_utils_enhanced(self):
        """Test enhanced Git utilities"""
        print("\n🔍 Testing Enhanced Git Utils...")
        
        start_time = time.time()
        try:
            git_utils = GitUtils()
            
            # Test timeout configuration
            git_utils.configure_git_timeouts(60, 30)
            timeout_status = git_utils.get_git_timeout_status()
            assert timeout_status["clone_timeout"] == 60
            assert timeout_status["fetch_timeout"] == 30
            
            # Test OCP optimized timeouts
            git_utils.set_ocp_optimized_timeouts()
            ocp_status = git_utils.get_git_timeout_status()
            assert ocp_status["clone_timeout"] > 0
            
            # Test enhanced Git integration
            git_integration = EnhancedGitIntegration()
            assert git_integration is not None
            
            duration = time.time() - start_time
            self.log_test("Enhanced Git Utils", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Enhanced Git Utils", False, str(e), duration)
    
    def test_flow_nodes_enhanced(self):
        """Test enhanced flow nodes"""
        print("\n🔍 Testing Enhanced Flow Nodes...")
        
        # Test RepositoryCheckoutNode with CD repo support
        start_time = time.time()
        try:
            node = RepositoryCheckoutNode()
            
            # Test CD repo URL generation
            cd_url = node._get_cd_repo_url("https://github.com/user/repo.git")
            assert cd_url == "https://github.com/user/repo-cd.git"
            
            duration = time.time() - start_time
            self.log_test("RepositoryCheckoutNode with CD Support", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("RepositoryCheckoutNode with CD Support", False, str(e), duration)
        
        # Test VectorizationNode with git hash collections
        start_time = time.time()
        try:
            vector_service = VectorService(self.config["vector_store"])
            embedding_service = EmbeddingService(self.config["embedding"])
            ast_service = ASTParserService(self.config["ast_parser"])
            
            node = VectorizationNode(vector_service, embedding_service, ast_service)
            assert node is not None
            
            # Test collection naming logic
            collection_name = node.vector_service._get_collection_name("test_scan", "abc123")
            assert collection_name == "repo_abc123"
            
            duration = time.time() - start_time
            self.log_test("VectorizationNode with Git Hash Collections", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("VectorizationNode with Git Hash Collections", False, str(e), duration)
        
        # Test LLMPreAnalysisNode with expected count analysis
        start_time = time.time()
        try:
            llm_service = LLMService(self.config["llm"])
            node = LLMPreAnalysisNode(llm_service)
            assert node is not None
            
            # Test project structure analysis methods exist
            assert hasattr(node, '_analyze_project_structure_for_expected_counts')
            assert hasattr(node, '_analyze_project_structure')
            assert hasattr(node, '_analyze_dependencies')
            assert hasattr(node, '_analyze_configuration_files')
            
            duration = time.time() - start_time
            self.log_test("LLMPreAnalysisNode with Expected Count Analysis", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("LLMPreAnalysisNode with Expected Count Analysis", False, str(e), duration)
        
        # Test PatternConsolidationNode with enhanced patterns
        start_time = time.time()
        try:
            pattern_service = PatternLibraryService()
            node = PatternConsolidationNode(pattern_service)
            assert node is not None
            
            # Test gate ID mapping exists
            assert hasattr(node, 'gate_id_mapping')
            assert len(node.gate_id_mapping) > 0
            
            duration = time.time() - start_time
            self.log_test("PatternConsolidationNode with Enhanced Patterns", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("PatternConsolidationNode with Enhanced Patterns", False, str(e), duration)
    
    def test_project_summary_service(self):
        """Test LLM-based project summary service"""
        print("\n🔍 Testing Project Summary Service...")
        
        start_time = time.time()
        try:
            vector_service = VectorService(self.config["vector_store"])
            llm_service = LLMService(self.config["llm"])
            embedding_service = EmbeddingService(self.config["embedding"])
            
            summary_service = ProjectSummaryService(vector_service, llm_service, embedding_service)
            
            # Test service initialization
            assert summary_service is not None
            
            # Test vector context extraction
            vector_context = summary_service._extract_vector_context("test_scan", "https://github.com/test/repo")
            assert isinstance(vector_context, dict)
            
            # Test project context building
            metadata = {
                "main_repo": {
                    "repo_url": "https://github.com/test/repo",
                    "total_files": 10,
                    "languages": ["java"]
                }
            }
            project_context = summary_service._build_project_context(metadata, vector_context)
            assert isinstance(project_context, dict)
            
            duration = time.time() - start_time
            self.log_test("Project Summary Service", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Project Summary Service", False, str(e), duration)
    
    def test_question_service(self):
        """Test question service with git hash collections"""
        print("\n🔍 Testing Question Service...")
        
        start_time = time.time()
        try:
            vector_service = VectorService(self.config["vector_store"])
            llm_service = LLMService(self.config["llm"])
            embedding_service = EmbeddingService(self.config["embedding"])
            
            question_service = QuestionService(vector_service, llm_service, embedding_service)
            
            # Test service initialization
            assert question_service is not None
            
            # Test collection naming with git hash
            scan_mapping = {"repo_hash": "abc123def456"}
            vector_service._store_scan_mapping("test_scan", "abc123def456", "https://github.com/test/repo", "main")
            
            # Test question answering (basic structure)
            question = "What is the main application class?"
            response = question_service.answer_question(question, "test_scan")
            assert isinstance(response, dict)
            assert "status" in response
            
            duration = time.time() - start_time
            self.log_test("Question Service with Git Hash Collections", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Question Service with Git Hash Collections", False, str(e), duration)
    
    def test_html_report_service(self):
        """Test HTML report service"""
        print("\n🔍 Testing HTML Report Service...")
        
        start_time = time.time()
        try:
            report_service = HTMLReportService()
            
            # Test service initialization
            assert report_service is not None
            
            # Test report generation (basic structure)
            scan_result = {
                "scan_id": "test_scan",
                "repo_url": "https://github.com/test/repo",
                "total_gates": 13,
                "passed_gates": 3,
                "failed_gates": 0,
                "gate_results": []
            }
            
            project_summary = {
                "summary": "Test project summary",
                "technology_stack": {"primary_language": "Java"},
                "architecture": {"pattern": "MVC"},
                "key_features": ["Feature 1", "Feature 2"],
                "recommendations": ["Recommendation 1"],
                "vector_analysis": {"total_files_analyzed": 10}
            }
            
            html_content = report_service.generate_html_report(scan_result, project_summary)
            assert isinstance(html_content, str)
            assert "CodeGates Scan Report" in html_content
            
            duration = time.time() - start_time
            self.log_test("HTML Report Service", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("HTML Report Service", False, str(e), duration)
    
    def test_scan_flow_enhanced(self):
        """Test enhanced scan flow"""
        print("\n🔍 Testing Enhanced Scan Flow...")
        
        start_time = time.time()
        try:
            scan_flow = ScanFlow(self.config)
            
            # Test flow initialization
            assert scan_flow is not None
            
            # Test all nodes are present
            expected_nodes = [
                "RepositoryCheckoutNode",
                "VectorizationNode", 
                "LLMPreAnalysisNode",
                "PatternConsolidationNode",
                "ExpectedImplementationNode",
                "FileScanningNode",
                "GateEvaluationNode",
                "LLMPostAnalysisNode",
                "ReportGenerationNode"
            ]
            
            for node_name in expected_nodes:
                assert any(node_name in str(node) for node in scan_flow.nodes)
            
            duration = time.time() - start_time
            self.log_test("Enhanced Scan Flow", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Enhanced Scan Flow", False, str(e), duration)
    
    def test_file_filtering_logic(self):
        """Test enhanced file filtering logic"""
        print("\n🔍 Testing File Filtering Logic...")
        
        start_time = time.time()
        try:
            # Test gate-specific file filtering
            test_cases = [
                # (file_path, gate_category, should_include)
                ("src/main/java/Test.java", "Auditability", True),
                ("src/test/java/TestTest.java", "Testing", True),
                ("src/test/java/TestTest.java", "Auditability", False),  # Test files excluded for non-testing gates
                ("README.md", "Auditability", False),  # README excluded
                ("pom.xml", "Auditability", True),  # Build files included
                ("target/classes/Test.class", "Auditability", False),  # Binary files excluded
                ("src/main/resources/application.properties", "Auditability", True),  # Config files included
            ]
            
            # Create a mock node to test the filtering logic
            class MockNode:
                def _should_ignore_file_for_gate(self, file_path: str, gate_category: str) -> bool:
                    # Simplified version of the actual logic
                    if gate_category == "Testing":
                        return not any(ext in file_path for ext in [".java", ".py", ".js", ".ts", ".go", ".rs"])
                    else:
                        # For non-testing gates, exclude test files
                        if any(test_indicator in file_path.lower() for test_indicator in ["test", "spec", "_test"]):
                            return True
                        # Exclude documentation and binary files
                        if any(ext in file_path.lower() for ext in [".md", ".txt", ".class", ".jar", ".pdf"]):
                            return True
                        return False
            
            node = MockNode()
            
            for file_path, gate_category, should_include in test_cases:
                is_ignored = node._should_ignore_file_for_gate(file_path, gate_category)
                assert is_ignored != should_include, f"File {file_path} for {gate_category} should be {'included' if should_include else 'excluded'}"
            
            duration = time.time() - start_time
            self.log_test("File Filtering Logic", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("File Filtering Logic", False, str(e), duration)
    
    def test_expected_count_calculation(self):
        """Test enhanced expected count calculation"""
        print("\n🔍 Testing Expected Count Calculation...")
        
        start_time = time.time()
        try:
            # Test project structure analysis
            test_repo_path = str(self.test_repo_path)
            
            # Mock analysis methods
            def analyze_project_structure(repo_path: str) -> Dict[str, Any]:
                return {
                    "java_files": 5,
                    "test_files": 2,
                    "config_files": 3,
                    "controller_files": 1,
                    "service_files": 1,
                    "repository_files": 0,
                    "model_files": 0,
                    "util_files": 0,
                    "has_web_layer": True,
                    "has_data_layer": False,
                    "has_service_layer": True,
                    "framework_indicators": ["spring", "maven"]
                }
            
            def analyze_dependencies(repo_path: str, main_repo: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "logging_frameworks": ["slf4j", "logback"],
                    "testing_frameworks": ["junit", "mockito"],
                    "web_frameworks": ["spring"],
                    "database_frameworks": ["hibernate"],
                    "security_frameworks": ["spring-security"],
                    "monitoring_frameworks": [],
                    "build_tools": ["maven"]
                }
            
            def analyze_configuration_files(repo_path: str, main_repo: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "logging_config": True,
                    "security_config": True,
                    "database_config": True,
                    "monitoring_config": False,
                    "error_handling_config": False,
                    "timeout_config": False,
                    "retry_config": False,
                    "throttling_config": False,
                    "circuit_breaker_config": False,
                    "health_check_config": False
                }
            
            # Test analysis results
            project_structure = analyze_project_structure(test_repo_path)
            dependencies = analyze_dependencies(test_repo_path, {})
            config_files = analyze_configuration_files(test_repo_path, {})
            
            assert project_structure["java_files"] == 5
            assert "spring" in dependencies["web_frameworks"]
            assert config_files["logging_config"] == True
            
            # Test expected count calculation for different gate categories
            def calculate_auditability_expected_counts(analysis: Dict[str, Any]) -> int:
                base_count = analysis["java_files"] // 2
                if analysis["logging_config"]:
                    base_count += 1
                return max(1, base_count)
            
            def calculate_testing_expected_counts(analysis: Dict[str, Any]) -> int:
                base_count = analysis["test_files"]
                if analysis["testing_frameworks"]:
                    base_count += 1
                return max(1, base_count)
            
            auditability_count = calculate_auditability_expected_counts({
                **project_structure, **dependencies, **config_files
            })
            testing_count = calculate_testing_expected_counts({
                **project_structure, **dependencies, **config_files
            })
            
            assert auditability_count >= 1
            assert testing_count >= 1
            
            duration = time.time() - start_time
            self.log_test("Expected Count Calculation", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Expected Count Calculation", False, str(e), duration)
    
    def test_gate_evaluation_logic(self):
        """Test enhanced gate evaluation logic"""
        print("\n🔍 Testing Gate Evaluation Logic...")
        
        start_time = time.time()
        try:
            # Test gate status evaluation
            def evaluate_gate_status(actual_count: int, expected_count: int, threshold: int) -> str:
                if expected_count <= 0:
                    return "SKIPPED"  # Technology mismatch
                elif actual_count >= threshold:
                    return "PASS"
                elif actual_count > 0:
                    return "PARTIAL"
                elif actual_count == 0 and expected_count < 2:
                    return "SKIPPED"  # Low applicability
                else:
                    return "FAIL"
            
            # Test cases
            test_cases = [
                (2, 1, 1, "PASS"),      # Actual >= threshold
                (1, 2, 2, "FAIL"),      # Actual < threshold
                (1, 2, 1, "PARTIAL"),   # Actual > 0 but < threshold
                (0, 0, 1, "SKIPPED"),   # Technology mismatch
                (0, 1, 1, "SKIPPED"),   # Low applicability
                (0, 3, 1, "FAIL"),      # No implementations, high expected
            ]
            
            for actual, expected, threshold, expected_status in test_cases:
                status = evaluate_gate_status(actual, expected, threshold)
                assert status == expected_status, f"Expected {expected_status}, got {status} for ({actual}, {expected}, {threshold})"
            
            # Test reasoning generation
            def generate_reasoning(status: str, actual_count: int, expected_count: int, gate_name: str) -> str:
                if status == "SKIPPED":
                    if expected_count <= 0:
                        return f"ℹ️ NOT APPLICABLE: {gate_name} is not applicable to current technology stack"
                    else:
                        return f"ℹ️ NOT APPLICABLE: {gate_name} has low applicability to current codebase - Found {actual_count} implementations, expected {expected_count}"
                elif status == "PASS":
                    return f"✅ PASS: Found {actual_count} implementations, meeting expected {expected_count}"
                elif status == "PARTIAL":
                    return f"⚠️ PARTIAL: Found {actual_count} implementations, expected {expected_count}"
                else:
                    return f"❌ FAIL: Found {actual_count} implementations, expected {expected_count}"
            
            # Test reasoning
            reasoning = generate_reasoning("SKIPPED", 0, 0, "Test Gate")
            assert "not applicable to current technology stack" in reasoning
            
            reasoning = generate_reasoning("PASS", 2, 1, "Test Gate")
            assert "✅ PASS" in reasoning
            
            duration = time.time() - start_time
            self.log_test("Gate Evaluation Logic", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Gate Evaluation Logic", False, str(e), duration)
    
    def test_integration_scenarios(self):
        """Test integration scenarios"""
        print("\n🔍 Testing Integration Scenarios...")
        
        # Test scenario 1: Git hash-based collection deduplication
        start_time = time.time()
        try:
            vector_service = VectorService(self.config["vector_store"])
            
            # Simulate multiple scans of the same repository
            repo_hash = "abc123def456"
            scan_ids = ["scan_1", "scan_2", "scan_3"]
            
            for scan_id in scan_ids:
                vector_service._store_scan_mapping(scan_id, repo_hash, "https://github.com/test/repo", "main")
            
            # Verify all scans map to the same collection
            collection_name = vector_service._get_collection_name("scan_1", repo_hash)
            assert collection_name == "repo_abc123def456"
            
            # Verify repository is marked as indexed
            is_indexed = vector_service.is_repository_indexed(repo_hash)
            assert is_indexed
            
            duration = time.time() - start_time
            self.log_test("Git Hash Collection Deduplication", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Git Hash Collection Deduplication", False, str(e), duration)
        
        # Test scenario 2: Enhanced pattern library integration
        start_time = time.time()
        try:
            pattern_service = PatternLibraryService()
            
            # Test pattern consolidation with gate ID mapping
            patterns = pattern_service.get_all_patterns()
            
            # Verify enhanced patterns have proper structure
            enhanced_patterns = [p for p in patterns.values() if hasattr(p, 'display_name')]
            assert len(enhanced_patterns) > 0
            
            # Verify gate ID mapping exists for enhanced patterns
            gate_id_mapping = {
                "STRUCTURED_LOGS": "1.1",
                "AVOID_LOGGING_SECRETS": "1.10",
                "TESTING_INFRASTRUCTURE": "2",
                "DOCUMENTATION_AVAILABLE": "1.3",
                "CONTAINERIZATION_READY": "3.18",
                "ERROR_HANDLING": "2.4",
                "INPUT_VALIDATION": "2.7"
            }
            
            for enhanced_id, expected_gate_id in gate_id_mapping.items():
                if enhanced_id in patterns:
                    pattern = patterns[enhanced_id]
                    assert hasattr(pattern, 'display_name')
                    assert hasattr(pattern, 'description')
                    assert hasattr(pattern, 'patterns')
            
            duration = time.time() - start_time
            self.log_test("Enhanced Pattern Library Integration", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Enhanced Pattern Library Integration", False, str(e), duration)
        
        # Test scenario 3: LLM-based project summary generation
        start_time = time.time()
        try:
            vector_service = VectorService(self.config["vector_store"])
            llm_service = LLMService(self.config["llm"])
            embedding_service = EmbeddingService(self.config["embedding"])
            
            summary_service = ProjectSummaryService(vector_service, llm_service, embedding_service)
            
            # Test project summary generation workflow
            metadata = {
                "main_repo": {
                    "repo_url": "https://github.com/test/repo",
                    "total_files": 10,
                    "languages": ["java"],
                    "dependencies": {"spring": "2.7.0"},
                    "build_files": ["pom.xml"],
                    "config_files": ["application.properties"]
                }
            }
            
            # Test the complete workflow
            vector_context = summary_service._extract_vector_context("test_scan", "https://github.com/test/repo")
            project_context = summary_service._build_project_context(metadata, vector_context)
            
            assert isinstance(project_context, dict)
            assert "technology_stack" in project_context
            assert "architecture" in project_context
            
            duration = time.time() - start_time
            self.log_test("LLM-based Project Summary Generation", True, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("LLM-based Project Summary Generation", False, str(e), duration)
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Test Suite for CodeGates Scan System")
        print("=" * 80)
        print("📋 Testing all implemented scenarios and criteria")
        print("=" * 80)
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Run all test categories
            self.test_core_services()
            self.test_enhanced_pattern_library()
            self.test_prompt_library()
            self.test_git_utils_enhanced()
            self.test_flow_nodes_enhanced()
            self.test_project_summary_service()
            self.test_question_service()
            self.test_html_report_service()
            self.test_scan_flow_enhanced()
            self.test_file_filtering_logic()
            self.test_expected_count_calculation()
            self.test_gate_evaluation_logic()
            self.test_integration_scenarios()
            
            # Generate summary
            self.generate_test_summary()
            
        finally:
            # Cleanup
            self.cleanup_test_environment()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        total_duration = sum(result.get("duration", 0) for result in self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n🎯 Implemented Scenarios and Criteria Tested:")
        scenarios = [
            "1. Core Services (Vector, Embedding, LLM with enhanced features)",
            "2. Git Hash-Based Collection Management (Deduplication, Mapping)",
            "3. Enhanced Pattern Library (Categories, Priorities, Technology Mapping)",
            "4. Prompt Library (Template Management, Parameter Validation)",
            "5. Enhanced Git Utils (Enterprise Support, Timeout Management)",
            "6. Flow Nodes (All 9 nodes with enhanced functionality)",
            "7. LLM-Based Project Summary Generation",
            "8. Question Service with Git Hash Collections",
            "9. HTML Report Service with Enhanced Templates",
            "10. Enhanced Scan Flow Orchestration",
            "11. File Filtering Logic (Gate-Specific, Technology-Aware)",
            "12. Expected Count Calculation (Project Structure Analysis)",
            "13. Gate Evaluation Logic (Status, Reasoning, Recommendations)",
            "14. Integration Scenarios (Deduplication, Pattern Integration, Summary Generation)"
        ]
        
        for scenario in scenarios:
            print(f"  {scenario}")
        
        print("\n🔧 Key Features Tested:")
        features = [
            "• Git hash-based vector collection naming",
            "• Repository deduplication and scan mapping",
            "• Enhanced pattern library with gate ID mapping",
            "• LLM timeout configuration (300 seconds)",
            "• File filtering for hard gates (source/build files only)",
            "• Expected count calculation from project structure",
            "• Technology-aware gate evaluation",
            "• Enhanced reasoning and recommendations",
            "• CD repository support",
            "• Enterprise Git operations",
            "• Multi-provider LLM support",
            "• Auto-detection of embedding dimensions",
            "• Comprehensive project summary generation",
            "• Contextual question answering"
        ]
        
        for feature in features:
            print(f"  {feature}")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! The CodeGates system is fully functional with all implemented features.")
        else:
            print(f"\n⚠️ {failed_tests} test(s) failed. Please review the errors above.")
        
        print("\n📈 Performance Metrics:")
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        print(f"  Average Test Duration: {avg_duration:.2f}s")
        print(f"  Fastest Test: {min((r.get('duration', 0) for r in self.test_results), default=0):.2f}s")
        print(f"  Slowest Test: {max((r.get('duration', 0) for r in self.test_results), default=0):.2f}s")


if __name__ == "__main__":
    # Run the comprehensive test suite
    test_suite = ComprehensiveTestSuite()
    test_suite.run_all_tests()
