"""
Unified Evidence Collector
Collects evidence from multiple sources: patterns, API, database, LLM, website, static, and custom
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

# Import all evidence collection methods
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright not available. Install with: pip install playwright && playwright install")

try:
    import aiohttp
    import requests
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    print("⚠️ HTTP libraries not available. Install with: pip install requests aiohttp")

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("⚠️ YAML not available. Install with: pip install PyYAML")


@dataclass
class EvidenceResult:
    """Result of an evidence collection operation"""
    success: bool
    evidence_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    score: float = 0.0
    error: Optional[str] = None


@dataclass
class EvidenceConfig:
    """Configuration for evidence collection"""
    enabled: bool
    method: str
    config: Dict[str, Any]
    weight: float = 1.0


class EvidenceCollector:
    """Unified evidence collector for all validation types"""
    
    def __init__(self, headless: bool = True, screenshot_dir: Optional[str] = None):
        """Initialize the evidence collector"""
        self.headless = headless
        self.screenshot_dir = screenshot_dir or "evidence_screenshots"
        self.browser = None
        self.context = None
        self.logger = logging.getLogger(__name__)
        
        # Create screenshot directory
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        """Start the evidence collector (initialize browser if needed)"""
        if PLAYWRIGHT_AVAILABLE:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
                self.context = await self.browser.new_context()
                self.logger.info("Browser context initialized for evidence collection")
            except Exception as e:
                self.logger.error(f"Failed to initialize browser: {e}")
    
    async def stop(self):
        """Stop the evidence collector"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def collect_evidence(self, gate_config: Any, app_domain: str, repo_path: Optional[Path] = None, 
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, EvidenceResult]:
        """Collect evidence using all configured methods for a gate"""
        evidence_results = {}
        
        # Get evidence configuration from gate
        evidence_configs = self._get_evidence_configs(gate_config)
        
        for method_name, config in evidence_configs.items():
            if not config.enabled:
                continue
            
            try:
                self.logger.info(f"Collecting {method_name} evidence for gate {gate_config.name}")
                
                if method_name == "pattern":
                    result = await self._collect_pattern_evidence(config, repo_path, metadata)
                elif method_name == "api":
                    result = await self._collect_api_evidence(config, app_domain)
                elif method_name == "database":
                    result = await self._collect_database_evidence(config, app_domain)
                elif method_name == "llm":
                    result = await self._collect_llm_evidence(config, gate_config, metadata)
                elif method_name == "website":
                    result = await self._collect_website_evidence(config, app_domain)
                elif method_name == "static":
                    result = await self._collect_static_evidence(config, metadata)
                elif method_name == "custom":
                    result = await self._collect_custom_evidence(config, gate_config, app_domain)
                else:
                    result = EvidenceResult(
                        success=False,
                        evidence_type=method_name,
                        data={},
                        metadata={'error': f'Unknown evidence method: {method_name}'},
                        timestamp=datetime.now(),
                        error=f"Unknown evidence method: {method_name}"
                    )
                
                evidence_results[method_name] = result
                
            except Exception as e:
                self.logger.error(f"Error collecting {method_name} evidence: {e}")
                evidence_results[method_name] = EvidenceResult(
                    success=False,
                    evidence_type=method_name,
                    data={},
                    metadata={'error': str(e)},
                    timestamp=datetime.now(),
                    error=str(e)
                )
        
        return evidence_results
    
    def _get_evidence_configs(self, gate_config: Any) -> Dict[str, EvidenceConfig]:
        """Extract evidence configurations from gate config"""
        evidence_configs = {}
        
        # Get validation types and convert them to evidence configs
        for val_type, val_config in gate_config.validation_types.items():
            if not val_config.enabled:
                continue
            
            # Map validation types to evidence methods
            method_mapping = {
                'pattern': 'pattern',
                'api': 'api', 
                'database': 'database',
                'llm': 'llm',
                'evidence': 'website',  # Legacy evidence -> website
                'static': 'static'
            }
            
            method_name = method_mapping.get(val_type.value, val_type.value)
            
            evidence_configs[method_name] = EvidenceConfig(
                enabled=val_config.enabled,
                method=method_name,
                config=val_config.config,
                weight=gate_config.weight
            )
        
        return evidence_configs
    
    async def _collect_pattern_evidence(self, config: EvidenceConfig, repo_path: Path, 
                                      metadata: Dict[str, Any]) -> EvidenceResult:
        """Collect pattern-based evidence from source code"""
        try:
            patterns_config = config.config.get('patterns', {})
            positive_patterns = patterns_config.get('positive', [])
            negative_patterns = patterns_config.get('negative', [])
            
            matches = []
            violations = []
            
            # Scan source code files
            for file_info in metadata.get('files', []):
                if file_info.get('type') == 'Source Code':
                    file_path = repo_path / file_info['relative_path']
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Check positive patterns
                            for pattern in positive_patterns:
                                if pattern in content:
                                    matches.append({
                                        'file': file_info['relative_path'],
                                        'pattern': pattern,
                                        'language': file_info.get('language', 'unknown')
                                    })
                            
                            # Check negative patterns
                            for pattern in negative_patterns:
                                if pattern in content:
                                    violations.append({
                                        'file': file_info['relative_path'],
                                        'pattern': pattern,
                                        'language': file_info.get('language', 'unknown')
                                    })
                    except Exception as e:
                        continue
            
            # Calculate score
            total_files = len([f for f in metadata.get('files', []) if f.get('type') == 'Source Code'])
            positive_score = (len(matches) / max(total_files, 1)) * 100 if positive_patterns else 0
            negative_penalty = (len(violations) / max(total_files, 1)) * 100 if negative_patterns else 0
            score = max(0, positive_score - negative_penalty)
            
            return EvidenceResult(
                success=score > 0,
                evidence_type="pattern",
                data={
                    'matches': matches,
                    'violations': violations,
                    'total_files_scanned': total_files,
                    'positive_patterns': positive_patterns,
                    'negative_patterns': negative_patterns
                },
                metadata={
                    'method': 'pattern',
                    'total_files': total_files,
                    'match_count': len(matches),
                    'violation_count': len(violations)
                },
                timestamp=datetime.now(),
                score=score
            )
            
        except Exception as e:
            return EvidenceResult(
                success=False,
                evidence_type="pattern",
                data={},
                metadata={'error': str(e)},
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _collect_api_evidence(self, config: EvidenceConfig, app_domain: str) -> EvidenceResult:
        """Collect API-based evidence"""
        if not HTTP_AVAILABLE:
            return EvidenceResult(
                success=False,
                evidence_type="api",
                data={},
                metadata={'error': 'HTTP libraries not available'},
                timestamp=datetime.now(),
                error="HTTP libraries not available"
            )
        
        try:
            api_config = config.config.get('api_validation', {})
            endpoints = api_config.get('endpoints', [])
            
            results = []
            total_endpoints = len(endpoints)
            successful_endpoints = 0
            
            for endpoint_data in endpoints:
                try:
                    # Format URL with app domain
                    url = endpoint_data['url'].format(app_domain=app_domain)
                    
                    # Make HTTP request
                    async with aiohttp.ClientSession() as session:
                        method = endpoint_data.get('method', 'GET').upper()
                        headers = endpoint_data.get('headers', {})
                        body = endpoint_data.get('body')
                        params = endpoint_data.get('params')
                        timeout = endpoint_data.get('timeout', 30)
                        
                        start_time = datetime.now()
                        
                        if method == 'GET':
                            async with session.get(url, headers=headers, params=params, 
                                                 timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                                response_data = await response.json() if response.headers.get('content-type', '').startswith('application/json') else await response.text()
                                response_time = (datetime.now() - start_time).total_seconds()
                                
                                # Validate response
                                success = self._validate_api_response(response.status, response_data, endpoint_data.get('response_validation', {}))
                                
                                results.append({
                                    'url': url,
                                    'method': method,
                                    'status_code': response.status,
                                    'response_time': response_time,
                                    'success': success,
                                    'response_data': response_data
                                })
                                
                                if success:
                                    successful_endpoints += 1
                        
                        # Similar for POST, PUT, DELETE...
                        
                except Exception as e:
                    results.append({
                        'url': endpoint_data.get('url', 'unknown'),
                        'method': endpoint_data.get('method', 'GET'),
                        'error': str(e),
                        'success': False
                    })
            
            score = (successful_endpoints / total_endpoints) * 100 if total_endpoints > 0 else 0
            
            return EvidenceResult(
                success=score > 0,
                evidence_type="api",
                data={
                    'endpoints': results,
                    'total_endpoints': total_endpoints,
                    'successful_endpoints': successful_endpoints
                },
                metadata={
                    'method': 'api',
                    'app_domain': app_domain
                },
                timestamp=datetime.now(),
                score=score
            )
            
        except Exception as e:
            return EvidenceResult(
                success=False,
                evidence_type="api",
                data={},
                metadata={'error': str(e)},
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _collect_database_evidence(self, config: EvidenceConfig, app_domain: str) -> EvidenceResult:
        """Collect database-based evidence"""
        try:
            query_name = config.config.get('query')
            
            if query_name == 'fetch_alerting_integrations_status':
                # Import database integration
                from .db_integration import fetch_alerting_integrations_status, extract_app_id_from_url
                
                # Extract app_id from app_domain or use default
                app_id = extract_app_id_from_url(app_domain) or app_domain
                
                # Execute database query
                integration_status = fetch_alerting_integrations_status(app_id)
                present = [k for k, v in integration_status.items() if v]
                missing = [k for k, v in integration_status.items() if not v]
                all_present = all(integration_status.values())
                
                score = 100.0 if all_present else 0.0
                
                return EvidenceResult(
                    success=all_present,
                    evidence_type="database",
                    data={
                        'integration_status': integration_status,
                        'present': present,
                        'missing': missing,
                        'app_id': app_id
                    },
                    metadata={
                        'method': 'database',
                        'query': query_name,
                        'app_domain': app_domain
                    },
                    timestamp=datetime.now(),
                    score=score
                )
            else:
                return EvidenceResult(
                    success=False,
                    evidence_type="database",
                    data={},
                    metadata={'error': f'Unknown database query: {query_name}'},
                    timestamp=datetime.now(),
                    error=f"Unknown database query: {query_name}"
                )
                
        except Exception as e:
            return EvidenceResult(
                success=False,
                evidence_type="database",
                data={},
                metadata={'error': str(e)},
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _collect_llm_evidence(self, config: EvidenceConfig, gate_config: Any, 
                                  metadata: Dict[str, Any]) -> EvidenceResult:
        """Collect LLM-based evidence"""
        try:
            from .llm_client import create_llm_client_from_env
            
            # Create LLM client
            llm_client = create_llm_client_from_env()
            
            # Create prompt for gate validation
            prompt = self._create_llm_prompt(gate_config, metadata)
            
            # Get LLM response
            response = llm_client.generate_response(prompt)
            
            # Parse LLM response
            llm_score = self._parse_llm_response(response, gate_config)
            
            return EvidenceResult(
                success=llm_score > 0,
                evidence_type="llm",
                data={
                    'llm_response': response,
                    'prompt': prompt,
                    'gate_config': {
                        'name': gate_config.name,
                        'display_name': gate_config.display_name,
                        'description': gate_config.description
                    }
                },
                metadata={
                    'method': 'llm',
                    'total_files': metadata.get('total_files', 0),
                    'languages': metadata.get('languages', [])
                },
                timestamp=datetime.now(),
                score=llm_score
            )
            
        except Exception as e:
            return EvidenceResult(
                success=False,
                evidence_type="llm",
                data={},
                metadata={'error': str(e)},
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _collect_website_evidence(self, config: EvidenceConfig, app_domain: str) -> EvidenceResult:
        """Collect website-based evidence using Playwright"""
        if not PLAYWRIGHT_AVAILABLE:
            return EvidenceResult(
                success=False,
                evidence_type="website",
                data={},
                metadata={'error': 'Playwright not available'},
                timestamp=datetime.now(),
                error="Playwright not available"
            )
        
        try:
            website_config = config.config.get('website_validation', {})
            urls_to_check = website_config.get('urls_to_check', [])
            checks = website_config.get('checks', [])
            
            results = []
            total_checks = 0
            successful_checks = 0
            
            for url_template in urls_to_check:
                url = url_template.format(app_domain=app_domain)
                
                try:
                    # Create new page
                    page = await self.context.new_page()
                    
                    # Navigate to URL
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                    
                    # Perform checks
                    for check in checks:
                        total_checks += 1
                        check_result = await self._perform_website_check(page, check, url)
                        results.append(check_result)
                        
                        if check_result.get('success', False):
                            successful_checks += 1
                    
                    # Close page
                    await page.close()
                    
                except Exception as e:
                    results.append({
                        'url': url,
                        'error': str(e),
                        'success': False
                    })
            
            score = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
            
            return EvidenceResult(
                success=score > 0,
                evidence_type="website",
                data={
                    'checks': results,
                    'total_checks': total_checks,
                    'successful_checks': successful_checks,
                    'urls_checked': urls_to_check
                },
                metadata={
                    'method': 'website',
                    'app_domain': app_domain
                },
                timestamp=datetime.now(),
                score=score
            )
            
        except Exception as e:
            return EvidenceResult(
                success=False,
                evidence_type="website",
                data={},
                metadata={'error': str(e)},
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _collect_static_evidence(self, config: EvidenceConfig, metadata: Dict[str, Any]) -> EvidenceResult:
        """Collect static analysis evidence"""
        try:
            total_files = metadata.get('total_files', 0)
            languages = metadata.get('languages', [])
            file_types = metadata.get('file_types', {})
            
            # Calculate static score based on metadata
            static_score = 0.0
            static_details = []
            
            if total_files > 0:
                static_score += 20.0
                static_details.append(f"Codebase has {total_files} files")
            
            if len(languages) > 0:
                static_score += 20.0
                static_details.append(f"Supports {len(languages)} languages")
            
            # Add more static analysis logic as needed
            
            return EvidenceResult(
                success=static_score > 0,
                evidence_type="static",
                data={
                    'metadata': metadata,
                    'static_analysis': {
                        'total_files': total_files,
                        'languages': languages,
                        'file_types': file_types,
                        'details': static_details
                    }
                },
                metadata={
                    'method': 'static'
                },
                timestamp=datetime.now(),
                score=static_score
            )
            
        except Exception as e:
            return EvidenceResult(
                success=False,
                evidence_type="static",
                data={},
                metadata={'error': str(e)},
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _collect_custom_evidence(self, config: EvidenceConfig, gate_config: Any, 
                                     app_domain: str) -> EvidenceResult:
        """Collect custom evidence using user-defined functions"""
        try:
            custom_config = config.config.get('custom_validation', {})
            custom_function = custom_config.get('function')
            
            if custom_function:
                # Execute custom function
                # This could be a callable or a string to eval/exec
                if callable(custom_function):
                    result = await custom_function(gate_config, app_domain)
                else:
                    # Execute as string (be careful with security)
                    result = eval(custom_function, {
                        'gate_config': gate_config,
                        'app_domain': app_domain,
                        'datetime': datetime
                    })
                
                return EvidenceResult(
                    success=result.get('success', False),
                    evidence_type="custom",
                    data=result.get('data', {}),
                    metadata={
                        'method': 'custom',
                        'custom_function': str(custom_function)
                    },
                    timestamp=datetime.now(),
                    score=result.get('score', 0.0)
                )
            else:
                return EvidenceResult(
                    success=False,
                    evidence_type="custom",
                    data={},
                    metadata={'error': 'No custom function defined'},
                    timestamp=datetime.now(),
                    error="No custom function defined"
                )
                
        except Exception as e:
            return EvidenceResult(
                success=False,
                evidence_type="custom",
                data={},
                metadata={'error': str(e)},
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def _perform_website_check(self, page: Page, check: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Perform a specific website check"""
        check_type = check.get('type')
        
        try:
            if check_type == 'text_extraction':
                return await self._extract_text(page, check, url)
            elif check_type == 'screenshot':
                return await self._take_screenshot(page, check, url)
            elif check_type == 'javascript_error_detection':
                return await self._detect_javascript_errors(page, check, url)
            elif check_type == 'element_validation':
                return await self._validate_elements(page, check, url)
            elif check_type == 'api_call_detection':
                return await self._detect_api_calls(page, check, url)
            else:
                return {
                    'type': check_type,
                    'success': False,
                    'error': f'Unknown check type: {check_type}'
                }
        except Exception as e:
            return {
                'type': check_type,
                'success': False,
                'error': str(e)
            }
    
    async def _extract_text(self, page: Page, check: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Extract text from page elements"""
        selectors = check.get('selectors', ['body'])
        patterns = check.get('patterns', [])
        
        extracted_text = []
        matches = []
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    extracted_text.append({
                        'selector': selector,
                        'text': text
                    })
                    
                    # Check patterns
                    for pattern in patterns:
                        if pattern.lower() in text.lower():
                            matches.append({
                                'selector': selector,
                                'pattern': pattern,
                                'text_snippet': text[:100] + '...' if len(text) > 100 else text
                            })
            except Exception as e:
                continue
        
        return {
            'type': 'text_extraction',
            'success': len(matches) > 0,
            'extracted_text': extracted_text,
            'matches': matches,
            'url': url
        }
    
    async def _take_screenshot(self, page: Page, check: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Take screenshot of page or elements"""
        name = check.get('name', 'screenshot')
        selectors = check.get('selectors', [])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = Path(self.screenshot_dir) / filename
        
        try:
            if selectors:
                # Screenshot specific elements
                screenshots = []
                for selector in selectors:
                    element = await page.query_selector(selector)
                    if element:
                        element_filename = f"{name}_{selector.replace('.', '_').replace('#', '')}_{timestamp}.png"
                        element_filepath = Path(self.screenshot_dir) / element_filename
                        await element.screenshot(path=str(element_filepath))
                        screenshots.append(str(element_filepath))
            else:
                # Screenshot full page
                await page.screenshot(path=str(filepath))
                screenshots = [str(filepath)]
            
            return {
                'type': 'screenshot',
                'success': True,
                'screenshots': screenshots,
                'url': url
            }
        except Exception as e:
            return {
                'type': 'screenshot',
                'success': False,
                'error': str(e),
                'url': url
            }
    
    async def _detect_javascript_errors(self, page: Page, check: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Detect JavaScript errors on the page"""
        errors = []
        
        try:
            # Listen for console errors
            page.on("console", lambda msg: errors.append({
                'type': msg.type,
                'text': msg.text,
                'timestamp': datetime.now().isoformat()
            }) if msg.type == 'error' else None)
            
            # Wait a bit for errors to accumulate
            await page.wait_for_timeout(2000)
            
            return {
                'type': 'javascript_error_detection',
                'success': len(errors) == 0,
                'errors': errors,
                'error_count': len(errors),
                'url': url
            }
        except Exception as e:
            return {
                'type': 'javascript_error_detection',
                'success': False,
                'error': str(e),
                'url': url
            }
    
    async def _validate_elements(self, page: Page, check: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Validate presence and properties of elements"""
        selectors = check.get('selectors', [])
        properties = check.get('properties', {})
        
        validation_results = []
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    element_properties = {}
                    for prop_name, expected_value in properties.items():
                        if prop_name == 'text':
                            element_properties[prop_name] = await element.text_content()
                        elif prop_name == 'visible':
                            element_properties[prop_name] = await element.is_visible()
                        else:
                            element_properties[prop_name] = await element.get_attribute(prop_name)
                    
                    validation_results.append({
                        'selector': selector,
                        'found': True,
                        'properties': element_properties
                    })
                else:
                    validation_results.append({
                        'selector': selector,
                        'found': False
                    })
            except Exception as e:
                validation_results.append({
                    'selector': selector,
                    'found': False,
                    'error': str(e)
                })
        
        success = all(result.get('found', False) for result in validation_results)
        
        return {
            'type': 'element_validation',
            'success': success,
            'validation_results': validation_results,
            'url': url
        }
    
    async def _detect_api_calls(self, page: Page, check: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Detect API calls made by the page"""
        api_calls = []
        
        try:
            # Listen for network requests
            page.on("request", lambda request: api_calls.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'timestamp': datetime.now().isoformat()
            }))
            
            # Wait for network activity
            await page.wait_for_timeout(3000)
            
            return {
                'type': 'api_call_detection',
                'success': True,
                'api_calls': api_calls,
                'call_count': len(api_calls),
                'url': url
            }
        except Exception as e:
            return {
                'type': 'api_call_detection',
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def _validate_api_response(self, status_code: int, response_data: Any, validation_rules: Dict[str, Any]) -> bool:
        """Validate API response based on rules"""
        # Check status code
        expected_codes = validation_rules.get('expected_status_codes', [200, 201, 202, 204])
        if status_code not in expected_codes:
            return False
        
        # Check required fields
        required_fields = validation_rules.get('required_fields', [])
        if required_fields and isinstance(response_data, dict):
            for field in required_fields:
                if field not in response_data:
                    return False
        
        # Check field patterns
        field_patterns = validation_rules.get('field_patterns', {})
        if field_patterns and isinstance(response_data, dict):
            for field, pattern in field_patterns.items():
                if field in response_data:
                    field_value = str(response_data[field])
                    if not re.search(pattern, field_value):
                        return False
        
        return True
    
    def _create_llm_prompt(self, gate_config: Any, metadata: Dict[str, Any]) -> str:
        """Create LLM prompt for gate validation"""
        return f"""
        Analyze the following codebase for {gate_config.name} compliance:
        
        Gate: {gate_config.display_name}
        Description: {gate_config.description}
        Category: {gate_config.category}
        Priority: {gate_config.priority}
        
        Codebase Information:
        - Total files: {metadata.get('total_files', 0)}
        - Languages: {', '.join(metadata.get('languages', []))}
        - Primary technology: {metadata.get('primary_technology', 'Unknown')}
        
        Please provide:
        1. A compliance score (0-100)
        2. Specific findings
        3. Recommendations for improvement
        
        Respond in JSON format:
        {{
            "score": <number>,
            "findings": ["finding1", "finding2"],
            "recommendations": ["rec1", "rec2"]
        }}
        """
    
    def _parse_llm_response(self, response: str, gate_config: Any) -> float:
        """Parse LLM response and extract score"""
        try:
            # Try to parse JSON response
            data = json.loads(response)
            return float(data.get('score', 0))
        except:
            # Fallback: try to extract score from text
            score_match = re.search(r'score["\s:]*(\d+)', response, re.IGNORECASE)
            if score_match:
                return float(score_match.group(1))
            return 0.0


class EvidenceManager:
    """Manages evidence collection for gates"""
    
    def __init__(self, headless: bool = True, screenshot_dir: Optional[str] = None):
        """Initialize the evidence manager"""
        self.collector = EvidenceCollector(headless=headless, screenshot_dir=screenshot_dir)
    
    async def collect_gate_evidence(self, gate_config: Any, app_domain: str, repo_path: Optional[Path] = None, 
                                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, EvidenceResult]:
        """Collect evidence for a specific gate"""
        await self.collector.start()
        try:
            return await self.collector.collect_evidence(gate_config, app_domain, repo_path, metadata)
        finally:
            await self.collector.stop()


# Convenience functions
async def collect_evidence_for_gate(gate_config: Any, app_domain: str, repo_path: Optional[Path] = None, 
                                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, EvidenceResult]:
    """Collect evidence for a gate"""
    manager = EvidenceManager()
    return await manager.collect_gate_evidence(gate_config, app_domain, repo_path, metadata)


def is_evidence_available() -> bool:
    """Check if evidence collection is available"""
    return PLAYWRIGHT_AVAILABLE or HTTP_AVAILABLE or YAML_AVAILABLE 