"""
Command Line Interface for CodeGates Hard Gate Validation System
"""

import click
import os
import json
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from datetime import datetime
import sys

from codegates.models import Language, GateType, ScanConfig, ReportConfig
from codegates.core.gate_validator import GateValidator
from codegates.core.language_detector import LanguageDetector
from codegates.reports import ReportGenerator
from codegates.core.llm_analyzer import LLMConfig, LLMProvider, LLMIntegrationManager
from codegates.utils.env_loader import EnvironmentLoader
from codegates.api.services.github import GitHubService
from codegates.api.utils import validate_github_token, validate_github_url
from codegates.utils.config_loader import get_config

console = Console()


def display_banner():
    """Display the CodeGates banner"""
    banner = Text.assemble(
        ("█▀▄▀█", "bright_blue"),
        ("█▄█", "bright_cyan"),
        ("▄▀█", "bright_green"),
        ("▀█▀", "bright_yellow"),
        ("██▄", "bright_red"),
        ("▄▀█", "bright_magenta"),
        ("▀█▀", "bright_white"),
        ("██▄", "bright_blue"),
        ("▄▀▀", "bright_cyan"),
        style="bold"
    )
    
    subtitle = Text("Cross-Language Hard Gate Validation & Scoring System", style="italic dim")
    version = Text("v1.0.0", style="dim")
    
    console.print(Panel.fit(
        Text.assemble(banner, "\n", subtitle, "\n", version),
        title="CodeGates",
        border_style="bright_blue"
    ))


@click.group()
@click.version_option(version="1.0.0")
def main():
    """CodeGates - Cross-Language Hard Gate Validation & Scoring System"""
    display_banner()


@main.command()
@click.argument('repository_url')
@click.option('--branch', '-b', default='main', help='Branch to scan (defaults to main)')
@click.option('--token', '-t', envvar='GITHUB_TOKEN', help='GitHub token (optional, required for private repositories)')
@click.option('--threshold', '-q', default=70, type=int, help='Quality threshold (default: 70)')
def scan(repository_url: str, branch: str, token: Optional[str], threshold: int):
    """
    Scan a GitHub repository for code quality.
    
    REPOSITORY_URL should be in the format: https://github.com/owner/repo
    
    Example:
        codegates scan https://github.com/owner/repo -b main -t your_token
    """
    try:
        # Validate repository URL
        if not validate_github_url(repository_url):
            click.echo('Error: Invalid GitHub repository URL format', err=True)
            os.exit(1)
        
        # Initialize GitHub service with or without token
        github_service = GitHubService(token)
        
        # Check repository access
        if not github_service.can_access_repository(repository_url):
            if token:
                click.echo(
                    'Error: Cannot access repository.\n'
                    'Please check if the token has access to this repository.',
                    err=True
                )
            else:
                click.echo(
                    'Error: Repository is private.\n'
                    'You can provide a GitHub token in one of two ways:\n'
                    '1. Use the --token option: codegates scan ... --token your_token\n'
                    '2. Set the GITHUB_TOKEN environment variable\n\n'
                    'Generate a token with repo scope from: https://github.com/settings/tokens',
                    err=True
                )
            os.exit(1)
        
        # Start scan
        click.echo(f'Starting scan of {repository_url} ({branch})...')
        
        # Create temporary directory for cloning
        with click.progressbar(length=100, label='Scanning repository') as bar:
            try:
                # Clone repository
                repo_path = github_service.clone_repository(
                    repository_url,
                    branch,
                    '/tmp/codegates'
                )
                bar.update(20)
                
                # Run analysis
                from codegates.core.gate_validator import GateValidator
                from codegates.core.language_detector import LanguageDetector
                from codegates.models import ScanConfig, Language
                
                # Detect languages
                detector = LanguageDetector()
                languages = detector.detect_languages(Path(repo_path))
                
                if not languages:
                    languages = [Language.PYTHON]  # Default fallback
                
                # Create scan configuration
                config = ScanConfig(
                    target_path=repo_path,
                    languages=languages,
                    min_coverage_threshold=threshold,
                    exclude_patterns=[
                        "node_modules/**", ".git/**", "**/__pycache__/**",
                        "**/target/**", "**/bin/**", "**/obj/**"
                    ]
                )
                
                # Run validation
                validator = GateValidator(config)
                results = validator.validate(Path(repo_path))
                bar.update(70)
                
                # Generate report
                from codegates.reports import generate_report
                report = generate_report(results)
                bar.update(10)
                
                # Cleanup
                github_service.cleanup_repository(repo_path)
                
                # Display results
                click.echo('\nScan Results:')
                click.echo(f'Overall Score: {results.overall_score:.1f}%')
                click.echo('\nQuality Gates:')
                for gate_score in results.gate_scores:
                    status_color = 'green' if gate_score.status == 'PASS' else 'yellow' if gate_score.status == 'WARNING' else 'red'
                    status = click.style(
                        gate_score.status,
                        fg=status_color
                    )
                    click.echo(f'- {gate_score.gate.value}: {status} ({gate_score.final_score:.1f}%)')
                    for detail in gate_score.details[:2]:  # Show first 2 details
                        click.echo(f'  • {detail}')
                
                if results.recommendations:
                    click.echo('\nRecommendations:')
                    for rec in results.recommendations[:5]:  # Show top 5
                        click.echo(f'• {rec}')
                
                # Exit with status code based on threshold
                exit_code = 0 if results.overall_score >= threshold else 1
                click.echo(f'\n{"✅ PASSED" if exit_code == 0 else "❌ FAILED"} - Threshold: {threshold}%')
                os.exit(exit_code)
                
            except Exception as e:
                click.echo(f'\nError: {str(e)}', err=True)
                os.exit(1)
            finally:
                # Ensure cleanup
                if 'repo_path' in locals():
                    github_service.cleanup_repository(repo_path)
    
    except Exception as e:
        click.echo(f'Error: {str(e)}', err=True)
        os.exit(1)


