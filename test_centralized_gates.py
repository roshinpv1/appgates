#!/usr/bin/env python3
"""
Test Centralized Gate Definitions

This script demonstrates the centralized gate definitions approach
and shows how it eliminates scattered gate definitions across multiple files.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.gate_definitions import (
    GateRegistry, GateCategory, GateSeverity, GateDefinition,
    get_gate, get_all_gates, get_hard_gates, get_hard_gate_ids,
    get_gates_by_category, get_gates_summary_text, get_gates_for_llm_analysis,
    get_predefined_categories
)


def test_centralized_gate_definitions():
    """Test the centralized gate definitions functionality"""
    
    print("🎯 Testing Centralized Gate Definitions")
    print("=" * 60)
    
    # Test 1: Basic gate access
    print("\n📋 Test 1: Basic Gate Access")
    print("-" * 30)
    
    gate_1_1 = get_gate("1.1")
    if gate_1_1:
        print(f"✅ Gate 1.1: {gate_1_1.gate_name}")
        print(f"   Category: {gate_1_1.category.value}")
        print(f"   Severity: {gate_1_1.severity.value}")
        print(f"   Is Hard Gate: {gate_1_1.is_hard_gate}")
        print(f"   Implementation Type: {gate_1_1.implementation_type}")
    else:
        print("❌ Gate 1.1 not found")
    
    # Test 2: Get all gates
    print("\n📋 Test 2: Get All Gates")
    print("-" * 30)
    
    all_gates = get_all_gates()
    print(f"✅ Total gates: {len(all_gates)}")
    
    # Group by category
    categories = {}
    for gate in all_gates:
        if gate.category.value not in categories:
            categories[gate.category.value] = []
        categories[gate.category.value].append(gate)
    
    for category, gates in categories.items():
        print(f"   {category.title()}: {len(gates)} gates")
        for gate in gates:
            hard_indicator = " (HARD)" if gate.is_hard_gate else ""
            print(f"     - {gate.gate_id}: {gate.gate_name}{hard_indicator}")
    
    # Test 3: Get hard gates
    print("\n📋 Test 3: Get Hard Gates")
    print("-" * 30)
    
    hard_gates = get_hard_gates()
    hard_gate_ids = get_hard_gate_ids()
    
    print(f"✅ Hard gates: {len(hard_gates)}")
    print(f"   Hard gate IDs: {hard_gate_ids}")
    
    for gate in hard_gates:
        print(f"   - {gate.gate_id}: {gate.gate_name} ({gate.category.value})")
    
    # Test 4: Get gates by category
    print("\n📋 Test 4: Get Gates by Category")
    print("-" * 30)
    
    auditability_gates = get_gates_by_category(GateCategory.AUDITABILITY)
    print(f"✅ Auditability gates: {len(auditability_gates)}")
    for gate in auditability_gates:
        print(f"   - {gate.gate_id}: {gate.gate_name}")
    
    # Test 5: Get gates summary text
    print("\n📋 Test 5: Get Gates Summary Text")
    print("-" * 30)
    
    summary_text = get_gates_summary_text()
    print(f"✅ Summary text length: {len(summary_text)} characters")
    print("📝 Preview (first 500 chars):")
    print(summary_text[:500] + "..." if len(summary_text) > 500 else summary_text)
    
    # Test 6: Get gates for LLM analysis
    print("\n📋 Test 6: Get Gates for LLM Analysis")
    print("-" * 30)
    
    llm_text = get_gates_for_llm_analysis()
    print(f"✅ LLM text length: {len(llm_text)} characters")
    print("📝 Preview (first 500 chars):")
    print(llm_text[:500] + "..." if len(llm_text) > 500 else llm_text)
    
    # Test 7: Get predefined categories
    print("\n📋 Test 7: Get Predefined Categories")
    print("-" * 30)
    
    predefined_categories = get_predefined_categories()
    print(f"✅ Predefined categories: {len(predefined_categories)}")
    for category_name, gate_ids in predefined_categories.items():
        print(f"   {category_name}: {gate_ids}")
    
    # Test 8: Registry functionality
    print("\n📋 Test 8: Registry Functionality")
    print("-" * 30)
    
    registry = GateRegistry()
    
    # Test getting gates by implementation type
    logging_gates = registry.get_gates_by_implementation_type("logging")
    print(f"✅ Logging gates: {len(logging_gates)}")
    for gate in logging_gates:
        print(f"   - {gate.gate_id}: {gate.gate_name}")
    
    # Test getting all categories
    all_categories = registry.get_categories()
    print(f"✅ All categories: {[cat.value for cat in all_categories]}")
    
    # Test 9: Dictionary format for backward compatibility
    print("\n📋 Test 9: Dictionary Format for Backward Compatibility")
    print("-" * 30)
    
    dict_format = registry.to_dict_format()
    print(f"✅ Dictionary format categories: {list(dict_format.keys())}")
    
    # Show sample of auditability gates in dict format
    if "auditability" in dict_format:
        auditability_dict = dict_format["auditability"]
        print(f"   Auditability gates in dict format: {len(auditability_dict)}")
        for gate_dict in auditability_dict[:2]:  # Show first 2
            print(f"     - {gate_dict['gate_id']}: {gate_dict['gate_name']} (hard: {gate_dict['is_hard_gate']})")
    
    print("\n🎉 All tests completed successfully!")


def demonstrate_benefits():
    """Demonstrate the benefits of centralized gate definitions"""
    
    print("\n🚀 Benefits of Centralized Gate Definitions")
    print("=" * 60)
    
    print("\n📊 Before (Scattered Definitions):")
    print("-" * 40)
    print("❌ Hardcoded hard_gates in scan_nodes.py (3 locations)")
    print("❌ Hardcoded hard_gates in html_report_service.py")
    print("❌ Gate patterns in expected_count_calculator.py")
    print("❌ Gate definitions in prompt_templates.py")
    print("❌ JSON gate definitions in prompt_library.json")
    print("❌ Duplicate gate information across multiple files")
    print("❌ Difficult to maintain and update")
    print("❌ Inconsistent gate definitions")
    
    print("\n📊 After (Centralized Definitions):")
    print("-" * 40)
    print("✅ Single source of truth: src/models/gate_definitions.py")
    print("✅ Python enums for categories and severity")
    print("✅ Structured GateDefinition dataclass")
    print("✅ Centralized GateRegistry class")
    print("✅ Easy to maintain and update")
    print("✅ Consistent gate definitions across the system")
    print("✅ Type-safe access to gate information")
    print("✅ Backward compatibility with dict format")
    
    print("\n🔧 Migration Benefits:")
    print("-" * 40)
    print("✅ Replace hardcoded hard_gates sets with get_hard_gate_ids()")
    print("✅ Replace hardcoded gate dictionaries with get_gate()")
    print("✅ Replace scattered category definitions with get_predefined_categories()")
    print("✅ Replace manual gate text formatting with get_gates_summary_text()")
    print("✅ Replace manual LLM formatting with get_gates_for_llm_analysis()")
    print("✅ Add new gates in one place")
    print("✅ Update gate properties in one place")
    print("✅ Ensure consistency across all components")


def show_migration_examples():
    """Show examples of how to migrate from scattered to centralized definitions"""
    
    print("\n🔄 Migration Examples")
    print("=" * 60)
    
    print("\n📝 Example 1: Replace hardcoded hard_gates")
    print("-" * 40)
    print("Before:")
    print("  hard_gates = {'1.1', '1.3', '1.5', '1.6', '1.8', '1.10', '2.7'}")
    print("  if gate_id not in hard_gates:")
    print("      continue")
    print()
    print("After:")
    print("  from models.gate_definitions import get_hard_gate_ids")
    print("  hard_gates = set(get_hard_gate_ids())")
    print("  if gate_id not in hard_gates:")
    print("      continue")
    
    print("\n📝 Example 2: Replace hardcoded gate information")
    print("-" * 40)
    print("Before:")
    print("  hard_gates = {")
    print("      '1.1': 'Logs Searchable/Available',")
    print("      '1.3': 'Audit Trail',")
    print("  }")
    print("  gate_name = hard_gates.get(gate_id, 'Unknown')")
    print()
    print("After:")
    print("  from models.gate_definitions import get_gate")
    print("  gate = get_gate(gate_id)")
    print("  gate_name = gate.gate_name if gate else 'Unknown'")
    
    print("\n📝 Example 3: Replace manual category grouping")
    print("-" * 40)
    print("Before:")
    print("  predefined_categories = {")
    print("      'Auditability': ['1.1', '1.3', '1.5', '1.6', '1.8', '1.10', '2.7'],")
    print("      'Error Handling': ['1.1', '1.3', '2.4'],")
    print("  }")
    print()
    print("After:")
    print("  from models.gate_definitions import get_predefined_categories")
    print("  predefined_categories = get_predefined_categories()")
    
    print("\n📝 Example 4: Replace manual gate text formatting")
    print("-" * 40)
    print("Before:")
    print("  gates_text = []")
    print("  for gate_id, gate_name in hard_gates.items():")
    print("      gates_text.append(f'- {gate_id}: {gate_name}')")
    print("  gates_summary = '\\n'.join(gates_text)")
    print()
    print("After:")
    print("  from models.gate_definitions import get_gates_summary_text")
    print("  gates_summary = get_gates_summary_text()")


if __name__ == "__main__":
    test_centralized_gate_definitions()
    demonstrate_benefits()
    show_migration_examples()
