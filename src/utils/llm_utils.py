"""
LLM utilities for common operations
"""

import json
import re
from typing import Dict, Any, List, Optional


def format_prompt_with_context(
    base_prompt: str, 
    context: Dict[str, Any], 
    max_context_length: int = 4000
) -> str:
    """
    Format a prompt with context data, respecting length limits
    
    Args:
        base_prompt: The base prompt template
        context: Context data to inject
        max_context_length: Maximum length for context
    
    Returns:
        Formatted prompt
    """
    # Truncate context if too long
    context_str = json.dumps(context, indent=2)
    if len(context_str) > max_context_length:
        context_str = context_str[:max_context_length] + "... (truncated)"
    
    # Replace context placeholder
    formatted_prompt = base_prompt.replace("{context}", context_str)
    
    # Replace individual context fields
    for key, value in context.items():
        if isinstance(value, (str, int, float, bool)):
            formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))
    
    return formatted_prompt


def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON data from LLM response
    
    Args:
        response: LLM response text
    
    Returns:
        Extracted JSON data or None
    """
    try:
        # Try to parse as direct JSON
        return json.loads(response.strip())
    except:
        pass
    
    # Look for JSON blocks
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.strip())
            except:
                continue
    
    return None


def clean_llm_response(response: str) -> str:
    """
    Clean LLM response by removing common artifacts
    
    Args:
        response: Raw LLM response
    
    Returns:
        Cleaned response
    """
    if not response:
        return ""
    
    # Remove common prefixes/suffixes
    prefixes_to_remove = [
        "Here's",
        "Here is",
        "I'll",
        "I will",
        "Let me",
        "Based on",
        "According to"
    ]
    
    suffixes_to_remove = [
        "Is there anything else you'd like to know?",
        "Let me know if you need any clarification.",
        "Feel free to ask if you have questions."
    ]
    
    cleaned = response.strip()
    
    # Remove prefixes
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
            if cleaned.startswith(':'):
                cleaned = cleaned[1:].strip()
            break
    
    # Remove suffixes
    for suffix in suffixes_to_remove:
        if cleaned.lower().endswith(suffix.lower()):
            cleaned = cleaned[:-len(suffix)].strip()
            break
    
    return cleaned


def chunk_text_for_llm(
    text: str, 
    max_chunk_size: int = 2000, 
    overlap: int = 200
) -> List[str]:
    """
    Chunk text for LLM processing with overlap
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum size per chunk
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to break at sentence boundary
        chunk = text[start:end]
        last_sentence = chunk.rfind('.')
        last_newline = chunk.rfind('\n')
        
        break_point = max(last_sentence, last_newline)
        if break_point > start + max_chunk_size // 2:
            end = start + break_point + 1
        
        chunks.append(text[start:end])
        start = end - overlap
        
        if start < 0:
            start = 0
    
    return chunks


def validate_llm_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate LLM configuration
    
    Args:
        config: LLM configuration dictionary
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    if "provider" not in config:
        errors.append("Missing 'provider' field")
    
    if "model" not in config:
        errors.append("Missing 'model' field")
    
    # Provider-specific validation
    provider = config.get("provider", "").lower()
    
    if provider in ["openai", "anthropic"]:
        if not config.get("api_key"):
            errors.append(f"{provider} requires 'api_key'")
    
    if provider in ["local", "ollama"]:
        if not config.get("base_url"):
            errors.append(f"{provider} requires 'base_url'")
    
    # Numeric validation
    numeric_fields = ["temperature", "max_tokens", "timeout", "max_retries"]
    for field in numeric_fields:
        if field in config:
            try:
                float(config[field])
            except (ValueError, TypeError):
                errors.append(f"'{field}' must be a number")
    
    # Range validation
    if "temperature" in config:
        temp = config["temperature"]
        if not (0.0 <= temp <= 2.0):
            errors.append("'temperature' must be between 0.0 and 2.0")
    
    if "max_tokens" in config:
        max_tokens = config["max_tokens"]
        if max_tokens <= 0:
            errors.append("'max_tokens' must be positive")
    
    return errors


def estimate_token_count(text: str) -> int:
    """
    Rough estimation of token count for text
    
    Args:
        text: Input text
    
    Returns:
        Estimated token count
    """
    # Very rough estimate: ~4 characters per token on average
    return len(text) // 4


def truncate_to_token_limit(text: str, max_tokens: int) -> str:
    """
    Truncate text to approximate token limit
    
    Args:
        text: Input text
        max_tokens: Maximum tokens allowed
    
    Returns:
        Truncated text
    """
    estimated_tokens = estimate_token_count(text)
    
    if estimated_tokens <= max_tokens:
        return text
    
    # Truncate to approximately the right length
    target_chars = max_tokens * 4
    if len(text) <= target_chars:
        return text
    
    # Try to break at sentence boundary
    truncated = text[:target_chars]
    last_sentence = truncated.rfind('.')
    last_newline = truncated.rfind('\n')
    
    break_point = max(last_sentence, last_newline)
    if break_point > target_chars // 2:
        return text[:break_point + 1]
    
    return truncated + "..."


def create_system_prompt(
    task_description: str, 
    output_format: str, 
    examples: Optional[List[str]] = None
) -> str:
    """
    Create a well-structured system prompt
    
    Args:
        task_description: Description of the task
        output_format: Expected output format
        examples: Optional examples
    
    Returns:
        Formatted system prompt
    """
    prompt_parts = [
        f"Task: {task_description}",
        f"Output Format: {output_format}"
    ]
    
    if examples:
        prompt_parts.append("Examples:")
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"{i}. {example}")
    
    prompt_parts.extend([
        "Instructions:",
        "- Be precise and accurate",
        "- Follow the specified output format exactly",
        "- If uncertain, indicate uncertainty clearly",
        "- Focus on the specific task requirements"
    ])
    
    return "\n\n".join(prompt_parts)
