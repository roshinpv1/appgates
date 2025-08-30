"""
Main entry point for CodeGates Scan Process
"""

import asyncio
import json
import argparse
from typing import Dict, Any, Optional

from .flow.scan_flow import ScanFlow


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration"""
    default_config = {
        "cocoindex": {
            "qdrant_path": "./qdrant_data",
            "chunk_size": 1000,
            "chunk_overlap": 300,
            "embedding_model": "text-embedding-nomic-embed-text-v1.5-embedding",
            "included_patterns": [
                "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cs", 
                "*.go", "*.rs", "*.cpp", "*.c", "*.h", "*.hpp", "*.md", "*.mdx"
            ],
            "excluded_patterns": [
                ".*", "node_modules", "__pycache__", "target", "build", "dist", 
                "*.pyc", "*.class", "*.o", "*.so", "*.dylib", "*.dll"
            ]
        },
        "llm": {
            "provider": "local",
            "model": "llama-3.2-3b-instruct",
            "base_url": "http://localhost:1234",
            "temperature": 0.3,
            "max_tokens": 2000
        }
    }
    
    if config_path:
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Merge with default config
                default_config.update(user_config)
        except Exception as e:
            print(f"⚠️ Failed to load config from {config_path}: {e}")
    
    return default_config


async def run_scan(repo_url: str, branch: str = "main", git_token: Optional[str] = None,
                  config_path: Optional[str] = None, scan_id: Optional[str] = None) -> Dict[str, Any]:
    """Run the scan process"""
    try:
        # Load configuration
        config = load_config(config_path)
        
        # Create scan flow
        scan_flow = ScanFlow(config)
        
        # Run scan
        result = await scan_flow.run_scan(
            repo_url=repo_url,
            branch=branch,
            git_token=git_token,
            scan_id=scan_id
        )
        
        return result
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="CodeGates Scan Process")
    parser.add_argument("repo_url", help="Repository URL to scan")
    parser.add_argument("--branch", default="main", help="Branch to scan (default: main)")
    parser.add_argument("--token", help="Git token for private repositories")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--scan-id", help="Custom scan ID")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    # Run scan
    result = asyncio.run(run_scan(
        repo_url=args.repo_url,
        branch=args.branch,
        git_token=args.token,
        config_path=args.config,
        scan_id=args.scan_id
    ))
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"📄 Results saved to: {args.output}")
    else:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
