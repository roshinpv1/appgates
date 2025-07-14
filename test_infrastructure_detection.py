#!/usr/bin/env python3
"""
Test script to verify infrastructure pattern detection
"""

import json
import os
import sys
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, str(Path(__file__).parent / "gates"))

from nodes import GeneratePromptNode, CallLLMNode

def test_infrastructure_detection():
    """Test the enhanced LLM analysis for infrastructure pattern detection"""
    
    print("🧪 Testing Infrastructure Pattern Detection")
    print("=" * 50)
    
    # Mock data for a Spring Boot project with centralized logging
    mock_data = {
        "repo_url": "https://github.com/test/spring-app",
        "metadata": {
            "total_files": 150,
            "total_lines": 5000,
            "languages": {"Java": 120, "XML": 20, "Properties": 10},
            "language_stats": {
                "Java": {"files": 120, "lines": 4000},
                "XML": {"files": 20, "lines": 800},
                "Properties": {"files": 10, "lines": 200}
            },
            "file_types": {
                "Source Code": 120,
                "Configuration": 30
            }
        },
        "config": {
            "build_files": {
                "pom.xml": {
                    "type": "Maven",
                    "content": """
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-logging</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.retry</groupId>
        <artifactId>spring-retry</artifactId>
    </dependency>
    <dependency>
        <groupId>io.github.resilience4j</groupId>
        <artifactId>resilience4j-spring-boot2</artifactId>
    </dependency>
</dependencies>
"""
                }
            },
            "config_files": {
                "application.properties": {
                    "type": "Properties",
                    "content": """
logging.level.root=INFO
logging.pattern.console=%d{yyyy-MM-dd HH:mm:ss} - %msg%n
logging.file.name=logs/application.log
"""
                },
                "logback-spring.xml": {
                    "type": "XML",
                    "content": """
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
</configuration>
"""
                }
            },
            "dependencies": [
                "spring-boot-starter-web",
                "spring-boot-starter-logging", 
                "spring-retry",
                "resilience4j-spring-boot2",
                "logback-classic",
                "slf4j-api"
            ]
        },
        "hard_gates": [
            {"name": "STRUCTURED_LOGS", "description": "Ensure logs are structured and searchable"},
            {"name": "RETRY_LOGIC", "description": "Implement retry mechanisms for resilient operations"},
            {"name": "CIRCUIT_BREAKERS", "description": "Implement circuit breaker pattern for fault tolerance"},
            {"name": "TIMEOUTS", "description": "Set appropriate timeouts for I/O operations"},
            {"name": "THROTTLING", "description": "Implement rate limiting and request throttling"}
        ]
    }
    
    # Test prompt generation
    print("📋 Testing Enhanced Prompt Generation...")
    prompt_node = GeneratePromptNode()
    prompt = prompt_node.exec(mock_data)
    
    # Check if infrastructure detection instructions are in the prompt
    infrastructure_keywords = [
        "CENTRALIZED LOGGING FRAMEWORKS",
        "RESILIENCE PATTERNS", 
        "CIRCUIT BREAKERS",
        "RETRY LOGIC",
        "TIMEOUTS",
        "THROTTLING",
        "100%",
        "Infrastructure framework detected"
    ]
    
    print("\n🔍 Checking for infrastructure detection instructions:")
    for keyword in infrastructure_keywords:
        if keyword in prompt:
            print(f"✅ Found: {keyword}")
        else:
            print(f"❌ Missing: {keyword}")
    
    # Test LLM response parsing with mock infrastructure detection
    print("\n🧠 Testing LLM Response Parsing...")
    
    # Mock LLM response with infrastructure detection
    mock_llm_response = '''
{
  "STRUCTURED_LOGS": {
    "patterns": [
      "r'import\\s+org\\.slf4j\\.Logger'",
      "r'@Slf4j'",
      "r'logback\\.xml'",
      "r'logback-spring\\.xml'"
    ],
    "description": "Centralized logging framework (Logback/SLF4J) detected",
    "significance": "Enterprise-grade structured logging infrastructure in place",
    "expected_coverage": {
      "percentage": 100,
      "reasoning": "Centralized logging framework (Logback/SLF4J) detected in dependencies and configuration",
      "confidence": "high"
    }
  },
  "RETRY_LOGIC": {
    "patterns": [
      "r'@Retryable'",
      "r'RetryTemplate'",
      "r'spring-retry'"
    ],
    "description": "Spring Retry framework detected",
    "significance": "Resilience pattern for handling transient failures",
    "expected_coverage": {
      "percentage": 100,
      "reasoning": "Spring Retry framework detected in dependencies",
      "confidence": "high"
    }
  },
  "CIRCUIT_BREAKERS": {
    "patterns": [
      "r'@CircuitBreaker'",
      "r'Resilience4j'",
      "r'resilience4j-spring-boot2'"
    ],
    "description": "Resilience4j circuit breaker framework detected",
    "significance": "Fault tolerance pattern for handling service failures",
    "expected_coverage": {
      "percentage": 100,
      "reasoning": "Resilience4j framework detected in dependencies",
      "confidence": "high"
    }
  }
}
'''
    
    # Test parsing
    llm_node = CallLLMNode()
    parsed_data = llm_node._parse_enhanced_llm_response(mock_llm_response)
    
    print("\n📊 Parsed Infrastructure Detection Results:")
    for gate_name, gate_data in parsed_data.items():
        coverage = gate_data.get("expected_coverage", {})
        percentage = coverage.get("percentage", 0)
        reasoning = coverage.get("reasoning", "")
        confidence = coverage.get("confidence", "")
        
        print(f"\n🎯 {gate_name}:")
        print(f"   Coverage: {percentage}%")
        print(f"   Reasoning: {reasoning}")
        print(f"   Confidence: {confidence}")
        
        if percentage == 100:
            print(f"   ✅ Infrastructure pattern detected!")
        else:
            print(f"   ⚠️ Standard pattern (not infrastructure)")
    
    print("\n✅ Infrastructure pattern detection test completed!")
    return True

if __name__ == "__main__":
    test_infrastructure_detection() 