@main.command()
@click.argument('config_path', type=click.Path(path_type=Path))
def init_config(config_path: Path):
    """Initialize a configuration file"""
    
    default_config = {
        "scan": {
            "exclude_patterns": [
                "node_modules/**",
                ".git/**",
                "**/__pycache__/**",
                "**/target/**",
                "**/bin/**",
                "**/obj/**",
                "**/.vscode/**"
            ],
            "include_patterns": [
                "**/*.java",
                "**/*.py",
                "**/*.js",
                "**/*.ts",
                "**/*.cs"
            ],
            "max_file_size": 1048576,
            "min_coverage_threshold": 70.0,
            "min_quality_threshold": 80.0
        },
        "gates": {
            gate.value: {
                "enabled": True,
                "weight": 1.0,
                "threshold": 70.0
            } for gate in GateType
        },
        "reports": {
            "format": "json",
            "include_details": True,
            "include_recommendations": True
        },
        "llm": {
            "enabled": False,
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 8000,
            "api_key_env": "OPENAI_API_KEY"
        }
    }
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        console.print(f"✅ Configuration file created: [bold blue]{config_path}[/bold blue]")
        console.print("Edit the file to customize your validation settings.")
        
    except Exception as e:
        raise click.ClickException(f"Failed to create config file: {str(e)}")


@main.command()
def list_gates():
    """List all available hard gates"""
    
    console.print("\n🚪 Available Hard Gates:\n")
    
    gate_descriptions = {
        GateType.STRUCTURED_LOGS: "Structured logging implementation with proper formatting",
        GateType.AVOID_LOGGING_SECRETS: "Prevention of sensitive data in logs",
        GateType.AUDIT_TRAIL: "Audit logging for critical business operations",
        GateType.CORRELATION_ID: "Request correlation ID tracking",
        GateType.LOG_API_CALLS: "API endpoint logging (entry/exit)",
        GateType.LOG_BACKGROUND_JOBS: "Background job execution logging",
        GateType.UI_ERRORS: "Frontend error handling and reporting",
        GateType.RETRY_LOGIC: "Retry mechanisms for failure recovery",
        GateType.TIMEOUTS: "Timeout configuration for I/O operations",
        GateType.THROTTLING: "Rate limiting and throttling mechanisms",
        GateType.CIRCUIT_BREAKERS: "Circuit breaker pattern for service calls",
        GateType.ERROR_LOGS: "Error logging and exception handling",
        GateType.HTTP_CODES: "Proper HTTP status code usage",
        GateType.UI_ERROR_TOOLS: "Error monitoring tools (Sentry, etc.)",
        GateType.AUTOMATED_TESTS: "Test coverage and quality"
    }
    
    table = Table(title="Hard Gates", show_header=True, header_style="bold magenta")
    table.add_column("Gate", style="dim", width=25)
    table.add_column("Description", width=50)
    
    for gate, description in gate_descriptions.items():
        table.add_row(gate.value.replace('_', ' ').title(), description)
    
    console.print(table)


