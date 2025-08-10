"""
Playwright Integration for CodeGates
Provides functionality to access evidence from web portals using headless browser automation

Preferred configuration:

    BAM_PORTAL_URL=https://your-bam-portal.com
    BAM_USERNAME=your-username
    BAM_PASSWORD=your-password
    PLAYWRIGHT_TIMEOUT=30000  # milliseconds
    PLAYWRIGHT_HEADLESS=true  # run in headless mode
    PLAYWRIGHT_SCREENSHOT_DIR=./screenshots  # directory for screenshots
    PLAYWRIGHT_VIEWPORT_WIDTH=1920
    PLAYWRIGHT_VIEWPORT_HEIGHT=1080

Supports multiple portal types:
- BAM (Business Activity Monitoring)
- Splunk Web UI
- AppDynamics Web UI
- Custom monitoring portals
"""

import os
import asyncio
import json
import base64
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import time
import re

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[PlaywrightIntegration] ⚠️ Warning: Playwright not installed. Install with: pip install playwright")
    print("[PlaywrightIntegration] ⚠️ Then run: playwright install")

class PlaywrightIntegration:
    """Handles Playwright integration for CodeGates web portal evidence collection"""
    
    def __init__(self):
        self.bam_url = os.getenv("BAM_PORTAL_URL")
        self.bam_username = os.getenv("BAM_USERNAME")
        self.bam_password = os.getenv("BAM_PASSWORD")
        self.splunk_web_url = os.getenv("SPLUNK_WEB_URL")
        self.appd_web_url = os.getenv("APPDYNAMICS_WEB_URL")
        self.timeout = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))
        self.headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
        self.screenshot_dir = Path(os.getenv("PLAYWRIGHT_SCREENSHOT_DIR", "./screenshots"))
        self.viewport_width = int(os.getenv("PLAYWRIGHT_VIEWPORT_WIDTH", "1920"))
        self.viewport_height = int(os.getenv("PLAYWRIGHT_VIEWPORT_HEIGHT", "1080"))
        self.browser = None
        self.context = None
        self.page = None
        
        # Ensure screenshot directory exists
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
    def is_configured(self) -> bool:
        """Check if Playwright is properly configured"""
        if not PLAYWRIGHT_AVAILABLE:
            print("[PlaywrightIntegration] ⚠️ Warning: Playwright not available. Please install playwright.")
            return False
        
        # Check if at least one portal URL is configured
        if not any([self.bam_url, self.splunk_web_url, self.appd_web_url]):
            print("[PlaywrightIntegration] ⚠️ Warning: No portal URLs configured. Please set BAM_PORTAL_URL, SPLUNK_WEB_URL, or APPDYNAMICS_WEB_URL.")
            return False
        
        return True
    
    async def initialize_browser(self) -> bool:
        """Initialize Playwright browser"""
        if not self.is_configured():
            return False
        
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # Create context
            self.context = await self.browser.new_context(
                viewport={'width': self.viewport_width, 'height': self.viewport_height},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            await self.page.set_default_timeout(self.timeout)
            
            print("[PlaywrightIntegration] ✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            print(f"[PlaywrightIntegration] ❌ Error initializing browser: {str(e)}")
            return False
    
    async def close_browser(self):
        """Close Playwright browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            print("[PlaywrightIntegration] ✅ Browser closed successfully")
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error closing browser: {str(e)}")
    
    async def take_screenshot(self, name: str) -> Optional[str]:
        """Take a screenshot and save it"""
        if not self.page:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            await self.page.screenshot(path=str(filepath), full_page=True)
            print(f"[PlaywrightIntegration] 📸 Screenshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"[PlaywrightIntegration] ❌ Error taking screenshot: {str(e)}")
            return None
    
    async def extract_text_content(self, selectors: List[str] = None) -> Dict[str, Any]:
        """Extract text content from the current page"""
        if not self.page:
            return {"content": "", "elements": []}
        
        try:
            content = {}
            
            # Default selectors for common portal elements
            default_selectors = [
                "body",
                "main",
                ".content",
                ".main-content",
                "#content",
                ".dashboard",
                ".monitoring-panel"
            ]
            
            selectors_to_use = selectors or default_selectors
            
            for selector in selectors_to_use:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        text_content = []
                        for element in elements:
                            text = await element.text_content()
                            if text and text.strip():
                                text_content.append(text.strip())
                        
                        if text_content:
                            content[selector] = text_content
                except Exception as e:
                    print(f"[PlaywrightIntegration] ⚠️ Error extracting from selector '{selector}': {str(e)}")
            
            # Get page title and URL
            title = await self.page.title()
            url = self.page.url
            
            return {
                "title": title,
                "url": url,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[PlaywrightIntegration] ❌ Error extracting text content: {str(e)}")
            return {"content": "", "elements": [], "error": str(e)}
    
    async def access_bam_portal(self, app_id: str = None) -> Dict[str, Any]:
        """Access BAM portal and collect evidence"""
        if not self.bam_url:
            return {
                "status": "error",
                "message": "BAM portal URL not configured",
                "evidence": {}
            }
        
        try:
            print(f"[PlaywrightIntegration] 🔍 Accessing BAM portal: {self.bam_url}")
            
            # Navigate to BAM portal
            await self.page.goto(self.bam_url)
            
            # Take initial screenshot
            screenshot_path = await self.take_screenshot("bam_initial")
            
            # Check if login is required
            login_required = await self._check_login_required()
            
            if login_required and (self.bam_username and self.bam_password):
                print("[PlaywrightIntegration] 🔐 Logging into BAM portal...")
                login_success = await self._login_bam_portal()
                if not login_success:
                    return {
                        "status": "error",
                        "message": "Failed to login to BAM portal",
                        "evidence": {}
                    }
            
            # Navigate to monitoring dashboard
            await self._navigate_bam_dashboard(app_id)
            
            # Take dashboard screenshot
            dashboard_screenshot = await self.take_screenshot("bam_dashboard")
            
            # Extract monitoring data
            monitoring_data = await self._extract_bam_monitoring_data()
            
            # Extract text content
            text_content = await self.extract_text_content([
                ".monitoring-panel",
                ".dashboard-content",
                ".status-panel",
                ".alert-panel",
                ".metric-panel"
            ])
            
            evidence = {
                "portal_type": "BAM",
                "url": self.bam_url,
                "app_id": app_id,
                "screenshots": {
                    "initial": screenshot_path,
                    "dashboard": dashboard_screenshot
                },
                "monitoring_data": monitoring_data,
                "text_content": text_content,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": "BAM portal evidence collected successfully",
                "evidence": evidence
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error accessing BAM portal: {str(e)}",
                "evidence": {}
            }
    
    async def access_splunk_web_ui(self, app_id: str = None) -> Dict[str, Any]:
        """Access Splunk Web UI and collect evidence"""
        if not self.splunk_web_url:
            return {
                "status": "error",
                "message": "Splunk Web UI URL not configured",
                "evidence": {}
            }
        
        try:
            print(f"[PlaywrightIntegration] 🔍 Accessing Splunk Web UI: {self.splunk_web_url}")
            
            # Navigate to Splunk Web UI
            await self.page.goto(self.splunk_web_url)
            
            # Take initial screenshot
            screenshot_path = await self.take_screenshot("splunk_initial")
            
            # Check if login is required
            login_required = await self._check_login_required()
            
            if login_required:
                print("[PlaywrightIntegration] 🔐 Login required for Splunk Web UI")
                # Note: Splunk Web UI login would need specific implementation
                # based on the Splunk instance configuration
            
            # Navigate to search interface
            await self._navigate_splunk_search(app_id)
            
            # Take search screenshot
            search_screenshot = await self.take_screenshot("splunk_search")
            
            # Extract search results
            search_data = await self._extract_splunk_search_data()
            
            # Extract text content
            text_content = await self.extract_text_content([
                ".search-results",
                ".dashboard-panel",
                ".search-status",
                ".result-count"
            ])
            
            evidence = {
                "portal_type": "Splunk Web UI",
                "url": self.splunk_web_url,
                "app_id": app_id,
                "screenshots": {
                    "initial": screenshot_path,
                    "search": search_screenshot
                },
                "search_data": search_data,
                "text_content": text_content,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": "Splunk Web UI evidence collected successfully",
                "evidence": evidence
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error accessing Splunk Web UI: {str(e)}",
                "evidence": {}
            }
    
    async def access_appdynamics_web_ui(self, app_id: str = None) -> Dict[str, Any]:
        """Access AppDynamics Web UI and collect evidence"""
        if not self.appd_web_url:
            return {
                "status": "error",
                "message": "AppDynamics Web UI URL not configured",
                "evidence": {}
            }
        
        try:
            print(f"[PlaywrightIntegration] 🔍 Accessing AppDynamics Web UI: {self.appd_web_url}")
            
            # Navigate to AppDynamics Web UI
            await self.page.goto(self.appd_web_url)
            
            # Take initial screenshot
            screenshot_path = await self.take_screenshot("appd_initial")
            
            # Check if login is required
            login_required = await self._check_login_required()
            
            if login_required:
                print("[PlaywrightIntegration] 🔐 Login required for AppDynamics Web UI")
                # Note: AppDynamics Web UI login would need specific implementation
                # based on the AppDynamics instance configuration
            
            # Navigate to application dashboard
            await self._navigate_appd_dashboard(app_id)
            
            # Take dashboard screenshot
            dashboard_screenshot = await self.take_screenshot("appd_dashboard")
            
            # Extract application data
            app_data = await self._extract_appd_application_data()
            
            # Extract text content
            text_content = await self.extract_text_content([
                ".application-dashboard",
                ".health-rules",
                ".metrics-panel",
                ".alerts-panel"
            ])
            
            evidence = {
                "portal_type": "AppDynamics Web UI",
                "url": self.appd_web_url,
                "app_id": app_id,
                "screenshots": {
                    "initial": screenshot_path,
                    "dashboard": dashboard_screenshot
                },
                "application_data": app_data,
                "text_content": text_content,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": "AppDynamics Web UI evidence collected successfully",
                "evidence": evidence
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error accessing AppDynamics Web UI: {str(e)}",
                "evidence": {}
            }
    
    async def access_custom_portal(self, portal_url: str, app_id: str = None, 
                                 custom_selectors: List[str] = None) -> Dict[str, Any]:
        """Access a custom portal and collect evidence"""
        try:
            print(f"[PlaywrightIntegration] 🔍 Accessing custom portal: {portal_url}")
            
            # Navigate to custom portal
            await self.page.goto(portal_url)
            
            # Take initial screenshot
            screenshot_path = await self.take_screenshot("custom_initial")
            
            # Wait for page to load
            await self.page.wait_for_load_state("networkidle")
            
            # Take loaded screenshot
            loaded_screenshot = await self.take_screenshot("custom_loaded")
            
            # Extract text content with custom selectors
            text_content = await self.extract_text_content(custom_selectors)
            
            # Extract any monitoring data
            monitoring_data = await self._extract_generic_monitoring_data()
            
            evidence = {
                "portal_type": "Custom Portal",
                "url": portal_url,
                "app_id": app_id,
                "screenshots": {
                    "initial": screenshot_path,
                    "loaded": loaded_screenshot
                },
                "monitoring_data": monitoring_data,
                "text_content": text_content,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "message": "Custom portal evidence collected successfully",
                "evidence": evidence
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error accessing custom portal: {str(e)}",
                "evidence": {}
            }
    
    async def _check_login_required(self) -> bool:
        """Check if login is required on the current page"""
        try:
            # Common login indicators
            login_indicators = [
                "input[type='password']",
                "input[name*='password']",
                "input[name*='passwd']",
                ".login-form",
                "#login",
                "[data-testid*='login']"
            ]
            
            for selector in login_indicators:
                element = await self.page.query_selector(selector)
                if element:
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _login_bam_portal(self) -> bool:
        """Login to BAM portal"""
        try:
            # Common BAM login selectors (adjust based on actual BAM portal)
            username_selector = "input[name='username'], input[name='user'], input[type='email'], #username"
            password_selector = "input[name='password'], input[name='passwd'], input[type='password'], #password"
            submit_selector = "button[type='submit'], input[type='submit'], .login-button, #login-button"
            
            # Fill username
            await self.page.fill(username_selector, self.bam_username)
            
            # Fill password
            await self.page.fill(password_selector, self.bam_password)
            
            # Submit form
            await self.page.click(submit_selector)
            
            # Wait for navigation
            await self.page.wait_for_load_state("networkidle")
            
            print("[PlaywrightIntegration] ✅ BAM portal login successful")
            return True
            
        except Exception as e:
            print(f"[PlaywrightIntegration] ❌ BAM portal login failed: {str(e)}")
            return False
    
    async def _navigate_bam_dashboard(self, app_id: str = None):
        """Navigate to BAM dashboard"""
        try:
            # Common BAM dashboard navigation patterns
            dashboard_selectors = [
                "a[href*='dashboard']",
                "a[href*='monitoring']",
                ".dashboard-link",
                "#dashboard",
                "[data-testid='dashboard']"
            ]
            
            for selector in dashboard_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await self.page.wait_for_load_state("networkidle")
                        break
                except:
                    continue
            
            # If app_id is provided, try to navigate to specific app
            if app_id:
                await self._navigate_to_specific_app(app_id)
                
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error navigating BAM dashboard: {str(e)}")
    
    async def _navigate_splunk_search(self, app_id: str = None):
        """Navigate to Splunk search interface"""
        try:
            # Navigate to search interface
            search_selectors = [
                "a[href*='search']",
                ".search-link",
                "#search",
                "[data-testid='search']"
            ]
            
            for selector in search_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await self.page.wait_for_load_state("networkidle")
                        break
                except:
                    continue
            
            # If app_id is provided, try to search for it
            if app_id:
                await self._search_for_app_id(app_id)
                
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error navigating Splunk search: {str(e)}")
    
    async def _navigate_appd_dashboard(self, app_id: str = None):
        """Navigate to AppDynamics dashboard"""
        try:
            # Common AppDynamics dashboard navigation patterns
            dashboard_selectors = [
                "a[href*='dashboard']",
                "a[href*='application']",
                ".dashboard-link",
                "#dashboard",
                "[data-testid='dashboard']"
            ]
            
            for selector in dashboard_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await self.page.wait_for_load_state("networkidle")
                        break
                except:
                    continue
            
            # If app_id is provided, try to navigate to specific app
            if app_id:
                await self._navigate_to_specific_app(app_id)
                
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error navigating AppDynamics dashboard: {str(e)}")
    
    async def _navigate_to_specific_app(self, app_id: str):
        """Navigate to a specific application"""
        try:
            # Try to find and click on app-specific elements
            app_selectors = [
                f"a[href*='{app_id}']",
                f"[data-app-id='{app_id}']",
                f"[data-testid*='{app_id}']",
                f".app-{app_id}",
                f"#{app_id}"
            ]
            
            for selector in app_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await self.page.wait_for_load_state("networkidle")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error navigating to specific app: {str(e)}")
    
    async def _search_for_app_id(self, app_id: str):
        """Search for a specific app ID"""
        try:
            # Try to find search input and search for app_id
            search_selectors = [
                "input[type='search']",
                "input[name*='search']",
                "#search",
                ".search-input",
                "[data-testid='search-input']"
            ]
            
            for selector in search_selectors:
                try:
                    search_input = await self.page.query_selector(selector)
                    if search_input:
                        await search_input.fill(app_id)
                        await search_input.press("Enter")
                        await self.page.wait_for_load_state("networkidle")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error searching for app ID: {str(e)}")
    
    async def _extract_bam_monitoring_data(self) -> Dict[str, Any]:
        """Extract monitoring data from BAM portal"""
        try:
            data = {}
            
            # Extract common monitoring elements
            monitoring_selectors = {
                "alerts": ".alert, .alert-panel, [data-testid*='alert']",
                "metrics": ".metric, .metric-panel, [data-testid*='metric']",
                "status": ".status, .status-panel, [data-testid*='status']",
                "health": ".health, .health-panel, [data-testid*='health']"
            }
            
            for key, selector in monitoring_selectors.items():
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        data[key] = []
                        for element in elements:
                            text = await element.text_content()
                            if text and text.strip():
                                data[key].append(text.strip())
                except:
                    continue
            
            return data
            
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error extracting BAM monitoring data: {str(e)}")
            return {}
    
    async def _extract_splunk_search_data(self) -> Dict[str, Any]:
        """Extract search data from Splunk Web UI"""
        try:
            data = {}
            
            # Extract search results
            result_selectors = [
                ".search-result",
                ".result-row",
                "[data-testid*='result']"
            ]
            
            for selector in result_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        data["search_results"] = []
                        for element in elements:
                            text = await element.text_content()
                            if text and text.strip():
                                data["search_results"].append(text.strip())
                        break
                except:
                    continue
            
            return data
            
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error extracting Splunk search data: {str(e)}")
            return {}
    
    async def _extract_appd_application_data(self) -> Dict[str, Any]:
        """Extract application data from AppDynamics Web UI"""
        try:
            data = {}
            
            # Extract common AppDynamics elements
            appd_selectors = {
                "health_rules": ".health-rule, [data-testid*='health-rule']",
                "metrics": ".metric, [data-testid*='metric']",
                "alerts": ".alert, [data-testid*='alert']",
                "performance": ".performance, [data-testid*='performance']"
            }
            
            for key, selector in appd_selectors.items():
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        data[key] = []
                        for element in elements:
                            text = await element.text_content()
                            if text and text.strip():
                                data[key].append(text.strip())
                except:
                    continue
            
            return data
            
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error extracting AppDynamics application data: {str(e)}")
            return {}
    
    async def _extract_generic_monitoring_data(self) -> Dict[str, Any]:
        """Extract generic monitoring data from any portal"""
        try:
            data = {}
            
            # Generic monitoring selectors
            generic_selectors = {
                "alerts": ".alert, .notification, [class*='alert'], [class*='notification']",
                "metrics": ".metric, .stat, [class*='metric'], [class*='stat']",
                "status": ".status, .state, [class*='status'], [class*='state']",
                "health": ".health, .wellness, [class*='health'], [class*='wellness']"
            }
            
            for key, selector in generic_selectors.items():
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        data[key] = []
                        for element in elements:
                            text = await element.text_content()
                            if text and text.strip():
                                data[key].append(text.strip())
                except:
                    continue
            
            return data
            
        except Exception as e:
            print(f"[PlaywrightIntegration] ⚠️ Error extracting generic monitoring data: {str(e)}")
            return {}


# Global instance
playwright_integration = PlaywrightIntegration()

async def access_web_portal(portal_type: str, app_id: str = None, 
                          portal_url: str = None, custom_selectors: List[str] = None) -> Dict[str, Any]:
    """
    Access a web portal and collect evidence
    
    Args:
        portal_type: Type of portal (bam, splunk, appdynamics, custom)
        app_id: Optional application ID
        portal_url: Custom portal URL (for custom portal type)
        custom_selectors: Custom CSS selectors for text extraction
        
    Returns:
        Dictionary containing portal evidence
    """
    if not playwright_integration.is_configured():
        return {
            "status": "error",
            "message": "Playwright not configured or not available",
            "evidence": {}
        }
    
    try:
        # Initialize browser
        browser_initialized = await playwright_integration.initialize_browser()
        if not browser_initialized:
            return {
                "status": "error",
                "message": "Failed to initialize browser",
                "evidence": {}
            }
        
        # Access portal based on type
        if portal_type.lower() == "bam":
            result = await playwright_integration.access_bam_portal(app_id)
        elif portal_type.lower() == "splunk":
            result = await playwright_integration.access_splunk_web_ui(app_id)
        elif portal_type.lower() == "appdynamics":
            result = await playwright_integration.access_appdynamics_web_ui(app_id)
        elif portal_type.lower() == "custom":
            if not portal_url:
                return {
                    "status": "error",
                    "message": "Portal URL required for custom portal type",
                    "evidence": {}
                }
            result = await playwright_integration.access_custom_portal(portal_url, app_id, custom_selectors)
        else:
            return {
                "status": "error",
                "message": f"Unsupported portal type: {portal_type}",
                "evidence": {}
            }
        
        # Close browser
        await playwright_integration.close_browser()
        
        return result
        
    except Exception as e:
        # Ensure browser is closed on error
        await playwright_integration.close_browser()
        return {
            "status": "error",
            "message": f"Error accessing web portal: {str(e)}",
            "evidence": {}
        }

def collect_web_portal_evidence(portal_type: str, app_id: str = None, 
                              portal_url: str = None, custom_selectors: List[str] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for web portal evidence collection
    
    Args:
        portal_type: Type of portal (bam, splunk, appdynamics, custom)
        app_id: Optional application ID
        portal_url: Custom portal URL (for custom portal type)
        custom_selectors: Custom CSS selectors for text extraction
        
    Returns:
        Dictionary containing portal evidence
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            access_web_portal(portal_type, app_id, portal_url, custom_selectors)
        )
        loop.close()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error in synchronous wrapper: {str(e)}",
            "evidence": {}
        } 