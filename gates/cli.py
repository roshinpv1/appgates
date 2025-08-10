#!/usr/bin/env python3
"""
CodeGates CLI - Command Line Interface
"""

import sys
import os
import uuid
import tempfile
import click
from pathlib import Path
from typing import Optional

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow import create_static_only_flow
from utils.hard_gates import HARD_GATES
from utils.llm_client import LLMProvider


@click.group()
@click.version_option(version="2.0.0", prog_name="CodeGates")
def main():
    """
    CodeGates - Hard Gate Validation System
    
    A comprehensive tool for validating enterprise security and reliability standards
    in your codebase using AI-powered pattern generation.
    """
    pass


@main.command()
@click.argument('repository_url')
@click.option('--branch', '-b', default='main', help='Branch to scan (default: main)')
@click.option('--token', '-t', envvar='GITHUB_TOKEN', help='GitHub token (optional, from env GITHUB_TOKEN)')
@click.option('--threshold', '-q', default=70, type=int, help='Quality threshold (default: 70)')
@click.option('--output', '-o', default='./reports', help='Output directory for reports (default: ./reports)')
@click.option('--format', '-f', type=click.Choice(['html', 'json', 'both']), default='both', 
              help='Report format (default: both)')
@click.option('--llm-provider', type=click.Choice(['openai', 'anthropic', 'gemini', 'ollama', 'local', 'enterprise', 'apigee', 'auto']), 
              default='auto', help='LLM provider to use (default: auto)')