@main.command()
@click.argument('report_path', type=click.Path(exists=True, path_type=Path))
def view_report(report_path: Path):
    """View a generated report"""
    
    try:
        if report_path.suffix == '.json':
            with open(report_path) as f:
                data = json.load(f)
            _display_json_report(data)
        else:
            console.print(f"Opening report: [bold blue]{report_path}[/bold blue]")
            os.system(f"open '{report_path}'")  # macOS
            
    except Exception as e:
        raise click.ClickException(f"Failed to view report: {str(e)}")


@main.command()
@click.option('--llm-provider', 
              type=click.Choice(['openai', 'anthropic', 'gemini', 'ollama', 'local']),
              default='openai',
              help='LLM provider to test')
@click.option('--llm-model', help='LLM model to test (e.g., gpt-4, claude-3, gemini-pro)')
@click.option('--llm-api-key', help='API key for LLM provider')
@click.option('--llm-base-url', help='Base URL for LLM provider (for local/custom endpoints)')
@click.option('--llm-temperature', type=click.FloatRange(0, 2), default=0.1, 
              help='Temperature for LLM responses (0-2)')
@click.option('--llm-max-tokens', type=int, default=8000, help='Maximum tokens for LLM responses')
def test_llm(llm_provider: str, llm_model: Optional[str], llm_api_key: Optional[str], 
             llm_base_url: Optional[str], llm_temperature: float, llm_max_tokens: int):
    """Test LLM connection and functionality"""
    
    try:
        console.print(f"\n🤖 Testing LLM Provider: [bold blue]{llm_provider}[/bold blue]")
        
        # Create LLM configuration
        llm_config = LLMConfig(
            provider=LLMProvider(llm_provider),
            model=llm_model or _get_default_model(llm_provider),
            api_key=llm_api_key or os.getenv(f"{llm_provider.upper()}_API_KEY"),
            base_url=llm_base_url,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens
        )
        
        # Initialize LLM manager
        llm_manager = LLMIntegrationManager(llm_config)
        
        if not llm_manager.is_enabled():
            console.print("❌ LLM integration failed to initialize", style="bold red")
            return
        
        console.print("✅ LLM integration initialized successfully", style="bold green")
        console.print(f"Model: {llm_config.model}")
        console.print(f"Temperature: {llm_config.temperature}")
        console.print(f"Max Tokens: {llm_config.max_tokens}")
        if llm_config.base_url:
            console.print(f"Base URL: {llm_config.base_url}")
        
        # Test basic functionality
        console.print("\n🔍 Testing basic LLM functionality...")
        
        test_gate_name = "structured_logs"
        test_code_samples = [
            "logger.info('User logged in', user_id=123)",
            "console.log(JSON.stringify({event: 'user_action', data: userData}))"
        ]
        test_language = Language.PYTHON
        test_technologies = {"logging": ["python-logging"], "frameworks": ["flask"]}
        test_recommendations = ["Use structured logging", "Add correlation IDs"]
        
        # Test LLM analysis
        with console.status("[bold green]Calling LLM..."):
            enhancement = llm_manager.enhance_gate_validation(
                test_gate_name,
                [{"match": sample} for sample in test_code_samples],
                test_language,
                test_technologies,
                test_recommendations
            )
        
        if enhancement.get('enhanced_quality_score') is not None:
            console.print("✅ LLM analysis successful", style="bold green")
            console.print(f"Quality Score: {enhancement['enhanced_quality_score']}")
            console.print(f"Enhanced Recommendations: {len(enhancement['llm_recommendations'])}")
            console.print(f"Code Examples: {len(enhancement['code_examples'])}")
            console.print(f"Security Insights: {len(enhancement['security_insights'])}")
        else:
            console.print("⚠️ LLM analysis returned basic results", style="yellow")
        
        console.print("\n🎉 LLM test completed successfully!", style="bold green")
        
    except Exception as e:
        console.print(f"❌ LLM test failed: {str(e)}", style="bold red")
        raise click.ClickException(str(e))


