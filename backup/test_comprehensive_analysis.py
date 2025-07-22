#!/usr/bin/env python3
"""
Test script to demonstrate comprehensive LLM pattern generation
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from codegates.core.llm_pattern_manager import LLMPatternManager
from codegates.models import Language, GateType

def create_complex_test_codebase():
    """Create a more complex test codebase with config files and dependencies"""
    
    test_dir = Path("test_complex_codebase")
    test_dir.mkdir(exist_ok=True)
    
    # Create a Java Spring Boot application structure
    src_dir = test_dir / "src" / "main" / "java" / "com" / "example" / "demo"
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # Main application class
    main_app = src_dir / "DemoApplication.java"
    main_app.write_text("""
package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@SpringBootApplication
public class DemoApplication {
    private static final Logger log = LoggerFactory.getLogger(DemoApplication.class);
    
    public static void main(String[] args) {
        log.info("Starting Demo Application");
        SpringApplication.run(DemoApplication.class, args);
    }
}
""")
    
    # Controller with logging
    controller = src_dir / "DemoController.java"
    controller.write_text("""
package com.example.demo;

import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;

@RestController
@RequestMapping("/api")
public class DemoController {
    private static final Logger log = LoggerFactory.getLogger(DemoController.class);
    
    @GetMapping("/hello")
    public ResponseEntity<String> hello() {
        log.info("Received hello request");
        return ResponseEntity.ok("Hello World!");
    }
    
    @PostMapping("/data")
    public ResponseEntity<String> processData(@RequestBody String data) {
        log.info("Processing data: {}", data);
        try {
            // Process data
            return ResponseEntity.ok("Data processed successfully");
        } catch (Exception e) {
            log.error("Error processing data", e);
            return ResponseEntity.status(500).body("Error processing data");
        }
    }
}
""")
    
    # Service with error handling
    service = src_dir / "DemoService.java"
    service.write_text("""
package com.example.demo;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.retry.annotation.Retryable;
import org.springframework.retry.annotation.Backoff;

@Service
public class DemoService {
    private static final Logger log = LoggerFactory.getLogger(DemoService.class);
    
    @Retryable(value = {Exception.class}, maxAttempts = 3, backoff = @Backoff(delay = 1000))
    public String processWithRetry(String input) {
        log.info("Processing with retry: {}", input);
        if (input == null || input.isEmpty()) {
            throw new IllegalArgumentException("Input cannot be null or empty");
        }
        return "Processed: " + input;
    }
    
    public void logUserActivity(String userId, String action) {
        log.info("User {} performed action: {}", userId, action);
    }
}
""")
    
    # Maven pom.xml
    pom_xml = test_dir / "pom.xml"
    pom_xml.write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>demo</artifactId>
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
            <groupId>org.springframework.retry</groupId>
            <artifactId>spring-retry</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-aop</artifactId>
        </dependency>
        <dependency>
            <groupId>ch.qos.logback</groupId>
            <artifactId>logback-classic</artifactId>
        </dependency>
    </dependencies>
</project>
""")
    
    # Application properties
    app_props = test_dir / "src" / "main" / "resources" / "application.properties"
    app_props.parent.mkdir(parents=True, exist_ok=True)
    app_props.write_text("""
# Server configuration
server.port=8080
server.servlet.context-path=/demo

# Logging configuration
logging.level.com.example.demo=INFO
logging.level.org.springframework.web=DEBUG
logging.pattern.console=%d{yyyy-MM-dd HH:mm:ss} - %msg%n
logging.pattern.file=%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n

# Retry configuration
spring.retry.max-attempts=3
spring.retry.initial-interval=1000
spring.retry.multiplier=2.0
spring.retry.max-interval=10000
""")
    
    # Logback configuration
    logback_xml = test_dir / "src" / "main" / "resources" / "logback-spring.xml"
    logback_xml.write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/demo.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/demo.%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <root level="INFO">
        <appender-ref ref="CONSOLE" />
        <appender-ref ref="FILE" />
    </root>
</configuration>
""")
    
    return test_dir

def test_comprehensive_analysis():
    """Test comprehensive LLM pattern generation"""
    
    print("🧪 Testing Comprehensive LLM Pattern Generation")
    print("=" * 60)
    
    # Create complex test codebase
    test_dir = create_complex_test_codebase()
    print(f"📁 Created test codebase at: {test_dir}")
    
    try:
        # Initialize LLM Pattern Manager
        llm_manager = LLMPatternManager()
        print("✅ LLM Pattern Manager initialized")
        
        # Generate patterns for the complex codebase
        print("\n🤖 Generating comprehensive patterns...")
        result = llm_manager.generate_patterns_for_codebase(test_dir, [Language.JAVA])
        
        if result.get('success', False):
            print("✅ Comprehensive pattern generation successful!")
            
            # Show analysis results
            analysis = result.get('analysis', {})
            tech_context = analysis.get('tech_context', {})
            
            print(f"\n📊 Analysis Results:")
            print(f"   - Languages: {tech_context.get('languages', [])}")
            print(f"   - Total Files: {tech_context.get('total_files', 0)}")
            print(f"   - Total Lines: {tech_context.get('total_lines', 0)}")
            print(f"   - Config Files: {len(analysis.get('config_files', {}))}")
            print(f"   - Build Files: {len(analysis.get('build_files', {}))}")
            print(f"   - Dependencies: {len(analysis.get('dependencies', []))}")
            print(f"   - Custom Libraries: {len(analysis.get('custom_libraries', {}))}")
            
            # Show generated patterns
            gate_config = result.get('gate_config', {})
            print(f"\n🎯 Generated Patterns:")
            for gate, patterns in gate_config.items():
                if isinstance(patterns, list):
                    print(f"   - {gate}: {len(patterns)} patterns")
                else:
                    print(f"   - {gate}: {len(patterns.get('patterns', []))} patterns")
            
            # Show prompt length
            prompt = result.get('prompt', '')
            print(f"\n📋 Prompt Length: {len(prompt)} characters")
            
        else:
            print("❌ Comprehensive pattern generation failed")
            error = result.get('error', 'Unknown error')
            print(f"   Error: {error}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"\n🧹 Cleaned up test directory")

if __name__ == "__main__":
    test_comprehensive_analysis() 