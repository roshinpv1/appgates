import os
import json
import datetime # Although not used in modified code, kept for consistency
import re
import xml.etree.ElementTree as ET
import collections # For defaultdict and OrderedDict
import argparse
import logging # For proper logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Default Configuration ---
DEFAULT_CONFIG = {
    "LANGUAGE_MAP": {
        '.java': 'Java',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.py': 'Python',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C/C++',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
        '.xml': 'XML',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.properties': 'Properties',
        '.md': 'Markdown',
        '.txt': 'Text',
        '.sh': 'Shell',
        '.bat': 'Batch',
        '.ps1': 'PowerShell',
        '.sql': 'SQL',
        '.kt': 'Kotlin',
        '.swift': 'Swift',
        '.dockerfile': 'Dockerfile', # Special case for Dockerfile
        'Dockerfile': 'Dockerfile'   # Handle no extension
    },
    "BUILD_CONFIG_FILES": {
        'pom.xml': 'Maven Build File',         # Java (Maven)
        'build.gradle': 'Gradle Build File',   # Java (Gradle)
        'package.json': 'NPM Package File',    # JavaScript/TypeScript (Node.js)
        'requirements.txt': 'Python Dependencies', # Python
        'pyproject.toml': 'Python Build File', # Python (newer)
        'go.mod': 'Go Module File',            # Go
        'Gemfile': 'Ruby Gem File',            # Ruby
        'Gemfile.lock': 'Ruby Gem Lock File',  # Ruby
        'appsettings.json': '.NET Configuration', # C# (.NET)
        '.csproj': '.NET Project File',       # C# (.NET)
        'web.config': '.NET Web Configuration', # C# (.NET)
        'Dockerfile': 'Dockerfile',            # Docker
        'docker-compose.yml': 'Docker Compose File', # Docker
        '.env': 'Environment Variables',       # Generic
        'application.properties': 'Spring Boot Configuration', # Java (Spring Boot)
        'application.yml': 'Spring Boot Configuration', # Java (Spring Boot)
        'logback.xml': 'Logback Configuration', # Java Logging
        'log4j.xml': 'Log4j Configuration',     # Java Logging
        'log4j2.xml': 'Log4j2 Configuration',   # Java Logging
    },
    "IGNORE_EXTENSIONS": [
        '.jar', '.class', '.dll', '.exe', '.obj', '.o', '.pyc', '.iml', '.ipr', '.iws',
        '.zip', '.tar.gz', '.tgz', '.rar', '.7z', '.log', '.swp', '.tmp', '.DS_Store',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.otf',
        '.mp4', '.mov', '.avi', '.mp3', '.wav'
    ],
    "IGNORE_DIRS": [
        '.git', '.svn', '.idea', '.vscode', '__pycache__', 'node_modules', 'venv', 'env',
        'target', 'build', 'dist', 'out', '.terraform', '.next', '.serverless',
        'typings', 'flow-typed' # Common JS/TS folders
    ],
    "HARD_GATES": [
        "Logs Searchable/Available",
        "Avoid Logging Confidential Data",
        "Create Audit Trail Logs",
        "Tracking ID for Logs",
        "Log REST API Calls",
        "Log Application Messages",
        "Client UI Errors Logged",
        "Retry Logic",
        "Timeouts in IO Ops",
        "Throttling & Drop Request",
        "Circuit Breakers",
        "Log System Errors",
        "HTTP Error Codes",
        "Client Error Tracking",
        "Automated Tests"
    ],
    "CUSTOM_LIBRARY_SUMMARIES": {
        # Java/Spring Libraries
        "spring-boot-starter": {
            "category": "Java Framework",
            "description": "Spring Boot starter with embedded Tomcat, auto-configuration, and production-ready features",
            "hard_gate_implications": {
                "Logs Searchable/Available": "Spring Boot provides built-in logging with Logback. Look for application.properties/yml logging configuration",
                "Log REST API Calls": "Spring Boot has built-in request/response logging. Check for @RestController and logging configurations",
                "HTTP Error Codes": "Spring Boot provides @ControllerAdvice and @ExceptionHandler for proper HTTP status codes",
                "Retry Logic": "Spring Retry library can be used. Look for @Retryable annotations and RetryTemplate usage",
                "Circuit Breakers": "Spring Cloud Circuit Breaker with Resilience4j. Check for @CircuitBreaker annotations"
            },
            "common_patterns": ["spring-boot-starter", "spring-boot-starter-web", "spring-boot-starter-logging"]
        },
        "logback": {
            "category": "Java Logging",
            "description": "Logback is the successor to Log4j, providing advanced logging capabilities",
            "hard_gate_implications": {
                "Logs Searchable/Available": "Logback provides structured logging with JSON format support",
                "Avoid Logging Confidential Data": "Logback has built-in masking capabilities for sensitive data",
                "Create Audit Trail Logs": "Logback supports audit logging with specific appenders",
                "Tracking ID for Logs": "Logback MDC (Mapped Diagnostic Context) for correlation IDs"
            },
            "common_patterns": ["logback", "logback-classic", "logback-core"]
        },
        "slf4j": {
            "category": "Java Logging",
            "description": "Simple Logging Facade for Java - logging abstraction layer",
            "hard_gate_implications": {
                "Logs Searchable/Available": "SLF4J provides structured logging capabilities",
                "Avoid Logging Confidential Data": "SLF4J supports parameterized logging to avoid string concatenation"
            },
            "common_patterns": ["slf4j-api", "slf4j-simple"]
        },
        "resilience4j": {
            "category": "Java Resilience",
            "description": "Resilience4j is a fault tolerance library designed for Java 8 and functional programming",
            "hard_gate_implications": {
                "Retry Logic": "Resilience4j provides @Retry annotation and RetryConfig",
                "Circuit Breakers": "Resilience4j provides @CircuitBreaker annotation and CircuitBreakerConfig",
                "Timeouts in IO Ops": "Resilience4j provides @Timeout annotation and TimeoutConfig",
                "Throttling & Drop Request": "Resilience4j provides @Bulkhead annotation for rate limiting"
            },
            "common_patterns": ["resilience4j-spring-boot2", "resilience4j-retry", "resilience4j-circuitbreaker"]
        },
        
        # Python Libraries
        "flask": {
            "category": "Python Web Framework",
            "description": "Lightweight web framework for Python with extensive extension ecosystem",
            "hard_gate_implications": {
                "Log REST API Calls": "Flask provides request/response logging. Look for @app.before_request and @app.after_request",
                "HTTP Error Codes": "Flask provides proper HTTP status codes with abort() and error handlers",
                "Logs Searchable/Available": "Flask can integrate with Python logging module for structured logs"
            },
            "common_patterns": ["flask", "flask-cors", "flask-restful"]
        },
        "django": {
            "category": "Python Web Framework",
            "description": "High-level Python web framework with built-in admin interface",
            "hard_gate_implications": {
                "Log REST API Calls": "Django provides middleware for request/response logging",
                "HTTP Error Codes": "Django provides proper HTTP status codes and error handling",
                "Logs Searchable/Available": "Django has built-in logging configuration",
                "Avoid Logging Confidential Data": "Django provides sensitive data filtering in logs"
            },
            "common_patterns": ["django", "djangorestframework"]
        },
        "structlog": {
            "category": "Python Logging",
            "description": "Structured logging for Python with JSON output support",
            "hard_gate_implications": {
                "Logs Searchable/Available": "Structlog provides structured logging with JSON format",
                "Avoid Logging Confidential Data": "Structlog supports value filtering and masking",
                "Create Audit Trail Logs": "Structlog supports audit logging with specific processors",
                "Tracking ID for Logs": "Structlog supports correlation IDs through bound loggers"
            },
            "common_patterns": ["structlog", "structlog[dev]"]
        },
        "tenacity": {
            "category": "Python Resilience",
            "description": "Retry library for Python with exponential backoff and circuit breaker support",
            "hard_gate_implications": {
                "Retry Logic": "Tenacity provides @retry decorator with configurable retry strategies",
                "Circuit Breakers": "Tenacity provides circuit breaker functionality",
                "Timeouts in IO Ops": "Tenacity provides timeout decorators"
            },
            "common_patterns": ["tenacity"]
        },
        
        # JavaScript/TypeScript Libraries
        "winston": {
            "category": "JavaScript Logging",
            "description": "Universal logging library for Node.js with multiple transport support",
            "hard_gate_implications": {
                "Logs Searchable/Available": "Winston provides structured logging with JSON format",
                "Avoid Logging Confidential Data": "Winston supports sensitive data filtering",
                "Create Audit Trail Logs": "Winston supports multiple transports for audit logging",
                "Tracking ID for Logs": "Winston supports correlation IDs through metadata"
            },
            "common_patterns": ["winston", "winston-daily-rotate-file"]
        },
        "express": {
            "category": "JavaScript Web Framework",
            "description": "Fast, unopinionated, minimalist web framework for Node.js",
            "hard_gate_implications": {
                "Log REST API Calls": "Express provides middleware for request/response logging",
                "HTTP Error Codes": "Express provides proper HTTP status codes and error handling",
                "Logs Searchable/Available": "Express can integrate with logging libraries like Winston"
            },
            "common_patterns": ["express", "express-winston"]
        },
        "axios": {
            "category": "JavaScript HTTP Client",
            "description": "Promise-based HTTP client for the browser and Node.js",
            "hard_gate_implications": {
                "Retry Logic": "Axios provides interceptors for retry logic",
                "Timeouts in IO Ops": "Axios provides timeout configuration",
                "HTTP Error Codes": "Axios provides proper error handling for HTTP status codes"
            },
            "common_patterns": ["axios", "axios-retry"]
        },
        "sentry": {
            "category": "JavaScript Error Tracking",
            "description": "Application monitoring and error tracking for JavaScript applications",
            "hard_gate_implications": {
                "Client Error Tracking": "Sentry provides comprehensive error tracking and monitoring",
                "Log System Errors": "Sentry captures and reports system errors automatically"
            },
            "common_patterns": ["@sentry/node", "@sentry/browser", "@sentry/react"]
        },
        
        # C#/.NET Libraries
        "serilog": {
            "category": "C# Logging",
            "description": "Diagnostic logging library for .NET with structured logging support",
            "hard_gate_implications": {
                "Logs Searchable/Available": "Serilog provides structured logging with JSON format",
                "Avoid Logging Confidential Data": "Serilog supports sensitive data filtering",
                "Create Audit Trail Logs": "Serilog supports audit logging with specific sinks",
                "Tracking ID for Logs": "Serilog supports correlation IDs through enrichers"
            },
            "common_patterns": ["Serilog", "Serilog.AspNetCore", "Serilog.Sinks.Console"]
        },
        "polly": {
            "category": "C# Resilience",
            "description": "Polly is a .NET resilience and transient-fault-handling library",
            "hard_gate_implications": {
                "Retry Logic": "Polly provides retry policies with exponential backoff",
                "Circuit Breakers": "Polly provides circuit breaker policies",
                "Timeouts in IO Ops": "Polly provides timeout policies",
                "Throttling & Drop Request": "Polly provides bulkhead isolation policies"
            },
            "common_patterns": ["Polly", "Polly.Extensions.Http"]
        },
        "aspnetcore": {
            "category": "C# Web Framework",
            "description": "Cross-platform web framework for building modern cloud-based applications",
            "hard_gate_implications": {
                "Log REST API Calls": "ASP.NET Core provides middleware for request/response logging",
                "HTTP Error Codes": "ASP.NET Core provides proper HTTP status codes and error handling",
                "Logs Searchable/Available": "ASP.NET Core has built-in logging with ILogger"
            },
            "common_patterns": ["Microsoft.AspNetCore.App", "Microsoft.AspNetCore.Mvc"]
        },
        
        # Testing Libraries
        "junit": {
            "category": "Java Testing",
            "description": "Unit testing framework for Java",
            "hard_gate_implications": {
                "Automated Tests": "JUnit provides comprehensive unit testing capabilities"
            },
            "common_patterns": ["junit", "junit-jupiter", "junit-vintage"]
        },
        "pytest": {
            "category": "Python Testing",
            "description": "Testing framework for Python with extensive plugin ecosystem",
            "hard_gate_implications": {
                "Automated Tests": "Pytest provides comprehensive testing capabilities with fixtures and parametrization"
            },
            "common_patterns": ["pytest", "pytest-cov", "pytest-mock"]
        },
        "jest": {
            "category": "JavaScript Testing",
            "description": "JavaScript testing framework with built-in mocking and coverage",
            "hard_gate_implications": {
                "Automated Tests": "Jest provides comprehensive testing capabilities with mocking and coverage"
            },
            "common_patterns": ["jest", "@types/jest"]
        },
        "mstest": {
            "category": "C# Testing",
            "description": "Microsoft's unit testing framework for .NET",
            "hard_gate_implications": {
                "Automated Tests": "MSTest provides unit testing capabilities for .NET applications"
            },
            "common_patterns": ["MSTest.TestFramework", "MSTest.TestAdapter"]
        },
        
        # Enterprise Libraries
        "eser": {
            "category": "Enterprise Security Event Reporting",
            "description": "ESER (Enterprise Security Event Reporting) provides standardized logging for enterprise applications with 24 different event types and compliance features",
            "hard_gate_implications": {
                "Logs Searchable/Available": "ESER provides structured logging with standardized event types and searchable attributes",
                "Create Audit Trail Logs": "ESER is specifically designed for audit trail logging with 24 different event types",
                "Tracking ID for Logs": "ESER includes correlation IDs through MDC (parent_id, span_id, trace_id) and X-REQUEST-ID header",
                "Log Application Messages": "ESER provides ApplicationLifecycleEvent and other application-specific event types",
                "Log System Errors": "ESER includes system error logging with standardized event types",
                "Avoid Logging Confidential Data": "ESER provides controlled logging through factory methods and augmenters"
            },
            "common_patterns": [
                "eser", "ESEREventFactoryWrapperAPI", "ESEREventFactory", "ESERLoggingAugmenter",
                "SearoseESERLoggingAugmenter", "LoglibConfiguration", "ApplicationLifecycleEvent",
                "AppLifeCycleEventType", "orchestra-loglib", "loglib", "ESEREventFactoryWrapperAPI",
                "createApplicationLifecycleEvent", "SERVER_STARTUP", "WF_ID", "ENVIRONMENT",
                "parent_id", "span_id", "trace_id", "X-REQUEST-ID", "WFRequestID"
            ]
        },
        "ebssh": {
            "category": "Enterprise Business Security and Shared Hosting",
            "description": "EBSSH (Enterprise Business Security and Shared Hosting) provides enterprise-grade security, authentication, and hosting capabilities",
            "hard_gate_implications": {
                "Logs Searchable/Available": "EBSSH LogLib Starters provide enterprise logging capabilities",
                "Avoid Logging Confidential Data": "EBSSH AuthX Starters provide secure authentication and data protection",
                "Create Audit Trail Logs": "EBSSH provides comprehensive audit logging for enterprise applications",
                "Log REST API Calls": "EBSSH Framework Starters include API logging capabilities",
                "HTTP Error Codes": "EBSSH provides proper HTTP status code handling for enterprise applications",
                "Client Error Tracking": "EBSSH includes error tracking and monitoring capabilities"
            },
            "common_patterns": [
                "ebssh", "ebssh-loglib-starter", "ebssh-auth-starter", "ebssh-cloud-config-starter",
                "ebssh-searose-starter", "ebssh-oauth2-client-starter", "ebssh-framework-starter",
                "EBSSH", "orchestra-framework", "ebssh-loglib", "ebssh-auth", "ebssh-cloud-config",
                "ebssh-searose", "ebssh-oauth2-client", "ebssh-framework"
            ]
        },
        "orchestra": {
            "category": "Enterprise Framework",
            "description": "Orchestra Framework provides enterprise-grade application framework with logging, security, and hosting capabilities",
            "hard_gate_implications": {
                "Logs Searchable/Available": "Orchestra Loglib provides structured logging with WF_ID and ENVIRONMENT fields",
                "Create Audit Trail Logs": "Orchestra Framework supports comprehensive audit logging",
                "Tracking ID for Logs": "Orchestra includes correlation ID support through MDC and request headers",
                "Log Application Messages": "Orchestra provides application lifecycle event logging",
                "Avoid Logging Confidential Data": "Orchestra includes secure logging capabilities",
                "HTTP Error Codes": "Orchestra Framework provides proper HTTP status code handling"
            },
            "common_patterns": [
                "orchestra", "orchestra-loglib", "orchestra-framework", "LoglibConfiguration",
                "WF_ID", "ENVIRONMENT", "loggingApplicationId", "ESEREventFactoryWrapperAPI",
                "orchestra-framework", "orchestra-loglib", "LoglibConfiguration", "WF_ID",
                "ENVIRONMENT", "loggingApplicationId", "orchestra-version", "orchestra-config"
            ]
        }
    }
}