def _load_scan_config(path: Path, languages: tuple, exclude: tuple, 
                     include: tuple, threshold: float, 
                     config_path: Optional[Path]) -> ScanConfig:
    """Load scan configuration from file or parameters"""
    
    config_data = {}
    if config_path:
        with open(config_path) as f:
            config_data = json.load(f)
    
    return ScanConfig(
        target_path=str(path),
        languages=[Language(lang) for lang in languages] if languages else [],
        exclude_patterns=list(exclude) or config_data.get('scan', {}).get('exclude_patterns', []),
        include_patterns=list(include) or config_data.get('scan', {}).get('include_patterns', []),
        min_coverage_threshold=threshold,
        **config_data.get('scan', {})
    )


def _display_results(result, verbose: bool):
    """Display validation results in the console"""
    
    # Overall score
    score_color = "green" if result.overall_score >= 80 else "yellow" if result.overall_score >= 60 else "red"
    console.print(f"\n🎯 Overall Score: [bold {score_color}]{result.overall_score:.1f}%[/bold {score_color}]")
    
    # Gate summary table
    table = Table(title="Gate Validation Results", show_header=True, header_style="bold magenta")
    table.add_column("Gate", style="dim", width=20)
    table.add_column("Expected", justify="right", width=10) 
    table.add_column("Found", justify="right", width=8)
    table.add_column("Coverage", justify="right", width=10)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Status", width=10)
    
    for gate_score in result.gate_scores:
        status_style = "green" if gate_score.final_score >= 80 else "yellow" if gate_score.final_score >= 60 else "red"
        status_icon = "✅" if gate_score.final_score >= 80 else "⚠️" if gate_score.final_score >= 60 else "❌"
        
        table.add_row(
            gate_score.gate.value.replace('_', ' ').title(),
            str(gate_score.expected),
            str(gate_score.found),
            f"{gate_score.coverage:.1f}%",
            f"{gate_score.final_score:.0f}",
            f"[{status_style}]{status_icon}[/{status_style}]"
        )
    
    console.print(table)
    
    # Critical issues
    if result.critical_issues:
        console.print(f"\n🚨 Critical Issues:")
        for issue in result.critical_issues[:5]:  # Show top 5
            console.print(f"   • {issue}")
    
    # Top recommendations
    if result.recommendations:
        console.print(f"\n💡 Top Recommendations:")
        for rec in result.recommendations[:3]:  # Show top 3
            console.print(f"   • {rec}")


def _display_json_report(data):
    """Display JSON report in formatted way"""
    
    console.print(f"\n📊 Report: [bold blue]{data.get('project_name', 'Unknown')}[/bold blue]")
    console.print(f"Language: {data.get('language', 'Unknown')}")
    console.print(f"Overall Score: [bold]{data.get('overall_score', 0):.1f}%[/bold]")
    console.print(f"Files Scanned: {data.get('total_files', 0)}")
    console.print(f"Scan Date: {data.get('timestamp', 'Unknown')}")


def _get_default_model(provider: str) -> str:
    """Get default model for LLM provider"""
    defaults = {
        'openai': 'meta-llama-3.1-8b-instruct',  # Use local model instead
        'anthropic': 'claude-3-sonnet-20240229',
        'gemini': 'gemini-pro',
        'ollama': 'meta-llama-3.1-8b-instruct',
        'local': 'meta-llama-3.1-8b-instruct'  # Default for local OpenAI-compatible APIs
    }
    return defaults.get(provider, 'meta-llama-3.1-8b-instruct')  # Use local model as fallback


@main.group()
def reports():
    """Manage HTML reports"""
    pass


