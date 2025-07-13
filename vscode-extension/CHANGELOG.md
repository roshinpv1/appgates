# Change Log

All notable changes to the CodeGates VS Code extension will be documented in this file.

## [1.0.0] - 2024-01-01

### Added
- Initial release of CodeGates VS Code extension
- Real-time hard gate validation for 15 production-critical gates
- Multi-language support (Python, Java, JavaScript, TypeScript, C#)
- Activity bar panel with comprehensive views:
  - Overview dashboard with visual score and statistics
  - Hard Gates tree view organized by priority
  - Issues tree view categorized by severity
  - Recommendations panel with actionable insights
- LLM-enhanced analysis with support for:
  - OpenAI (GPT-4, GPT-3.5-turbo)
  - Anthropic (Claude-3 models)
  - Google (Gemini Pro)
  - Ollama (local models)
  - Custom OpenAI-compatible APIs
- Comprehensive configuration options
- Status bar integration with live updates
- Context menu integration for files and folders
- Inline diagnostics in the editor
- Problem panel integration
- Interactive HTML and JSON report generation
- Auto-scan capabilities (on open, on save)
- Command palette integration
- Webview-based gate details viewer

### Features
- **Workspace Scanning**: Complete project analysis
- **File-Level Scanning**: Quick validation of individual files
- **Real-Time Feedback**: Instant validation results
- **Configurable Thresholds**: Customizable quality standards
- **Exclude Patterns**: Skip irrelevant files and directories
- **Progress Indicators**: Visual feedback during analysis
- **Error Handling**: Robust error reporting and recovery

### Commands
- `CodeGates: Scan Workspace` - Analyze entire workspace
- `CodeGates: Scan Current File` - Analyze active file
- `CodeGates: Show Report` - Open latest HTML report
- `CodeGates: Configure Settings` - Open extension settings
- `CodeGates: Enable LLM Analysis` - Setup AI-powered analysis
- `CodeGates: View Hard Gates` - Show gates reference
- `CodeGates: Refresh Results` - Re-run last analysis
- `CodeGates: Show Gate Details` - View detailed gate information

### Configuration
- Comprehensive settings for all aspects of the extension
- LLM provider configuration with API key management
- Language selection and exclusion patterns
- Report format preferences
- Notification level controls
- Auto-scan behavior settings

### Requirements
- VS Code 1.80.0 or higher
- CodeGates CLI tool installed
- Python 3.8+ for CodeGates execution
- Optional: API keys for LLM providers

### Known Issues
- None at this time

### Future Enhancements
- Integration with CI/CD pipelines
- Custom gate definitions
- Team collaboration features
- Historical trend analysis
- Advanced filtering and search
- Custom report templates 