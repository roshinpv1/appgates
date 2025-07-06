import pytest
from unittest.mock import Mock, patch
from codegates.core.llm_analyzer import LLMAnalyzer, LLMConfig, LLMProvider
from codegates.core.analysis_result import CodeAnalysisResult

@pytest.fixture
def analyzer():
    config = LLMConfig(
        provider=LLMProvider.LOCAL,
        model="test-model",
        temperature=0.1,
        max_tokens=1000
    )
    return LLMAnalyzer(config)

@pytest.fixture
def enhanced_context():
    return {
        'gate_name': 'StructuredLogs',
        'language': 'python',
        'total_matches': 10,
        'severity_distribution': {'HIGH': 2, 'MEDIUM': 5, 'LOW': 3},
        'pattern_types': {
            'string_logging': 5,
            'print_statement': 3,
            'unstructured_error': 2
        },
        'detected_technologies': {
            'framework': ['Django', 'Flask'],
            'libraries': ['logging', 'structlog'],
            'language_features': ['f-strings', 'exception handling']
        },
        'high_priority_issues': [
            {
                'file': 'test.py',
                'line': 10,
                'code': 'print("error occurred")',
                'severity': 'HIGH',
                'priority': 9,
                'suggested_fix': 'Use structured logging',
                'category': 'logging',
                'function_context': {
                    'function_name': 'handle_error',
                    'line_number': 8,
                    'signature': 'def handle_error(error: Exception) -> None:'
                }
            }
        ],
        'enhanced_samples': [
            {
                'file': 'test.py',
                'line': 10,
                'code': 'print("error occurred")',
                'full_line': 'print("error occurred")',
                'severity': 'HIGH',
                'pattern_type': 'string_logging',
                'category': 'logging',
                'function_context': {
                    'function_name': 'handle_error',
                    'line_number': 8,
                    'signature': 'def handle_error(error: Exception) -> None:'
                },
                'suggested_fix': 'Replace with logger.error("Error occurred", exc_info=True)'
            }
        ],
        'coverage_stats': {
            'total_files': 5,
            'high_severity_count': 2,
            'medium_severity_count': 5,
            'low_severity_count': 3,
            'security_issues': 1,
            'functions_affected': 3
        }
    }

def test_parse_json_response(analyzer):
    json_response = '''
    {
        "recommendations": ["Use structured logging", "Add correlation IDs"],
        "quality_insights": ["Good coverage", "Some issues found"],
        "improvement_areas": ["Logging format", "Error context"]
    }
    '''
    
    result = analyzer._parse_llm_response(json_response)
    
    assert 'recommendations' in result
    assert len(result['recommendations']) == 2
    assert 'quality_insights' in result
    assert len(result['quality_insights']) == 2
    assert 'improvement_areas' in result
    assert len(result['improvement_areas']) == 2

def test_parse_invalid_json_response(analyzer):
    invalid_response = "This is not JSON"
    
    result = analyzer._parse_llm_response(invalid_response)
    
    assert 'recommendations' in result
    assert len(result['recommendations']) == 0
    assert 'quality_insights' in result
    assert len(result['quality_insights']) == 0
    assert 'improvement_areas' in result
    assert len(result['improvement_areas']) == 0

def test_enhanced_analysis_response(analyzer, enhanced_context):
    expected_result = CodeAnalysisResult(
        quality_score=75.5,
        security_issues=["Unstructured error logging"],
        patterns_found=["String logging detected"],
        recommendations=["Use logging module", "Add correlation IDs"],
        technology_insights={
            "framework": "Basic Python logging",
            "language": "Python 3.x detected",
            "libraries": "No logging framework used"
        },
        code_smells=["Direct print statements"],
        best_practices=["Use logging module", "Add correlation IDs"]
    )
    
    with patch.object(analyzer, '_call_llm') as mock_call:
        with patch.object(analyzer, '_parse_enhanced_analysis_response') as mock_parse:
            mock_call.return_value = "{}"  # Doesn't matter what we return
            mock_parse.return_value = expected_result
            result = analyzer.analyze_gate_with_enhanced_metadata(enhanced_context)
            
            assert result.quality_score == expected_result.quality_score
            assert result.security_issues == expected_result.security_issues
            assert result.patterns_found == expected_result.patterns_found
            assert result.technology_insights == expected_result.technology_insights
            assert result.code_smells == expected_result.code_smells
            assert result.best_practices == expected_result.best_practices