def get_reports_directory_default() -> str:
    """Get the default reports directory from environment configuration"""
    try:
        config = get_config()
        reports_config = config.get_reports_config()
        return reports_config['reports_dir']
    except Exception:
        # Fallback to environment variable or default
        return os.getenv('CODEGATES_REPORTS_DIR', 'reports')


@reports.command()
@click.option('--reports-dir', default=get_reports_directory_default(), type=click.Path(), 
              help=f'Reports directory (default: {get_reports_directory_default()})')
def list(reports_dir):
    """List all saved HTML reports"""
    
    reports_path = Path(reports_dir)
    
    if not reports_path.exists():
        click.echo(f"📁 Reports directory not found: {reports_path}")
        return
    
    report_files = list(reports_path.glob("hard_gate_report_*.html"))
    
    if not report_files:
        click.echo(f"📄 No reports found in: {reports_path}")
        return
    
    click.echo(f"📄 Found {len(report_files)} report(s) in: {reports_path}")
    click.echo()
    
    for report_file in sorted(report_files, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            # Extract scan_id from filename
            scan_id = report_file.stem.replace("hard_gate_report_", "")
            
            # Get file stats
            stat = report_file.stat()
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Format file size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            click.echo(f"🔍 {scan_id}")
            click.echo(f"   📁 File: {report_file.name}")
            click.echo(f"   📊 Size: {size_str}")
            click.echo(f"   🕒 Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo()
            
        except Exception as e:
            click.echo(f"⚠️ Error processing {report_file}: {e}")


@reports.command()
@click.argument('scan_id')
@click.option('--reports-dir', default=get_reports_directory_default(), type=click.Path(), 
              help=f'Reports directory (default: {get_reports_directory_default()})')
def show(scan_id, reports_dir):
    """Show report file path for a specific scan ID"""
    
    reports_path = Path(reports_dir)
    report_file = reports_path / f"hard_gate_report_{scan_id}.html"
    
    if not report_file.exists():
        click.echo(f"❌ Report not found: {report_file}")
        sys.exit(1)
    
    # Get API base URL from environment
    api_base_url = os.getenv('CODEGATES_API_BASE_URL', 'http://localhost:8000')
    api_version_prefix = os.getenv('CODEGATES_API_VERSION_PREFIX', '/api/v1')
    
    click.echo(f"📄 Report file: {report_file.absolute()}")
    click.echo(f"🌐 URL: {api_base_url}{api_version_prefix}/reports/{scan_id}")


@reports.command()
@click.option('--reports-dir', default=get_reports_directory_default(), type=click.Path(), 
              help=f'Reports directory (default: {get_reports_directory_default()})')
@click.option('--older-than', type=int, help='Delete reports older than N days')
@click.option('--all', 'delete_all', is_flag=True, help='Delete all reports')
@click.confirmation_option(prompt='Are you sure you want to delete reports?')
def clean(reports_dir, older_than, delete_all):
    """Clean up old HTML reports"""
    
    reports_path = Path(reports_dir)
    
    if not reports_path.exists():
        click.echo(f"📁 Reports directory not found: {reports_path}")
        return
    
    report_files = list(reports_path.glob("hard_gate_report_*.html"))
    
    if not report_files:
        click.echo(f"📄 No reports found in: {reports_path}")
        return
    
    files_to_delete = []
    
    if delete_all:
        files_to_delete = report_files
    elif older_than:
        cutoff_time = datetime.now().timestamp() - (older_than * 24 * 60 * 60)
        files_to_delete = [f for f in report_files if f.stat().st_mtime < cutoff_time]
    else:
        click.echo("❌ Please specify --all or --older-than option")
        return
    
    if not files_to_delete:
        if older_than:
            click.echo(f"📄 No reports older than {older_than} days found")
        else:
            click.echo("📄 No reports to delete")
        return
    
    deleted_count = 0
    for report_file in files_to_delete:
        try:
            report_file.unlink()
            click.echo(f"🗑️ Deleted: {report_file.name}")
            deleted_count += 1
        except Exception as e:
            click.echo(f"⚠️ Failed to delete {report_file.name}: {e}")
    
    click.echo(f"✅ Deleted {deleted_count} report(s)")


if __name__ == "__main__":
    main() 