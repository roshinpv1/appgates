import os
import json

# Define the maximum size (in KB) for build file content to include in the prompt
MAX_BUILD_FILE_CONTENT_SIZE_KB = 50
MAX_BUILD_FILE_CONTENT_BYTES = MAX_BUILD_FILE_CONTENT_SIZE_KB * 1024

def get_file_metadata_and_content_recursively(root_dir):
    """
    Recursively captures file metadata and, for specific build files, their content.
    """
    file_metadata = []
    build_file_contents = {}

    # Define patterns for build files whose content we want to read
    # These are typically XML, JSON, or plain text files that list dependencies
    build_file_patterns_to_read_content = [
        "pom.xml",          # Java Maven
        "build.gradle",     # Java Gradle
        ".csproj",          # .NET C# project file
        "package.json",     # Javascript/TypeScript npm/yarn
        "requirements.txt", # Python pip
        "setup.py",         # Python setuptools
        "pyproject.toml"    # Python PEP 518/517
    ]

    # Define patterns for other key config files (we just note their presence)
    other_key_config_patterns = [
        "application.properties", "application.yml", # Java Spring Boot
        "logback.xml", "log4j.properties", "log4j2.xml", # Java Logging
        "appsettings.json", "web.config", "app.config", # .NET Config
        "nlog.config", "serilog.json", # .NET Logging
        "config.py", "settings.py", "logging.conf", ".env", # Python Config
        "config.js", # Javascript/TypeScript general config
        "tsconfig.json", "webpack.config.js", # JS/TS build/dev config
        ".sln" # .NET solution file (just for presence, content is less useful for libs)
    ]

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(full_path, root_dir)
            file_extension = os.path.splitext(filename)[1]

            meta_entry = {
                "relative_path": relative_path,
                "file_name": filename,
                "extension": file_extension
            }
            file_metadata.append(meta_entry)

            # Check if this is a build file whose content we need
            if any(pattern in filename.lower() for pattern in build_file_patterns_to_read_content):
                try:
                    file_size = os.path.getsize(full_path)
                    if file_size > MAX_BUILD_FILE_CONTENT_BYTES:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(MAX_BUILD_FILE_CONTENT_BYTES)
                        build_file_contents[relative_path] = (
                            f"--- TRUNCATED TO {MAX_BUILD_FILE_CONTENT_SIZE_KB}KB ---\n"
                            f"{content}\n"
                            f"--- END TRUNCATED CONTENT ---"
                        )
                    else:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        build_file_contents[relative_path] = content
                except Exception as e:
                    build_file_contents[relative_path] = f"Error reading file content: {e}"

    return file_metadata, build_file_contents

