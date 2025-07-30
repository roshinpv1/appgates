#!/usr/bin/env python3
"""
Test script for the new criteria-based evaluation system
Demonstrates AND/OR/NOT logic, file patterns, and simplified scoring
"""

import json
import os
from typing import Dict, List, Any
from gates.criteria_evaluator import EnhancedGateEvaluator, migrate_legacy_gate


def create_sample_codebase() -> tuple[List[str], Dict[str, str]]:
    """Create a sample codebase for testing"""
    
    codebase_files = [
        "src/main/java/com/example/UserService.java",
        "src/main/java/com/example/OrderService.java",
        "src/main/java/com/example/UserServiceTest.java",
        "src/main/java/com/example/OrderServiceTest.java",
        "src/main/resources/application.yml",
        "src/test/java/com/example/UserServiceTest.java",
        "src/test/java/com/example/OrderServiceTest.java",
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        ".dockerignore",
        "pom.xml",
        "src/main/java/com/example/ConfigService.java",
        "src/main/java/com/example/SecurityService.java"
    ]
    
    file_contents = {
        "src/main/java/com/example/UserService.java": """
package com.example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import javax.validation.Valid;
import javax.validation.constraints.NotNull;

public class UserService {
    private static final Logger logger = LoggerFactory.getLogger(UserService.class);
    
    public void createUser(@Valid @NotNull User user) {
        try {
            logger.info("Creating user: {}", user.getName());
            // User creation logic
        } catch (Exception e) {
            logger.error("Error creating user: {}", e.getMessage());
        }
    }
    
    public void updateUser(@Valid @NotNull User user) {
        if (user == null) {
            throw new IllegalArgumentException("User cannot be null");
        }
        logger.info("Updating user: {}", user.getName());
    }
}
""",
        "src/main/java/com/example/OrderService.java": """
package com.example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderService {
    private static final Logger logger = LoggerFactory.getLogger(OrderService.class);
    
    public void processOrder(Order order) {
        try {
            logger.info("Processing order: {}", order.getId());
            // Order processing logic
        } catch (Exception e) {
            logger.error("Error processing order: {}", e.getMessage());
        }
    }
}
""",
        "src/main/java/com/example/UserServiceTest.java": """
package com.example;

import org.junit.Test;
import static org.junit.Assert.*;

public class UserServiceTest {
    
    @Test
    public void testCreateUser() {
        // Test implementation
    }
    
    @Test
    public void testUpdateUser() {
        // Test implementation
    }
}
""",
        "src/main/java/com/example/OrderServiceTest.java": """
package com.example;

import org.junit.Test;
import static org.junit.Assert.*;

public class OrderServiceTest {
    
    @Test
    public void testProcessOrder() {
        // Test implementation
    }
}
""",
        "src/main/resources/application.yml": """
spring:
  application:
    name: example-app
  logging:
    level: INFO
""",
        "README.md": """
# Example Application

This is a sample application demonstrating various code quality practices.

## Features
- User management
- Order processing
- Comprehensive logging
- Input validation
""",
        "Dockerfile": """
FROM openjdk:11-jre-slim
COPY target/app.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
""",
        "docker-compose.yml": """
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
""",
        ".dockerignore": """
target/
*.log
.git/
""",
        "pom.xml": """
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>example-app</artifactId>
    <version>1.0.0</version>
</project>
""",
        "src/main/java/com/example/ConfigService.java": """
package com.example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConfigService {
    private static final Logger logger = LoggerFactory.getLogger(ConfigService.class);
    
    public void loadConfig() {
        logger.info("Loading configuration");
        // Config loading logic
    }
}
""",
        "src/main/java/com/example/SecurityService.java": """
package com.example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SecurityService {
    private static final Logger logger = LoggerFactory.getLogger(SecurityService.class);
    
    public void authenticate(String username, String password) {
        // Note: This is intentionally NOT logging sensitive data
        logger.info("Authenticating user: {}", username);
        // Authentication logic
    }
}
"""
    }
    
    return codebase_files, file_contents


def load_enhanced_pattern_library() -> Dict[str, Any]:
    """Load the enhanced pattern library"""
    
    try:
        with open("gates/patterns/enhanced_pattern_library.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Enhanced pattern library not found, using sample gates...")
        return create_sample_gates()


