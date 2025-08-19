# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Evidence Collection Tool - Collects evidence from external sources"""

from google.adk.tools import ToolContext
from typing import Dict, Any, List, Optional


def collect_evidence(app_id: str, sources: Optional[List[str]], time_range: str, tool_context: Optional[ToolContext]) -> Dict[str, Any]:
    """
    Collect evidence from external sources including Splunk, AppDynamics, and web portals.
    
    Args:
        app_id: Application identifier
        sources: List of sources to collect from (splunk, appdynamics, web_portal)
        time_range: Time range for evidence collection (e.g., "24h", "7d", "30d")
        tool_context: The ADK tool context
    
    Returns:
        Dictionary containing collected evidence from all sources
    """
    evidence = {
        "app_id": app_id,
        "time_range": time_range,
        "sources": sources or ["splunk", "appdynamics", "web_portal"],
        "evidence": {}
    }
    
    # Simulate evidence collection from different sources
    if "splunk" in evidence["sources"]:
        evidence["evidence"]["splunk"] = {
            "logs": "Security logs and monitoring data collected",
            "alerts": "Security alerts and incidents identified",
            "metrics": "Performance and security metrics analyzed"
        }
    
    if "appdynamics" in evidence["sources"]:
        evidence["evidence"]["appdynamics"] = {
            "performance": "Application performance data collected",
            "errors": "Error logs and exception data analyzed",
            "transactions": "Transaction monitoring data reviewed"
        }
    
    if "web_portal" in evidence["sources"]:
        evidence["evidence"]["web_portal"] = {
            "accessibility": "Web portal accessibility verified",
            "functionality": "Core functionality tests completed",
            "security": "Security controls assessment performed"
        }
    
    return evidence


# The function itself is the tool - no need to wrap it in a Tool class
evidence_collection_tool = collect_evidence 