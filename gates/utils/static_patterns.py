"""
Static Pattern Library for Hard Gate Validation
Comprehensive technology-specific patterns as secondary validation
"""

STATIC_PATTERN_LIBRARY = {
    "STRUCTURED_LOGS": {
        "java": [
            r'\blogger\.(info|debug|error|warn|trace)',
            r'<encoder.*class=.*JsonEncoder.*>',
            r'logback\.xml',
            r'log4j2\.xml'
        ],
        "python": [
            r'logging\.(info|debug|error|warning|critical)',
            r'logger\.(info|debug|error|warning|critical)',
            r'structlog\.',
            r'loguru\.'
        ],
        "javascript": [
            r'console\.(log|info|debug|error|warn)',
            r'logger\.(info|debug|error|warn)',
            r'winston\.',
            r'bunyan\.'
        ]
    },
    
    "AUTOMATED_TESTS": {
        "java": [
            r'@Test',
            r'JUnit',
            r'TestNG',
            r'Mockito'
        ],
        "python": [
            r'def test_',
            r'pytest',
            r'unittest'
        ],
        "javascript": [
            r'describe\(',
            r'it\(',
            r'jest',
            r'mocha'
        ]
    }
}

def get_static_patterns_for_gate(gate_name: str, primary_technologies: list) -> list:
    """Get static patterns for a specific gate and technology stack"""
    patterns = []
    
    if gate_name not in STATIC_PATTERN_LIBRARY:
        return patterns
    
    gate_patterns = STATIC_PATTERN_LIBRARY[gate_name]
    
    # Add patterns for detected technologies
    for tech in primary_technologies:
        tech_key = tech.lower()
        if tech_key in gate_patterns:
            patterns.extend(gate_patterns[tech_key])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_patterns = []
    for pattern in patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)
    
    return unique_patterns

def get_pattern_statistics() -> dict:
    """Get statistics about the static pattern library"""
    stats = {
        'total_gates': len(STATIC_PATTERN_LIBRARY),
        'total_technologies': 0,
        'total_patterns': 0,
        'patterns_by_gate': {},
        'patterns_by_technology': {}
    }
    
    technologies = set()
    for gate_name, gate_patterns in STATIC_PATTERN_LIBRARY.items():
        gate_pattern_count = 0
        for tech, patterns in gate_patterns.items():
            technologies.add(tech)
            pattern_count = len(patterns)
            gate_pattern_count += pattern_count
            stats['total_patterns'] += pattern_count
            
            if tech not in stats['patterns_by_technology']:
                stats['patterns_by_technology'][tech] = 0
            stats['patterns_by_technology'][tech] += pattern_count
        
        stats['patterns_by_gate'][gate_name] = gate_pattern_count
    
    stats['total_technologies'] = len(technologies)
    return stats

def get_supported_technologies() -> list:
    """Get list of all supported technologies"""
    technologies = set()
    for gate_patterns in STATIC_PATTERN_LIBRARY.values():
        for tech in gate_patterns.keys():
            technologies.add(tech)
    return sorted(list(technologies))
