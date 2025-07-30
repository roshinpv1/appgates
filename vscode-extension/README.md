# CodeGates Hard Gate Assessment

A comprehensive VS Code extension for validating your repository against production-ready quality gates with enhanced pattern library, auto-scaling validation, and elegant metric boxes.

## Features

### 🎯 **Comprehensive Hard Gate Assessment**
- **15+ Production-Ready Gates**: Validate your codebase against industry-standard quality gates
- **Enhanced Pattern Library**: Advanced pattern matching with criteria-based evaluation
- **Auto-Scaling Validation**: Infrastructure validation including Kubernetes, Docker, and cloud providers
- **Real-time Progress Tracking**: Live updates during assessment with detailed step information

### 📊 **Elegant Metric Boxes**
- **Simple and Clean Design**: Elegant metric boxes for better visualization of gate results
- **Core Metrics Display**: Score, Status, Patterns, Matches, and Relevant Files in clean boxes
- **Enhanced Evaluation Metrics**: Criteria Score and Coverage Score for advanced evaluation
- **Condition Results Visualization**: Visual indicators (✅/❌) for condition results with detailed breakdown
- **VS Code Theme Integration**: Metric boxes adapt to VS Code's light/dark theme

### 🔧 **Enhanced Pattern Library**
The extension leverages an enhanced pattern library that provides:
- **Criteria-based Evaluation**: Advanced evaluation system with weights and logical operators
- **Technology-specific Patterns**: Patterns tailored for different technologies and frameworks
- **File Context Filtering**: Patterns applied based on file types (config, source, test files)
- **Comprehensive Coverage**: Complete coverage of all hard gates with enhanced evaluation

### 🚀 **Infrastructure Validation**
Comprehensive infrastructure validation including:
- **Kubernetes Patterns**: HorizontalPodAutoscaler, replica configurations, scaling policies
- **Docker Patterns**: Docker Compose scaling, container orchestration patterns
- **Cloud Provider Patterns**: AWS Auto Scaling Groups, Azure Scale Sets, GCP Managed Instance Groups
- **Application-level Scaling**: Spring Cloud, thread pools, connection pools

### 📈 **Advanced Reporting**
- **Interactive HTML Reports**: Detailed reports with expandable gate details
- **Pattern Analysis**: Comprehensive pattern matching with confidence levels
- **Coverage Metrics**: Detailed coverage analysis with expected vs actual metrics
- **Recommendations**: Actionable recommendations for each gate
- **Comment Integration**: Add comments to individual gates for team collaboration

## Hard Gates Overview

| Gate Number | Gate Name | Category | Description |
|-------------|-----------|----------|-------------|
| 1.10 | Avoid Logging Confidential Data | Auditability | Ensure sensitive data is not logged |
| 1.3 | Create Audit Trail Logs | Auditability | Implement comprehensive audit logging |
| 1.5 | Tracking ID For Log Messages | Auditability | Add correlation IDs to log messages |
| 1.6 | Log REST API Calls | Auditability | Log all API calls for monitoring |
| 1.8 | Log Application Messages | Auditability | Log application-level messages |
| 2.7 | Client UI Errors Logged | Auditability | Log client-side errors |
| 1.12 | Retry Logic | Availability | Implement retry mechanisms |
| 1.5 | Set Timeouts on I/O Operations | Availability | Configure appropriate timeouts |
| 3.6 | Throttling, Drop Request | Availability | Implement request throttling |
| 3.9 | Circuit Breakers on Outgoing Requests | Availability | Add circuit breaker patterns |
| 3.18 | Auto Scale | Availability | Implement auto-scaling capabilities |
| 1.1 | Log System Errors | Error Handling | Log system-level errors |
| 1.3 | Use HTTP Standard Error Codes | Error Handling | Use proper HTTP status codes |
| 2.4 | Include Client Error Tracking | Error Handling | Track client-side errors |
| 1.14 | URL Monitoring | Error Handling | Monitor URL availability |
| 2.0 | Automated Regression Testing | Testing | Implement comprehensive testing |

## Enhanced Pattern Library

The extension uses an enhanced pattern library that provides:

### **Criteria-based Evaluation**
- **Weighted Scoring**: Patterns have weights that contribute to overall gate scores
- **Logical Operators**: Support for AND, OR, NOT logic in pattern combinations
- **Technology-specific Patterns**: Patterns tailored for different technologies
- **File Context Filtering**: Patterns applied based on file types and contexts

