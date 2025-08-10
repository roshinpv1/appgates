"""
API Validator
Validates API endpoints and responses for gate validation
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ Requests not available. Install with: pip install requests")


@dataclass
class APIValidationResult:
    """Result of an API validation check"""
    success: bool
    endpoint: str
    method: str
    status_code: Optional[int]
    response_time: float
    response_data: Optional[Dict[str, Any]]
    validation_results: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class APIEndpointConfig:
    """Configuration for an API endpoint to validate"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    timeout: int = 30
    expected_status_codes: List[int] = None
    response_validation: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, str]] = None


class APIValidator:
    """Validates API endpoints and responses"""
    
    def __init__(self, base_url: Optional[str] = None, default_headers: Optional[Dict[str, str]] = None):
        """Initialize the API validator"""
        self.base_url = base_url
        self.default_headers = default_headers or {
            'User-Agent': 'CodeGates-API-Validator/1.0',
            'Content-Type': 'application/json'
        }
        self.logger = logging.getLogger(__name__)
    
    async def validate_endpoint(self, endpoint_config: APIEndpointConfig) -> APIValidationResult:
        """Validate a single API endpoint"""
        start_time = datetime.now()
        
        try:
            # Build full URL
            url = endpoint_config.url
            if self.base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(self.base_url, url)
            
            # Prepare headers
            headers = self.default_headers.copy()
            if endpoint_config.headers:
                headers.update(endpoint_config.headers)
            
            # Prepare authentication
            auth = None
            if endpoint_config.auth:
                if 'basic' in endpoint_config.auth:
                    import base64
                    username = endpoint_config.auth['basic'].get('username', '')
                    password = endpoint_config.auth['basic'].get('password', '')
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    headers['Authorization'] = f"Basic {credentials}"
                elif 'bearer' in endpoint_config.auth:
                    headers['Authorization'] = f"Bearer {endpoint_config.auth['bearer']}"
                elif 'api_key' in endpoint_config.auth:
                    headers['X-API-Key'] = endpoint_config.auth['api_key']
            
            # Make request
            async with aiohttp.ClientSession() as session:
                if endpoint_config.method.upper() == 'GET':
                    async with session.get(
                        url, 
                        headers=headers, 
                        params=endpoint_config.params,
                        timeout=aiohttp.ClientTimeout(total=endpoint_config.timeout)
                    ) as response:
                        return await self._process_response(response, endpoint_config, start_time)
                
                elif endpoint_config.method.upper() == 'POST':
                    async with session.post(
                        url, 
                        headers=headers,
                        json=endpoint_config.body,
                        params=endpoint_config.params,
                        timeout=aiohttp.ClientTimeout(total=endpoint_config.timeout)
                    ) as response:
                        return await self._process_response(response, endpoint_config, start_time)
                
                elif endpoint_config.method.upper() == 'PUT':
                    async with session.put(
                        url, 
                        headers=headers,
                        json=endpoint_config.body,
                        params=endpoint_config.params,
                        timeout=aiohttp.ClientTimeout(total=endpoint_config.timeout)
                    ) as response:
                        return await self._process_response(response, endpoint_config, start_time)
                
                elif endpoint_config.method.upper() == 'DELETE':
                    async with session.delete(
                        url, 
                        headers=headers,
                        params=endpoint_config.params,
                        timeout=aiohttp.ClientTimeout(total=endpoint_config.timeout)
                    ) as response:
                        return await self._process_response(response, endpoint_config, start_time)
                
                else:
                    return APIValidationResult(
                        success=False,
                        endpoint=url,
                        method=endpoint_config.method,
                        status_code=None,
                        response_time=(datetime.now() - start_time).total_seconds(),
                        response_data=None,
                        validation_results={},
                        error=f"Unsupported HTTP method: {endpoint_config.method}"
                    )
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return APIValidationResult(
                success=False,
                endpoint=endpoint_config.url,
                method=endpoint_config.method,
                status_code=None,
                response_time=response_time,
                response_data=None,
                validation_results={},
                error=str(e)
            )
    
    async def _process_response(self, response, endpoint_config: APIEndpointConfig, start_time: datetime) -> APIValidationResult:
        """Process the API response and validate it"""
        response_time = (datetime.now() - start_time).total_seconds()
        
        try:
            # Get response data
            response_data = None
            try:
                response_data = await response.json()
            except:
                try:
                    response_data = await response.text()
                except:
                    response_data = None
            
            # Validate status code
            status_validation = self._validate_status_code(
                response.status, 
                endpoint_config.expected_status_codes
            )
            
            # Validate response content
            content_validation = self._validate_response_content(
                response_data, 
                endpoint_config.response_validation
            )
            
            # Compile validation results
            validation_results = {
                'status_code': status_validation,
                'content': content_validation,
                'response_time': {
                    'actual': response_time,
                    'acceptable': response_time <= 5.0  # 5 seconds threshold
                }
            }
            
            # Determine overall success
            success = (
                status_validation['valid'] and 
                content_validation['valid'] and 
                validation_results['response_time']['acceptable']
            )
            
            return APIValidationResult(
                success=success,
                endpoint=str(response.url),
                method=endpoint_config.method,
                status_code=response.status,
                response_time=response_time,
                response_data=response_data,
                validation_results=validation_results
            )
        
        except Exception as e:
            return APIValidationResult(
                success=False,
                endpoint=str(response.url),
                method=endpoint_config.method,
                status_code=response.status,
                response_time=response_time,
                response_data=None,
                validation_results={},
                error=f"Error processing response: {str(e)}"
            )
    
    def _validate_status_code(self, status_code: int, expected_codes: Optional[List[int]]) -> Dict[str, Any]:
        """Validate HTTP status code"""
        if expected_codes is None:
            # Default: 2xx is success
            expected_codes = [200, 201, 202, 204]
        
        valid = status_code in expected_codes
        
        return {
            'valid': valid,
            'actual': status_code,
            'expected': expected_codes,
            'success': valid,
            'message': f"Status {status_code} {'is' if valid else 'is not'} in expected codes {expected_codes}"
        }
    
    def _validate_response_content(self, response_data: Any, validation_rules: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate response content based on rules"""
        if validation_rules is None:
            return {
                'valid': True,
                'message': 'No validation rules specified'
            }
        
        validation_results = {}
        all_valid = True
        
        # Check required fields
        if 'required_fields' in validation_rules:
            required_fields = validation_rules['required_fields']
            missing_fields = []
            
            for field in required_fields:
                if isinstance(response_data, dict):
                    if field not in response_data:
                        missing_fields.append(field)
                else:
                    # For non-dict responses, check if field exists in string
                    if isinstance(response_data, str) and field not in response_data:
                        missing_fields.append(field)
            
            validation_results['required_fields'] = {
                'valid': len(missing_fields) == 0,
                'missing': missing_fields,
                'message': f"Missing required fields: {missing_fields}" if missing_fields else "All required fields present"
            }
            all_valid = all_valid and validation_results['required_fields']['valid']
        
        # Check field patterns
        if 'field_patterns' in validation_rules:
            field_patterns = validation_rules['field_patterns']
            pattern_results = {}
            
            for field, pattern in field_patterns.items():
                if isinstance(response_data, dict) and field in response_data:
                    field_value = str(response_data[field])
                    matches = bool(re.search(pattern, field_value))
                    pattern_results[field] = {
                        'valid': matches,
                        'value': field_value,
                        'pattern': pattern,
                        'message': f"Field '{field}' {'matches' if matches else 'does not match'} pattern '{pattern}'"
                    }
                    all_valid = all_valid and matches
            
            validation_results['field_patterns'] = pattern_results
        
        # Check response size
        if 'max_size' in validation_rules:
            max_size = validation_rules['max_size']
            if isinstance(response_data, str):
                actual_size = len(response_data)
            elif isinstance(response_data, dict):
                actual_size = len(json.dumps(response_data))
            else:
                actual_size = 0
            
            size_valid = actual_size <= max_size
            validation_results['size'] = {
                'valid': size_valid,
                'actual': actual_size,
                'max': max_size,
                'message': f"Response size {actual_size} {'is within' if size_valid else 'exceeds'} limit {max_size}"
            }
            all_valid = all_valid and size_valid
        
        # Check response structure
        if 'structure' in validation_rules:
            structure_rules = validation_rules['structure']
            structure_results = {}
            
            if isinstance(response_data, dict):
                # Check if response is an object
                if structure_rules.get('type') == 'object':
                    structure_results['type'] = {
                        'valid': True,
                        'message': 'Response is an object as expected'
                    }
                # Check if response is an array
                elif structure_rules.get('type') == 'array':
                    structure_results['type'] = {
                        'valid': False,
                        'message': 'Expected array but got object'
                    }
                    all_valid = False
                
                # Check array length if specified
                if 'array_length' in structure_rules and isinstance(response_data, list):
                    min_length = structure_rules['array_length'].get('min', 0)
                    max_length = structure_rules['array_length'].get('max', float('inf'))
                    actual_length = len(response_data)
                    
                    length_valid = min_length <= actual_length <= max_length
                    structure_results['array_length'] = {
                        'valid': length_valid,
                        'actual': actual_length,
                        'min': min_length,
                        'max': max_length,
                        'message': f"Array length {actual_length} {'is within' if length_valid else 'is outside'} range [{min_length}, {max_length}]"
                    }
                    all_valid = all_valid and length_valid
            
            validation_results['structure'] = structure_results
        
        return {
            'valid': all_valid,
            'results': validation_results,
            'message': 'All content validations passed' if all_valid else 'Some content validations failed'
        }
    
    def validate_multiple_endpoints(self, endpoint_configs: List[APIEndpointConfig]) -> List[APIValidationResult]:
        """Validate multiple API endpoints"""
        async def validate_all():
            tasks = [self.validate_endpoint(config) for config in endpoint_configs]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(validate_all())
            loop.close()
            
            # Handle exceptions
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append(APIValidationResult(
                        success=False,
                        endpoint="unknown",
                        method="GET",
                        status_code=None,
                        response_time=0.0,
                        response_data=None,
                        validation_results={},
                        error=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
        
        except Exception as e:
            return [APIValidationResult(
                success=False,
                endpoint="unknown",
                method="GET",
                status_code=None,
                response_time=0.0,
                response_data=None,
                validation_results={},
                error=f"Error validating endpoints: {str(e)}"
            )]


class APIManager:
    """Manages API validation for gates"""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the API manager"""
        self.validator = APIValidator(base_url=base_url)
        self.logger = logging.getLogger(__name__)
    
    def validate_gate_apis(self, gate_config: Any, app_domain: str) -> Dict[str, Any]:
        """Validate APIs for a specific gate"""
        api_results = {}
        
        # Check if gate has API validation enabled
        api_config = gate_config.validation_types.get('api', None)
        if not api_config or not api_config.enabled:
            return api_results
        
        try:
            # Get API configuration
            api_validation_config = api_config.config.get('api_validation', {})
            if not api_validation_config.get('enabled', False):
                return api_results
            
            # Get endpoints to validate
            endpoints = api_validation_config.get('endpoints', [])
            
            # Convert endpoint configs to APIEndpointConfig objects
            endpoint_configs = []
            for endpoint_data in endpoints:
                # Format URL with app domain
                url = endpoint_data['url'].format(app_domain=app_domain)
                
                config = APIEndpointConfig(
                    url=url,
                    method=endpoint_data.get('method', 'GET'),
                    headers=endpoint_data.get('headers'),
                    body=endpoint_data.get('body'),
                    params=endpoint_data.get('params'),
                    timeout=endpoint_data.get('timeout', 30),
                    expected_status_codes=endpoint_data.get('expected_status_codes'),
                    response_validation=endpoint_data.get('response_validation'),
                    auth=endpoint_data.get('auth')
                )
                endpoint_configs.append(config)
            
            # Validate all endpoints
            results = self.validator.validate_multiple_endpoints(endpoint_configs)
            
            # Compile results
            for i, result in enumerate(results):
                endpoint_key = f"endpoint_{i+1}"
                api_results[endpoint_key] = {
                    'url': result.endpoint,
                    'method': result.method,
                    'success': result.success,
                    'status_code': result.status_code,
                    'response_time': result.response_time,
                    'validation_results': result.validation_results,
                    'error': result.error
                }
            
        except Exception as e:
            self.logger.error(f"Error validating APIs for gate {gate_config.name}: {e}")
            api_results['error'] = str(e)
        
        return api_results


# Convenience functions
def validate_api_endpoint(url: str, method: str = "GET", **kwargs) -> APIValidationResult:
    """Validate a single API endpoint"""
    config = APIEndpointConfig(url=url, method=method, **kwargs)
    validator = APIValidator()
    
    async def validate():
        return await validator.validate_endpoint(config)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(validate())
        loop.close()
        return result
    except Exception as e:
        return APIValidationResult(
            success=False,
            endpoint=url,
            method=method,
            status_code=None,
            response_time=0.0,
            response_data=None,
            validation_results={},
            error=str(e)
        )


def is_api_validation_available() -> bool:
    """Check if API validation is available"""
    return REQUESTS_AVAILABLE 