def test_enhanced_analysis_text_response(analyzer, enhanced_context):
    text_response = """
    Quality Score: 65.5
    
    Security Issues:
    - Unstructured logging found
    - Missing error context
    
    Patterns:
    - Basic print statements
    - String concatenation in logs
    
    Recommendations:
    1. Use structured logging
    2. Add error context
    3. Implement correlation IDs
    """
    
    with patch.object(analyzer, '_call_llm', return_value=text_response):
        result = analyzer.analyze_gate_with_enhanced_metadata(enhanced_context)
        
        assert result.quality_score > 0
        assert len(result.security_issues) > 0
        assert len(result.patterns_found) > 0
        assert len(result.recommendations) > 0

def test_enhanced_recommendation_generation(analyzer, enhanced_context):
    base_recommendations = [
        "Use logging module",
        "Add error handling"
    ]
    
    expected_recommendations = [
        "Implement structured logging with JSON format",
        "Add correlation IDs for request tracing",
        "Use proper log levels (INFO, ERROR, DEBUG)",
        "Include contextual data in logs"
    ]
    
    json_response = '''
    {
        "recommendations": [
            "Implement structured logging with JSON format",
            "Add correlation IDs for request tracing",
            "Use proper log levels (INFO, ERROR, DEBUG)",
            "Include contextual data in logs"
        ]
    }
    '''
    
    with patch.object(analyzer, '_call_llm', return_value=json_response):
        with patch.object(analyzer, '_parse_recommendation_response') as mock_parse:
            mock_parse.return_value = expected_recommendations
            enhanced_recs = analyzer.generate_enhanced_recommendations(enhanced_context, base_recommendations)
            
            assert len(enhanced_recs) == 4
            assert any('JSON' in rec for rec in enhanced_recs)
            assert any('correlation' in rec.lower() for rec in enhanced_recs)

def test_recommendation_generation_fallback(analyzer, enhanced_context):
    base_recommendations = [
        "Use logging module",
        "Add error handling"
    ]
    
    with patch.object(analyzer, '_call_llm', side_effect=Exception('LLM Error')):
        result = analyzer.generate_enhanced_recommendations(enhanced_context, base_recommendations)
        
        assert result == base_recommendations

def test_recommendation_prompt_generation(analyzer, enhanced_context):
    base_recommendations = [
        "Use logging module",
        "Add error handling"
    ]
    
    prompt = analyzer._build_enhanced_recommendation_prompt(enhanced_context, base_recommendations)
    
    assert 'StructuredLogs' in prompt
    assert 'python' in prompt
    assert 'HIGH' in prompt
    assert 'Use logging module' in prompt
    assert 'recommendations' in prompt.lower()
    assert 'json' in prompt.lower()
    assert 'Django' in prompt  # From detected_technologies
    assert 'Flask' in prompt   # From detected_technologies

def test_parse_recommendation_response_json(analyzer):
    json_response = '''
    {
        "recommendations": [
            "Implement structured logging",
            "Add correlation IDs",
            "Use proper log levels"
        ]
    }
    '''
    
    result = analyzer._parse_recommendation_response(json_response)
    
    assert len(result) == 3
    assert all(isinstance(rec, str) for rec in result)
    assert any('structured' in rec.lower() for rec in result)

def test_parse_recommendation_response_text(analyzer):
    text_response = """
    1. Implement structured logging with JSON format
    2. Add correlation IDs for request tracing
    3. Use proper log levels
    4. Include contextual data
    5. Set up log rotation
    6. Configure log aggregation
    """
    
    result = analyzer._parse_recommendation_response(text_response)
    
    assert len(result) <= 5  # Should limit to 5 recommendations
    assert all(len(rec) > 20 for rec in result)  # Each should be meaningful
    assert any('structured' in rec.lower() for rec in result) 