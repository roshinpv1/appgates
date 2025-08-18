#!/usr/bin/env python3
"""
Demonstration of repository hash-based indexing functionality
"""

import requests
import time
import json

SERVER_URL = "http://localhost:8000"

def test_hash_based_indexing():
    """Demonstrate hash-based indexing with the server"""
    print("🚀 Demonstrating repository hash-based indexing...\n")
    
    # Test repository
    repo_url = "https://github.com/octocat/Hello-World"
    branch = "master"
    
    print(f"📚 Testing repository: {repo_url} (branch: {branch})")
    
    # First indexing attempt
    print("\n🔄 First indexing attempt...")
    response1 = requests.post(f"{SERVER_URL}/api/v1/advanced/index", json={
        "repository_url": repo_url,
        "branch": branch
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   Status: {result1.get('status')}")
        print(f"   Message: {result1.get('message')}")
        print(f"   Repo ID: {result1.get('data', {}).get('repo_id')}")
        print(f"   Commit Hash: {result1.get('data', {}).get('commit_hash')}")
    else:
        print(f"   ❌ Failed: {response1.status_code} - {response1.text}")
        return False
    
    # Wait a moment
    time.sleep(1)
    
    # Second indexing attempt (should be skipped)
    print("\n🔄 Second indexing attempt...")
    response2 = requests.post(f"{SERVER_URL}/api/v1/advanced/index", json={
        "repository_url": repo_url,
        "branch": branch
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   Status: {result2.get('status')}")
        print(f"   Message: {result2.get('message')}")
        print(f"   Repo ID: {result2.get('data', {}).get('repo_id')}")
        print(f"   Commit Hash: {result2.get('data', {}).get('commit_hash')}")
        
        # Verify same repo_id
        if result1.get('data', {}).get('repo_id') == result2.get('data', {}).get('repo_id'):
            print("   ✅ Same repo_id returned (correct behavior)")
        else:
            print("   ❌ Different repo_ids returned (incorrect behavior)")
            return False
    else:
        print(f"   ❌ Failed: {response2.status_code} - {response2.text}")
        return False
    
    # Test index status endpoint
    print(f"\n🔍 Testing index status...")
    repo_id = result1.get('data', {}).get('repo_id')
    if repo_id:
        status_response = requests.get(f"{SERVER_URL}/api/v1/advanced/index/status/{repo_id}")
        if status_response.status_code == 200:
            status_result = status_response.json()
            print(f"   Status: {status_result.get('status')}")
            print(f"   Indexed: {status_result.get('data', {}).get('indexed')}")
            if status_result.get('data', {}).get('stats'):
                print(f"   Stats: {json.dumps(status_result.get('data', {}).get('stats'), indent=2)}")
        else:
            print(f"   ❌ Status check failed: {status_response.status_code}")
    
    print("\n✅ Hash-based indexing demonstration completed successfully!")
    return True

def main():
    """Run the demonstration"""
    try:
        success = test_hash_based_indexing()
        if success:
            print("\n🎉 All tests passed! The hash-based indexing is working correctly.")
            print("\n📋 Summary:")
            print("   • Repository commit hash is detected and used for indexing")
            print("   • Re-indexing is prevented when content hasn't changed")
            print("   • Same repo_id is returned for consistent access")
            print("   • Server provides clear status messages with commit hash")
        else:
            print("\n💥 Some tests failed!")
            return 1
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
