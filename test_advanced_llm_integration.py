#!/usr/bin/env python3
"""
Comprehensive Test Script for Advanced LLM Integration
Tests the complete advanced LLM system with CodeGates integration
"""

import os
import sys
import asyncio
import json
import requests
import time
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

# Test configuration
TEST_REPO = "https://github.com/octocat/Hello-World"
TEST_BRANCH = "main"
SERVER_URL = "http://localhost:8000"

class AdvancedLLMIntegrationTest:
    """Test suite for advanced LLM integration"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
    
    async def test_server_health(self):
        """Test server health and basic endpoints"""
        try:
            # Test basic health
            response = requests.get(f"{SERVER_URL}/health")
            if response.status_code == 200:
                self.log_test("Server Health", True, "Server is running")
            else:
                self.log_test("Server Health", False, f"Server returned {response.status_code}")
                return False
            
            # Test advanced LLM health
            response = requests.get(f"{SERVER_URL}/api/v1/advanced/health")
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get("status", "unknown")
                self.log_test("Advanced LLM Health", status == "healthy", f"Status: {status}")
            else:
                self.log_test("Advanced LLM Health", False, f"Health check failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Server Health", False, f"Connection failed: {e}")
            return False
    
    async def test_repository_indexing(self):
        """Test repository indexing"""
        try:
            # Index repository
            index_data = {
                "repository_url": TEST_REPO,
                "branch": TEST_BRANCH,
                "enable_ast_parsing": True,
                "enable_symbol_extraction": True
            }
            
            response = requests.post(f"{SERVER_URL}/api/v1/advanced/index", json=index_data)
            
            if response.status_code == 200:
                result = response.json()
                repo_id = result.get("data", {}).get("repo_id")
                self.log_test("Repository Indexing", True, f"Indexed repo: {repo_id}")
                return repo_id
            else:
                self.log_test("Repository Indexing", False, f"Indexing failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Repository Indexing", False, f"Indexing error: {e}")
            return None
    
    async def test_index_status(self, repo_id: str):
        """Test index status check"""
        try:
            response = requests.get(f"{SERVER_URL}/api/v1/advanced/index/status/{repo_id}")
            
            if response.status_code == 200:
                result = response.json()
                indexed = result.get("data", {}).get("indexed", False)
                self.log_test("Index Status Check", indexed, f"Repository indexed: {indexed}")
                return indexed
            else:
                self.log_test("Index Status Check", False, f"Status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Index Status Check", False, f"Status check error: {e}")
            return False
    
    async def test_context_retrieval(self, repo_id: str):
        """Test context retrieval"""
        try:
            # Test different types of queries
            test_queries = [
                "How is the main function implemented?",
                "What are the key features of this project?",
                "Show me the project structure"
            ]
            
            for query in test_queries:
                context_data = {
                    "query": query,
                    "max_chunks": 8,
                    "search_mode": "hybrid"
                }
                
                response = requests.post(f"{SERVER_URL}/api/v1/advanced/context/{repo_id}", json=context_data)
                
                if response.status_code == 200:
                    result = response.json()
                    chunks = result.get("data", {}).get("chunks", [])
                    self.log_test(f"Context Retrieval: {query[:30]}...", True, f"Retrieved {len(chunks)} chunks")
                else:
                    self.log_test(f"Context Retrieval: {query[:30]}...", False, f"Retrieval failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Context Retrieval", False, f"Retrieval error: {e}")
            return False
    
    async def test_llm_completion(self, repo_id: str):
        """Test LLM completion with context"""
        try:
            # First get context
            context_data = {
                "query": "How is the main function implemented?",
                "max_chunks": 4
            }
            
            response = requests.post(f"{SERVER_URL}/api/v1/advanced/context/{repo_id}", json=context_data)
            
            if response.status_code != 200:
                self.log_test("LLM Completion", False, "Failed to get context for completion")
                return False
            
            context_result = response.json().get("data", {})
            
            # Test completion
            completion_data = {
                "instruction": "Explain the main functionality of this project",
                "context_result": context_result,
                "mode": "chat",
                "stream": False
            }
            
            response = requests.post(f"{SERVER_URL}/api/v1/advanced/complete/{repo_id}", json=completion_data)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("data", {}).get("content", "")
                self.log_test("LLM Completion", True, f"Generated {len(content)} characters")
            else:
                self.log_test("LLM Completion", False, f"Completion failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("LLM Completion", False, f"Completion error: {e}")
            return False
    
    async def test_patch_generation(self, repo_id: str):
        """Test patch generation"""
        try:
            # Get context for patch generation
            context_data = {
                "query": "error handling",
                "max_chunks": 4
            }
            
            response = requests.post(f"{SERVER_URL}/api/v1/advanced/context/{repo_id}", json=context_data)
            
            if response.status_code != 200:
                self.log_test("Patch Generation", False, "Failed to get context for patch")
                return False
            
            context_result = response.json().get("data", {})
            
            # Test patch generation
            patch_data = {
                "instruction": "Add error handling to the main function",
                "context_result": context_result,
                "target_file": "README.md"
            }
            
            response = requests.post(f"{SERVER_URL}/api/v1/advanced/patch/{repo_id}", json=patch_data)
            
            if response.status_code == 200:
                result = response.json()
                patch_content = result.get("data", {}).get("patch_content", "")
                self.log_test("Patch Generation", True, f"Generated patch: {len(patch_content)} characters")
            else:
                self.log_test("Patch Generation", False, f"Patch generation failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Patch Generation", False, f"Patch generation error: {e}")
            return False
    
    async def test_system_stats(self):
        """Test system statistics"""
        try:
            response = requests.get(f"{SERVER_URL}/api/v1/advanced/stats")
            
            if response.status_code == 200:
                result = response.json()
                stats = result.get("data", {})
                
                # Check if stats are available
                has_stats = all([
                    "service" in stats,
                    "vector_store" in stats,
                    "cache" in stats,
                    "embedding" in stats,
                    "retrieval" in stats,
                    "llm_proxy" in stats
                ])
                
                self.log_test("System Statistics", has_stats, f"Stats available: {has_stats}")
                return has_stats
            else:
                self.log_test("System Statistics", False, f"Stats failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("System Statistics", False, f"Stats error: {e}")
            return False
    
    async def test_cleanup(self, repo_id: str):
        """Test cleanup operations"""
        try:
            # Delete index
            response = requests.delete(f"{SERVER_URL}/api/v1/advanced/index/{repo_id}")
            
            if response.status_code == 200:
                self.log_test("Index Cleanup", True, f"Deleted index for {repo_id}")
            else:
                self.log_test("Index Cleanup", False, f"Cleanup failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Index Cleanup", False, f"Cleanup error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Advanced LLM Integration Test Suite")
        print("=" * 50)
        
        # Test 1: Server Health
        if not await self.test_server_health():
            print("❌ Server health check failed, stopping tests")
            return
        
        # Test 2: Repository Indexing
        repo_id = await self.test_repository_indexing()
        if not repo_id:
            print("❌ Repository indexing failed, stopping tests")
            return
        
        # Test 3: Index Status
        await self.test_index_status(repo_id)
        
        # Test 4: Context Retrieval
        await self.test_context_retrieval(repo_id)
        
        # Test 5: LLM Completion
        await self.test_llm_completion(repo_id)
        
        # Test 6: Patch Generation
        await self.test_patch_generation(repo_id)
        
        # Test 7: System Statistics
        await self.test_system_stats()
        
        # Test 8: Cleanup
        await self.test_cleanup(repo_id)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        total_time = time.time() - self.start_time
        print(f"\n⏱️ Total Test Time: {total_time:.2f} seconds")
        
        # Save results
        with open("advanced_llm_test_results.json", "w") as f:
            json.dump({
                "timestamp": time.time(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests/total_tests)*100,
                "total_time": total_time,
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: advanced_llm_test_results.json")

async def main():
    """Main test function"""
    # Check if server is running
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding at {SERVER_URL}")
            print("Please start the server with: python run_integrated_server.py")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server at {SERVER_URL}")
        print("Please start the server with: python run_integrated_server.py")
        return
    
    # Run tests
    test_suite = AdvancedLLMIntegrationTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