@click.option('--llm-model', help='LLM model to use (e.g., gpt-4, claude-3-sonnet-20240229)')
@click.option('--llm-url', envvar='LLM_URL', help='LLM service URL (from env LLM_URL)')
@click.option('--llm-api-key', envvar='LLM_API_KEY', help='LLM API key (from env LLM_API_KEY)')
@click.option('--llm-temperature', type=float, default=0.1, help='LLM temperature (default: 0.1)')
@click.option('--llm-max-tokens', type=int, default=4000, help='LLM max tokens (default: 4000)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def scan(repository_url: str, branch: str, token: Optional[str], threshold: int, 
         output: str, format: str, llm_provider: str, llm_model: Optional[str], 
         llm_url: Optional[str], llm_api_key: Optional[str], llm_temperature: float, 
         llm_max_tokens: int, verbose: bool):
    """
    Scan a repository for hard gate compliance.
    
    REPOSITORY_URL: Git repository URL (GitHub, GitLab, etc.)
    
    Examples:
    
        # Scan public repository with auto LLM detection
        codegates scan https://github.com/owner/repo
        
        # Scan with specific LLM provider
        codegates scan https://github.com/owner/repo --llm-provider openai --llm-model gpt-4
        
        # Scan with local LLM
        codegates scan https://github.com/owner/repo --llm-provider local --llm-url http://localhost:11434/v1
        
        # Scan with enterprise Apigee LLM
        codegates scan https://github.com/owner/repo --llm-provider apigee
        
        # Scan private repository with token
        codegates scan https://github.com/owner/private-repo --token ghp_xxxx
        
        # Scan with custom threshold and output
        codegates scan https://github.com/owner/repo --threshold 80 --output ./my-reports
        
        # Generate only HTML report
        codegates scan https://github.com/owner/repo --format html
    """
    
    if verbose:
        click.echo("🚀 CodeGates - Hard Gate Validation System")
        click.echo("=" * 50)
        click.echo(f"Repository: {repository_url}")
        click.echo(f"Branch: {branch}")
        click.echo(f"Threshold: {threshold}%")
        click.echo(f"Output: {output}")
        click.echo(f"Format: {format}")
        click.echo(f"Token: {'✓ Provided' if token else '✗ Not provided'}")
        click.echo(f"LLM Provider: {llm_provider}")
        if llm_model:
            click.echo(f"LLM Model: {llm_model}")
        if llm_url:
            click.echo(f"LLM URL: {llm_url}")
    
    # Initialize shared store
    shared = {
        "request": {
            "repository_url": repository_url,
            "branch": branch,
            "github_token": token,
            "threshold": threshold,
            "scan_id": str(uuid.uuid4()),
            "output_dir": output,
            "report_format": format,
            "verbose": verbose
        },
        "llm_config": {
            "provider": llm_provider,
            "model": llm_model,
            "url": llm_url,
            "api_key": llm_api_key,
            "temperature": llm_temperature,
            "max_tokens": llm_max_tokens
        },
        "repository": {
            "local_path": None,
            "metadata": {}
        },
        "config": {
            "build_files": {},
            "config_files": {},
            "dependencies": []
        },
        "llm": {
            "prompt": None,
            "response": None,
            "patterns": {},
            "source": "unknown",
            "model": "unknown"
        },
        "validation": {
            "gate_results": [],
            "overall_score": 0.0
        },
        "reports": {
            "html_path": None,
            "json_path": None
        },
        "hard_gates": HARD_GATES,
        "temp_dir": tempfile.mkdtemp(prefix="codegates_"),
        "errors": []
    }
    
    try:
        # Create and run the validation flow
        with click.progressbar(length=100, label='Validating repository') as bar:
            # Mock progress updates - in real implementation, nodes would update this
            validation_flow = create_static_only_flow()
            validation_flow.run(shared)
            bar.update(100)
        
        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("🎯 VALIDATION COMPLETE")
        click.echo("=" * 60)
        
        if shared["validation"]["gate_results"]:
            # Overall metrics
            overall_score = shared["validation"]["overall_score"]
            total_files = shared["repository"]["metadata"].get("total_files", 0)
            total_lines = shared["repository"]["metadata"].get("total_lines", 0)
            
            click.echo(f"📊 Overall Score: {overall_score:.1f}%")
            click.echo(f"📁 Total Files: {total_files}")
            click.echo(f"📝 Total Lines: {total_lines}")
            
            # LLM info
            llm_source = shared["llm"].get("source", "unknown")
            llm_model = shared["llm"].get("model", "unknown")
            click.echo(f"🤖 LLM: {llm_source} ({llm_model})")
            
            # Gate summary
            gate_results = shared["validation"]["gate_results"]
            passed = len([g for g in gate_results if g.get("status") == "PASS"])
            failed = len([g for g in gate_results if g.get("status") == "FAIL"])
            warnings = len([g for g in gate_results if g.get("status") == "WARNING"])
            total = len(gate_results)
            
            click.echo(f"✅ Passed Gates: {passed}/{total}")
            if warnings > 0:
                click.echo(f"⚠️  Warning Gates: {warnings}/{total}")
            click.echo(f"❌ Failed Gates: {failed}/{total}")
            
            # Threshold check
            if overall_score >= threshold:
                click.echo(f"🎉 SUCCESS: Score {overall_score:.1f}% meets threshold {threshold}%")
            else:
                click.echo(f"💥 FAILURE: Score {overall_score:.1f}% below threshold {threshold}%")
                sys.exit(1)
            
            # Report locations
            if shared["reports"]["html_path"]:
                click.echo(f"📄 HTML Report: {shared['reports']['html_path']}")
            if shared["reports"]["json_path"]:
                click.echo(f"📄 JSON Report: {shared['reports']['json_path']}")
                
            # Show top failed gates if verbose
            if verbose and failed > 0:
                click.echo("\n🔍 Failed Gates Details:")
                failed_gates = [g for g in gate_results if g.get("status") == "FAIL"]
                for gate in failed_gates[:5]:  # Show top 5
                    click.echo(f"   ❌ {gate.get('gate', 'Unknown')}: {gate.get('score', 0):.1f}%")
                    if gate.get("details"):
                        click.echo(f"      {gate['details'][0]}")
        else:
            click.echo("❌ No validation results generated")
            sys.exit(1)
            
        # Show any errors
        if shared["errors"]:
            click.echo("\n⚠️ Errors encountered:")
            for error in shared["errors"]:
                click.echo(f"   - {error}")
    
    except Exception as e:
        click.echo(f"\n❌ Validation failed: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('report_path')
def view(report_path: str):
    """
    View a generated report.
    
    REPORT_PATH: Path to the HTML or JSON report file
    """
    report_file = Path(report_path)
    
    if not report_file.exists():
        click.echo(f"❌ Report file not found: {report_path}")
        sys.exit(1)
    
    if report_file.suffix.lower() == '.html':
        # Open HTML report in browser
        import webbrowser
        webbrowser.open(f"file://{report_file.absolute()}")
        click.echo(f"📄 Opened HTML report in browser: {report_path}")
    elif report_file.suffix.lower() == '.json':
        # Display JSON report summary
        import json
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)
            
            click.echo(f"📊 Report Summary: {report_path}")
            click.echo(f"   Overall Score: {data.get('summary', {}).get('overall_score', 'N/A')}")
            click.echo(f"   Total Gates: {len(data.get('gates', []))}")
            click.echo(f"   Generated: {data.get('report_metadata', {}).get('generated_at', 'N/A')}")
            click.echo(f"   LLM: {data.get('report_metadata', {}).get('llm_source', 'N/A')} ({data.get('report_metadata', {}).get('llm_model', 'N/A')})")
            
        except json.JSONDecodeError:
            click.echo(f"❌ Invalid JSON report: {report_path}")
            sys.exit(1)
    else:
        click.echo(f"❌ Unsupported report format: {report_file.suffix}")
        sys.exit(1)