def load_config(config_filepath):
    """
    Loads configuration from a JSON file, overriding default settings.
    Includes basic validation and merging for dictionary and list types.
    """
    config = DEFAULT_CONFIG.copy() # Start with a copy of default config
    if config_filepath:
        try:
            with open(config_filepath, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                for key, value in user_config.items():
                    if key in config:
                        # Merge dictionaries for configuration maps
                        if isinstance(config[key], dict) and isinstance(value, dict):
                            config[key].update(value)
                        # Extend lists for ignore lists, avoiding duplicates
                        elif isinstance(config[key], list) and isinstance(value, list):
                            config[key].extend([item for item in value if item not in config[key]])
                        # Override other types directly (e.g., HARD_GATES if completely replaced)
                        else:
                            config[key] = value
                    else:
                        logging.warning(f"Unknown configuration key '{key}' found in '{config_filepath}'. Ignoring.")
            logging.info(f"Loaded custom configuration from '{config_filepath}'.")
        except FileNotFoundError:
            logging.error(f"Configuration file not found at '{config_filepath}'. Using default settings.")
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing configuration file '{config_filepath}': {e}. Using default settings.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading config '{config_filepath}': {e}. Using default settings.")
    return config

# --- Utility Functions for Dependency Extraction ---
# (These functions were already robust, changed print statements to logging)

def extract_maven_dependencies(filepath):
    """Extracts artifact IDs from a pom.xml file."""
    dependencies = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        if root.tag.startswith('{http://maven.apache.org/POM/4.0.0}'):
            dep_elements = root.findall('.//maven:dependency', namespace)
            parent_elem = root.find('maven:parent', namespace)
        else:
            dep_elements = root.findall('.//dependency')
            parent_elem = root.find('.//parent')

        for dep in dep_elements:
            group_id_elem = dep.find('maven:groupId', namespace) if root.tag.startswith('{http://maven.apache.org/POM/4.0.0}') else dep.find('groupId')
            artifact_id_elem = dep.find('maven:artifactId', namespace) if root.tag.startswith('{http://maven.apache.org/POM/4.0.0}') else dep.find('artifactId')
            
            if group_id_elem is not None and artifact_id_elem is not None:
                dependencies.append(f"{group_id_elem.text}:{artifact_id_elem.text}")
            elif artifact_id_elem is not None:
                dependencies.append(artifact_id_elem.text)

        if parent_elem is not None:
            group_id_elem = parent_elem.find('maven:groupId', namespace) if root.tag.startswith('{http://maven.apache.org/POM/4.0.0}') else parent_elem.find('groupId')
            artifact_id_elem = parent_elem.find('maven:artifactId', namespace) if root.tag.startswith('{http://maven.apache.org/POM/4.0.0}') else parent_elem.find('artifactId')
            if group_id_elem is not None and artifact_id_elem is not None:
                dependencies.append(f"PARENT_MODULE:{group_id_elem.text}:{artifact_id_elem.text}")

    except ET.ParseError as e:
        logging.error(f"Error parsing XML file {filepath}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred parsing Maven file {filepath}: {e}")
    return dependencies

def extract_gradle_dependencies(filepath):
    """
    Extracts dependencies and plugins from a build.gradle file using regex.
    Note: This is a simplistic regex and may not cover all Gradle DSL complexities (e.g., closures, variables).
    """
    dependencies = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            dep_patterns = re.findall(
                r'(?:implementation|api|compile|runtimeOnly|testImplementation|androidTestImplementation|annotationProcessor|kapt|classpath|ksp)\s*[\'"]([a-zA-Z0-9\._-]+:[a-zA-Z0-9\._-]+(?:[:\$][a-zA-Z0-9\._-]+)?|project\([\'"]:[a-zA-Z0-9\._-]+[\'"]\))[\'"]',
                content
            )
            for dep_string in dep_patterns:
                dependencies.append(dep_string.strip())
            
            plugin_patterns = re.findall(
                r'id\s*[\'"]([a-zA-Z0-9\._-]+)[\'"](?:\s*version\s*[\'"]([a-zA-Z0-9\._-]+)[\'"])?',
                content
            )
            for plugin_id, plugin_version in plugin_patterns:
                if plugin_id not in dependencies:
                    dependencies.append(f"plugin:{plugin_id}{':'+plugin_version if plugin_version else ''}")

    except Exception as e:
        logging.error(f"Error reading or parsing Gradle file {filepath}: {e}")
    return dependencies

def extract_npm_dependencies(filepath):
    """Extracts dependencies from package.json."""
    dependencies = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for dep_type in ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies', 'bundleDependencies']:
                if dep_type in data and isinstance(data[dep_type], dict):
                    for package, version in data[dep_type].items():
                        dependencies.append(f"{package}@{version}")
            
            if "engines" in data and isinstance(data["engines"], dict):
                for engine, version_spec in data["engines"].items():
                    dependencies.append(f"engine:{engine}@{version_spec}")

    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file {filepath}: {e}")
    except Exception as e:
        logging.error(f"Error reading NPM file {filepath}: {e}")
    return dependencies

def extract_python_requirements(filepath):
    """Extracts dependencies from requirements.txt."""
    dependencies = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    match = re.match(r'([a-zA-Z0-9._-]+(?:==|>=|<=|>|<|~=|\!=)?(?:[a-zA-Z0-9._*-]+)?(?:\[.*?\])?).*', line)
                    if match:
                        dependencies.append(match.group(1))
    except Exception as e:
        logging.error(f"Error reading Python requirements file {filepath}: {e}")
    return dependencies

def extract_go_dependencies(filepath):
    """Extracts dependencies from go.mod."""
    dependencies = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            module_match = re.search(r'^module\s+([^\s]+)', content, re.MULTILINE)
            if module_match:
                dependencies.append(f"go_module:{module_match.group(1)}")
            
            require_matches = re.findall(r'^\s*require\s+([^\s]+)\s+([^\s]+)(?:\s+//\s+indirect)?', content, re.MULTILINE)
            for module, version in require_matches:
                dependencies.append(f"{module}@{version}")
            
            go_version_match = re.search(r'^go\s+([\d\.]+)', content, re.MULTILINE)
            if go_version_match:
                dependencies.append(f"go_version:{go_version_match.group(1)}")

    except Exception as e:
        logging.error(f"Error reading Go module file {filepath}: {e}")
    return dependencies

def extract_ruby_gems(filepath):
    """Extracts gems from Gemfile."""
    dependencies = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            gem_matches = re.findall(r"gem\s*['\"]([^'\"]+)['\"](?:,\s*['\"~>=<]*([^'\"]*)['\"])?", content)
            for gem_name, gem_version in gem_matches:
                if gem_version:
                    dependencies.append(f"{gem_name}@{gem_version.strip()}")
                else:
                    dependencies.append(gem_name)
    except Exception as e:
        logging.error(f"Error reading Gemfile {filepath}: {e}")
    return dependencies

def extract_csproj_dependencies(filepath):
    """Extracts PackageReference and ProjectReference from .csproj files."""
    dependencies = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]
        
        package_refs = root.findall('.//PackageReference')
        for pkg_ref in package_refs:
            include = pkg_ref.get('Include')
            version = pkg_ref.get('Version')
            if include:
                dependencies.append(f"NuGet_Package:{include}@{version}" if version else f"NuGet_Package:{include}")

        project_refs = root.findall('.//ProjectReference')
        for proj_ref in project_refs:
            include = proj_ref.get('Include')
            if include:
                proj_name = os.path.splitext(os.path.basename(include))[0]
                dependencies.append(f"Internal_Project:{proj_name}")

        references = root.findall('.//Reference')
        for ref in references:
            include = ref.get('Include')
            if include:
                dependencies.append(f"Assembly_Reference:{include}")

    except ET.ParseError as e:
        logging.error(f"Error parsing XML file {filepath}: {e}")
    except Exception as e:
        logging.error(f"Error processing .csproj file {filepath}: {e}")
    return dependencies