def create_sample_gates() -> Dict[str, Any]:
    """Create sample gates for testing"""
    
    return {
        "version": "2.0",
        "gates": {
            "STRUCTURED_LOGS": {
                "display_name": "Logs Searchable/Available",
                "category": "Logging",
                "weight": 15.0,
                "expected_coverage": {
                    "percentage": 25,
                    "reasoning": "Structured logging should be implemented across core application files"
                },
                "scoring": {
                    "pass_threshold": 20.0,
                    "perfect_threshold": 80.0,
                    "criteria_weight": 0.8,
                    "coverage_weight": 0.2
                },
                "criteria": {
                    "operator": "AND",
                    "conditions": [
                        {
                            "name": "logging_framework_import",
                            "type": "pattern",
                            "operator": "OR",
                            "weight": 5.0,
                            "patterns": [
                                {"pattern": "import org.slf4j.Logger", "weight": 3.0, "technology": "java"}
                            ]
                        },
                        {
                            "name": "logging_usage",
                            "type": "pattern",
                            "operator": "OR",
                            "weight": 3.0,
                            "patterns": [
                                {"pattern": "logger\\.(info|debug|warn|error)", "weight": 2.0, "technology": "java"}
                            ]
                        }
                    ]
                }
            },
            "TESTING_INFRASTRUCTURE": {
                "display_name": "Testing Infrastructure",
                "category": "Testing",
                "weight": 10.0,
                "expected_coverage": {
                    "percentage": 15,
                    "reasoning": "15% of projects should have testing infrastructure"
                },
                "scoring": {
                    "pass_threshold": 30.0,
                    "criteria_weight": 0.7,
                    "coverage_weight": 0.3
                },
                "criteria": {
                    "operator": "AND",
                    "conditions": [
                        {
                            "name": "test_files_exist",
                            "type": "file_pattern",
                            "operator": "OR",
                            "weight": 5.0,
                            "file_patterns": [
                                {"pattern": ".*Test\\.java", "weight": 3.0, "technology": "java"}
                            ]
                        },
                        {
                            "name": "test_methods_in_test_files",
                            "type": "pattern",
                            "operator": "OR",
                            "weight": 3.0,
                            "patterns": [
                                {"pattern": "@Test", "weight": 2.0, "file_context": "test_files", "technology": "java"}
                            ]
                        }
                    ]
                }
            },
            "DOCUMENTATION_AVAILABLE": {
                "display_name": "Documentation Available",
                "category": "Documentation",
                "weight": 8.0,
                "expected_coverage": {
                    "percentage": 10,
                    "reasoning": "10% of projects should have documentation"
                },
                "scoring": {
                    "pass_threshold": 20.0,
                    "criteria_weight": 0.8,
                    "coverage_weight": 0.2
                },
                "criteria": {
                    "operator": "OR",
                    "conditions": [
                        {
                            "name": "readme_exists",
                            "type": "file_pattern",
                            "operator": "OR",
                            "weight": 4.0,
                            "file_patterns": [
                                {"pattern": "README\\.md", "weight": 4.0}
                            ]
                        }
                    ]
                }
            },
            "CONTAINERIZATION_READY": {
                "display_name": "Containerization Ready",
                "category": "DevOps",
                "weight": 12.0,
                "expected_coverage": {
                    "percentage": 20,
                    "reasoning": "20% of projects should be containerized"
                },
                "scoring": {
                    "pass_threshold": 40.0,
                    "criteria_weight": 0.9,
                    "coverage_weight": 0.1
                },
                "criteria": {
                    "operator": "AND",
                    "conditions": [
                        {
                            "name": "docker_files_exist",
                            "type": "file_pattern",
                            "operator": "OR",
                            "weight": 6.0,
                            "file_patterns": [
                                {"pattern": "Dockerfile", "weight": 4.0},
                                {"pattern": "docker-compose\\.yml", "weight": 3.0}
                            ]
                        },
                        {
                            "name": "container_config_files",
                            "type": "file_pattern",
                            "operator": "OR",
                            "weight": 4.0,
                            "file_patterns": [
                                {"pattern": "\\.dockerignore", "weight": 2.0}
                            ]
                        }
                    ]
                }
            }
        }
    }