### **Comprehensive Pattern Coverage**
- **Static Patterns**: Pre-defined patterns for common scenarios
- **LLM-generated Patterns**: AI-generated patterns for specific codebases
- **Combined Evaluation**: Integration of static and dynamic patterns
- **Confidence Levels**: Pattern matching with confidence indicators

## Infrastructure Validation

### **Auto-Scaling Validation (Gate 3.18)**
Comprehensive validation of auto-scaling implementations:

#### **Kubernetes Patterns**
- `HorizontalPodAutoscaler` configurations
- `minReplicas` and `maxReplicas` settings
- `targetCPUUtilizationPercentage` configurations
- Custom metrics for scaling

#### **Docker Patterns**
- `docker-compose` scaling configurations
- `deploy: replicas:` settings
- Container orchestration patterns
- Service scaling configurations

#### **Cloud Provider Patterns**
- **AWS**: Auto Scaling Groups, Launch Configurations
- **Azure**: Virtual Machine Scale Sets, App Service scaling
- **GCP**: Managed Instance Groups, Cloud Run scaling

#### **Application-level Scaling**
- Spring Cloud Kubernetes replicas
- Thread pool configurations
- Connection pool scaling
- Load balancer configurations

## Configuration

### **Enhanced Pattern Library Settings**

| Setting | Description | Default |
|---------|-------------|---------|
| `codegates.enableEnhancedPatternLibrary` | Enable enhanced pattern library for improved validation accuracy | `true` |
| `codegates.enableAutoScalingValidation` | Enable auto-scaling validation for infrastructure assessment | `true` |
| `codegates.enhancedEvaluationMode` | Evaluation mode for gate validation (auto/enhanced/legacy) | `auto` |
| `codegates.includeInfrastructureValidation` | Include infrastructure validation in assessment | `true` |
| `codegates.enableMetricBoxes` | Enable elegant metric boxes for better visualization | `true` |

### **Basic Settings**

| Setting | Description | Default |
|---------|-------------|---------|
| `codegates.apiUrl` | CodeGates API server URL | `http://localhost:8000` |
| `codegates.apiTimeout` | API request timeout in seconds | `300` |
| `codegates.maxRetries` | Maximum API retry attempts | `3` |

## Usage

### **Quick Start**

1. **Install the Extension**: Install the CodeGates extension from the VS Code marketplace
2. **Configure Settings**: Set your API server URL and other preferences
3. **Start Assessment**: Use the command palette (`Ctrl+Shift+P`) and run "CodeGates: Assess Repository"
4. **Enter Repository Details**: Provide the GitHub repository URL and branch
5. **Review Results**: View the comprehensive assessment report with metric boxes

### **Assessment Process**

1. **Repository Analysis**: The extension clones and analyzes your repository
2. **Pattern Matching**: Applies enhanced patterns to identify implementations
3. **Gate Evaluation**: Evaluates each gate against the codebase
4. **Report Generation**: Creates detailed HTML and JSON reports
5. **Metric Display**: Shows results in elegant metric boxes

### **Metric Boxes**

The extension displays comprehensive metrics in elegant boxes:

#### **Core Metrics**
- **Score**: Percentage score with color coding (green for pass, red for fail)
- **Status**: PASS/FAIL/WARNING with appropriate styling
- **Patterns**: Number of patterns used for evaluation
- **Matches**: Number of pattern matches found
- **Relevant Files**: Ratio of relevant files to total files

#### **Enhanced Evaluation Metrics**
- **Criteria Score**: Criteria-based evaluation score
- **Coverage Score**: Coverage-based evaluation score
- **Condition Results**: Visual indicators for individual conditions

## Installation

### **From VS Code Marketplace**
1. Open VS Code
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search for "CodeGates"
4. Click Install

### **From VSIX Package**
1. Download the `.vsix` package
2. In VS Code, go to Extensions
3. Click the "..." menu and select "Install from VSIX..."
4. Select the downloaded package

## Requirements

- **VS Code**: Version 1.74.0 or higher
- **Node.js**: Version 16.0.0 or higher
- **CodeGates Backend**: Running on the configured API server

## Support

For issues, questions, or feature requests:
- **GitHub Issues**: Create an issue in the extension repository
- **Documentation**: Check the comprehensive documentation
- **Community**: Join the CodeGates community discussions

## Contributing

We welcome contributions! Please see our contributing guidelines for details on:
- Code style and standards
- Testing requirements
- Pull request process
- Development setup

## License

This extension is licensed under the MIT License. See the LICENSE file for details. 