# --- Main Scanner Function ---

def detect_custom_libraries(detected_libraries, custom_library_summaries):
    """
    Detects custom libraries from the detected libraries list and returns relevant information.
    
    Args:
        detected_libraries: List of detected library names
        custom_library_summaries: Dictionary of custom library summaries
        
    Returns:
        Dictionary containing detected custom libraries and their implications
    """
    detected_custom_libraries = {}
    
    for lib_name in detected_libraries:
        # Check if this library matches any custom library patterns
        for custom_lib_key, custom_lib_info in custom_library_summaries.items():
            common_patterns = custom_lib_info.get("common_patterns", [])
            
            # Check if the library name matches any of the common patterns
            for pattern in common_patterns:
                if pattern.lower() in lib_name.lower():
                    detected_custom_libraries[custom_lib_key] = {
                        "library_name": lib_name,
                        "category": custom_lib_info.get("category", "Unknown"),
                        "description": custom_lib_info.get("description", ""),
                        "hard_gate_implications": custom_lib_info.get("hard_gate_implications", {}),
                        "matched_pattern": pattern
                    }
                    break  # Found a match, no need to check other patterns for this library
    
    return detected_custom_libraries

def scan_codebase(root_folder, config):
    """
    Scans a codebase folder, extracts file structure (hierarchically with only filename),
    and identifies libraries from known build and configuration files.
    """
    language_map = config["LANGUAGE_MAP"]
    build_config_files = config["BUILD_CONFIG_FILES"]
    ignore_extensions = config["IGNORE_EXTENSIONS"]
    ignore_dirs = config["IGNORE_DIRS"]
    custom_library_summaries = config.get("CUSTOM_LIBRARY_SUMMARIES", {})

    if not os.path.isdir(root_folder):
        raise FileNotFoundError(f"The specified path '{root_folder}' is not a directory.")

    hierarchical_file_structure = collections.OrderedDict()

    build_and_config_analysis = []
    all_detected_libraries = collections.defaultdict(int)
    programming_languages_detected = collections.defaultdict(int)
    key_config_files_found = collections.defaultdict(int)
    build_files_found = collections.defaultdict(int)

    total_files = 0
    total_directories = 0

    logging.info(f"Starting scan of '{root_folder}'...")

    def get_nested_dict(base_dict, path_components):
        current = base_dict
        for comp in path_components:
            current = current.setdefault(comp, collections.OrderedDict())
        return current

    for dirpath, dirnames, filenames in os.walk(root_folder):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith('.')]
        
        total_directories += 1

        relative_path_components = os.path.relpath(dirpath, root_folder).split(os.sep)
        
        if relative_path_components == ['.']:
            current_dir_node = hierarchical_file_structure
        else:
            current_dir_node = get_nested_dict(hierarchical_file_structure, relative_path_components)
        
        if '_files' not in current_dir_node:
            current_dir_node['_files'] = []

        for filename in filenames:
            total_files += 1
            filepath = os.path.join(dirpath, filename)
            
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext in ignore_extensions or filename in ignore_extensions:
                continue

            current_dir_node['_files'].append(filename)

            language = language_map.get(file_ext, language_map.get(filename, 'Unknown'))
            if language != 'Unknown':
                programming_languages_detected[language] += 1

            file_type_key = filename if filename in build_config_files else file_ext
            file_type = build_config_files.get(file_type_key)
            
            if file_type:
                logging.info(f"Processing {file_type}: {filepath}")
                analysis_entry = {
                    "filepath": filepath,
                    "file_type": file_type,
                    "detected_libraries": []
                }
                
                if 'Build File' in file_type or 'Dependencies' in file_type or 'Gem File' in file_type or 'Project File' in file_type:
                    build_files_found[filename if filename != '.csproj' else f"*{file_ext}"] += 1
                else:
                    key_config_files_found[filename if filename != '.csproj' else f"*{file_ext}"] += 1

                if filename == 'pom.xml':
                    libs = extract_maven_dependencies(filepath)
                elif filename == 'build.gradle':
                    libs = extract_gradle_dependencies(filepath)
                elif filename == 'package.json':
                    libs = extract_npm_dependencies(filepath)
                elif filename == 'requirements.txt':
                    libs = extract_python_requirements(filepath)
                elif filename == 'go.mod':
                    libs = extract_go_dependencies(filepath)
                elif filename == 'Gemfile':
                    libs = extract_ruby_gems(filepath)
                elif file_ext == '.csproj':
                    libs = extract_csproj_dependencies(filepath)
                else:
                    libs = []

                analysis_entry["detected_libraries"] = sorted(list(set(libs)))
                for lib in libs:
                    all_detected_libraries[lib] += 1
                
                build_and_config_analysis.append(analysis_entry)

        if '_files' in current_dir_node:
            current_dir_node['_files'].sort()

    def sort_dict_recursively(d):
        new_d = collections.OrderedDict()
        
        if '_files' in d:
            new_d['_files'] = sorted(d['_files'])
        
        sorted_keys = sorted([k for k in d.keys() if k != '_files'])
        for k in sorted_keys:
            if isinstance(d[k], dict):
                new_d[k] = sort_dict_recursively(d[k])
            else:
                new_d[k] = d[k]
        return new_d

    hierarchical_file_structure = sort_dict_recursively(hierarchical_file_structure)

    programming_languages_detected_list = sorted(programming_languages_detected.items(), key=lambda item: item[1], reverse=True)
    all_detected_libraries_list = sorted([item for item, count in all_detected_libraries.items()], key=lambda x: x.lower())
    key_config_files_found_list = sorted([item for item, count in key_config_files_found.items()])
    build_files_found_list = sorted([item for item, count in build_files_found.items()])

    # Detect custom libraries
    detected_custom_libraries = detect_custom_libraries(all_detected_libraries_list, custom_library_summaries)

    summary_languages = ', '.join([f"{lang} ({count})" for lang, count in programming_languages_detected_list[:5]]) if programming_languages_detected_list else 'Unknown'
    summary_libs = ', '.join(all_detected_libraries_list[:10])
    summary_config_files = ', '.join(key_config_files_found_list) if key_config_files_found_list else 'None'
    summary_build_files = ', '.join(build_files_found_list) if build_files_found_list else 'None'

    # Add custom library information to summary
    custom_lib_summary = ""
    if detected_custom_libraries:
        custom_lib_names = [lib_info["library_name"] for lib_info in detected_custom_libraries.values()]
        custom_lib_summary = f" Key custom libraries detected: {', '.join(custom_lib_names)}."

    summary_text = (
        f"The codebase located at '{os.path.abspath(root_folder)}' contains {total_files} files and {total_directories} directories."
        f" The primary programming languages detected are: {summary_languages}."
        f" Key build files identified include: {summary_build_files}."
        f" Important configuration files found are: {summary_config_files}."
        f" A total of {len(all_detected_libraries_list)} unique libraries/dependencies were detected across build/config files."
        f" Top detected libraries: {summary_libs}{'...' if len(all_detected_libraries_list) > 10 else ''}."
        f"{custom_lib_summary}"
        f" This provides foundational metadata and detected components relevant for assessing hard gates."
    )

    return {
        "codebase_summary": {
            "root_path": os.path.abspath(root_folder),
            "total_files": total_files,
            "total_directories": total_directories,
            "languages_detected_counts": dict(programming_languages_detected_list)
        },
        "file_structure": hierarchical_file_structure,
        "build_and_config_analysis": build_and_config_analysis,
        "detected_custom_libraries": detected_custom_libraries,
        "concise_prompt_data": {
            "programming_languages_detected": [lang for lang, _ in programming_languages_detected_list],
            "all_detected_libraries": all_detected_libraries_list,
            "key_config_files_found": key_config_files_found_list,
            "build_files_found": build_files_found_list,
            "detected_custom_libraries": detected_custom_libraries,
            "summary_of_potential_indicators": summary_text
        }
    }

