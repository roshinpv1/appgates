# Changelog

All notable changes to the CodeGates VS Code Extension will be documented in this file.

## [2.3.0] - 2025-07-30

### Added
- **Elegant Metric Boxes**: New simple and elegant metric boxes for better visualization of gate results
- **Enhanced Metric Display**: Core metrics (Score, Status, Patterns, Matches, Relevant Files) displayed in clean boxes
- **Enhanced Evaluation Metrics**: Criteria Score and Coverage Score boxes for advanced evaluation
- **Condition Results Visualization**: Visual indicators (✅/❌) for condition results with detailed breakdown
- **Auto Scale Gate Support**: Added support for the new Auto Scale gate (3.18) in the Availability category
- **Improved Client-Side Generation**: Enhanced fallback report generation with metric boxes when server HTML is unavailable
- **VS Code Theme Integration**: Metric boxes adapt to VS Code's light/dark theme using CSS variables

### Enhanced
- **Visual Consistency**: Metric boxes maintain consistent styling across both server-generated and client-side reports
- **Responsive Design**: Metric boxes adapt to different screen sizes with responsive grid layout
- **Color Coding**: Score and status values are color-coded for quick visual interpretation
- **Hover Effects**: Subtle hover effects on metric boxes for better user interaction

### Technical
- **CSS Integration**: Added comprehensive metric box styles to the extension's CSS file
- **JavaScript Enhancement**: Updated client-side report generation to include metric boxes
- **Configuration Option**: Added `codegates.enableMetricBoxes` setting for metric box display control

## [2.2.0] - 2025-07-30

### Added
- **Enhanced Pattern Library Integration**: Full integration with the enhanced pattern library for improved validation accuracy
- **Auto-Scaling Validation**: Comprehensive auto-scaling validation including Kubernetes, Docker, and cloud provider patterns
- **Infrastructure Validation**: Enhanced infrastructure validation patterns for production readiness assessment
- **New Configuration Options**: Added settings for enhanced pattern library, auto-scaling validation, and evaluation modes
- **Improved Pattern Detection**: Better pattern matching with criteria-based evaluation and weighted scoring
- **Enhanced Report Features**: Improved report generation with detailed pattern analysis and coverage metrics

### Enhanced
- **Pattern Library**: Complete migration to enhanced pattern library with criteria-based evaluation
- **Gate Coverage**: Comprehensive coverage of all hard gates with enhanced evaluation metrics
- **Report Accuracy**: Improved accuracy through enhanced pattern matching and scoring algorithms
- **Configuration Management**: Better configuration options for different validation scenarios

### Technical
- **Enhanced Evaluation System**: Criteria-based evaluation with weights and logical operators
- **Performance Optimization**: Improved performance with file limits and progress logging
- **Error Handling**: Better error handling and fallback mechanisms
- **API Integration**: Enhanced API integration for seamless backend communication

## [2.1.0] - 2025-07-29

### Added
- **Enhanced Report Generation**: Improved HTML and JSON report generation with better formatting
- **Gate Numbering System**: Added specific numerical identifiers for each gate (1.10, 1.3, 1.5, etc.)
- **Expansion Button Reordering**: Moved expansion button to the first column for better UX
- **Styled Detail Boxes**: Added elegant boxes for displaying gate details (Score, Status, Patterns, Matches, Relevant Files)
- **Formatted File View**: Restored and enhanced the formatted file view within expanded gate details
- **Dual Repository Support**: Automatic checkout of additional "-cd" repository variants for comprehensive validation
- **Enhanced Pattern Library**: Integration with enhanced pattern library for improved validation accuracy

### Enhanced
- **Report Layout**: Improved report layout with better visual hierarchy and spacing
- **Gate Details Display**: Enhanced gate details with structured information display
- **Repository Processing**: Improved repository handling with support for multiple repository variants
- **Pattern Matching**: Enhanced pattern matching with comprehensive pattern library integration

### Technical
- **HTML Generation**: Improved HTML generation with better structure and styling
- **CSS Styling**: Enhanced CSS styles for better visual presentation
- **Repository Management**: Improved repository cloning and processing logic
- **Pattern Library Integration**: Seamless integration with enhanced pattern library

## [2.0.0] - 2025-07-28

### Added
- **Comprehensive Hard Gate Assessment**: Full integration with CodeGates backend for comprehensive repository validation
- **Real-time Progress Tracking**: Live progress updates during assessment with detailed step information
- **Enhanced Report Generation**: Advanced HTML and JSON report generation with detailed analysis
- **Interactive Gate Details**: Expandable gate details with pattern matches and recommendations
- **Comment Integration**: Ability to add comments to individual gates for team collaboration
- **Screenshot Capture**: Built-in screenshot capture functionality for report documentation
- **JIRA Integration**: Direct upload of reports to JIRA for issue tracking
- **Configuration Management**: Comprehensive settings for API endpoints, timeouts, and validation options

### Enhanced
- **User Interface**: Modern, responsive webview interface with VS Code theme integration
- **Error Handling**: Robust error handling with user-friendly error messages
- **Performance**: Optimized performance with efficient API communication
- **Accessibility**: Improved accessibility with proper ARIA labels and keyboard navigation

### Technical
- **TypeScript Implementation**: Full TypeScript implementation for better type safety
- **VS Code API Integration**: Deep integration with VS Code APIs for seamless user experience
- **Webview Communication**: Efficient communication between extension and webview
- **Configuration System**: Flexible configuration system with workspace and user settings support

## [1.0.0] - 2025-07-27

### Initial Release
- **Basic CodeGates Integration**: Initial integration with CodeGates backend API
- **Repository Assessment**: Basic repository validation functionality
- **Report Generation**: Simple HTML report generation
- **VS Code Extension**: Basic VS Code extension with webview interface 