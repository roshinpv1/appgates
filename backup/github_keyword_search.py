import argparse
import shutil
import sys
import os


def clone_or_pull_repo(url, dest_dir):
    
    import subprocess
    repo_name = url.split('/')[-1].replace('.git', '')
    repo_path = os.path.join(dest_dir, repo_name)
    env = os.environ.copy()
    env["GIT_SSL_NO_VERIFY"] = "1"
    if not os.path.exists(repo_path):
        print(f"Cloning {url} to {repo_path}")
        subprocess.run(["git", "clone", url, repo_path], check=False, env=env)
        print(f"Cloned {url}")
    else:
        print(f"Pulling {url} from {repo_path}")
        subprocess.run(["git", "-C", repo_path, "pull"], check=False, env=env)
        print(f"Pulled {url}")
    return repo_path

def search_keyword_in_repo(repo_path, keyword):
    """Searches for a keyword in all files within a repository, skipping binary and irrelevant files."""
    matches = []
    for root, dirs, files in os.walk(repo_path):
        # Skip .git and __pycache__ directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Try to read a small chunk to check if it's a text file
                with open(file_path, 'rb') as f:
                    chunk = f.read(1024)
                    try:
                        chunk.decode('utf-8')
                    except UnicodeDecodeError:
                        continue  # Skip binary files
                # Now read as text
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            matches.append((file_path, line_num, line.strip()))
            except Exception:
                # Silently skip files that can't be read as text
                continue
    return matches

def get_github_repos(url, token):
    """Fetches repository URLs for an organization or user, public only if no token."""
    import requests
    parts = url.rstrip('/').split('/')
    if len(parts) < 2:
        raise ValueError("Invalid GitHub root URL")
    org_or_user = parts[-1]
    api_urls = [
        f"https://api.github.com/users/{org_or_user}/repos?per_page=100",
        f"https://api.github.com/orgs/{org_or_user}/repos?per_page=100"
    ]
    headers = {"Authorization": f"token {token}"} if token else {}
    repos = []
    for api_url in api_urls:
        resp = requests.get(api_url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                repos.extend(data)
    if not repos:
        raise Exception("Failed to list repos or no public repos found.")

    if not token:
        repos = [repo for repo in repos if not repo.get("private")]
    return [repo['clone_url'] for repo in repos]

def main():
    parser = argparse.ArgumentParser(description="Search for a keyword in all files of a GitHub repo or all repos in an org/user.")
    parser.add_argument("url", help="GitHub repo URL or org/user root URL")
    parser.add_argument("keyword", help="Keyword to search for")
    parser.add_argument("-t", "--token", help="GitHub token (for private repos or higher rate limits)")
    parser.add_argument("-o", "--output", help="Optional output file to write results (CSV)")
    parser.add_argument("--keep", action="store_true", help="Keep cloned repos after search (default: remove)")
    args = parser.parse_args()

    url = args.url
    keyword = args.keyword
    token = args.token or os.environ.get("GITHUB_TOKEN")
    dest_dir = "./_github_repos"
    os.makedirs(dest_dir, exist_ok=True)
    output_lines = []

    def log_result(line):
        print(line)
        if args.output:
            output_lines.append(line)

    def log_match(repo_url, file_path, line_num):
        line = f"{repo_url},{file_path},{line_num}"
        log_result(line)

    if url.endswith('.git') or url.count('/') > 4:
        # Single repo
        repo_path = clone_or_pull_repo(url, dest_dir)
        matches = search_keyword_in_repo(repo_path, keyword)
        for file_path, line_num, _ in matches:
            log_match(url, file_path, line_num)
        # Remove the repo folder after search unless --keep
        if not args.keep and os.path.isdir(repo_path):
            shutil.rmtree(repo_path)
    else:
        repo_urls = get_github_repos(url, token)
        for repo_url in repo_urls:
            repo_path = clone_or_pull_repo(repo_url, dest_dir)
            matches = search_keyword_in_repo(repo_path, keyword)
            for file_path, line_num, _ in matches:
                log_match(repo_url, file_path, line_num)
            if not args.keep and os.path.isdir(repo_path):
                shutil.rmtree(repo_path)

    if args.output and output_lines:
        with open(args.output, "w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")
        print(f"Results written to {args.output}")

if __name__ == "__main__":
    main() 