def generate_ai_prompt(concise_data, hard_gates):
    """
    Generates a structured prompt for an AI, incorporating codebase information and hard gates.
    """
    prompt_parts = []
    prompt_parts.append("As a code analyzer for hard gates, I need your initial analysis based on the provided codebase information.")
    prompt_parts.append("Your task is to identify relevant patterns (regular expressions) for all possible combinations across the specified hard gates, considering the detected programming languages, libraries, and file types. Response should be in JSON format, provide the reason why that pattern was also should be mentioned. Also, for each hard gates we should have an intial analysis based on the available libraries")
    prompt_parts.append("\n--- Codebase Overview ---")
    prompt_parts.append(concise_data["summary_of_potential_indicators"])
    prompt_parts.append(f"Detected Programming Languages: {', '.join(concise_data['programming_languages_detected'])}")
    prompt_parts.append(f"Detected Libraries/Dependencies: {', '.join(concise_data['all_detected_libraries'])}")
    prompt_parts.append(f"Key Configuration Files: {', '.join(concise_data['key_config_files_found'])}")
    prompt_parts.append(f"Build Files: {', '.join(concise_data['build_files_found'])}")

    # Add custom library information to prompt
    if concise_data.get("detected_custom_libraries"):
        prompt_parts.append("\n--- Custom Libraries Detected ---")
        for lib_key, lib_info in concise_data["detected_custom_libraries"].items():
            prompt_parts.append(f"- {lib_key}:")
            prompt_parts.append(f"  - Library Name: {lib_info['library_name']}")
            prompt_parts.append(f"  - Category: {lib_info['category']}")
            prompt_parts.append(f"  - Description: {lib_info['description']}")
            prompt_parts.append(f"  - Matched Pattern: {lib_info['matched_pattern']}")
            prompt_parts.append(f"  - Hard Gate Implications:")
            for gate, implications in lib_info['hard_gate_implications'].items():
                prompt_parts.append(f"    - {gate}: {implications}")

    prompt_parts.append("\n--- Hard Gates for Analysis ---")
    for gate in hard_gates:
        prompt_parts.append(f"- {gate}")
    
    prompt_parts.append("\n--- Your Task ---")
    prompt_parts.append("For each hard gate listed above, provide as many regular expression patterns as possible, consider import or equavalent statement based on the technology so that its usage can also be verified. These patterns should be designed to identify relevant code constructs, file names, configuration snippets, or library usages that indicate the presence or absence of measures related to that specific hard gate.")
    prompt_parts.append("Consider the programming languages and libraries identified in the codebase overview when formulating your patterns. Provide patterns that are specifically tailored to detect the required mechanisms (e.g., logging frameworks for 'Logs Searchable/Available', retry annotations/classes for 'Retry Logic').")
    
    # Add specific guidance for custom libraries
    if concise_data.get("detected_custom_libraries"):
        prompt_parts.append("\n--- Custom Library Guidance ---")
        prompt_parts.append("The following custom libraries have been detected in the codebase. Use this information to:")
        prompt_parts.append("1. Generate patterns specific to these libraries' APIs and conventions")
        prompt_parts.append("2. Consider the hard gate implications provided for each library")
        prompt_parts.append("3. Look for library-specific patterns (e.g., @Retryable for Spring Retry, @retry for Tenacity)")
        prompt_parts.append("4. Include patterns for library configuration files and imports")
        prompt_parts.append("5. Consider both positive patterns (indicating implementation) and negative patterns (indicating missing implementation)")
        
        for lib_key, lib_info in concise_data["detected_custom_libraries"].items():
            prompt_parts.append(f"\nFor {lib_key} ({lib_info['category']}):")
            prompt_parts.append(f"- Focus on {lib_info['description']}")
            prompt_parts.append("- Consider the following hard gate implications:")
            for gate, implications in lib_info['hard_gate_implications'].items():
                prompt_parts.append(f"  * {gate}: {implications}")
            
            # Add specific guidance for enterprise libraries
            if lib_key in ["eser", "ebssh", "orchestra"]:
                prompt_parts.append(f"\nEnterprise-Specific Considerations for {lib_key}:")
                if lib_key == "eser":
                    prompt_parts.append("- Look for ESEREventFactoryWrapperAPI usage and initialization")
                    prompt_parts.append("- Check for ApplicationLifecycleEvent and AppLifeCycleEventType usage")
                    prompt_parts.append("- Search for ESERLoggingAugmenter implementations and @Order annotations")
                    prompt_parts.append("- Include patterns for LoglibConfiguration and Spring context setup")
                    prompt_parts.append("- Look for WF_ID, ENVIRONMENT, and correlation ID patterns")
                    prompt_parts.append("- Check for SearoseESERLoggingAugmenter and custom augmenters")
                elif lib_key == "ebssh":
                    prompt_parts.append("- Look for EBSSH starter dependencies in build files")
                    prompt_parts.append("- Check for enterprise authentication and security patterns")
                    prompt_parts.append("- Search for cloud configuration and OAuth2 client patterns")
                    prompt_parts.append("- Include patterns for enterprise framework integration")
                elif lib_key == "orchestra":
                    prompt_parts.append("- Look for Orchestra Framework version and configuration")
                    prompt_parts.append("- Check for WF_ID and ENVIRONMENT field usage")
                    prompt_parts.append("- Search for LoglibConfiguration and Spring integration")
                    prompt_parts.append("- Include patterns for enterprise logging and security")
    
    prompt_parts.append("\n--- Expected Output Format ---")
    prompt_parts.append("For each hard gate, list the regex patterns. Use a format like:")
    prompt_parts.append("Hard Gate Name:")
    prompt_parts.append("  - Pattern 1: `(?i)regex_pattern_here` (Description of what it detects)")
    prompt_parts.append("  - Pattern 2: `(?i)another_pattern` (Another specific detection)")
    prompt_parts.append("  ...and so on.")
    prompt_parts.append("Ensure patterns are case-insensitive where appropriate (`(?i)`).")
    prompt_parts.append("Response should be in JSON format, There must a reasoning statement also why these patterns are relevant included in the response")
    prompt_parts.append("Response should have the technologies identifed and related sumary as well")
    prompt_parts.append("Response should not include the library lists, technology section should have what is relevant. primary technologies only should be listed ")
    
    # Add specific output format for custom libraries
    if concise_data.get("detected_custom_libraries"):
        prompt_parts.append("\n--- Custom Library Output Format ---")
        prompt_parts.append("For each detected custom library, include:")
        prompt_parts.append("- Library-specific patterns that leverage the library's APIs")
        prompt_parts.append("- Configuration patterns for the library")
        prompt_parts.append("- Import/usage patterns for the library")
        prompt_parts.append("- Patterns that indicate proper implementation vs. missing implementation")
        prompt_parts.append("- Consider both positive and negative patterns for comprehensive coverage")
    
    return "\n".join(prompt_parts)