@main.command()
def gates():
    """List all available hard gates."""
    click.echo("📋 Available Hard Gates:")
    click.echo("=" * 30)
    
    for i, gate in enumerate(HARD_GATES, 1):
        click.echo(f"{i:2d}. {gate['name']}")
        if gate.get('description'):
            click.echo(f"     {gate['description']}")
        click.echo()


@main.command()
@click.option('--llm-provider', type=click.Choice(['openai', 'anthropic', 'gemini', 'ollama', 'local', 'enterprise', 'apigee']), 
              default='openai', help='LLM provider to test')
@click.option('--llm-model', default='gpt-4', help='LLM model to test')
@click.option('--llm-url', help='LLM service URL (for local/enterprise providers)')
@click.option('--llm-api-key', help='LLM API key')
def test_llm(llm_provider, llm_model, llm_url, llm_api_key):
    """Test LLM connectivity and basic functionality"""
    print("🧪 Testing LLM connectivity...")
    
    try:
        from utils.llm_client import LLMClient, LLMConfig, LLMProvider
        
        # Map provider string to enum
        provider_map = {
            'openai': LLMProvider.OPENAI,
            'anthropic': LLMProvider.ANTHROPIC,
            'gemini': LLMProvider.GEMINI,
            'ollama': LLMProvider.OLLAMA,
            'local': LLMProvider.LOCAL,
            'enterprise': LLMProvider.ENTERPRISE,
            'apigee': LLMProvider.APIGEE
        }
        
        provider = provider_map.get(llm_provider, LLMProvider.OPENAI)
        
        # Create LLM config
        config = LLMConfig(
            provider=provider,
            model=llm_model,
            api_key=llm_api_key,
            base_url=llm_url,
            temperature=0.1,
            max_tokens=100,
            timeout=30
        )
        
        # Create LLM client
        client = LLMClient(config)
        
        if not client.is_available():
            print(f"❌ LLM client not available for provider: {llm_provider}")
            return
        
        print(f"✅ LLM client created successfully")
        print(f"   Provider: {llm_provider}")
        print(f"   Model: {llm_model}")
        print(f"   URL: {llm_url or 'default'}")
        
        # Test prompt
        test_prompt = "Hello! Please respond with 'LLM test successful!'"
        
        # Log the test prompt
        try:
            from utils.prompt_logger import prompt_logger
            
            context_data = {
                "test_type": "cli_llm_test",
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                "llm_url": llm_url or "default",
                "prompt_length": len(test_prompt)
            }
            
            metadata = {
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "timeout": config.timeout
            }
            
            prompt_logger.log_general_prompt(
                gate_name="CLI_TEST",
                prompt=test_prompt,
                context=context_data,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"⚠️ Failed to log test prompt: {e}")
        
        # Make test call
        print("📞 Making test LLM call...")
        response = client.call_llm(test_prompt)
        
        print(f"✅ LLM test successful!")
        print(f"   Response: {response.strip()}")
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 