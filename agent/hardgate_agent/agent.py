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

"""HardGate Agent - Enterprise-grade code security analysis using Google ADK"""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from hardgate_agent import prompt

from hardgate_agent.tools import repository_analysis_tool
from hardgate_agent.tools.evidence_collection import evidence_collection_tool
from hardgate_agent.tools.llm_analysis import llm_analysis_tool


root_agent = Agent(
    model=LiteLlm(model="gpt-3.5-turbo", base_url="http://localhost:1234/v1", api_key="sdsd", provider="openai"),
    name="hardgate_agent",
    description="Enterprise-grade code security analysis agent using Google ADK with comprehensive security tools",
    instruction=prompt.ROOT_AGENT_INSTR,
    tools=[
        repository_analysis_tool,
        evidence_collection_tool,
        llm_analysis_tool,
    ],
) 