def construct_llm_prompt(repo_metadata, build_file_contents, hard_gates):
    """
    Constructs a prompt for an LLM based on repository file metadata and build file content
    to identify patterns for hard gate evaluation.
    """

    # Summarize file types and their counts
    extension_counts = {}
    for meta in repo_metadata:
        ext = meta["extension"] if meta["extension"] else "[no_extension]"
        extension_counts[ext] = extension_counts.get(ext, 0) + 1

    file_summary = "\n".join([f"- {count} files with extension '{ext}'" for ext, count in sorted(extension_counts.items())])

    # Identify key build/config files (just by presence, content handled separately)
    key_files_identified_by_presence = set()
    # Combine patterns for both content-read and presence-only files for this list
    all_key_file_patterns = [
        "pom.xml", "build.gradle", ".csproj", "package.json", "requirements.txt", "setup.py", "pyproject.toml",
        "application.properties", "application.yml", "logback.xml", "log4j.properties", "log4j2.xml",
        "appsettings.json", "web.config", "app.config", "nlog.config", "serilog.json",
        "config.py", "settings.py", "logging.conf", ".env",
        "config.js", "tsconfig.json", "webpack.config.js", ".sln"
    ]

    for meta in repo_metadata:
        file_name_lower = meta["file_name"].lower()
        for pattern in all_key_file_patterns:
            if pattern in file_name_lower or (pattern.startswith('.') and file_name_lower.endswith(pattern)):
                key_files_identified_by_presence.add(meta["relative_path"])
                break

    key_files_list = "\n".join([f"- {path}" for path in sorted(list(key_files_identified_by_presence))])
    if not key_files_list:
        key_files_list = "No specific key build/config files were identified based on common patterns."

    # Section for build file contents
    build_content_section = ""
    if build_file_contents:
        build_content_section = "\n**Content of Key Build Files (Truncated if large):**\n"
        for path, content in build_file_contents.items():
            build_content_section += f"\n--- File: {path} ---\n"
            build_content_section += content
            build_content_section += "\n--- End File: {path} ---\n"
    else:
        build_content_section = "\nNo content from key build files was included (none found or all too large)."


    hard_gates_str = "\n".join([f"- {gate}" for gate in hard_gates])

    prompt = f"""
You are an expert in software codebase analysis, specializing in identifying logging best practices and security vulnerabilities.
I am providing you with metadata about files from a software repository, including the actual content of some key build files.
My goal is to analyze this codebase for adherence to the following "hard gates" related to application logging:

**Logging Hard Gates:**
{hard_gates_str}

**Repository File Metadata Summary:**
The repository contains a total of {len(repo_metadata)} files.
Here is a summary of file types found:
{file_summary}

**Key Build and Configuration Files Identified (by relative path):**
(These files are important indicators of technology and configuration. Content of some of them is provided below.)
{key_files_list}
{build_content_section}

Based on this file metadata (file names, extensions, and paths) AND the provided content of key build files,
please provide a comprehensive list of **high-level patterns (e.g., keywords, file locations, structural elements, common API calls, specific library names)** that you would expect to find and would look for within the *content* of the application's source and configuration files to evaluate if each of the listed hard gates is correctly implemented.

**Crucially, use the provided build file content to infer the specific logging libraries, frameworks, and technologies in use.** For example, if 'pom.xml' shows 'log4j-core', then suggest patterns specific to Log4j2.

For each hard gate, consider:
1.  **What specific technologies, frameworks, or logging libraries are implied by the build file content?**
2.  **What types of source or configuration files would you analyze for this gate?**
3.  **What specific keywords, regex patterns, or structural elements would indicate the presence, absence, or correct implementation of the hard gate's requirements, tailored to the inferred technologies/libraries?**

Organize your response by hard gate. Be as specific as possible about the patterns you would look for.
"""
    return prompt

if __name__ == "__main__":
    # Define the hard gates as provided in your request
    hard_gates_list = [
        "Logs Searchable/Available",
        "Avoid Logging Confidential Data",
        "Create Audit Trail Logs",
        "Tracking ID for Logs",
        "Log REST API Calls",
        "Log Application Messages",
        "Client UI Errors Logged",
        "Log System Errors",
        "Client Error Tracking"
    ]

    # --- User Input ---
    # IMPORTANT: Replace 'path/to/your/repository' with the actual absolute path to the repository
    # you want to analyze. For example:
    # On Windows: C:\\Users\\YourUser\\Documents\\MyProject
    # On Linux/macOS: /home/youruser/my_project
    repository_root_directory = input("Enter the absolute path to the repository you want to analyze: ")

    if not os.path.isdir(repository_root_directory):
        print(f"Error: Directory '{repository_root_directory}' not found. Please provide a valid path.")
    else:
        print(f"Analyzing repository: {repository_root_directory} for file metadata and build file content...\n")
        
        # 1. Capture file metadata and build file content
        repo_metadata, build_file_contents = get_file_metadata_and_content_recursively(repository_root_directory)
        print(f"Captured metadata for {len(repo_metadata)} files.")
        print(f"Captured content for {len(build_file_contents)} build files.")
        
        # 2. Construct the LLM prompt
        llm_prompt = construct_llm_prompt(repo_metadata, build_file_contents, hard_gates_list)

        print("\n--- Generated LLM Prompt (Copy this text to your LLM) ---")
        print(llm_prompt)
        print("\n--- End of Generated LLM Prompt ---")

        # Optional: Save the prompt to a file for easy copying
        # with open("llm_analysis_prompt_with_content.txt", "w", encoding="utf-8") as f:
        #     f.write(llm_prompt)
        # print("\nPrompt also saved to 'llm_analysis_prompt_with_content.txt'")