# --- Main execution block for the script ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan a codebase folder to extract file structure and detected libraries/configurations, and generate an AI prompt.")
    parser.add_argument("codebase_path", help="The path to the codebase folder to scan.")
    parser.add_argument("-o", "--output", default="codebase_analysis.json", help="Output JSON file name (default: codebase_analysis.json).")
    parser.add_argument("-p", "--prompt_output", help="Optional: File to save the generated AI prompt to.")
    parser.add_argument("-c", "--config", help="Optional: Path to a custom JSON configuration file.")


    args = parser.parse_args()

    # Load configuration (default or custom)
    app_config = load_config(args.config)

    try:
        analysis_results = scan_codebase(args.codebase_path, app_config)
        
        # Save detailed analysis JSON
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=4, ensure_ascii=False)
            logging.info(f"Analysis complete. Detailed results saved to {args.output}")
        except IOError as e:
            logging.error(f"Could not write analysis results to '{args.output}': {e}")
        
        # Generate and print the AI prompt
        ai_prompt_text = generate_ai_prompt(analysis_results['concise_prompt_data'], app_config["HARD_GATES"])
        
        logging.info("\n" + "="*80)
        logging.info("--- AI Prompt for Hard Gate Analysis ---")
        logging.info("="*80)
        # Use print for the actual prompt output to stdout, as it's the primary interactive output
        print(ai_prompt_text) 
        logging.info("="*80)
        logging.info("--- End of AI Prompt ---")
        logging.info("="*80 + "\n")

        if args.prompt_output:
            try:
                with open(args.prompt_output, 'w', encoding='utf-8') as f:
                    f.write(ai_prompt_text)
                logging.info(f"AI Prompt also saved to {args.prompt_output}")
            except IOError as e:
                logging.error(f"Could not write AI prompt to '{args.prompt_output}': {e}")

    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True) # exc_info=True to print traceback