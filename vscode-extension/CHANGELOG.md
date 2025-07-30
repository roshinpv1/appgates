# Changelog

All notable changes to the CodeGates VS Code extension will be documented in this file.

## [2.2.0] - 2024-01-XX

### Added
- **Enhanced Pattern Library Integration**: Added support for the new enhanced pattern library with:
  - Criteria-based evaluation system
  - Comprehensive pattern matching with weights
  - Technology-specific pattern detection
  - File context filtering (config files, source files, test files)
  - AND/OR/NOT logic support for complex pattern matching
- **Auto-Scaling Validation (Gate 3.18)**: Added comprehensive auto-scaling validation including:
  - Kubernetes HorizontalPodAutoscaler patterns
  - Docker Compose scaling configurations
  - Cloud provider auto-scaling groups (AWS, Azure, GCP)
  - Application-level scaling patterns
  - Monitoring and metrics patterns for scaling
- **Infrastructure Validation**: Enhanced infrastructure validation with:
  - Kubernetes deployment patterns
  - Docker containerization patterns
  - Cloud provider infrastructure patterns
  - Load balancer and scaling configurations
- **Enhanced Configuration Options**:
  - `codegates.enableEnhancedPatternLibrary`: Enable enhanced pattern library
  - `codegates.enableAutoScalingValidation`: Enable auto-scaling validation
  - `codegates.enhancedEvaluationMode`: Control evaluation mode (auto/enhanced/legacy)
  - `codegates.includeInfrastructureValidation`: Include infrastructure patterns
- **Improved Pattern Detection**: Enhanced pattern matching with:
  - Weighted pattern scoring
  - Technology-specific pattern recognition
  - File context-aware pattern matching
  - Multi-level criteria evaluation
- **Enhanced Report Features**: Improved reporting with:
  - Auto-scaling gate results and recommendations
  - Infrastructure validation details
  - Enhanced pattern library integration status
  - Comprehensive coverage analysis for new gates

### Improved
- **Pattern Library Integration**: Seamless integration with enhanced pattern library
- **Evaluation System**: Improved criteria-based evaluation with better accuracy
- **Infrastructure Support**: Enhanced support for infrastructure and DevOps patterns
- **Configuration Management**: More granular control over validation features

### Fixed
- **Enhanced Pattern Library Detection**: Fixed issues with enhanced pattern library not being detected
- **Auto-Scaling Gate Display**: Corrected display of auto-scaling gate in reports
- **Pattern Matching Accuracy**: Improved accuracy of infrastructure pattern detection

## [2.1.0] - 2024-01-XX

### Added
- **Enhanced Pattern Details Display**: Added collapsible sections showing detailed pattern information including:
  - Pattern source indicators (static library, LLM-generated, combined)
  - Pattern match counts and confidence levels
  - File-specific pattern matches with line numbers
  - Pattern type categorization and descriptions
- **Improved Coverage Analysis**: Enhanced coverage reporting with:
  - Clear expected vs actual coverage metrics
  - Confidence level indicators (high, medium, low)
  - Coverage result status (exceeds, meets, below expectations)
  - Detailed coverage reasoning and context
- **Gate Applicability Support**: Added support for NOT_APPLICABLE gates:
  - Visual indicators for non-applicable gates
  - Clear status badges and styling
  - Applicability reasoning and explanations
  - Proper exclusion from scoring while maintaining visibility
- **Enhanced UI Components**:
  - Collapsible pattern details sections with smooth animations
  - Interactive coverage analysis panels
  - Enhanced status indicators with color coding
  - Improved file path and line number display
  - Pattern source badges and confidence indicators
- **Responsive Design**: Added mobile-friendly responsive design for enhanced features
- **Dark Theme Support**: Enhanced dark theme compatibility for all new UI components
- **Configuration Option**: Added `codegates.enableEnhancedFeatures` setting to control enhanced features

### Improved
- **Error Handling**: Enhanced error messages with more specific guidance for different failure scenarios
- **Report Display**: Improved HTML report rendering with better structure and styling
- **Performance**: Optimized report loading and display for large repositories
- **Accessibility**: Added proper ARIA attributes and keyboard navigation for collapsible sections

### Fixed
- **Report Generation**: Fixed issues with pattern details not displaying correctly in VS Code webview
- **Status Display**: Corrected NOT_APPLICABLE gate status display and counting
- **Coverage Metrics**: Fixed confusing coverage percentages and made them more logical
- **Pattern Matching**: Improved pattern match display and organization

## [2.0.5] - 2024-01-XX

### Added
- Enhanced error handling for API connection issues
- Better progress reporting during repository scans
- Improved HTML report generation and display
- Support for GitHub Enterprise repositories
- Configuration options for API timeout and retries

### Fixed
- Connection timeout issues with large repositories
- HTML report display in VS Code webview
- Error message clarity and user guidance

## [2.0.4] - 2024-01-XX

### Added
- Support for custom API server URLs
- Enhanced progress reporting
- Better error handling and user feedback

### Fixed
- Connection issues with API server
- Report generation reliability

## [2.0.3] - 2024-01-XX

### Added
- Initial VS Code extension release
- API-driven repository scanning
- HTML report generation
- Basic configuration options

### Features
- Repository URL input and validation
- GitHub token support for private repositories
- Quality threshold configuration
- Real-time scan progress reporting
- HTML report generation and display
- Comment system for gate feedback 