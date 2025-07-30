"""
Hard Gates Definition
Defines all 15 enterprise hard gates for validation
"""

# Gate Number Mapping
GATE_NUMBER_MAPPING = {
    "ALERTING_ACTIONABLE": "1.1",
    "LOG_APPLICATION_MESSAGES": "1.2",
    "AVOID_LOGGING_SECRETS": "1.10",
    "AUDIT_TRAIL": "1.3", 
    "CORRELATION_ID": "1.5",
    "LOG_API_CALLS": "1.6",
    "STRUCTURED_LOGS": "1.8",
    "CLIENT_UI_ERRORS": "2.7",
    "RETRY_LOGIC": "1.12",
    "TIMEOUT_IO": "1.5",
    "THROTTLING": "3.6",
    "CIRCUIT_BREAKERS": "3.9",
    "HTTP_ERROR_CODES": "1.3",
    "CLIENT_ERROR_TRACKING": "2.4",
    "URL_MONITORING": "1.14",
    "AUTOMATED_TESTS": "2",
    "TIMEOUTS": "1.5",
    "ERROR_LOGS": "1.1",
    "HTTP_CODES" : "1.3",
    "UI_ERROR_TOOLS":"2.4",
    "UI_ERRORS":"2.7",
    "URL_MONITORING":"1.14",
    "API_MONITORING":"1.15",
    "API_SECURITY":"1.16",
    "API_PERFORMANCE":"1.17",
    "API_AVAILABILITY":"1.18",
    "API_ERRORS":"1.19",
    "API_USAGE":"1.20",
    "AUTO_SCALE": "3.18",
}

def get_gate_number(gate_name: str) -> str:
    """Get the gate number for a given gate name"""
    return GATE_NUMBER_MAPPING.get(gate_name, "N/A")

def get_gate_by_number(gate_number: str):
    """Get gate by its number"""
    for gate_name, number in GATE_NUMBER_MAPPING.items():
        if number == gate_number:
            return get_gate_by_name(gate_name)
    return None

