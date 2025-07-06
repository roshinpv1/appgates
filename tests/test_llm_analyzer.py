import pytest
from unittest.mock import Mock, patch
from codegates.core.llm_analyzer import LLMAnalyzer

@pytest.fixture
def analyzer():
    return LLMAnalyzer()

@pytest.fixture
def sample_validation_results():
    return {
        'gate_name': 'StructuredLogs',
        'quality_score': 75.5,
        'coverage_score': 80.0,
        'found_patterns': 15,
        'expected_patterns': 20,
        'severity_distribution': {'high': 2, 'medium': 5, 'low': 8},
        'implementation_details': [
            'JSON logging implemented in auth service',
            'Correlation IDs present in 80% of logs',
            'Log levels properly used across services',
            'Some logs missing structured format',
            'Inconsistent error context in logs'
        ]
    }

def test_split_into_chunks(analyzer, sample_validation_results):
    chunks = analyzer._split_into_chunks(sample_validation_results)
    assert len(chunks) > 0
    assert all('gate_name' in chunk for chunk in chunks)
    assert all('quality_score' in chunk for chunk in chunks)
    assert all('coverage_score' in chunk for chunk in chunks)
    assert all('implementation_details' in chunk for chunk in chunks)

def test_merge_analysis_results(analyzer):
    result1 = {
        'recommendations': ['Improve error handling', 'Add structured logging'],
        'quality_insights': ['Good coverage', 'Missing patterns'],
        'improvement_areas': ['Error handling', 'Logging format']
    }
    
    result2 = {
        'recommendations': ['Add structured logging', 'Implement correlation IDs'],
        'quality_insights': ['Inconsistent format', 'Good practices'],
        'improvement_areas': ['Logging format', 'Tracing']
    }
    
    combined = {
        'recommendations': [],
        'quality_insights': [],
        'improvement_areas': []
    }
    
    analyzer._merge_analysis_results(combined, result1)
    analyzer._merge_analysis_results(combined, result2)
    
    # Check for duplicates removed
    assert len(combined['recommendations']) == 3
    assert len(combined['quality_insights']) == 4
    assert len(combined['improvement_areas']) == 3

def test_fallback_analysis_low_score(analyzer):
    results = {
        'gate_name': 'ErrorHandling',
        'quality_score': 45.0
    }
    
    analysis = analyzer._fallback_analysis(results)
    
    assert len(analysis['recommendations']) == 3
    assert any('low' in rec.lower() for rec in analysis['recommendations'])
    assert len(analysis['quality_insights']) == 2
    assert len(analysis['improvement_areas']) == 3

def test_fallback_analysis_high_score(analyzer):
    results = {
        'gate_name': 'ErrorHandling',
        'quality_score': 85.0
    }
    
    analysis = analyzer._fallback_analysis(results)
    
    assert len(analysis['recommendations']) == 3
    assert any('maintain' in rec.lower() for rec in analysis['recommendations'])
    assert len(analysis['quality_insights']) == 2
    assert len(analysis['improvement_areas']) == 3

def test_analyze_validation_results_integration(analyzer, sample_validation_results):
    with patch.object(analyzer, '_call_llm', return_value='{"recommendations": ["Test"], "quality_insights": ["Test"], "improvement_areas": ["Test"]}'):
        result = analyzer.analyze_validation_results(sample_validation_results)
        
        assert 'recommendations' in result
        assert 'quality_insights' in result
        assert 'improvement_areas' in result
        assert len(result['recommendations']) > 0
        assert len(result['quality_insights']) > 0
        assert len(result['improvement_areas']) > 0

def test_analyze_validation_results_fallback(analyzer, sample_validation_results):
    with patch.object(analyzer, '_call_llm', side_effect=Exception('LLM Error')):
        result = analyzer.analyze_validation_results(sample_validation_results)
        
        assert 'recommendations' in result
        assert 'quality_insights' in result
        assert 'improvement_areas' in result
        assert len(result['recommendations']) > 0
        assert len(result['quality_insights']) > 0
        assert len(result['improvement_areas']) > 0

def test_format_details_truncation(analyzer):
    long_details = ['A' * 1000 for _ in range(5)]  # 5KB of data
    formatted = analyzer._format_details(long_details)
    
    assert len(formatted) <= 2000
    assert '...' in formatted  # Should include truncation indicator

def test_create_analysis_prompt(analyzer):
    chunk = {
        'gate_name': 'TestGate',
        'quality_score': 75.0,
        'coverage_score': 80.0,
        'implementation_details': ['Detail 1', 'Detail 2']
    }
    
    prompt = analyzer._create_analysis_prompt(chunk)
    
    assert 'TestGate' in prompt
    assert '75.0' in prompt
    assert '80.0' in prompt
    assert 'Detail 1' in prompt
    assert 'Detail 2' in prompt
    assert 'recommendations' in prompt.lower()
    assert 'quality insights' in prompt.lower()
    assert 'improvement areas' in prompt.lower() 