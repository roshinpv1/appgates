#!/usr/bin/env python3
"""
Test script for Enhanced Expected Count Calculation

This script demonstrates:
1. Project structure analysis for expected counts
2. Dependency analysis for expected counts
3. Configuration file analysis for expected counts
4. Integration with LLM pre-analysis
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from flow.scan_nodes import LLMPreAnalysisNode
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService
from services.ast_parser_service import ASTParserService


class EnhancedExpectedCountTester:
    """Test the enhanced expected count calculation system"""
    
    def __init__(self):
        self.vector_service = VectorService({
            "vector_size": 768,
            "use_qdrant": False  # Use in-memory for testing
        })
        self.embedding_service = EmbeddingService({
            "provider": "local",
            "model": "text-embedding-nomic-embed-text-v1.5-embedding",
            "base_url": "http://localhost:1234",
            "vector_size": 768
        })
        self.ast_parser_service = ASTParserService()
        
        # Create a mock LLM pre-analysis node
        self.llm_pre_analysis_node = LLMPreAnalysisNode(
            self.vector_service, 
            self.embedding_service, 
            self.ast_parser_service
        )
    
    def test_project_structure_analysis(self):
        """Test project structure analysis"""
        print("🧪 Testing Project Structure Analysis...")
        
        # Create mock metadata for a Spring Boot project
        mock_metadata = {
            "main_repo": {
                "local_path": "/tmp/mock_spring_project",
                "repo_url": "https://github.com/user/spring-project",
                "branch": "main",
                "total_files": 150,
                "total_lines": 5000,
                "languages": ["Java", "XML", "YAML"],
                "dependencies": {
                    "spring-boot-starter-web": "2.7.0",
                    "spring-boot-starter-data-jpa": "2.7.0",
                    "spring-boot-starter-security": "2.7.0",
                    "logback": "1.2.11",
                    "junit": "5.8.2"
                },
                "build_files": ["pom.xml", "build.gradle"],
                "config_files": ["application.yml", "logback.xml", "application.properties"]
            }
        }
        
        # Test the analysis methods
        print("\n📁 Testing project structure analysis...")
        structure = self.llm_pre_analysis_node._analyze_project_structure("/tmp/mock_spring_project")
        print(f"Project structure: {json.dumps(structure, indent=2)}")
        
        print("\n📦 Testing dependency analysis...")
        dependencies = self.llm_pre_analysis_node._analyze_dependencies("/tmp/mock_spring_project", mock_metadata["main_repo"])
        print(f"Dependencies: {json.dumps(dependencies, indent=2)}")
        
        print("\n⚙️ Testing configuration analysis...")
        config = self.llm_pre_analysis_node._analyze_configuration_files("/tmp/mock_spring_project", mock_metadata["main_repo"])
        print(f"Configuration: {json.dumps(config, indent=2)}")
    
    def test_expected_count_calculation(self):
        """Test expected count calculation for different gate categories"""
        print("\n🧪 Testing Expected Count Calculation...")
        
        # Mock project structure data
        structure = {
            "total_files": 150,
            "java_files": 80,
            "test_files": 20,
            "config_files": 10,
            "controller_files": 5,
            "service_files": 8,
            "repository_files": 3,
            "model_files": 12,
            "util_files": 4,
            "has_web_layer": True,
            "has_data_layer": True,
            "has_service_layer": True,
            "framework_indicators": ["spring_boot", "maven_or_gradle"]
        }
        
        dependencies = {
            "logging_frameworks": ["logback", "slf4j"],
            "testing_frameworks": ["junit", "mockito"],
            "web_frameworks": ["spring-web"],
            "database_frameworks": ["spring-data", "jpa"],
            "security_frameworks": ["spring-security"],
            "monitoring_frameworks": ["actuator"],
            "build_tools": ["maven"]
        }
        
        config = {
            "logging_config": True,
            "security_config": True,
            "database_config": True,
            "monitoring_config": True,
            "error_handling_config": False,
            "timeout_config": False,
            "retry_config": False,
            "throttling_config": False,
            "circuit_breaker_config": False,
            "health_check_config": True
        }
        
        # Test auditability gates
        print("\n📊 Testing Auditability Gates...")
        auditability_counts = self.llm_pre_analysis_node._calculate_auditability_expected_counts(structure, dependencies, config)
        for gate_id, analysis in auditability_counts.items():
            print(f"  Gate {gate_id}: {analysis['expected_count']} expected - {analysis['reason']}")
        
        # Test error handling gates
        print("\n📊 Testing Error Handling Gates...")
        error_handling_counts = self.llm_pre_analysis_node._calculate_error_handling_expected_counts(structure, dependencies, config)
        for gate_id, analysis in error_handling_counts.items():
            print(f"  Gate {gate_id}: {analysis['expected_count']} expected - {analysis['reason']}")
        
        # Test availability gates
        print("\n📊 Testing Availability Gates...")
        availability_counts = self.llm_pre_analysis_node._calculate_availability_expected_counts(structure, dependencies, config)
        for gate_id, analysis in availability_counts.items():
            print(f"  Gate {gate_id}: {analysis['expected_count']} expected - {analysis['reason']}")
        
        # Test testing gates
        print("\n📊 Testing Testing Gates...")
        testing_counts = self.llm_pre_analysis_node._calculate_testing_expected_counts(structure, dependencies, config)
        for gate_id, analysis in testing_counts.items():
            print(f"  Gate {gate_id}: {analysis['expected_count']} expected - {analysis['reason']}")
    
    def test_integration_with_llm_pre_analysis(self):
        """Test integration with LLM pre-analysis"""
        print("\n🧪 Testing Integration with LLM Pre-Analysis...")
        
        # Create mock metadata
        mock_metadata = {
            "main_repo": {
                "local_path": "/tmp/mock_project",
                "repo_url": "https://github.com/user/test-project",
                "branch": "main",
                "total_files": 100,
                "total_lines": 3000,
                "languages": ["Java"],
                "dependencies": {},
                "build_files": ["pom.xml"],
                "config_files": ["application.yml"]
            }
        }
        
        # Test the full analysis
        print("🔍 Running full project structure analysis...")
        expected_counts = self.llm_pre_analysis_node._analyze_project_structure_for_expected_counts(mock_metadata)
        
        print(f"\n📊 Expected Counts Analysis Results:")
        for gate_id, analysis in expected_counts.items():
            print(f"  Gate {gate_id}: {analysis['expected_count']} expected")
            print(f"    Reason: {analysis['reason']}")
        
        return expected_counts
    
    def test_different_project_types(self):
        """Test expected count calculation for different project types"""
        print("\n🧪 Testing Different Project Types...")
        
        # Test 1: Simple Java project
        print("\n📁 Simple Java Project:")
        simple_structure = {
            "java_files": 10,
            "controller_files": 1,
            "service_files": 2,
            "has_web_layer": True,
            "has_data_layer": False,
            "has_service_layer": True
        }
        simple_dependencies = {
            "logging_frameworks": ["logback"],
            "testing_frameworks": ["junit"],
            "web_frameworks": ["spring-web"]
        }
        simple_config = {
            "logging_config": True,
            "security_config": False,
            "monitoring_config": False
        }
        
        simple_counts = self.llm_pre_analysis_node._calculate_auditability_expected_counts(simple_structure, simple_dependencies, simple_config)
        for gate_id, analysis in simple_counts.items():
            print(f"  Gate {gate_id}: {analysis['expected_count']} expected")
        
        # Test 2: Complex enterprise project
        print("\n📁 Complex Enterprise Project:")
        complex_structure = {
            "java_files": 500,
            "controller_files": 20,
            "service_files": 50,
            "repository_files": 15,
            "has_web_layer": True,
            "has_data_layer": True,
            "has_service_layer": True
        }
        complex_dependencies = {
            "logging_frameworks": ["logback", "log4j", "slf4j"],
            "testing_frameworks": ["junit", "mockito", "spring-test"],
            "web_frameworks": ["spring-web"],
            "database_frameworks": ["spring-data", "jpa", "hibernate"],
            "security_frameworks": ["spring-security"],
            "monitoring_frameworks": ["actuator", "micrometer"]
        }
        complex_config = {
            "logging_config": True,
            "security_config": True,
            "database_config": True,
            "monitoring_config": True,
            "retry_config": True,
            "throttling_config": True,
            "circuit_breaker_config": True,
            "health_check_config": True
        }
        
        complex_counts = self.llm_pre_analysis_node._calculate_auditability_expected_counts(complex_structure, complex_dependencies, complex_config)
        for gate_id, analysis in complex_counts.items():
            print(f"  Gate {gate_id}: {analysis['expected_count']} expected")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Enhanced Expected Count Calculation Tests")
        print("=" * 70)
        
        self.test_project_structure_analysis()
        self.test_expected_count_calculation()
        expected_counts = self.test_integration_with_llm_pre_analysis()
        self.test_different_project_types()
        
        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"Total expected counts calculated: {len(expected_counts)}")
        total_expected = sum(analysis['expected_count'] for analysis in expected_counts.values())
        print(f"Total expected implementations: {total_expected}")
        
        # Show breakdown by category
        categories = {}
        for gate_id, analysis in expected_counts.items():
            category = gate_id.split('.')[0] if '.' in gate_id else 'general'
            if category not in categories:
                categories[category] = 0
            categories[category] += analysis['expected_count']
        
        print(f"\n📈 Breakdown by category:")
        for category, count in categories.items():
            print(f"  Category {category}: {count} expected implementations")


async def main():
    """Main test function"""
    tester = EnhancedExpectedCountTester()
    tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
