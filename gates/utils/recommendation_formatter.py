#!/usr/bin/env python3
"""
Recommendation Formatter Utility
Provides consistent, clean, and readable formatting for recommendations across all UIs and reports
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class RecommendationFormat:
    """Format configuration for recommendations"""
    max_length: int = 200
    show_priority: bool = True
    show_impact: bool = True
    show_actions: bool = True
    compact_mode: bool = False
    consistent_spacing: bool = True  # New: Ensure consistent spacing


class RecommendationFormatter:
    """Centralized recommendation formatting utility with clean, consistent formatting"""
    
    def __init__(self):
        self.priority_icons = {
            "critical": "🔴",
            "high": "🟠", 
            "medium": "🟡",
            "low": "🟢"
        }
        
        self.impact_icons = {
            "security": "🔒",
            "performance": "⚡",
            "reliability": "🛡️",
            "maintainability": "🔧",
            "compliance": "📋"
        }
        
        self.action_icons = {
            "implement": "➕",
            "improve": "📈",
            "maintain": "✅",
            "review": "👀",
            "test": "🧪"
        }
    
    def format_recommendation(self, gate: Dict[str, Any], format_config: RecommendationFormat = None) -> str:
        """Format a single recommendation with consistent styling"""
        if not format_config:
            format_config = RecommendationFormat()
        
        # Get the recommendation text
        recommendation_text = self._extract_recommendation_text(gate)
        if not recommendation_text:
            return self._get_default_recommendation(gate)
        
        # Format based on gate status and type
        status = gate.get("status", "FAIL")
        gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
        priority = gate.get("priority", "medium")
        
        if format_config.compact_mode:
            return self._format_compact_recommendation(recommendation_text, status, gate_name)
        else:
            return self._format_detailed_recommendation(recommendation_text, status, gate_name, priority, format_config)
    
    def format_llm_recommendation(self, llm_recommendation: str, gate: Dict[str, Any] = None) -> str:
        """Format LLM-generated recommendations with enhanced styling"""
        if not llm_recommendation:
            return ""
        
        # Clean and structure the LLM recommendation
        cleaned_recommendation = self._clean_llm_recommendation(llm_recommendation)
        
        # Format with enhanced styling
        return self._format_enhanced_llm_recommendation(cleaned_recommendation, gate)
    
    def format_recommendation_for_table(self, gate: Dict[str, Any]) -> str:
        """Format recommendation for table display (compact)"""
        return self.format_recommendation(gate, RecommendationFormat(compact_mode=True))
    
    def format_recommendation_for_details(self, gate: Dict[str, Any]) -> str:
        """Format recommendation for detailed view"""
        return self.format_recommendation(gate, RecommendationFormat(compact_mode=False))
    
    def _extract_recommendation_text(self, gate: Dict[str, Any]) -> str:
        """Extract recommendation text from gate data"""
        # Priority order: LLM recommendation, recommendations list, default
        llm_recommendation = gate.get("llm_recommendation")
        if llm_recommendation:
            return llm_recommendation
        
        recommendations = gate.get("recommendations", [])
        if recommendations and isinstance(recommendations, list):
            return recommendations[0]
        
        return ""
    
    def _get_default_recommendation(self, gate: Dict[str, Any]) -> str:
        """Generate default recommendation based on gate status with natural language"""
        status = gate.get("status", "FAIL")
        gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
        
        # Convert gate name to more readable format
        readable_name = gate_name.replace("_", " ").lower()
        
        if status == "PASS":
            return f"Continue maintaining good practices for {readable_name} as the current implementation meets the required standards."
        elif status == "WARNING":
            return f"Consider expanding the implementation of {readable_name} to improve coverage and ensure comprehensive compliance."
        elif status == "NOT_APPLICABLE":
            return f"This validation is not applicable to the current technology stack and can be safely ignored."
        else:
            return f"Implement {readable_name} to meet the required security and compliance standards for this application."
    
    def _format_compact_recommendation(self, text: str, status: str, gate_name: str) -> str:
        """Format recommendation for compact display with natural language"""
        if not text:
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
        
        # Clean the text first
        text = self._clean_text_for_display(text)
        
        # Check if the text contains placeholder content
        if not self._is_valid_content(text):
            # If it's just placeholder text, return default recommendation
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
        
        # Additional check: if the text contains placeholder patterns, filter them out
        lines = text.split('\n')
        valid_lines = []
        
        for line in lines:
            line = line.strip()
            if line and self._is_valid_content(line):
                # Make the line more natural
                line = self._make_text_more_natural(line)
                valid_lines.append(line)
        
        if valid_lines:
            # Use the first valid line for compact display
            result = valid_lines[0]
            
            # Make it more natural by ensuring it flows well
            if result.lower().startswith(("this issue occurs because", "the impact is", "to resolve this")):
                # It's already in natural language, use as is
                pass
            elif result.lower().startswith(("implement", "add", "configure", "enable", "disable")):
                # It's an action, make it more natural
                result = f"To resolve this, {result.lower()}"
            else:
                # It's a general recommendation, use as is
                pass
            
            # Truncate if too long while preserving natural language
            if len(result) > 150:
                # Try to truncate at a sentence boundary
                if '.' in result[:150]:
                    last_period = result[:150].rfind('.')
                    if last_period > 100:  # Only truncate if we have a reasonable sentence
                        result = result[:last_period + 1]
                    else:
                        result = result[:147] + "..."
                else:
                    result = result[:147] + "..."
            
            return result
        else:
            # If no valid lines, return default recommendation
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
    
    def _format_detailed_recommendation(self, text: str, status: str, gate_name: str, priority: str, config: RecommendationFormat) -> str:
        """Format recommendation for detailed display with clean formatting"""
        if not text:
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
        
        # Clean the text first
        text = self._clean_text_for_display(text)
        
        # Split into sections if it's a structured recommendation
        sections = self._parse_structured_recommendation(text)
        
        if sections and any(sections.values()):
            # Check if we have valid content (not just placeholder text)
            valid_sections = {}
            for section_name, content in sections.items():
                if self._is_valid_content(content):
                    valid_sections[section_name] = content
            
            if valid_sections:
                # Pass the filtered valid sections to the formatting method
                return self._format_structured_recommendation(valid_sections, status, priority, config)
        
        # Fallback to simple formatting if structured parsing fails or has no valid content
        return self._format_simple_recommendation(text, status, config)
    
    def _format_structured_recommendation(self, sections: Dict[str, str], status: str, priority: str, config: RecommendationFormat) -> str:
        """Format structured recommendation with natural language and improved readability"""
        formatted_parts = []
        
        # Start with the main recommendation (most important)
        if "recommendation" in sections and self._is_valid_content(sections["recommendation"]):
            recommendation_text = sections["recommendation"].strip()
            # Make it more natural by removing "Recommendation:" prefix if it exists
            if recommendation_text.lower().startswith("recommendation:"):
                recommendation_text = recommendation_text[15:].strip()
            formatted_parts.append(recommendation_text)
        
        # Add root cause analysis with natural language
        if "root_cause_analysis" in sections and self._is_valid_content(sections["root_cause_analysis"]):
            analysis_text = sections["root_cause_analysis"].strip()
            # Make it more natural
            if analysis_text.lower().startswith(("analysis:", "root cause analysis:", "root cause:")):
                # Remove the prefix and make it flow naturally
                prefix_end = analysis_text.find(":")
                if prefix_end != -1:
                    analysis_text = analysis_text[prefix_end + 1:].strip()
                formatted_parts.append(f"This issue occurs because {analysis_text.lower()}")
            else:
                formatted_parts.append(f"This issue occurs because {analysis_text}")
        
        # Add impact with natural language
        if config.show_impact and "impact" in sections and self._is_valid_content(sections["impact"]):
            impact_text = sections["impact"].strip()
            # Make it more natural
            if impact_text.lower().startswith("impact:"):
                impact_text = impact_text[7:].strip()
            formatted_parts.append(f"The impact of this issue is {impact_text.lower()}")
        
        # Add actions with natural language
        if config.show_actions and "actions" in sections and self._is_valid_content(sections["actions"]):
            actions_text = sections["actions"].strip()
            # Make it more natural
            if actions_text.lower().startswith("actions:"):
                actions_text = actions_text[8:].strip()
            # Fix the "s:" issue by properly handling the text
            if actions_text.startswith("s:"):
                actions_text = actions_text[2:].strip()
            formatted_parts.append(f"To resolve this, {actions_text.lower()}")
        
        # Add code examples with natural language
        if "code_examples" in sections and self._is_valid_content(sections["code_examples"]):
            examples_text = sections["code_examples"].strip()
            # Make it more natural
            if examples_text.lower().startswith(("code examples:", "examples:", "code:")):
                prefix_end = examples_text.find(":")
                if prefix_end != -1:
                    examples_text = examples_text[prefix_end + 1:].strip()
            formatted_parts.append(f"Example implementation: {examples_text}")
        
        # If no valid sections found, return empty string
        if not formatted_parts:
            return ""
        
        # Join with natural paragraph breaks
        return "\n\n".join(formatted_parts)
    
    def _format_simple_recommendation(self, text: str, status: str, config: RecommendationFormat) -> str:
        """Format simple recommendation text with natural language and improved readability"""
        # Clean the text first
        text = self._clean_text_for_display(text)
        
        # Check if the text contains placeholder content
        if not self._is_valid_content(text):
            # If it's just placeholder text, return empty string
            return ""
        
        # Additional check: if the text contains placeholder patterns, filter them out
        lines = text.split('\n')
        valid_lines = []
        
        for line in lines:
            line = line.strip()
            if line and self._is_valid_content(line):
                # Make the line more natural
                line = self._make_text_more_natural(line)
                valid_lines.append(line)
        
        if valid_lines:
            # Join with natural paragraph breaks
            return '\n\n'.join(valid_lines)
        else:
            return ""
    
    def _make_text_more_natural(self, text: str) -> str:
        """Convert technical text to more natural language while preserving case"""
        if not text:
            return ""
        
        # Preserve original case for the first character
        original_first_char = text[0] if text else ""
        
        # Convert to lowercase for processing
        text_lower = text.lower()
        
        # Remove common prefixes
        if text_lower.startswith("s:"):
            text = text[2:].strip()
        elif text_lower.startswith("recommendation:"):
            text = text[15:].strip()
        elif text_lower.startswith("impact:"):
            text = text[7:].strip()
        elif text_lower.startswith("actions:"):
            text = text[8:].strip()
        elif text_lower.startswith("analysis:"):
            text = text[9:].strip()
        elif text_lower.startswith("assessment:"):
            text = text[12:].strip()
        elif text_lower.startswith("mitigation:"):
            text = text[11:].strip()
        elif text_lower.startswith("next steps:"):
            text = text[11:].strip()
        elif text_lower.startswith("code examples:"):
            text = text[14:].strip()
        elif text_lower.startswith("best practices:"):
            text = text[15:].strip()
        elif text_lower.startswith("priority actions:"):
            text = text[16:].strip()
        
        # Only add "To resolve this, " if the text is a short command-like phrase
        # and not a complete sentence
        action_verbs = ["implement", "add", "configure", "enable", "disable", "update", "modify", "create", "set", "use", "apply", "install", "deploy", "test", "validate", "monitor", "log", "track", "handle", "manage", "secure", "protect", "encrypt", "decrypt", "authenticate", "authorize", "validate", "sanitize", "escape", "filter", "rate", "limit", "throttle", "retry", "timeout", "circuit", "breaker", "fallback", "graceful", "degradation"]
        
        text_lower = text.lower()
        for verb in action_verbs:
            if text_lower.startswith(verb):
                # Only add "To resolve this, " if the text is short and command-like
                # (not a complete sentence with multiple clauses)
                if len(text) < 100 and not any(char in text for char in ['.', '!', '?', ';', ',']):
                    # Preserve the original case of the verb
                    verb_in_text = text[:len(verb)]
                    rest_of_text = text[len(verb):]
                    text = f"To resolve this, {verb_in_text}{rest_of_text}"
                break
        
        # Ensure proper capitalization
        if text and text[0].isalpha():
            text = text[0].upper() + text[1:]
        
        return text
    
    def _clean_text_for_display(self, text: str) -> str:
        """Clean text for natural language display with improved formatting"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove all bullet points and convert to natural sentences
        text = re.sub(r'^[\s]*[-•*][\s]*', '', text, flags=re.MULTILINE)
        
        # Convert numbered lists to natural sentences
        text = re.sub(r'^[\s]*(\d+)[\s]*[\.\)][\s]*', r'Step \1: ', text, flags=re.MULTILINE)
        
        # Remove trailing whitespace
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        
        # Remove empty lines that might be left after removing bullets
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Ensure proper sentence endings
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        return text.strip()
    
    def _parse_structured_recommendation(self, text: str) -> Dict[str, str]:
        """Parse structured recommendation text into sections with improved patterns"""
        sections = {}
        
        # Split text into lines for better parsing
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new section
            section_patterns = {
                "recommendation": r"^(?:recommendation|suggestion|advice)[:\s]*",
                "root_cause_analysis": r"^(?:root cause analysis|analysis|root cause)[:\s]*",
                "impact": r"^(?:impact|implication|consequence|effect)[:\s]*",
                "actions": r"^(?:action|step|task|next step)[:\s]*",
                "code_examples": r"^(?:code|example|implementation|sample)[:\s]*"
            }
            
            found_section = None
            for section_name, pattern in section_patterns.items():
                if re.match(pattern, line, re.IGNORECASE):
                    found_section = section_name
                    break
            
            if found_section:
                # Save previous section if exists
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = found_section
                current_content = []
                
                # Extract content after the section header
                content_start = re.search(section_patterns[found_section], line, re.IGNORECASE)
                if content_start:
                    content = line[content_start.end():].strip()
                    if content:
                        current_content.append(content)
            else:
                # Add line to current section content
                if current_section:
                    current_content.append(line)
        
        # Save the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _clean_llm_recommendation(self, text: str) -> str:
        """Clean and normalize LLM recommendation text without bullet points"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove bullet points and convert to plain text
        text = re.sub(r'^[\s]*[-•*][\s]*', '', text, flags=re.MULTILINE)
        
        # Clean up numbered lists
        text = re.sub(r'^[\s]*(\d+)[\s]*[\.\)][\s]*', r'\1. ', text, flags=re.MULTILINE)
        
        # Clean up markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold formatting
        
        # Remove trailing whitespace
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        
        # Remove empty lines that might be left after removing bullets
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Split into lines and filter out placeholder text
        lines = text.split('\n')
        valid_lines = []
        
        for line in lines:
            line = line.strip()
            if line and self._is_valid_content(line):
                # Filter out lines that are just headers with minimal content
                if re.match(r'^(root cause analysis|impact assessment|specific recommendations|code examples|best practices|priority actions):\s*', line, re.IGNORECASE):
                    # Extract the content after the header
                    header_match = re.match(r'^([^:]+):\s*(.*)$', line, re.IGNORECASE)
                    if header_match:
                        content_after_header = header_match.group(2).strip()
                        if content_after_header and self._is_valid_content(content_after_header):
                            # Make the content more natural
                            natural_content = self._make_text_more_natural(content_after_header)
                            valid_lines.append(natural_content)
                    continue
                
                # Make the line more natural (but preserve case)
                line = self._make_text_more_natural(line)
                valid_lines.append(line)
        
        if valid_lines:
            # Join valid lines and clean up
            result = ' '.join(valid_lines)
            
            # Remove any remaining placeholder patterns (case insensitive)
            result = re.sub(r'\*Gate Validation Analysis Report\*\*', '', result, flags=re.IGNORECASE)
            result = re.sub(r'\*Root Cause Analysis\*\*', '', result, flags=re.IGNORECASE)
            result = re.sub(r'\*Impact Assessment\*\*', '', result, flags=re.IGNORECASE)
            result = re.sub(r'\*Code Examples\*\*', '', result, flags=re.IGNORECASE)
            result = re.sub(r'\*Mitigation Strategy\*\*', '', result, flags=re.IGNORECASE)
            result = re.sub(r'\*Recommendations\*\*', '', result, flags=re.IGNORECASE)
            result = re.sub(r'\*Next Steps\*\*', '', result, flags=re.IGNORECASE)
            
            # Remove generic introductory phrases (case insensitive)
            result = re.sub(r'based on the provided Gate Validation Analysis Request, I\'ll provide a comprehensive response addressing each section\.', '', result, flags=re.IGNORECASE)
            result = re.sub(r'based on the provided data, I\'ll provide a comprehensive analysis\.', '', result, flags=re.IGNORECASE)
            result = re.sub(r'here is the analysis based on the provided information\.', '', result, flags=re.IGNORECASE)
            result = re.sub(r'I will provide a comprehensive response addressing each section\.', '', result, flags=re.IGNORECASE)
            result = re.sub(r'let me provide a comprehensive analysis of this gate\.', '', result, flags=re.IGNORECASE)
            result = re.sub(r'I\'ll analyze the gate validation results and provide recommendations\.', '', result, flags=re.IGNORECASE)
            
            # Clean up extra whitespace
            result = re.sub(r'\s+', ' ', result).strip()
            
            # Final validation: ensure we have substantial content
            if len(result) >= 15 and self._is_valid_content(result):
                return result
            else:
                return ""
        else:
            return ""
    
    def _format_enhanced_llm_recommendation(self, text: str, gate: Dict[str, Any] = None) -> str:
        """Format LLM recommendation with clean, elegant, and readable formatting"""
        if not text:
            return ""
        
        # Clean and structure the text
        cleaned_text = self._clean_and_structure_text(text)
        
        # Format with elegant styling
        return self._apply_elegant_formatting(cleaned_text, gate)
    
    def _clean_and_structure_text(self, text: str) -> str:
        """Clean and structure text for elegant formatting"""
        if not text:
            return ""
        
        # Remove markdown headers and formatting
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Remove # headers
        text = re.sub(r'^\*\*\s*([^*]+)\s*\*\*', r'\1', text, flags=re.MULTILINE)  # Remove ** headers
        text = re.sub(r'^\*\s*([^*]+)\s*\*', r'\1', text, flags=re.MULTILINE)  # Remove * headers
        text = re.sub(r'###\s*', '', text, flags=re.MULTILINE)  # Remove ### headers
        text = re.sub(r'##\s*', '', text, flags=re.MULTILINE)   # Remove ## headers
        text = re.sub(r'#\s*', '', text, flags=re.MULTILINE)    # Remove # headers
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Remove bullet points and numbered lists
        text = re.sub(r'^[\s]*[-•*][\s]*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*(\d+)[\s]*[\.\)][\s]*', '', text, flags=re.MULTILINE)
        
        # Remove "Generated by AI Assistant" and similar endings
        text = re.sub(r'Generated by AI Assistant.*$', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'This analysis was generated.*$', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n+', ' ', text)
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove robotic prefixes
        text = self._remove_robotic_prefixes(text)
        
        # For complex LLM output, extract the key information and create a clean summary
        return self._extract_key_information(text)
    
    def _extract_key_information(self, text: str) -> str:
        """Extract key information from complex LLM output and create a comprehensive summary"""
        # Look for key patterns in the text
        key_sentences = []
        
        # Extract the main problem statement
        problem_patterns = [
            r'failed due to a critical deficiency in its integrations with ([^.]+)',
            r'failed because ([^.]+)',
            r'failed due to ([^.]+)',
            r'critical issue because ([^.]+)',
            r'problem is that ([^.]+)',
            r'failed due to the presence of ([^.]+)',
            r'issue is that ([^.]+)',
            r'problem with ([^.]+)'
        ]
        
        for pattern in problem_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                problem = match.group(1).strip()
                if len(problem) > 20:
                    key_sentences.append(f"The gate failed due to {problem}.")
                break
        
        # Extract the main recommendation
        recommendation_patterns = [
            r'configure and set up the missing ([^.]+)',
            r'need to configure ([^.]+)',
            r'should configure ([^.]+)',
            r'must configure ([^.]+)',
            r'configure ([^.]+)',
            r'use ([^.]+)',
            r'implement ([^.]+)',
            r'set up ([^.]+)',
            r'add ([^.]+)'
        ]
        
        for pattern in recommendation_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                recommendation = match.group(1).strip()
                if len(recommendation) > 20:
                    key_sentences.append(f"Configure {recommendation}.")
                break
        
        # Extract impact information
        impact_patterns = [
            r'has significant implications for ([^.]+)',
            r'can lead to ([^.]+)',
            r'can result in ([^.]+)',
            r'prevents ([^.]+)',
            r'impacts ([^.]+)',
            r'affects ([^.]+)'
        ]
        
        for pattern in impact_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                impact = match.group(1).strip()
                if len(impact) > 20:
                    key_sentences.append(f"This can lead to {impact}.")
                break
        
        # Extract specific actions or steps
        action_patterns = [
            r'([^.]+) by following ([^.]+)',
            r'([^.]+) by setting up ([^.]+)',
            r'([^.]+) by implementing ([^.]+)',
            r'([^.]+) such as ([^.]+)',
            r'([^.]+) including ([^.]+)'
        ]
        
        for pattern in action_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                action = match.group(1).strip()
                details = match.group(2).strip()
                if len(action) > 10 and len(details) > 10:
                    key_sentences.append(f"{action} such as {details}.")
                break
        
        # If we found key sentences, use them
        if key_sentences:
            return ' '.join(key_sentences)
        
        # Fallback: try to extract meaningful sentences from the text
        sentences = self._split_into_sentences(text)
        meaningful_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 30:  # Only keep substantial sentences
                # Remove common technical artifacts
                sentence = re.sub(r'\.\.', '.', sentence)  # Fix double periods
                sentence = re.sub(r'\s+', ' ', sentence)   # Normalize whitespace
                
                # Capitalize first letter
                if sentence and sentence[0].isalpha():
                    sentence = sentence[0].upper() + sentence[1:]
                
                meaningful_sentences.append(sentence)
        
        # Take the first 3-4 meaningful sentences for more comprehensive coverage
        if meaningful_sentences:
            return '. '.join(meaningful_sentences[:4]) + '.'
        
        # Last resort: return a generic message
        return "The gate validation failed and requires attention to resolve the identified issues."
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences more intelligently"""
        # First, normalize the text
        text = re.sub(r'\s+', ' ', text)
        
        # Split by common sentence endings, but be careful with abbreviations
        # This regex handles periods, exclamation marks, and question marks
        # while avoiding splitting on common abbreviations
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # If the above didn't work well, try a simpler approach
        if len(sentences) <= 1:
            # Split by periods followed by space and capital letter
            sentences = re.split(r'\.\s+', text)
            # Add periods back to all but the last sentence
            for i in range(len(sentences) - 1):
                sentences[i] = sentences[i] + '.'
        
        # Clean up sentences
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                # Remove any remaining markdown artifacts
                sentence = re.sub(r'^\*\*\s*', '', sentence)
                sentence = re.sub(r'\s*\*\*$', '', sentence)
                clean_sentences.append(sentence)
        
        return clean_sentences
    
    def _remove_robotic_prefixes(self, text: str) -> str:
        """Remove robotic prefixes to make text more natural"""
        prefixes_to_remove = [
            "to resolve this issue,",
            "in order to fix this,",
            "to address this problem,",
            "to mitigate this issue,",
            "to resolve this,",
            "to fix this,",
            "to address this,",
            "to mitigate this,",
            "the solution is to",
            "the recommended approach is to",
            "it is recommended to",
            "you should",
            "you need to",
            "you must",
            "the team should",
            "the developers should",
            "to improve this gate,",
            "to address this critical issue,",
            "by following these recommendations,",
            "to ensure that",
            "it's essential to",
            "here are some",
            "here are the",
            "the following",
            "we recommend",
            "we need to"
        ]
        
        text_lower = text.lower()
        for prefix in prefixes_to_remove:
            if text_lower.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        
        return text
    
    def _apply_elegant_formatting(self, text: str, gate: Dict[str, Any] = None) -> str:
        """Apply elegant formatting to the recommendation text"""
        if not text:
            return ""
        
        # The text is already cleaned and structured, just return it
        return text
    
    def _format_compact_recommendation(self, text: str, status: str, gate_name: str) -> str:
        """Format recommendation for compact display with elegant natural language"""
        if not text:
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
        
        # Clean and structure the text
        cleaned_text = self._clean_and_structure_text(text)
        
        # Check if the text contains valid content
        if not self._is_valid_content(cleaned_text):
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
        
        # For compact display, use the first substantial sentence
        sentences = re.split(r'[.!?]+', cleaned_text)
        valid_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 20 and self._is_valid_content(sentence):
                valid_sentences.append(sentence)
        
        if valid_sentences:
            result = valid_sentences[0] + '.'
            
            # Ensure proper length for compact display
            if len(result) > 120:
                # Try to truncate at a natural break
                if '.' in result[:120]:
                    last_period = result[:120].rfind('.')
                    if last_period > 80:
                        result = result[:last_period + 1]
                    else:
                        result = result[:117] + "..."
                else:
                    result = result[:117] + "..."
            
            return result
        else:
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
    
    def _format_detailed_recommendation(self, text: str, status: str, gate_name: str, priority: str, config: RecommendationFormat) -> str:
        """Format recommendation for detailed display with comprehensive information"""
        if not text:
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
        
        # Clean and structure the text
        cleaned_text = self._clean_and_structure_text(text)
        
        # Check if the text contains valid content
        if not self._is_valid_content(cleaned_text):
            return self._get_default_recommendation({"status": status, "display_name": gate_name})
        
        # For detailed view, provide more comprehensive information
        return self._create_comprehensive_recommendation(cleaned_text, text)
    
    def _create_comprehensive_recommendation(self, cleaned_text: str, original_text: str) -> str:
        """Create a comprehensive recommendation that includes more details"""
        # Extract key information
        key_info = self._extract_key_information(original_text)
        
        # If the key info is too short, try to add more context
        if len(key_info) < 100:
            # Try to extract additional context from the original text
            additional_context = self._extract_additional_context(original_text)
            if additional_context:
                return f"{key_info} {additional_context}"
        
        return key_info
    
    def _extract_additional_context(self, text: str) -> str:
        """Extract additional context from the original text"""
        context_sentences = []
        
        # Look for specific technical details
        technical_patterns = [
            r'([^.]+) in multiple files ([^.]+)',
            r'([^.]+) across the codebase ([^.]+)',
            r'([^.]+) throughout the application ([^.]+)',
            r'([^.]+) in the codebase ([^.]+)',
            r'([^.]+) such as ([^.]+)',
            r'([^.]+) including ([^.]+)',
            r'([^.]+) like ([^.]+)'
        ]
        
        for pattern in technical_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                context = match.group(1).strip()
                details = match.group(2).strip()
                if len(context) > 10 and len(details) > 10:
                    context_sentences.append(f"{context} such as {details}.")
                break
        
        # Look for specific recommendations
        specific_patterns = [
            r'([^.]+) by following ([^.]+)',
            r'([^.]+) by implementing ([^.]+)',
            r'([^.]+) by setting up ([^.]+)',
            r'([^.]+) by configuring ([^.]+)'
        ]
        
        for pattern in specific_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                action = match.group(1).strip()
                method = match.group(2).strip()
                if len(action) > 10 and len(method) > 10:
                    context_sentences.append(f"{action} by {method}.")
                break
        
        # Look for impact details
        impact_patterns = [
            r'([^.]+) can lead to ([^.]+)',
            r'([^.]+) may result in ([^.]+)',
            r'([^.]+) could cause ([^.]+)',
            r'([^.]+) affects ([^.]+)'
        ]
        
        for pattern in impact_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cause = match.group(1).strip()
                effect = match.group(2).strip()
                if len(cause) > 10 and len(effect) > 10:
                    context_sentences.append(f"{cause} can lead to {effect}.")
                break
        
        # Return the additional context if found
        if context_sentences:
            return ' '.join(context_sentences[:2])  # Limit to 2 additional sentences
        
        return ""
    
    def _get_default_recommendation(self, gate: Dict[str, Any]) -> str:
        """Generate elegant default recommendation based on gate status"""
        status = gate.get("status", "FAIL")
        gate_name = gate.get("display_name", gate.get("gate", "Unknown"))
        
        # Convert gate name to more readable format
        readable_name = gate_name.replace("_", " ").lower()
        
        if status == "PASS":
            return f"The current implementation of {readable_name} meets the required standards. Continue maintaining these good practices to ensure ongoing compliance."
        elif status == "WARNING":
            return f"The {readable_name} implementation could be enhanced to improve coverage and ensure comprehensive compliance across the application."
        elif status == "NOT_APPLICABLE":
            return f"This validation is not applicable to the current technology stack and can be safely ignored."
        else:
            return f"Implement {readable_name} to meet the required security and compliance standards for this application."
    
    def _get_status_icon(self, status: str) -> str:
        """Get empty string to remove status icons"""
        return ""
    
    def _is_valid_content(self, content: str) -> bool:
        """Check if content is valid (not placeholder text)"""
        if not content or not content.strip():
            return False
        
        # First, check for placeholder patterns on the original content
        placeholder_patterns = [
            # Original patterns
            r'^\w+\*\*$',  # "Analysis**", "Assessment**", etc.
            r'^\w+\s*\*\*$',  # "Analysis **", etc.
            r'^\w+:\s*\w+\*\*$',  # "Analysis: Analysis**", etc.
            r'^\w+\s*$',  # Just a single word
            r'^\w+\s+\w+\*\*$',  # "Code Examples**", etc.
            r'^\w+\*\*$',  # "Examples**", etc.
            r'^\w+\s+\w+:\s*\w+\*\*$',  # "Code Examples: Examples**", etc.
            
            # New specific patterns from HTML report (fixed regex)
            r'^\*Gate Validation Analysis Report\*\*$',  # "*Gate Validation Analysis Report**"
            r'^\*Root Cause Analysis\*\*$',  # "*Root Cause Analysis**"
            r'^\*Gate Validation Analysis Request Response\*\*$',  # "*Gate Validation Analysis Request Response**"
            r'^\*Impact Assessment\*\*$',  # "*Impact Assessment**"
            r'^\*Code Examples\*\*$',  # "*Code Examples**"
            r'^\*Mitigation Strategy\*\*$',  # "*Mitigation Strategy**"
            r'^\*Recommendations\*\*$',  # "*Recommendations**"
            r'^\*Next Steps\*\*$',  # "*Next Steps**"
            
            # More flexible patterns to catch variations
            r'^\*.*\*\*$',  # Any text surrounded by * and **
            r'^\*\*.*\*\*$',  # Any text surrounded by ** and **
            r'^\*.*Analysis.*\*\*$',  # Any analysis-related placeholder
            r'^\*.*Assessment.*\*\*$',  # Any assessment-related placeholder
            r'^\*.*Examples.*\*\*$',  # Any examples-related placeholder
            r'^\*.*Strategy.*\*\*$',  # Any strategy-related placeholder
            r'^\*.*Recommendations.*\*\*$',  # Any recommendations-related placeholder
            r'^\*.*Steps.*\*\*$',  # Any steps-related placeholder
            
            # Patterns for content after markdown cleanup (no leading asterisk)
            r'^.*Analysis.*\*\*$',  # Any analysis-related placeholder without leading *
            r'^.*Assessment.*\*\*$',  # Any assessment-related placeholder without leading *
            r'^.*Examples.*\*\*$',  # Any examples-related placeholder without leading *
            r'^.*Strategy.*\*\*$',  # Any strategy-related placeholder without leading *
            r'^.*Recommendations.*\*\*$',  # Any recommendations-related placeholder without leading *
            r'^.*Steps.*\*\*$',  # Any steps-related placeholder without leading *
            r'^.*Report\*\*$',  # Any report-related placeholder without leading *
            r'^.*Response\*\*$',  # Any response-related placeholder without leading *
            
            # Very short content ending with **
            r'^[A-Za-z\s]{1,30}\*\*$',  # Short content ending with **
            
            # Generic introductory phrases
            r'^based on the provided Gate Validation Analysis Request, I\'ll provide a comprehensive response addressing each section\.$',
            r'^based on the provided data, I\'ll provide a comprehensive analysis\.$',
            r'^here is the analysis based on the provided information\.$',
            r'^I will provide a comprehensive response addressing each section\.$',
            r'^let me provide a comprehensive analysis of this gate\.$',
            r'^I\'ll analyze the gate validation results and provide recommendations\.$',
            
            # Generic analysis phrases
            r'^analysis:$',
            r'^assessment:$',
            r'^recommendations:$',
            r'^impact:$',
            r'^mitigation:$',
            r'^next steps:$',
            
            # Very short or repetitive content
            r'^[A-Za-z\s]{1,20}$',  # Very short content (1-20 chars, letters and spaces only)
            r'^(analysis|assessment|recommendation|impact|mitigation)\s+(analysis|assessment|recommendation|impact|mitigation)$',  # Repeated words
        ]
        
        for pattern in placeholder_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                return False
        
        # Now strip leading/trailing markdown characters and whitespace for additional checks
        content = content.strip()
        content = re.sub(r'^[*#\-+\s]+', '', content)  # Remove leading markdown chars
        content = re.sub(r'[*#\-+\s]+$', '', content)  # Remove trailing markdown chars
        content = content.strip()
        
        if not content:
            return False
        
        # Additional checks for common placeholder patterns
        if content.endswith("**") and len(content.split()) <= 3:
            return False
        
        # Check if content is too short
        if len(content) < 15:
            return False
        
        # Check for repeated words (like "Analysis Analysis**")
        words = content.split()
        if len(words) <= 3 and len(set(words)) <= 1:
            return False
        
        # Check for content that's mostly punctuation or special characters
        if len(re.sub(r'[A-Za-z0-9\s]', '', content)) > len(content) * 0.3:
            return False
        
        # Check for content that's all uppercase (likely a placeholder)
        if content.isupper() and len(content) < 50:
            return False
        
        return True
    
    def format_recommendation_html(self, gate: Dict[str, Any], format_type: str = "table") -> str:
        """Format recommendation as HTML with clean text formatting without graphics"""
        if format_type == "table":
            recommendation = self.format_recommendation_for_table(gate)
        else:
            recommendation = self.format_recommendation_for_details(gate)
        
        # Convert to HTML with clean text formatting
        html = recommendation
        
        # Convert line breaks with consistent spacing
        html = html.replace('\n', '<br>')
        
        return html
    
    def format_recommendation_for_ui(self, gate: Dict[str, Any], ui_type: str = "vscode") -> str:
        """Format recommendation for specific UI type with consistent formatting"""
        if ui_type == "vscode":
            return self.format_recommendation_for_table(gate)
        elif ui_type == "streamlit":
            return self.format_recommendation_for_details(gate)
        elif ui_type == "html_report":
            return self.format_recommendation_html(gate, "details")
        else:
            return self.format_recommendation_for_table(gate)


# Global instance for consistent formatting
recommendation_formatter = RecommendationFormatter() 