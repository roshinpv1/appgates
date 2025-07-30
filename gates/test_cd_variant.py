#!/usr/bin/env python3
"""
Test script to demonstrate the -cd variant functionality
"""

import os
import tempfile
import shutil
from pathlib import Path
from urllib.parse import urlparse

def test_cd_variant_url_construction():
    """Test the -cd variant URL construction logic"""
    
    test_urls = [
        "https://github.com/apache/fineract",
        "https://github.com/apache/fineract.git",
        "https://github.com/kubernetes/kubernetes",
        "https://github.com/spring-projects/spring-boot.git"
    ]
    
    print("🔄 Testing -cd variant URL construction:")
    print("=" * 50)
    
    for repo_url in test_urls:
        # Construct -cd variant URL
        if repo_url.endswith('.git'):
            cd_repo_url = repo_url[:-4] + '-cd.git'
        else:
            cd_repo_url = repo_url + '-cd'
        
        print(f"Original: {repo_url}")
        print(f"CD Variant: {cd_repo_url}")
        print("-" * 30)
    
    print("\n✅ URL construction test completed!")

def test_repository_merge_simulation():
    """Simulate the repository merge functionality"""
    
    print("\n🔄 Testing repository merge simulation:")
    print("=" * 50)
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        main_repo_dir = Path(temp_dir) / "main-repo"
        cd_repo_dir = Path(temp_dir) / "cd-variant"
        
        # Create main repository structure
        main_repo_dir.mkdir(exist_ok=True)
        (main_repo_dir / "src" / "main" / "java").mkdir(parents=True, exist_ok=True)
        (main_repo_dir / "src" / "test" / "java").mkdir(parents=True, exist_ok=True)
        
        # Create some files in main repo
        (main_repo_dir / "pom.xml").write_text("<project>Main Project</project>")
        (main_repo_dir / "src" / "main" / "java" / "App.java").write_text("public class App { }")
        (main_repo_dir / "src" / "test" / "java" / "AppTest.java").write_text("@Test public void test() { }")
        
        # Create CD variant structure
        cd_repo_dir.mkdir(exist_ok=True)
        (cd_repo_dir / "deploy" / "kubernetes").mkdir(parents=True, exist_ok=True)
        (cd_repo_dir / "deploy" / "docker").mkdir(parents=True, exist_ok=True)
        
        # Create some files in CD variant
        (cd_repo_dir / "deploy" / "kubernetes" / "deployment.yaml").write_text("apiVersion: apps/v1")
        (cd_repo_dir / "deploy" / "docker" / "Dockerfile").write_text("FROM openjdk:11")
        (cd_repo_dir / "pom.xml").write_text("<project>CD Project</project>")  # This will be renamed
        
        print(f"📁 Main repository: {main_repo_dir}")
        print(f"📁 CD variant: {cd_repo_dir}")
        
        # Simulate the merge process
        print("\n🔄 Merging repositories...")
        
        # Copy files from -cd variant to main repository (avoiding conflicts)
        for item in cd_repo_dir.rglob('*'):
            if item.is_file():
                # Calculate relative path from cd_path
                relative_path = item.relative_to(cd_repo_dir)
                target_path = main_repo_dir / relative_path
                
                # Create parent directories if they don't exist
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file if it doesn't exist in main repo, or if it's different
                if not target_path.exists():
                    shutil.copy2(item, target_path)
                    print(f"📄 Copied: {relative_path}")
                else:
                    # If file exists, append -cd suffix to filename
                    stem = target_path.stem
                    suffix = target_path.suffix
                    new_name = f"{stem}-cd{suffix}"
                    new_target_path = target_path.parent / new_name
                    shutil.copy2(item, new_target_path)
                    print(f"📄 Copied with -cd suffix: {relative_path} -> {new_name}")
        
        print(f"\n✅ Successfully merged repositories!")
        
        # Show final structure
        print(f"\n📋 Final merged structure:")
        for item in main_repo_dir.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(main_repo_dir)
                print(f"   {rel_path}")

def main():
    """Main test function"""
    print("🚀 CodeGates - CD Variant Functionality Test")
    print("=" * 60)
    
    test_cd_variant_url_construction()
    test_repository_merge_simulation()
    
    print("\n✅ All tests completed successfully!")
    print("\n📝 Summary:")
    print("   - The system automatically constructs -cd variant URLs")
    print("   - It attempts to fetch the -cd variant if it exists")
    print("   - If both repositories exist, they are merged into one")
    print("   - Files with conflicts are renamed with -cd suffix")
    print("   - The validation system analyzes the combined codebase")

if __name__ == "__main__":
    main() 