HARD_GATES = [
    {
        "name": "ALERTING_ACTIONABLE",
        "display_name": "All alerting is actionable",
        "description": "Ensure all alerting integrations (Splunk, AppDynamics, ThousandEyes) are present and actionable.",
        "category": "Alerting",
        "priority": "high",
        "patterns": [],
        "scoring": {},
        "expected_coverage": {
            "percentage": 100,
            "reasoning": "All integrations should be present",
            "confidence": "high"
        }
    },
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
    },
    {
        "name": "AUTO_SCALE",
        "display_name": "Auto Scale",
        "description": "Ensure infrastructure can automatically scale up or down based on demand with proper replica configurations",
        "category": "Availability",
        "priority": "high",
        "patterns": {
            "positive": [
                "auto.*scale",
                "scale.*up",
                "scale.*down",
                "load.*balancer",
                "auto.*scaling",
                "replicas:",
                "replicas\\s*:",
                "replicaCount:",
                "replicaCount\\s*:",
                "minReplicas:",
                "maxReplicas:",
                "targetCPUUtilizationPercentage:",
                "targetMemoryUtilizationPercentage:",
                "HorizontalPodAutoscaler",
                "HPA",
                "autoscaling/v2",
                "autoscaling/v1",
                "scaleTargetRef:",
                "metrics:",
                "resource:",
                "type: Resource",
                "type: ResourcePods",
                "type: Object",
                "type: External",
                "type: Pods",
                "type: ContainerResource",
                "scale.*policy",
                "scaling.*policy",
                "elastic.*scaling",
                "auto.*scaling.*group",
                "ASG",
                "AutoScalingGroup",
                "desired.*capacity",
                "min.*size",
                "max.*size",
                "target.*tracking.*scaling.*policy",
                "step.*scaling.*policy",
                "simple.*scaling.*policy",
                "cloudformation.*autoscaling",
                "terraform.*autoscaling",
                "kubernetes.*autoscaler",
                "cluster.*autoscaler",
                "node.*autoscaler",
                "pod.*autoscaler",
                "vertical.*pod.*autoscaler",
                "VPA",
                "horizontal.*pod.*autoscaler",
                "hpa.*spec",
                "hpa.*status",
                "scaling.*algorithm",
                "scaling.*behavior",
                "scaling.*rules",
                "scaling.*triggers",
                "scaling.*metrics",
                "scaling.*targets",
                "scaling.*policies",
                "scaling.*schedules",
                "scaling.*conditions",
                "scaling.*thresholds",
                "scaling.*cooldown",
                "scaling.*warmup",
                "scaling.*grace.*period",
                "scaling.*stabilization",
                "scaling.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp",
                "scaling.*behavior.*scaleDown",
                "scaling.*behavior.*scaleUp.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies",
                "scaling.*behavior.*scaleDown.*policies",
                "scaling.*behavior.*scaleUp.*selectPolicy",
                "scaling.*behavior.*scaleDown.*selectPolicy",
                "scaling.*behavior.*scaleUp.*policies.*type",
                "scaling.*behavior.*scaleDown.*policies.*type",
                "scaling.*behavior.*scaleUp.*policies.*value",
                "scaling.*behavior.*scaleDown.*policies.*value",
                "scaling.*behavior.*scaleUp.*policies.*periodSeconds",
                "scaling.*behavior.*scaleDown.*policies.*periodSeconds",
                "scaling.*behavior.*scaleUp.*policies.*percent",
                "scaling.*behavior.*scaleDown.*policies.*percent",
                "scaling.*behavior.*scaleUp.*policies.*pods",
                "scaling.*behavior.*scaleDown.*policies.*pods",
                "scaling.*behavior.*scaleUp.*policies.*seconds",
                "scaling.*behavior.*scaleDown.*policies.*seconds",
                "scaling.*behavior.*scaleUp.*policies.*period",
                "scaling.*behavior.*scaleDown.*policies.*period",
                "scaling.*behavior.*scaleUp.*policies.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*policies.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies.*selectPolicy",
                "scaling.*behavior.*scaleDown.*policies.*selectPolicy",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object",
                "scaling.*behavior.*scaleUp.*policies.*type.*External",
                "scaling.*behavior.*scaleDown.*policies.*type.*External",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods.*value",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods.*value",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent.*value",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent.*value",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic.*value",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic.*value",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource.*value",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource.*value",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object.*value",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object.*value",
                "scaling.*behavior.*scaleUp.*policies.*type.*External.*value",
                "scaling.*behavior.*scaleDown.*policies.*type.*External.*value",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource.*value",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource.*value",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods.*periodSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods.*periodSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent.*periodSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent.*periodSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic.*periodSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic.*periodSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource.*periodSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource.*periodSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object.*periodSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object.*periodSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*External.*periodSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*External.*periodSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource.*periodSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource.*periodSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods.*percent",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods.*percent",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent.*percent",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent.*percent",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic.*percent",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic.*percent",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource.*percent",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource.*percent",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object.*percent",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object.*percent",
                "scaling.*behavior.*scaleUp.*policies.*type.*External.*percent",
                "scaling.*behavior.*scaleDown.*policies.*type.*External.*percent",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource.*percent",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource.*percent",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods.*pods",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods.*pods",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent.*pods",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent.*pods",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic.*pods",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic.*pods",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource.*pods",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource.*pods",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object.*pods",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object.*pods",
                "scaling.*behavior.*scaleUp.*policies.*type.*External.*pods",
                "scaling.*behavior.*scaleDown.*policies.*type.*External.*pods",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource.*pods",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource.*pods",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods.*seconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods.*seconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent.*seconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent.*seconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic.*seconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic.*seconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource.*seconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource.*seconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object.*seconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object.*seconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*External.*seconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*External.*seconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource.*seconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource.*seconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods.*period",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods.*period",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent.*period",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent.*period",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic.*period",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic.*period",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource.*period",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource.*period",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object.*period",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object.*period",
                "scaling.*behavior.*scaleUp.*policies.*type.*External.*period",
                "scaling.*behavior.*scaleDown.*policies.*type.*External.*period",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource.*period",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource.*period",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*External.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*External.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource.*stabilizationWindowSeconds",
                "scaling.*behavior.*scaleUp.*policies.*type.*Pods.*selectPolicy",
                "scaling.*behavior.*scaleDown.*policies.*type.*Pods.*selectPolicy",
                "scaling.*behavior.*scaleUp.*policies.*type.*Percent.*selectPolicy",
                "scaling.*behavior.*scaleDown.*policies.*type.*Percent.*selectPolicy",
                "scaling.*behavior.*scaleUp.*policies.*type.*Periodic.*selectPolicy",
                "scaling.*behavior.*scaleDown.*policies.*type.*Periodic.*selectPolicy",
                "scaling.*behavior.*scaleUp.*policies.*type.*Resource.*selectPolicy",
                "scaling.*behavior.*scaleDown.*policies.*type.*Resource.*selectPolicy",
                "scaling.*behavior.*scaleUp.*policies.*type.*Object.*selectPolicy",
                "scaling.*behavior.*scaleDown.*policies.*type.*Object.*selectPolicy",
                "scaling.*behavior.*scaleUp.*policies.*type.*External.*selectPolicy",
                "scaling.*behavior.*scaleDown.*policies.*type.*External.*selectPolicy",
                "scaling.*behavior.*scaleUp.*policies.*type.*ContainerResource.*selectPolicy",
                "scaling.*behavior.*scaleDown.*policies.*type.*ContainerResource.*selectPolicy"
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