"""
Hard Gates Definition
Defines all 15 enterprise hard gates for validation
"""

HARD_GATES = [
    {
        "name": "STRUCTURED_LOGS",
        "display_name": "Logs Searchable/Available", 
        "description": "Ensure logs are structured and searchable for operational monitoring",
        "category": "Logging",
        "priority": "high",
        "patterns": {
            "positive": [
                "logger.info",
                "logging.info", 
                "log.info",
                "structured.*log",
                "json.*log"
            ],
            "negative": [
                "print(",
                "System.out.print",
                "console.log"
            ]
        }
    },
    {
        "name": "AVOID_LOGGING_SECRETS",
        "display_name": "Avoid Logging Confidential Data",
        "description": "Prevent sensitive data from being logged accidentally", 
        "category": "Security",
        "priority": "critical",
        "patterns": {
            "violations": [
                "password",
                "secret",
                "token",
                "api_key",
                "private_key",
                "credential"
            ]
        }
    },
    {
        "name": "AUDIT_TRAIL",
        "display_name": "Create Audit Trail Logs",
        "description": "Log critical business operations for audit compliance",
        "category": "Compliance", 
        "priority": "high",
        "patterns": {
            "positive": [
                "audit.*log",
                "audit_trail",
                "business.*log",
                "transaction.*log"
            ]
        }
    },
    {
        "name": "CORRELATION_ID", 
        "display_name": "Tracking ID for Logs",
        "description": "Include correlation IDs for distributed tracing",
        "category": "Observability",
        "priority": "medium",
        "patterns": {
            "positive": [
                "correlation_id",
                "request_id", 
                "trace_id",
                "tracking.*id"
            ]
        }
    },
    {
        "name": "LOG_API_CALLS",
        "display_name": "Log REST API Calls", 
        "description": "Log all API requests and responses for monitoring",
        "category": "API",
        "priority": "medium",
        "patterns": {
            "positive": [
                "api.*log",
                "request.*log",
                "response.*log",
                "endpoint.*log"
            ]
        }
    },
    {
        "name": "LOG_APPLICATION_MESSAGES",
        "display_name": "Log Application Messages",
        "description": "Log important application state changes and events",
        "category": "Logging",
        "priority": "medium", 
        "patterns": {
            "positive": [
                "application.*log",
                "app.*log",
                "business.*event",
                "state.*change"
            ]
        }
    },
    {
        "name": "UI_ERRORS",
        "display_name": "Client UI Errors Logged",
        "description": "Capture and log client-side UI errors",
        "category": "Frontend",
        "priority": "medium",
        "patterns": {
            "positive": [
                "ui.*error",
                "frontend.*error",
                "client.*error",
                "javascript.*error"
            ]
        }
    },
    {
        "name": "RETRY_LOGIC",
        "display_name": "Retry Logic",
        "description": "Implement retry mechanisms for resilient operations",
        "category": "Reliability",
        "priority": "high",
        "patterns": {
            "positive": [
                "retry",
                "@retry",
                "backoff",
                "exponential.*backoff",
                "max_retries"
            ]
        }
    },
    {
        "name": "TIMEOUTS",
        "display_name": "Timeouts in IO Ops", 
        "description": "Set appropriate timeouts for I/O operations",
        "category": "Reliability",
        "priority": "high",
        "patterns": {
            "positive": [
                "timeout",
                "connection.*timeout",
                "read.*timeout",
                "socket.*timeout"
            ]
        }
    },
    {
        "name": "THROTTLING",
        "display_name": "Throttling & Drop Request",
        "description": "Implement rate limiting and request throttling",
        "category": "Performance",
        "priority": "medium",
        "patterns": {
            "positive": [
                "throttle",
                "rate.*limit",
                "rate_limit",
                "rate.*limiter"
            ]
        }
    },
    {
        "name": "CIRCUIT_BREAKERS", 
        "display_name": "Circuit Breakers",
        "description": "Implement circuit breaker pattern for fault tolerance",
        "category": "Reliability",
        "priority": "high",
        "patterns": {
            "positive": [
                "circuit.*breaker",
                "circuit_breaker", 
                "@circuit_breaker",
                "hystrix",
                "resilience4j"
            ]
        }
    },
    {
        "name": "ERROR_LOGS",
        "display_name": "Log System Errors",
        "description": "Comprehensive error logging and exception handling",
        "category": "Error Handling",
        "priority": "high",
        "patterns": {
            "positive": [
                "error.*log",
                "exception.*log",
                "try.*catch",
                "error.*handler"
            ]
        }
    },
    {
        "name": "HTTP_CODES",
        "display_name": "HTTP Error Codes", 
        "description": "Use appropriate HTTP status codes for API responses",
        "category": "API",
        "priority": "medium",
        "patterns": {
            "positive": [
                "http.*status",
                "status.*code",
                "400",
                "401", 
                "403",
                "404",
                "500"
            ]
        }
    },
    {
        "name": "UI_ERROR_TOOLS",
        "display_name": "Client Error Tracking",
        "description": "Integrate client-side error tracking tools",
        "category": "Frontend", 
        "priority": "medium",
        "patterns": {
            "positive": [
                "sentry",
                "bugsnag",
                "rollbar",
                "error.*tracking",
                "crash.*analytics"
            ]
        }
    },
    {
        "name": "AUTOMATED_TESTS",
        "display_name": "Automated Tests",
        "description": "Comprehensive automated test coverage",
        "category": "Testing",
        "priority": "high",
        "patterns": {
            "positive": [
                "test",
                "@test",
                "junit",
                "pytest", 
                "jest",
                "mocha",
                "assert"
            ]
        }
    }
]


def get_gate_by_name(name: str):
    """Get a specific hard gate by name"""
    for gate in HARD_GATES:
        if gate["name"] == name:
            return gate
    return None


def get_gates_by_category(category: str):
    """Get all hard gates in a specific category"""
    return [gate for gate in HARD_GATES if gate["category"] == category]


def get_critical_gates():
    """Get all critical priority hard gates"""
    return [gate for gate in HARD_GATES if gate["priority"] == "critical"]


def get_high_priority_gates():
    """Get all high priority hard gates"""
    return [gate for gate in HARD_GATES if gate["priority"] == "high"] 