#!/usr/bin/env python3
"""
Test script to verify build and config content extraction
"""

import os
import tempfile
from flow.scan_nodes import LLMPreAnalysisNode


def test_build_config_extraction():
    """Test build and config content extraction"""
    
    print("🧪 Testing Build and Config Content Extraction")
    print("=" * 50)
    
    # Create a temporary directory with sample build/config files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Created temporary directory: {temp_dir}")
        
        # Create sample build files
        build_files = [
            "package.json",
            "requirements.txt",
            "Dockerfile",
            "pom.xml",
            "build.gradle"
        ]
        
        # Create sample config files
        config_files = [
            ".env",
            "config.py",
            "application.yml",
            "nginx.conf",
            "docker-compose.yml"
        ]
        
        # Create sample content for each file
        file_contents = {
            "package.json": """
{
  "name": "test-app",
  "version": "1.0.0",
  "scripts": {
    "start": "node app.js",
    "test": "jest",
    "build": "webpack"
  },
  "dependencies": {
    "express": "^4.17.1",
    "react": "^17.0.2"
  },
  "devDependencies": {
    "jest": "^27.0.0",
    "webpack": "^5.0.0"
  }
}
""",
            "requirements.txt": """
Flask==2.0.1
requests==2.25.1
pytest==6.2.5
sqlalchemy==1.4.23
redis==3.5.3
""",
            "Dockerfile": """
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
""",
            "pom.xml": """
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-app</artifactId>
    <version>1.0.0</version>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
""",
            "build.gradle": """
plugins {
    id 'java'
    id 'org.springframework.boot' version '2.5.0'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}
""",
            ".env": """
DATABASE_URL=postgresql://localhost:5432/testdb
REDIS_URL=redis://localhost:6379
API_KEY=your-secret-api-key
DEBUG=true
""",
            "config.py": """
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL')
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
""",
            "application.yml": """
spring:
  datasource:
    url: ${DATABASE_URL}
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
  redis:
    host: localhost
    port: 6379
logging:
  level: INFO
  pattern: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
""",
            "nginx.conf": """
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
""",
            "docker-compose.yml": """
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://db:5432/testdb
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: testdb
      POSTGRES_PASSWORD: password
  
  redis:
    image: redis:6-alpine
"""
        }
        
        # Create the files
        for filename, content in file_contents.items():
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Created {filename}")
        
        # Create metadata structure similar to what the system produces
        metadata = {
            "main_repo": {
                "repo_url": "https://github.com/example/test-repo",
                "branch": "main",
                "local_path": temp_dir,
                "total_files": 10,
                "total_lines": 500,
                "languages": ["Python", "JavaScript", "Java"],
                "dependencies": {
                    "python": ["Flask", "requests", "pytest"],
                    "javascript": ["express", "react"],
                    "java": ["spring-boot"]
                },
                "build_files": build_files,
                "config_files": config_files
            },
            "cd_repo": None,
            "has_cd_repo": False
        }
        
        # Test the build config extraction
        print("\n🔧 Testing Build Config Extraction")
        print("-" * 30)
        
        # Create LLM pre-analysis node instance
        llm_node = LLMPreAnalysisNode(None)  # No LLM service needed for this test
        
        # Extract build configs
        build_configs = llm_node._get_build_configs(metadata)
        
        print("📄 Extracted Build and Config Content:")
        print("=" * 50)
        print(build_configs)
        print("=" * 50)
        
        # Test project summary
        print("\n📊 Testing Project Summary")
        print("-" * 30)
        
        project_summary = llm_node._build_project_summary(metadata)
        print("📄 Project Summary:")
        print("=" * 50)
        print(project_summary)
        print("=" * 50)
        
        # Test full prompt creation
        print("\n🔧 Testing Full Prompt Creation")
        print("-" * 30)
        
        prompt = llm_node._create_pre_analysis_prompt(project_summary, build_configs)
        
        print("📄 Generated Prompt Preview:")
        print("=" * 50)
        print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
        print("=" * 50)
        
        # Analyze the results
        print("\n📈 Analysis Results")
        print("-" * 30)
        
        # Count files processed
        build_files_found = build_configs.count("BUILD FILES:")
        config_files_found = build_configs.count("CONFIG FILES:")
        
        print(f"✅ Build files section found: {build_files_found > 0}")
        print(f"✅ Config files section found: {config_files_found > 0}")
        print(f"✅ Total content length: {len(build_configs)} characters")
        print(f"✅ Prompt length: {len(prompt)} characters")
        
        # Check for specific content
        content_checks = [
            ("package.json", "package.json" in build_configs),
            ("requirements.txt", "Flask==2.0.1" in build_configs),
            ("Dockerfile", "FROM python:3.9-slim" in build_configs),
            (".env", "DATABASE_URL" in build_configs),
            ("config.py", "SECRET_KEY" in build_configs),
            ("docker-compose.yml", "version: '3.8'" in build_configs)
        ]
        
        print("\n📋 Content Verification:")
        for filename, found in content_checks:
            status = "✅" if found else "❌"
            print(f"   {status} {filename}: {'Found' if found else 'Not found'}")
        
        print("\n🎉 Build Config Extraction Test Complete!")


if __name__ == "__main__":
    test_build_config_extraction()
