import os
import json
import pathlib
import re
from collections import defaultdict, Counter

# === Configuration === #
CONFIG_FILES = {
    "java": ["pom.xml", "build.gradle"],
    "python": ["requirements.txt", "setup.py", "pyproject.toml"],
    "dotnet": ["*.csproj", "packages.config"],
    "php": ["composer.json"],
    "nodejs": ["package.json", ".env"],
    "typescript": ["tsconfig.json"],
    "angular": ["angular.json"],
    "react": ["vite.config.js", "vite.config.ts", "webpack.config.js", "next.config.js"]
}

EXT_TO_LANG = {
    ".java": "Java",
    ".py": "Python",
    ".cs": "C#",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".php": "PHP",
    ".jsx": "React (JSX)",
    ".tsx": "React (TSX)",
    ".html": "HTML",
    ".xml": "XML",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".properties": "Java Properties",
    ".env": "ENV",
    ".jmx": "jmx",
    ".sql": "sql",
    ".gradle": "gradle"
}

# File classification
def classify_file(file_path):
    ext = pathlib.Path(file_path).suffix.lower()
    if "test" in file_path.lower():
        return "test"
    if ext in EXT_TO_LANG:
        if ext in [".html", ".css", ".scss"]:
            return "web"
        elif ext in [".json", ".xml", ".yml", ".yaml", ".properties", ".env", ".toml", ".jmx", ".sql"]:
            return "config"
        return "source"
    return "other"

# Safe read
def read_file_safe(filepath, max_bytes=20000):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read(max_bytes)
    except Exception:
        return ""

# Grouping logic
def group_languages(lang_counter):
    groups = {
        "Programming Languages": ["Java", "Python", "C#", "JavaScript", "TypeScript", "PHP", "cmd", "bat"],
        "Markup/Templating": ["HTML", "XML"],
        "Stylesheets": ["css", "scss"],
        "Configuration": ["YAML", "Java Properties", "JSON", "ENV", "jmx", "sql"],
        "Build Scripts": ["gradle"]
    }

    grouped = defaultdict(dict)

    for lang, count in lang_counter.items():
        if lang.lower() in ["", "md", "txt", "png", "svg", "woff", "ttf", "eot", "jar"]:
            continue  # Ignore binary/assets/misc

        matched = False
        for category, keywords in groups.items():
            if lang.lower() in [k.lower() for k in keywords]:
                grouped[category][lang] = count
                matched = True
                break
        if not matched:
            grouped["Uncategorized"][lang] = count

    return dict(grouped)

# === Main Analyzer === #
def analyze_repository(repo_path):
    summary = {
        "total_source_files": 0,
        "total_source_lines": 0,
        "total_test_files": 0,
        "total_test_lines": 0,
        "languages_detected": {},
        "libraries_detected": defaultdict(set),
        "file_structure": defaultdict(list),
    }

    lang_counter = Counter()

    for root, dirs, files in os.walk(repo_path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)
            ext = pathlib.Path(file).suffix.lower()
            lang = EXT_TO_LANG.get(ext, ext.strip('.'))
            file_type = classify_file(full_path)

            try:
                size = os.path.getsize(full_path)
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = sum(1 for _ in f)
            except Exception:
                lines = 0
                size = 0

            if file_type == "source":
                summary["total_source_files"] += 1
                summary["total_source_lines"] += lines
            elif file_type == "test":
                summary["total_test_files"] += 1
                summary["total_test_lines"] += lines

            lang_counter[lang] += 1
            summary["file_structure"][file_type].append(rel_path)

            # Detect libraries from config
            for tool, patterns in CONFIG_FILES.items():
                for pattern in patterns:
                    if pathlib.Path(file).match(pattern):
                        content = read_file_safe(full_path)
                        if tool == "java":
                            matches = re.findall(r"<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>", content, re.DOTALL)
                            for g, a in matches:
                                summary["libraries_detected"]["java"].add(f"{g}:{a}")
                        elif tool == "python":
                            matches = re.findall(r"^\s*([a-zA-Z0-9_\-]+)==?[\d\.]+", content, re.MULTILINE)
                            summary["libraries_detected"]["python"].update(matches)
                        elif tool in ["nodejs", "react", "angular", "typescript"]:
                            matches = re.findall(r'"([a-zA-Z0-9_\-]+)"\s*:\s*"[\d\^~\.]+"', content)
                            summary["libraries_detected"][tool].update(matches)

    summary["languages_detected"] = group_languages(lang_counter)
    summary["libraries_detected"] = {k: sorted(list(v)) for k, v in summary["libraries_detected"].items()}
    summary["file_structure"] = dict(summary["file_structure"])
    return summary

# === CLI Entry Point === #
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Summarize a source code repository.")
    parser.add_argument("repo_path", help="Path to the repository")
    parser.add_argument("--output", help="Output JSON file", default="repo_summary.json")
    args = parser.parse_args()

    summary = analyze_repository(args.repo_path)

    with open(args.output, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Analysis complete. Summary saved to {args.output}")
