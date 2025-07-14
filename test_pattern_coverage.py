#!/usr/bin/env python3
"""
Test script to compare LLM-generated and static patterns against a codebase.
Reports which patterns work, which don't, and summarizes per gate.
"""

import os
import sys
import json
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

from nodes import ValidateGatesNode
from utils.hard_gates import HARD_GATES
from utils.static_patterns import get_static_patterns_for_gate

def load_sample_metadata(repo_path):
    """
    Scan the repo directory and build a minimal metadata structure.
    This is a simplified version; for full accuracy, use your real scanner.
    """
    file_list = []
    language_stats = {}
    for root, dirs, files in os.walk(repo_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, repo_path)
            ext = os.path.splitext(fname)[1].lower()
            # crude language guess
            if ext in [".py"]:
                lang = "Python"
            elif ext in [".js", ".jsx"]:
                lang = "JavaScript"
            elif ext in [".java"]:
                lang = "Java"
            elif ext in [".cs"]:
                lang = "C#"
            elif ext in [".ts", ".tsx"]:
                lang = "TypeScript"
            else:
                lang = "Other"
            size = os.path.getsize(fpath)
            file_list.append({
                "relative_path": rel_path,
                "type": "Source Code",
                "language": lang,
                "is_binary": False,
                "size": size
            })
            language_stats.setdefault(lang, {"files": 0, "lines": 0})
            language_stats[lang]["files"] += 1
    return {
        "file_list": file_list,
        "language_stats": language_stats,
        "total_files": len(file_list),
        "total_lines": 0
    }

def test_patterns_on_codebase(repo_path, llm_patterns, gates=HARD_GATES):
    """
    Run both LLM and static patterns for all gates, print detailed results.
    """
    print(f"\n🔍 Testing patterns on codebase: {repo_path}\n")
    metadata = load_sample_metadata(repo_path)
    node = ValidateGatesNode()

    for gate in gates:
        gate_name = gate["name"]
        print(f"\n=== Gate: {gate_name} ({gate['display_name']}) ===")
        static_patterns = get_static_patterns_for_gate(gate_name, ["Python", "Java", "JavaScript", "C#", "TypeScript"])
        llm_gate_patterns = llm_patterns.get(gate_name, [])
        print(f"LLM Patterns: {len(llm_gate_patterns)} | Static Patterns: {len(static_patterns)}")

        # Prepare a minimal shared context for this gate
        shared = {
            "repository": {
                "local_path": repo_path,
                "metadata": metadata
            },
            "llm": {
                "patterns": {gate_name: llm_gate_patterns}
            },
            "hard_gates": [gate]
        }
        prep = node.prep(shared)
        # Only run for this gate
        prep["patterns"] = {gate_name: llm_gate_patterns}
        prep["pattern_data"] = {gate_name: {"patterns": llm_gate_patterns}}
        prep["hard_gates"] = [gate]
        results = node.exec(prep)
        result = results[0] if results else None

        if not result:
            print("❌ No result for this gate.")
            continue

        # Print matches for LLM and static patterns
        print(f"Matches found: {result['matches_found']}")
        print(f"Patterns used: {result['patterns_used']}")
        print(f"Status: {result['status']}")
        print("Details:")
        for detail in result.get("details", []):
            print("  -", detail)
        print("Recommendations:")
        for rec in result.get("recommendations", []):
            print("  -", rec)

        # Analyze which patterns matched
        # (Note: This is a summary; for full match details, extend as needed)
        # LLM patterns
        llm_matches = [m for m in result.get("validation_sources", {}).get("llm_patterns", {}).get("matches", [])]
        matched_llm_patterns = set(m["pattern"] for m in llm_matches)
        unmatched_llm = [p for p in llm_gate_patterns if p not in matched_llm_patterns]
        if unmatched_llm:
            print("LLM patterns that did NOT match anything:")
            for p in unmatched_llm:
                print("  -", p)
        else:
            print("All LLM patterns matched at least once.")

        # Static pattern analysis
        static_matches = [m for m in result.get("validation_sources", {}).get("static_patterns", {}).get("matches", [])]
        matched_static = set(m["pattern"] for m in static_matches)
        unmatched_static = [p for p in static_patterns if p not in matched_static]
        if unmatched_static:
            print("Static patterns that did NOT match anything:")
            for p in unmatched_static:
                print("  -", p)
        else:
            print("All static patterns matched at least once.")

def main():
    # Path to your test repo (change as needed)
    repo_path = "./sample_repo"
    # Example LLM patterns (replace with real output from your LLM)
    llm_patterns = {
        "STRUCTURED_LOGS": [
            r"logger\.info",
            r"log\.debug",
            r"logging\.info"
        ],
        "AVOID_LOGGING_SECRETS": [
            r"password\s*=",
            r"secret\s*="
        ]
        # ... add more gates as needed
    }
    test_patterns_on_codebase(repo_path, llm_patterns)

if __name__ == "__main__":
    main() 