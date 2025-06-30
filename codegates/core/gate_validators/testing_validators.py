"""
Testing Gate Validators - Validators for testing-related hard gates
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from ...models import Language, FileAnalysis
from .base import BaseGateValidator, GateValidationResult


class AutomatedTestsValidator(BaseGateValidator):
    """Validates automated test coverage and quality"""
    
    def validate(self, target_path: Path, file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate automated test implementation"""
        
        # Detect technologies first
        detected_technologies = self._detect_technologies(target_path, file_analyses)
        
        # Estimate expected count
        expected = self._estimate_expected_count(file_analyses)
        
        # Search for test patterns
        extensions = self._get_file_extensions()
        patterns = self.patterns.get('test_patterns', [])
        
        matches = self._search_files_for_patterns(target_path, extensions, patterns)
        found = len(matches)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches, detected_technologies)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=found,
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            technologies=detected_technologies,
            matches=matches
        )
    
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get automated test patterns for each language"""
        
        if self.language == Language.PYTHON:
            return {
                'test_patterns': [
                    r'def\s+test_\w+\s*\(',
                    r'class\s+Test\w+\s*\(',
                    r'@pytest\.',
                    r'@unittest\.',
                    r'@mock\.',
                    r'assert\s+\w+',
                    r'assertEqual\s*\(',
                    r'assertTrue\s*\(',
                    r'assertFalse\s*\(',
                    r'assertRaises\s*\(',
                    r'pytest\.raises\s*\(',
                    r'unittest\.TestCase',
                    r'from\s+unittest\s+import',
                    r'import\s+pytest',
                    r'import\s+unittest',
                    r'mock\.patch\s*\(',
                    r'@patch\s*\(',
                    r'TestCase\s*\(',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'test_patterns': [
                    r'@Test\s*$',
                    r'@Test\s*\(',
                    r'@BeforeEach',
                    r'@AfterEach',
                    r'@BeforeAll',
                    r'@AfterAll',
                    r'@Mock\s*$',
                    r'@MockBean',
                    r'@InjectMocks',
                    r'@ExtendWith\s*\(',
                    r'@SpringBootTest',
                    r'@WebMvcTest',
                    r'@DataJpaTest',
                    r'assertEquals\s*\(',
                    r'assertTrue\s*\(',
                    r'assertFalse\s*\(',
                    r'assertThrows\s*\(',
                    r'Mockito\.',
                    r'when\s*\(',
                    r'verify\s*\(',
                    r'MockMvc\s+',
                    r'TestRestTemplate',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'test_patterns': [
                    r'describe\s*\(',
                    r'it\s*\(',
                    r'test\s*\(',
                    r'expect\s*\(',
                    r'beforeEach\s*\(',
                    r'afterEach\s*\(',
                    r'beforeAll\s*\(',
                    r'afterAll\s*\(',
                    r'jest\.',
                    r'sinon\.',
                    r'chai\.',
                    r'assert\.',
                    r'should\.',
                    r'\.toBe\s*\(',
                    r'\.toEqual\s*\(',
                    r'\.toHaveBeenCalled',
                    r'\.toThrow\s*\(',
                    r'mount\s*\(',
                    r'shallow\s*\(',
                    r'render\s*\(',
                    r'fireEvent\.',
                    r'screen\.',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'test_patterns': [
                    r'\[Test\]',
                    r'\[TestMethod\]',
                    r'\[Fact\]',
                    r'\[Theory\]',
                    r'\[SetUp\]',
                    r'\[TearDown\]',
                    r'\[TestInitialize\]',
                    r'\[TestCleanup\]',
                    r'Assert\.',
                    r'Should\.',
                    r'Expect\.',
                    r'Mock\.',
                    r'Verify\s*\(',
                    r'Setup\s*\(',
                    r'Returns\s*\(',
                    r'TestContext\s+',
                    r'TestFixture',
                    r'NUnit\.',
                    r'MSTest\.',
                    r'xUnit\.',
                ]
            }
        else:
            return {'test_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get test configuration patterns"""
        return {
            'test_config': [
                'pytest.ini', 'tox.ini', 'jest.config.js', 'karma.conf.js',
                'test.config.js', 'mocha.opts', 'jasmine.json', 
                'phpunit.xml', 'TestConfiguration.cs', 'app.config'
            ]
        }
    
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected test instances"""
        
        # Look for source files that should have corresponding tests
        source_files = len([f for f in lang_files 
                          if not any(test_indicator in f.file_path.lower() 
                                    for test_indicator in ['test', 'spec', '__tests__', 'tests'])])
        
        # Estimate 1-2 test methods per source file
        return max(source_files * 2, file_count // 2)
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess test implementation quality"""
        
        quality_scores = {}
        
        # Check for test framework usage
        framework_patterns = ['@test', 'describe', 'it(', 'def test_', 'assert']
        framework_matches = len([match for match in matches 
                               if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                     for pattern in framework_patterns)])
        
        if framework_matches > 0:
            quality_scores['test_framework'] = min(framework_matches * 2, 15)
        
        # Check for mocking/stubbing
        mock_patterns = ['mock', 'stub', 'spy', 'fake', '@mock', 'mockito']
        mock_matches = len([match for match in matches 
                          if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                for pattern in mock_patterns)])
        
        if mock_matches > 0:
            quality_scores['mocking'] = min(mock_matches * 3, 10)
        
        # Check for assertions
        assertion_patterns = ['assert', 'expect', 'should', 'verify', 'toequal', 'tobe']
        assertion_matches = len([match for match in matches 
                               if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                     for pattern in assertion_patterns)])
        
        if assertion_matches > 0:
            quality_scores['assertions'] = min(assertion_matches * 1, 10)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no tests found"""
        
        return [
            "Implement automated tests for your codebase",
            "Choose appropriate testing framework (pytest, JUnit, Jest, etc.)",
            "Start with unit tests for core business logic",
            "Add integration tests for API endpoints",
            "Implement test coverage reporting",
            "Set up continuous integration with automated testing"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial test implementation"""
        
        return [
            "Increase test coverage for untested modules",
            "Add more edge case testing scenarios",
            "Implement integration and end-to-end tests",
            "Add performance and load testing",
            "Implement test data factories and fixtures"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving test quality"""
        
        return [
            "Add more assertions and edge case testing",
            "Implement property-based testing",
            "Add mutation testing to verify test quality",
            "Implement test performance monitoring",
            "Add visual regression testing for UI components"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]], 
                         detected_technologies: Dict[str, List[str]]) -> List[str]:
        """Generate automated test details"""
        
        if not matches:
            return ["No automated test patterns found"]
        
        details = [f"Found {len(matches)} test implementations"]
        
        # Check for different test types
        test_types = []
        if any('unit' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            test_types.append('Unit tests')
        if any('integration' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            test_types.append('Integration tests')
        if any('e2e' in match.get('matched_text', match.get('match', '')).lower() or 'end-to-end' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            test_types.append('End-to-end tests')
        if any('mock' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            test_types.append('Mocked tests')
        
        if test_types:
            details.append(f"Test types found: {', '.join(test_types)}")
        
        # Check for test frameworks
        frameworks = []
        if any('pytest' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            frameworks.append('pytest')
        if any('junit' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            frameworks.append('JUnit')
        if any('jest' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            frameworks.append('Jest')
        if any('mocha' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            frameworks.append('Mocha')
        if any('nunit' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            frameworks.append('NUnit')
        
        if frameworks:
            details.append(f"Test frameworks found: {', '.join(frameworks)}")
        
        return details
    
    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on test findings"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations() 