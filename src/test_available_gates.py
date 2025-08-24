#!/usr/bin/env python3
"""
Test script to demonstrate the available_gates functionality
"""

from services.prompt_service import PromptService


def test_available_gates():
    """Test the available_gates functionality"""
    
    print("🧪 Testing Available Gates Functionality")
    print("=" * 50)
    
    # Initialize prompt service
    prompt_service = PromptService()
    
    # Test 1: Get gates summary
    print("\n📊 Test 1: Gates Summary")
    print("-" * 30)
    
    summary = prompt_service.get_gates_summary()
    print(f"Total Gates: {summary['total_gates']}")
    print(f"Categories: {', '.join(summary['categories'])}")
    print("Gates by Category:")
    for category, count in summary['gates_by_category'].items():
        print(f"  - {category}: {count} gates")
    
    # Test 2: Get available gates text
    print("\n📝 Test 2: Available Gates Text")
    print("-" * 30)
    
    gates_text = prompt_service.get_available_gates_text()
    print("Available Gates:")
    print(gates_text[:500] + "..." if len(gates_text) > 500 else gates_text)
    
    # Test 3: Get gates by category
    print("\n📂 Test 3: Gates by Category")
    print("-" * 30)
    
    gates_by_category = prompt_service.get_available_gates_by_category()
    for category, gates in gates_by_category.items():
        print(f"\n{category.upper()} ({len(gates)} gates):")
        for gate in gates[:3]:  # Show first 3 gates per category
            print(f"  - {gate['gate_id']}: {gate['gate_name']} ({gate['severity']})")
        if len(gates) > 3:
            print(f"  ... and {len(gates) - 3} more")
    
    # Test 4: Get flat list of gates
    print("\n📋 Test 4: Flat List of Gates")
    print("-" * 30)
    
    flat_gates = prompt_service.get_available_gates_flat()
    print(f"Total gates in flat list: {len(flat_gates)}")
    print("First 5 gates:")
    for gate in flat_gates[:5]:
        print(f"  - {gate['gate_id']}: {gate['gate_name']} ({gate['category']})")
    
    # Test 5: Test prompt formatting with available_gates
    print("\n🔧 Test 5: Prompt Formatting with Available Gates")
    print("-" * 30)
    
    # Test pre-analysis prompt
    pre_analysis_prompt = prompt_service.format_prompt(
        "llm_pre_analysis",
        code_structure="Sample project structure",
        config_files="Sample config files",
        hard_gate_summary="Sample hard gate summary"
    )
    
    if pre_analysis_prompt:
        print("✅ Pre-analysis prompt formatted successfully")
        print("Prompt preview:")
        print(pre_analysis_prompt[:300] + "..." if len(pre_analysis_prompt) > 300 else pre_analysis_prompt)
    else:
        print("❌ Failed to format pre-analysis prompt")
    
    # Test post-analysis prompt
    post_analysis_prompt = prompt_service.format_prompt(
        "llm_post_analysis",
        scan_results="Sample scan results",
        pattern_matches="Sample pattern matches",
        gate_evaluations="Sample gate evaluations",
        repo_context="Sample repo context"
    )
    
    if post_analysis_prompt:
        print("\n✅ Post-analysis prompt formatted successfully")
        print("Prompt preview:")
        print(post_analysis_prompt[:300] + "..." if len(post_analysis_prompt) > 300 else post_analysis_prompt)
    else:
        print("❌ Failed to format post-analysis prompt")
    
    # Test 6: List all available prompts
    print("\n📚 Test 6: Available Prompts")
    print("-" * 30)
    
    prompts = prompt_service.list_prompts()
    print(f"Available prompts ({len(prompts)}):")
    for prompt_id in prompts:
        info = prompt_service.get_prompt_info(prompt_id)
        if info:
            print(f"  - {prompt_id}: {info['description'][:50]}...")
    
    print("\n🎉 Available Gates Test Complete!")


if __name__ == "__main__":
    test_available_gates()