def test_criteria_evaluation():
    """Test the criteria-based evaluation system"""
    
    print("🧪 Testing Criteria-Based Evaluation System")
    print("=" * 50)
    
    # Create sample codebase
    codebase_files, file_contents = create_sample_codebase()
    print(f"📁 Sample codebase created with {len(codebase_files)} files")
    
    # Initialize enhanced gate evaluator
    evaluator = EnhancedGateEvaluator(codebase_files, file_contents)
    print("🔧 Enhanced gate evaluator initialized")
    
    # Load pattern library
    pattern_library = load_enhanced_pattern_library()
    gates = pattern_library.get("gates", {})
    print(f"📚 Loaded {len(gates)} gates from pattern library")
    
    # Evaluate each gate
    results = []
    total_score = 0.0
    total_weight = 0.0
    
    print("\n📊 Gate Evaluation Results:")
    print("-" * 50)
    
    for gate_name, gate_config in gates.items():
        print(f"\n🔍 Evaluating: {gate_config.get('display_name', gate_name)}")
        print(f"   Category: {gate_config.get('category', 'Unknown')}")
        print(f"   Weight: {gate_config.get('weight', 1.0)}")
        
        # Evaluate gate
        result = evaluator.evaluate_gate(gate_name, gate_config)
        
        # Display results
        score = result.get("score", 0.0)
        status = result.get("status", "FAIL")
        criteria_score = result.get("criteria_score", 0.0)
        coverage_score = result.get("coverage_score", 0.0)
        matches = result.get("matches", [])
        
        print(f"   Score: {score:.1f}/100 ({status})")
        print(f"   Criteria Score: {criteria_score:.1f}")
        print(f"   Coverage Score: {coverage_score:.1f}")
        print(f"   Matches: {len(matches)}")
        
        # Show condition results
        condition_results = result.get("condition_results", [])
        if condition_results:
            print("   Conditions:")
            for condition in condition_results:
                condition_status = "✅ PASS" if condition.passed else "❌ FAIL"
                print(f"     - {condition.condition_name}: {condition_status}")
        
        # Calculate weighted score
        weight = gate_config.get("weight", 1.0)
        weighted_score = score * weight
        total_score += weighted_score
        total_weight += weight
        
        results.append({
            "gate_name": gate_name,
            "display_name": gate_config.get("display_name", gate_name),
            "category": gate_config.get("category", "Unknown"),
            "weight": weight,
            "score": score,
            "status": status,
            "weighted_score": weighted_score
        })
    
    # Calculate overall score
    overall_score = total_score / total_weight if total_weight > 0 else 0.0
    
    print("\n" + "=" * 50)
    print("📈 OVERALL RESULTS")
    print("=" * 50)
    print(f"Overall Score: {overall_score:.1f}/100")
    print(f"Total Weight: {total_weight:.1f}")
    
    # Summary by category
    categories = {}
    for result in results:
        category = result["category"]
        if category not in categories:
            categories[category] = {"total_score": 0.0, "total_weight": 0.0, "gates": []}
        
        categories[category]["total_score"] += result["weighted_score"]
        categories[category]["total_weight"] += result["weight"]
        categories[category]["gates"].append(result)
    
    print("\n📊 Results by Category:")
    for category, data in categories.items():
        category_score = data["total_score"] / data["total_weight"] if data["total_weight"] > 0 else 0.0
        print(f"   {category}: {category_score:.1f}/100 ({len(data['gates'])} gates)")
    
    # Pass/Fail summary
    passed_gates = [r for r in results if r["status"] == "PASS"]
    failed_gates = [r for r in results if r["status"] == "FAIL"]
    
    print(f"\n✅ Passed Gates: {len(passed_gates)}")
    print(f"❌ Failed Gates: {len(failed_gates)}")
    
    return results, overall_score


def test_migration():
    """Test legacy gate migration"""
    
    print("\n🔄 Testing Legacy Gate Migration")
    print("-" * 30)
    
    # Sample legacy gate
    legacy_gate = {
        "LEGACY_LOGGING": {
            "display_name": "Legacy Logging Gate",
            "category": "Logging",
            "weight": 10.0,
            "patterns": [
                "import org.slf4j.Logger",
                "logger\\.(info|debug|warn|error)"
            ]
        }
    }
    
    print("Original legacy gate:")
    print(json.dumps(legacy_gate, indent=2))
    
    # Migrate to criteria-based format
    migrated_gate = migrate_legacy_gate(legacy_gate)
    
    print("\nMigrated to criteria-based format:")
    print(json.dumps(migrated_gate, indent=2))
    
    return migrated_gate


def main():
    """Main test function"""
    
    print("🚀 Criteria-Based Evaluation System Test")
    print("=" * 60)
    
    try:
        # Test criteria evaluation
        results, overall_score = test_criteria_evaluation()
        
        # Test migration
        migrated_gate = test_migration()
        
        print("\n✅ All tests completed successfully!")
        print(f"🎯 Final Overall Score: {overall_score:.1f}/100")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 