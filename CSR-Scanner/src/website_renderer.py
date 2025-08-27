import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import pandas as pd
from tqdm import tqdm
import time
import concurrent.futures
from typing import Dict, List, Tuple, Optional
import random
import json
import string
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib3
import warnings
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse, urljoin
from datetime import datetime

from models import ProcessingResult, RenderingType, ProcessingStatus, ErrorCategory, RetryConfig, DetectionMetrics, DetectorConfig, TimeoutConfig, BrowserConfig
from error_handler import ErrorHandler
from retry_manager import RetryManager
from performance_optimizer import PerformanceOptimizer
import re
from bs4 import BeautifulSoup

# Suppress only the InsecureRequestWarning from urllib3
warnings.filterwarnings('ignore', category=InsecureRequestWarning)
# Suppress other SSL related warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Disable SSL warnings for urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HumanLikeActions:
    """Class to simulate human-like interactions"""
    
    @staticmethod
    def random_delay(min_seconds=0.5, max_seconds=2.0):
        """Random delay between actions to appear more human-like"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    @staticmethod
    def human_type(element, text, delay_range=(0.05, 0.2)):
        """Type text with human-like delays and potential typos"""
        for char in text:
            element.send_keys(char)
            # Random delay between key presses
            time.sleep(random.uniform(*delay_range))
            
    @staticmethod
    def random_scroll(driver):
        """Random scroll to simulate human behavior"""
        scroll_pause_time = random.uniform(0.5, 2)
        scroll_amount = random.randint(300, 800)
        
        # Scroll down
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(scroll_pause_time)
        
        # Sometimes scroll back up a bit
        if random.random() > 0.7:
            driver.execute_script(f"window.scrollBy(0, -{scroll_amount//3});")
            time.sleep(scroll_pause_time / 2)
            
    @staticmethod
    def move_mouse_to_element(driver, element):
        """Move mouse to element with human-like movement"""
        action = ActionChains(driver)
        action.move_to_element(element)
        action.perform()
        HumanLikeActions.random_delay(0.2, 0.5)

class WebsiteRendererDetector:
    def __init__(self, max_workers: int = 3, headless: bool = True, timeout: int = 30, max_retries: int = 2, config: Optional[DetectorConfig] = None):
        # Use provided config or create default
        if config is None:
            from config import ConfigLoader
            self.config = DetectorConfig(
                max_workers=max_workers,
                timeouts=TimeoutConfig(
                    http_request=timeout,
                    browser_load=timeout + 5,
                    javascript_wait=5
                ),
                browser=BrowserConfig(
                    headless=headless,
                    disable_images=True,
                    disable_css=True,
                    user_agent_rotation=True
                )
            )
        else:
            self.config = config
        
        # Legacy compatibility
        self.max_workers = self.config.max_workers
        self.headless = self.config.browser.headless
        self.timeout = self.config.timeouts.http_request
        self.max_retries = max_retries
        
        self.ua = UserAgent()
        self.cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')
        os.makedirs(self.cookies_dir, exist_ok=True)
        self.driver = None  # Legacy - will be replaced by performance optimizer
        self.error_handler = ErrorHandler()  # Initialize error handler
        
        # Initialize performance optimizer
        self.performance_optimizer = PerformanceOptimizer(self.config)
        
        # Initialize retry manager with configuration
        retry_config = RetryConfig(
            max_attempts=max_retries,
            backoff_base=1.0,
            backoff_multiplier=2.0,
            non_retryable_errors=[ErrorCategory.DNS_ERROR, ErrorCategory.SSL_ERROR]
        )
        self.retry_manager = RetryManager(retry_config, self.error_handler)
        
        # Performance metrics tracking
        self.performance_metrics = {
            'total_processing_time': 0.0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_processing_time': 0.0,
            'requests_per_second': 0.0
        }
        
    def get_random_user_agent(self) -> str:
        """Get a random user agent that mimics a real browser"""
        return self.ua.random
    
    def get_chrome_options(self, url: str):
        """Configure Chrome options to appear more like a real browser"""
        options = uc.ChromeOptions()
        
        # Basic options to make it harder to detect as a bot
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        
        # Set a common viewport size
        width = random.randint(1280, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # Headless mode if specified
        if self.headless:
            options.add_argument('--headless=new')
        
        # Disable extensions and automation flags
        options.add_argument('--disable-extensions')
        # Removed problematic 'useAutomationExtension' option for undetected-chromedriver compatibility
        # Removed problematic 'excludeSwitches' option for undetected-chromedriver compatibility
        
        # Set a random user agent
        user_agent = self.get_random_user_agent()
        options.add_argument(f'user-agent={user_agent}')
        
        # Set accept language
        options.add_argument('--accept-lang=en-US,en;q=0.9')
        
        # Performance optimizations
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-setuid-sandbox')
        
        # Disable images and JavaScript for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.javascript": 1,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.plugins": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.notifications": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    def get_webdriver(self, url: str):
        """Get an optimized WebDriver instance using PerformanceOptimizer"""
        try:
            # Use performance optimizer to get browser instance
            driver = self.performance_optimizer.get_optimized_browser(url)
            
            # Load cookies if they exist
            self.load_cookies(driver, url)
            
            # Update legacy driver reference for backward compatibility
            self.driver = driver
            
            return driver
            
        except Exception as e:
            error_category = self.error_handler.categorize_error(e, url)
            self.error_handler.log_error(
                url=url,
                error_category=error_category,
                error_message=f"Optimized WebDriver initialization failed: {str(e)}"
            )
            raise  # Re-raise to be handled by calling method
        
    def close_driver(self):
        """Close the WebDriver if it exists - now handled by PerformanceOptimizer"""
        # Performance optimizer manages browser lifecycle
        # This method is kept for backward compatibility
        if self.driver is not None:
            try:
                # FIXED: Actually close the browser to prevent resource leaks
                self.driver.quit()
            except:
                pass
            self.driver = None
            
    def save_cookies(self, driver, url: str):
        """Save cookies for the current domain"""
        try:
            domain = url.split('//')[-1].split('/')[0]
            cookie_file = os.path.join(self.cookies_dir, f"{domain}_cookies.json")
            with open(cookie_file, 'w') as f:
                json.dump(driver.get_cookies(), f)
        except Exception as e:
            self.error_handler.log_error(
                url=url,
                error_category=ErrorCategory.PARSE_ERROR,
                error_message=f"Cookie save failed: {str(e)}"
            )
    
    def load_cookies(self, driver, url: str):
        """Load cookies for the current domain if they exist"""
        try:
            domain = url.split('//')[-1].split('/')[0]
            cookie_file = os.path.join(self.cookies_dir, f"{domain}_cookies.json")
            if os.path.exists(cookie_file):
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        try:
                            driver.add_cookie(cookie)
                        except Exception as e:
                            # Individual cookie failures are not critical
                            continue
        except Exception as e:
            self.error_handler.log_error(
                url=url,
                error_category=ErrorCategory.PARSE_ERROR,
                error_message=f"Cookie load failed: {str(e)}"
            )

    def _compare_content(self, http_content: str, browser_content: str) -> DetectionMetrics:
        """
        Analyze HTTP vs browser content differences to determine rendering type
        
        Args:
            http_content: HTML content from HTTP request
            browser_content: HTML content after browser rendering
            
        Returns:
            DetectionMetrics with analysis results
        """
        metrics = DetectionMetrics(
            content_size_difference=len(browser_content) - len(http_content)
        )
        
        try:
            # Parse HTML content for deeper analysis
            http_soup = BeautifulSoup(http_content, 'html.parser')
            browser_soup = BeautifulSoup(browser_content, 'html.parser')
            
            # Count meaningful content elements
            http_elements = len(http_soup.find_all(['div', 'p', 'span', 'article', 'section']))
            browser_elements = len(browser_soup.find_all(['div', 'p', 'span', 'article', 'section']))
            
            # Significant increase in elements suggests dynamic rendering
            element_increase = browser_elements - http_elements
            if element_increase > 10:
                metrics.dynamic_content_detected = True
            
            # Check for script tags and their content
            http_scripts = http_soup.find_all('script')
            browser_scripts = browser_soup.find_all('script')
            
            # More scripts in browser version suggests dynamic loading
            if len(browser_scripts) > len(http_scripts) + 2:
                metrics.dynamic_content_detected = True
            
            # Look for data attributes that suggest framework usage
            framework_patterns = [
                r'data-react',
                r'data-vue',
                r'ng-',
                r'data-next',
                r'data-nuxt'
            ]
            
            for pattern in framework_patterns:
                if re.search(pattern, browser_content, re.IGNORECASE):
                    metrics.framework_indicators.append(pattern)
            
        except Exception as e:
            # If parsing fails, continue with basic size comparison
            pass
        
        return metrics
    
    def _detect_frameworks(self, html: str, driver) -> List[str]:
        """
        Enhanced framework detection using both HTML analysis and JavaScript execution
        
        Args:
            html: HTML content to analyze
            driver: WebDriver instance for JavaScript checks
            
        Returns:
            List of detected frameworks
        """
        frameworks = []
        
        try:
            # HTML-based detection patterns
            html_lower = html.lower()
            
            # React detection
            react_patterns = [
                r'data-reactroot',
                r'data-reactid',
                r'__react',
                r'react\.js',
                r'react\.min\.js',
                r'reactdom'
            ]
            
            if any(re.search(pattern, html_lower) for pattern in react_patterns):
                frameworks.append('React')
            
            # Vue detection
            vue_patterns = [
                r'data-v-',
                r'vue\.js',
                r'vue\.min\.js',
                r'__vue__'
            ]
            
            if any(re.search(pattern, html_lower) for pattern in vue_patterns):
                frameworks.append('Vue')
            
            # Angular detection
            angular_patterns = [
                r'ng-app',
                r'ng-controller',
                r'angular\.js',
                r'angular\.min\.js',
                r'data-ng-'
            ]
            
            if any(re.search(pattern, html_lower) for pattern in angular_patterns):
                frameworks.append('Angular')
            
            # Next.js detection
            nextjs_patterns = [
                r'_next/',
                r'__next',
                r'data-next-hide-fouc',
                r'next\.js'
            ]
            
            if any(re.search(pattern, html_lower) for pattern in nextjs_patterns):
                frameworks.append('Next.js')
            
            # Nuxt.js detection
            nuxtjs_patterns = [
                r'__nuxt',
                r'_nuxt/',
                r'nuxt\.js'
            ]
            
            if any(re.search(pattern, html_lower) for pattern in nuxtjs_patterns):
                frameworks.append('Nuxt.js')
            
        except Exception as e:
            self.error_handler.log_error(
                url="framework_detection_html",
                error_category=ErrorCategory.PARSE_ERROR,
                error_message=f"HTML framework detection failed: {str(e)}"
            )
        
        # JavaScript-based detection (enhanced version of existing method)
        try:
            # Check for React
            has_react = driver.execute_script(
                """
                return !!(window.React || 
                         window.__REACT_DEVTOOLS_GLOBAL_HOOK__ ||
                         document.querySelector('[data-reactroot], [data-reactid]') ||
                         document.querySelector('script[src*="react"]'));
                """
            )
            if has_react and 'React' not in frameworks:
                frameworks.append('React')
        except Exception as e:
            self.error_handler.log_error(
                url="framework_detection_js",
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"React JS detection failed: {str(e)}"
            )
        
        try:
            # Check for Angular
            has_angular = driver.execute_script(
                """
                return !!(window.angular || 
                         window.ng ||
                         document.querySelector('[ng-app], [data-ng-app]') ||
                         document.querySelector('script[src*="angular"]'));
                """
            )
            if has_angular and 'Angular' not in frameworks:
                frameworks.append('Angular')
        except Exception as e:
            self.error_handler.log_error(
                url="framework_detection_js",
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"Angular JS detection failed: {str(e)}"
            )
        
        try:
            # Check for Vue
            has_vue = driver.execute_script(
                """
                return !!(window.Vue || 
                         window.__VUE__ ||
                         document.querySelector('[data-v-app], [v-app]') ||
                         document.querySelector('script[src*="vue"]'));
                """
            )
            if has_vue and 'Vue' not in frameworks:
                frameworks.append('Vue')
        except Exception as e:
            self.error_handler.log_error(
                url="framework_detection_js",
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"Vue JS detection failed: {str(e)}"
            )
        
        try:
            # Check for Next.js
            has_nextjs = driver.execute_script(
                """
                return !!(window.__NEXT_DATA__ ||
                         document.querySelector('[data-next-hide-fouc]') ||
                         document.querySelector('script[src*="_next/"]') ||
                         document.querySelector('#__next'));
                """
            )
            if has_nextjs and 'Next.js' not in frameworks:
                frameworks.append('Next.js')
        except Exception as e:
            self.error_handler.log_error(
                url="framework_detection_js",
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"Next.js JS detection failed: {str(e)}"
            )
        
        try:
            # Check for Nuxt.js
            has_nuxtjs = driver.execute_script(
                """
                return !!(window.__NUXT__ ||
                         document.querySelector('#__nuxt') ||
                         document.querySelector('script[src*="_nuxt/"]'));
                """
            )
            if has_nuxtjs and 'Nuxt.js' not in frameworks:
                frameworks.append('Nuxt.js')
        except Exception as e:
            self.error_handler.log_error(
                url="framework_detection_js",
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"Nuxt.js JS detection failed: {str(e)}"
            )
        
        return frameworks
    
    def _analyze_dynamic_content(self, driver) -> Tuple[bool, int]:
        """
        Monitor DOM changes over time to detect dynamic content rendering
        
        Args:
            driver: WebDriver instance
            
        Returns:
            Tuple of (dynamic_content_detected, mutation_count)
        """
        try:
            # Set up mutation observer to track DOM changes
            mutation_script = """
            window.mutationCount = 0;
            window.mutationObserver = new MutationObserver(function(mutations) {
                window.mutationCount += mutations.length;
            });
            
            window.mutationObserver.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeOldValue: true,
                characterData: true,
                characterDataOldValue: true
            });
            
            return true;
            """
            
            driver.execute_script(mutation_script)
            
            # Get initial content snapshot
            initial_html = driver.execute_script("return document.documentElement.outerHTML")
            initial_text_content = driver.execute_script("return document.body.textContent || document.body.innerText || ''")
            
            # Wait for potential dynamic content to load
            time.sleep(1)  # AGGRESSIVE FIX: Reduced to 1 second max
            
            # Get final content snapshot
            final_html = driver.execute_script("return document.documentElement.outerHTML")
            final_text_content = driver.execute_script("return document.body.textContent || document.body.innerText || ''")
            
            # Get mutation count
            mutation_count = driver.execute_script("return window.mutationCount || 0")
            
            # Stop observing
            driver.execute_script("if (window.mutationObserver) window.mutationObserver.disconnect();")
            
            # Check for significant changes
            html_changed = len(final_html) != len(initial_html)
            text_changed = len(final_text_content) != len(initial_text_content)
            significant_mutations = mutation_count > 5
            
            # Content size difference analysis
            size_difference = abs(len(final_text_content) - len(initial_text_content))
            significant_size_change = size_difference > 100
            
            dynamic_detected = (html_changed or text_changed or 
                              significant_mutations or significant_size_change)
            
            return dynamic_detected, mutation_count
            
        except Exception as e:
            self.error_handler.log_error(
                url="dynamic_content_analysis",
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"Dynamic content analysis failed: {str(e)}"
            )
            return False, 0
    
    def _calculate_weighted_score(self, metrics: DetectionMetrics, frameworks: List[str], 
                                dynamic_detected: bool, mutation_count: int) -> float:
        """
        Calculate weighted score for CSR classification
        
        Args:
            metrics: DetectionMetrics from content comparison
            frameworks: List of detected frameworks
            dynamic_detected: Whether dynamic content was detected
            mutation_count: Number of DOM mutations observed
            
        Returns:
            CSR likelihood score (0.0 to 1.0)
        """
        score = 0.0
        
        # Framework detection (strong indicator)
        if frameworks:
            score += 0.4
            # Modern frameworks get higher weight
            modern_frameworks = ['React', 'Vue', 'Next.js', 'Nuxt.js']
            if any(fw in modern_frameworks for fw in frameworks):
                score += 0.1
        
        # Content size difference
        size_diff = metrics.content_size_difference
        if size_diff > 2000:
            score += 0.3
        elif size_diff > 1000:
            score += 0.2
        elif size_diff > 500:
            score += 0.1
        
        # Dynamic content detection
        if dynamic_detected:
            score += 0.2
        
        # DOM mutations
        if mutation_count > 20:
            score += 0.2
        elif mutation_count > 10:
            score += 0.1
        elif mutation_count > 5:
            score += 0.05
        
        # Framework indicators in HTML
        if metrics.framework_indicators:
            score += 0.1
        
        return min(score, 1.0)

    def _detect_js_frameworks(self, driver) -> List[str]:
        """
        Legacy method - kept for backward compatibility
        Redirects to enhanced _detect_frameworks method
        """
        try:
            # Get current page HTML for analysis
            html = driver.page_source
            return self._detect_frameworks(html, driver)
        except Exception as e:
            self.error_handler.log_error(
                url="legacy_framework_detection",
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"Legacy framework detection failed: {str(e)}"
            )
            return []

    def _check_dynamic_content(self, driver) -> bool:
        """
        Legacy method - kept for backward compatibility
        Redirects to enhanced _analyze_dynamic_content method
        """
        try:
            dynamic_detected, _ = self._analyze_dynamic_content(driver)
            return dynamic_detected
        except Exception as e:
            self.error_handler.log_error(
                url="legacy_dynamic_content_check",
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"Legacy dynamic content check failed: {str(e)}"
            )
            return False
            
    def detect_rendering_type(self, url: str, max_retries: int = None) -> ProcessingResult:
        """
        Detect the rendering type of a website: Client-side, Server-side, or Not Accessible.
        
        Args:
            url: The URL to analyze
            max_retries: Maximum number of retries (uses instance default if None)
            
        Returns:
            ProcessingResult with detection results
        """
        start_time = time.time()
        original_url = url
        
        # Input validation
        if not url or not isinstance(url, str):
            return ProcessingResult(
                url=original_url,
                final_url=original_url,
                rendering_type=RenderingType.NOT_ACCESSIBLE.value,
                status=ProcessingStatus.FAILED.value,
                processing_time_sec=time.time() - start_time,
                timestamp=datetime.now().isoformat(),
                frameworks=[],
                error_category=ErrorCategory.PARSE_ERROR.value,
                error_message="Invalid URL format",
                retry_count=0,
                http_status_code=None
            )
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Update retry manager configuration if max_retries is specified
        if max_retries is not None and max_retries != self.retry_manager.config.max_attempts:
            retry_config = RetryConfig(
                max_attempts=max_retries,
                backoff_base=1.0,
                backoff_multiplier=2.0,
                non_retryable_errors=[ErrorCategory.DNS_ERROR, ErrorCategory.SSL_ERROR]
            )
            self.retry_manager = RetryManager(retry_config, self.error_handler)
            # Clear any existing history for this URL
            if url in self.retry_manager.retry_histories:
                del self.retry_manager.retry_histories[url]
        
        try:
            # Use RetryManager to execute the detection with retry logic
            result = self.retry_manager.execute_with_retry(self._detect_rendering_type_internal, url, start_time)
            
            # Get retry count from retry history (attempts - 1, since first attempt is not a retry)
            retry_history = self.retry_manager.get_retry_history(url)
            retry_count = max(0, retry_history.total_attempts - 1) if retry_history else 0
            
            # Update retry count in result
            result.retry_count = retry_count
            
            # Update performance metrics
            self._update_performance_metrics(result, True)
            
            # Trigger resource monitoring and cleanup if needed
            self.performance_optimizer.restart_browser_if_needed()
            
            return result
            
        except Exception as e:
            # Final failure after all retries exhausted
            error_category = self.error_handler.categorize_error(e, url)
            error_details = self.error_handler.get_error_details(e, url)
            formatted_error = self.error_handler.format_error_for_output(
                error_category, str(e), error_details
            )
            
            # Get retry count from retry history (attempts - 1, since first attempt is not a retry)
            retry_history = self.retry_manager.get_retry_history(url)
            retry_count = max(0, retry_history.total_attempts - 1) if retry_history else 0
            
            result = ProcessingResult(
                url=original_url,
                final_url=url,
                rendering_type=RenderingType.NOT_ACCESSIBLE.value,
                status=ProcessingStatus.FAILED.value,
                processing_time_sec=time.time() - start_time,
                timestamp=datetime.now().isoformat(),
                frameworks=[],
                error_category=error_category.value,
                error_message=formatted_error,
                retry_count=retry_count,
                http_status_code=error_details.get('http_status_code')
            )
            
            # Update performance metrics for failed request
            self._update_performance_metrics(result, False)
            
            return result
    
    def _detect_rendering_type_internal(self, url: str, start_time: float) -> ProcessingResult:
        """
        Internal method for detecting rendering type (called by RetryManager)
        
        Args:
            url: The URL to analyze
            start_time: Start time for processing time calculation
            
        Returns:
            ProcessingResult with detection results
        """
        original_url = url
        final_url = url
        frameworks = []
        
        # HTTP accessibility check with intelligent timeout management
        retry_history = self.retry_manager.get_retry_history(url)
        current_attempt = retry_history.total_attempts if retry_history else 1
        
        # Get intelligent timeouts from performance optimizer
        intelligent_timeouts = self.performance_optimizer.get_intelligent_timeout(url, current_attempt)
        http_timeout = intelligent_timeouts['http_request']
        browser_timeout = intelligent_timeouts['browser_load']
        js_timeout = intelligent_timeouts['javascript_wait']
        
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1'
        }
        
        resp = requests.get(url, timeout=http_timeout, headers=headers, 
                          allow_redirects=True, verify=False)
        
        # Update final URL after redirects
        final_url = resp.url
        
        # Check for HTTP errors
        if resp.status_code >= 400:
            # Create HTTP error to be handled by retry manager
            http_error = requests.HTTPError(f"HTTP {resp.status_code}: {resp.reason}")
            http_error.response = resp
            raise http_error
        
        html_requests = resp.text
        
        # Browser rendering check with intelligent timeout
        driver = self.get_webdriver(url)
        # AGGRESSIVE FIX: Set very short timeouts to prevent hangs
        driver.set_page_load_timeout(min(browser_timeout, 15))  # Max 15 seconds
        driver.set_script_timeout(min(js_timeout, 5))  # Max 5 seconds
        driver.get(final_url)
        time.sleep(min(js_timeout, 1))  # FIXED: Reduced to 1 second max
        
        html_selenium = driver.page_source
        
        # Detect JavaScript frameworks using enhanced detection (handle errors gracefully)
        try:
            frameworks = self._detect_frameworks(html_selenium, driver)
        except Exception as e:
            self.error_handler.log_error(
                url=url,
                error_category=ErrorCategory.BROWSER_ERROR,
                error_message=f"Enhanced framework detection failed: {str(e)}"
            )
            frameworks = []  # Continue with empty frameworks list
        
        # Determine rendering type based on content comparison and frameworks
        rendering_type = self._classify_rendering_type(
            html_requests, html_selenium, frameworks, driver
        )
        
        # Success - return result
        return ProcessingResult(
            url=original_url,
            final_url=final_url,
            rendering_type=rendering_type,
            status=ProcessingStatus.SUCCESS.value,
            processing_time_sec=time.time() - start_time,
            timestamp=datetime.now().isoformat(),
            frameworks=frameworks,
            error_category=None,
            error_message=None,
            retry_count=0,  # Will be updated by calling method
            http_status_code=resp.status_code
        )
    
    def _classify_rendering_type(self, html_requests: str, html_selenium: str, 
                               frameworks: List[str], driver) -> str:
        """
        Enhanced classification using weighted scoring system and comprehensive analysis
        
        Args:
            html_requests: HTML content from HTTP request
            html_selenium: HTML content after browser rendering
            frameworks: List of detected JavaScript frameworks
            driver: WebDriver instance for additional checks
            
        Returns:
            Rendering type classification
        """
        try:
            # Perform comprehensive content comparison
            metrics = self._compare_content(html_requests, html_selenium)
            
            # Analyze dynamic content changes
            dynamic_detected, mutation_count = self._analyze_dynamic_content(driver)
            
            # Update metrics with dynamic analysis results
            metrics.dynamic_content_detected = dynamic_detected
            metrics.dom_mutation_count = mutation_count
            
            # Calculate weighted CSR score
            csr_score = self._calculate_weighted_score(
                metrics, frameworks, dynamic_detected, mutation_count
            )
            
            # Classification thresholds
            CSR_THRESHOLD = 0.6
            SSR_THRESHOLD = 0.3
            
            if csr_score >= CSR_THRESHOLD:
                return RenderingType.CLIENT_SIDE_RENDERED.value
            elif csr_score <= SSR_THRESHOLD:
                return RenderingType.SERVER_SIDE_RENDERED.value
            else:
                # In the middle range, use additional heuristics
                
                # Strong framework presence suggests CSR
                modern_frameworks = ['React', 'Vue', 'Next.js', 'Nuxt.js']
                if any(fw in modern_frameworks for fw in frameworks):
                    return RenderingType.CLIENT_SIDE_RENDERED.value
                
                # Significant content size increase suggests CSR
                if metrics.content_size_difference > 1000:
                    return RenderingType.CLIENT_SIDE_RENDERED.value
                
                # High mutation count suggests CSR
                if mutation_count > 15:
                    return RenderingType.CLIENT_SIDE_RENDERED.value
                
                # Default to SSR for ambiguous cases
                return RenderingType.SERVER_SIDE_RENDERED.value
            
        except Exception as e:
            # If classification fails, log error and default to server-side
            self.error_handler.log_error(
                url="enhanced_classification",
                error_category=ErrorCategory.PARSE_ERROR,
                error_message=f"Enhanced classification error: {str(e)}"
            )
            return RenderingType.SERVER_SIDE_RENDERED.value

    def process_websites(self, input_file: str, output_csv: str, chunk_size: int = 1000):
        """Process a list of websites from CSV file with progress tracking and performance optimization.
        
        Args:
            input_file: Path to input CSV file
            output_csv: Path to output CSV file
            chunk_size: Number of rows to process at a time
        """
        try:
            print("\n" + "="*80)
            print(f"Starting website processing for: {input_file}")
            print("="*80)
            
            # Optimize worker count based on system resources
            optimized_workers = self.optimize_worker_count()
            if optimized_workers != self.max_workers:
                print(f"Optimizing worker count: {self.max_workers} -> {optimized_workers}")
                self.max_workers = optimized_workers
                self.config.max_workers = optimized_workers
            
            # Check if file exists
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input file not found: {input_file}")
            
            print(f"\nAnalyzing input file: {input_file}")
            
            # Count total rows in the CSV file
            print("Counting total rows...")
            with open(input_file, 'r', encoding='utf-8') as f:
                total_rows = sum(1 for _ in f) - 1  # Subtract 1 for header
            
            print(f"Total rows to process: {total_rows:,}")
            print(f"Processing in chunks of {chunk_size} rows...")
            
            # Read the CSV file in chunks
            csv_reader = pd.read_csv(
                input_file,
                chunksize=chunk_size,
                encoding='utf-8',
                on_bad_lines='skip',
                dtype=str  # Read all columns as strings to avoid type inference
            )
            
            # Initialize tracking variables
            processed_count = 0
            chunk_results = []
            chunk_idx = 0
            start_time = time.time()
            
            # Function to print progress
            def print_progress():
                elapsed = time.time() - start_time
                elapsed_min, elapsed_sec = divmod(int(elapsed), 60)
                elapsed_str = f"{elapsed_min:02d}:{elapsed_sec:02d}"
                
                if processed_count > 0 and elapsed > 0:
                    urls_per_sec = processed_count / elapsed
                    remaining = (total_rows - processed_count) / urls_per_sec if urls_per_sec > 0 else 0
                    remaining_min, remaining_sec = divmod(int(remaining), 60)
                    remaining_str = f"{remaining_min:02d}:{remaining_sec:02d}"
                    speed = f"{urls_per_sec:.1f} URLs/sec"
                else:
                    remaining_str = "--:--"
                    speed = "0.0 URLs/sec"
                
                progress = f"\r[Elapsed: {elapsed_str} | Remaining: {remaining_str} | Speed: {speed}] "
                progress += f"Processed: {processed_count:,}/{total_rows:,} ({processed_count/max(1, total_rows)*100:.1f}%) | Current: {current_url[:60]}{'...' if len(current_url) > 60 else ''}"
                print(progress, end='', flush=True)
            
            # Initialize results file with header
            pd.DataFrame(columns=['url', 'rendering_type']).to_csv(output_csv, index=False)
            processed_count = 0
            current_url = "Starting..."
            
            # Process each chunk
            for chunk_idx, chunk in enumerate(csv_reader, 1):
                print(f"\nProcessing chunk {chunk_idx}...")
                
                # Get URLs from the first column
                url_column = chunk.columns[0]  # Get first column name
                chunk_urls = chunk[url_column].dropna().tolist()
                chunk_count = len(chunk_urls)
                print(f"Found {chunk_count} URLs in this chunk")
                
                # Process this chunk's URLs with ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_url = {}
                    
                    # Submit initial batch of URLs
                    for url in chunk_urls[:self.max_workers * 2]:
                        future = executor.submit(self.detect_rendering_type, url)
                        future_to_url[future] = url
                    
                    # Remove submitted URLs from the queue
                    chunk_urls = chunk_urls[self.max_workers * 2:]
                    
                    # Process as they complete
                    while future_to_url:
                        try:
                            # Wait for the next future to complete
                            done, _ = concurrent.futures.wait(
                                future_to_url.keys(),
                                return_when=concurrent.futures.FIRST_COMPLETED
                            )
                            
                            for future in done:
                                url = future_to_url[future]
                                current_url = url
                                processed_count += 1
                                
                                try:
                                    result = future.result()
                                    chunk_results.append({'url': result.url, 'rendering_type': result.rendering_type})
                                    
                                    # Save progress every 10 URLs
                                    if len(chunk_results) >= 10:
                                        pd.DataFrame(chunk_results).to_csv(
                                            output_csv, 
                                            mode='a', 
                                            header=not os.path.exists(output_csv) or os.path.getsize(output_csv) == 0,
                                            index=False
                                        )
                                        chunk_results = []
                                        
                                except Exception as e:
                                    print(f"\nError processing {url}: {str(e)}")
                                    chunk_results.append({'url': url, 'rendering_type': f'Error: {str(e)}'})
                                
                                # Print progress
                                print_progress()
                                
                                # Submit next URL if any remaining in chunk
                                if chunk_urls:
                                    next_url = chunk_urls.pop(0)
                                    future = executor.submit(self.detect_rendering_type, next_url)
                                    future_to_url[future] = next_url
                                
                                # Remove completed future
                                del future_to_url[future]
                                
                        except KeyboardInterrupt:
                            print("\n\nProcess interrupted by user. Finishing current batch...")
                            # Cancel all pending futures
                            for future in future_to_url:
                                future.cancel()
                            break
                
                # Function to print progress within chunk
                def print_chunk_progress():
                    elapsed = time.time() - start_time
                    urls_per_min = (processed_count / (elapsed / 60)) if elapsed > 0 else 0
                    remaining = ((total_rows - processed_count) / urls_per_min) if urls_per_min > 0 else 0
                    print(f"\rChunk {chunk_idx} | "
                          f"Processed: {processed_count:,}/{total_rows:,} | "
                          f"Progress: {processed_count/total_rows*100:.1f}% | "
                          f"Speed: {urls_per_min:.1f} URLs/min | "
                          f"Elapsed: {elapsed/60:.1f} min | "
                          f"Remaining: ~{remaining:.1f} min | "
                          f"Current: {current_url[:50]}{'...' if len(current_url) > 50 else ''}",
                          end='', flush=True)
            
                # Process this chunk's URLs with ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_url = {}
                    current_url = ""
                    
                    # Convert chunk to list of URLs
                    chunk_urls = chunk['url'].dropna().tolist()
                    chunk_count = len(chunk_urls)
                    print(f"Processing {chunk_count} URLs in chunk {chunk_idx}...")
                    
                    # Submit initial batch of URLs
                    for url in chunk_urls[:self.max_workers * 2]:
                        future = executor.submit(self.detect_rendering_type, url)
                        future_to_url[future] = url
                    
                    # Process as they complete
                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        current_url = url
                        processed_count += 1
                        chunk_processed += 1
                        
                        try:
                            result = future.result()
                            chunk_results.append({'url': result.url, 'rendering_type': result.rendering_type})
                            
                            # Save progress every 10 URLs
                            if processed_count % 10 == 0:
                                pd.DataFrame(chunk_results).to_csv(
                                    output_csv, 
                                    mode='a', 
                                    header=not os.path.exists(output_csv) or os.path.getsize(output_csv) == 0,
                                    index=False
                                )
                                chunk_results = []
                                
                        except Exception as e:
                            print(f"\nError processing {url}: {str(e)}")
                            chunk_results.append({'url': url, 'rendering_type': f'Error: {str(e)}'})
                        
                        # Print progress
                        print_chunk_progress()
                        
                        # Submit next URL if any remaining in chunk
                        if chunk_urls:
                            next_url = chunk_urls.pop(0)
                            future = executor.submit(self.detect_rendering_type, next_url)
                            future_to_url[future] = next_url
                        
                        # Remove completed future
                        del future_to_url[future]
                
                # Save any remaining results from this chunk
                if chunk_results:
                    pd.DataFrame(chunk_results).to_csv(
                        output_csv, 
                        mode='a', 
                        header=not os.path.exists(output_csv) or os.path.getsize(output_csv) == 0,
                        index=False
                    )
                
                print(f"\nCompleted chunk {chunk_idx} | Processed {chunk_processed} URLs")
            
            # Final summary
            total_time = (time.time() - start_time) / 60
            print("\n" + "="*80)
            print(f"Processing complete! Processed {processed_count:,} URLs in {total_time:.1f} minutes")
            print(f"Results saved to: {os.path.abspath(output_csv)}")
            
            # Show summary of results if any
            try:
                if os.path.exists(output_csv) and os.path.getsize(output_csv) > 0:
                    results_df = pd.read_csv(output_csv)
                    print("\n=== Summary ===")
                    print(f"Total URLs processed: {len(results_df):,}")
                    print("\nRendering type distribution:")
                    print(results_df['rendering_type'].value_counts().to_string())
            except Exception as e:
                print(f"\nCould not generate summary: {str(e)}")
            
            # Show performance report
            try:
                print("\n" + self.get_performance_report())
            except Exception as e:
                print(f"\nCould not generate performance report: {str(e)}")
            
        except Exception as e:
            print(f"\nError in process_websites: {str(e)}")
            raise
        finally:
            # Clean up performance resources
            self.cleanup_performance_resources()

    def _update_performance_metrics(self, result: ProcessingResult, success: bool) -> None:
        """
        Update performance metrics based on processing result
        
        Args:
            result: ProcessingResult from detection
            success: Whether the processing was successful
        """
        self.performance_metrics['total_requests'] += 1
        self.performance_metrics['total_processing_time'] += result.processing_time_sec
        
        if success:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1
        
        # Update derived metrics
        if self.performance_metrics['total_requests'] > 0:
            self.performance_metrics['average_processing_time'] = (
                self.performance_metrics['total_processing_time'] / 
                self.performance_metrics['total_requests']
            )
        
        # Calculate requests per second (approximate)
        if self.performance_metrics['total_processing_time'] > 0:
            self.performance_metrics['requests_per_second'] = (
                self.performance_metrics['total_requests'] / 
                self.performance_metrics['total_processing_time']
            )
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get current performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        # Get optimizer metrics
        optimizer_metrics = self.performance_optimizer.monitor_resources()
        
        # Combine with detector metrics (detector metrics take precedence)
        combined_metrics = {
            **optimizer_metrics,
            **self.performance_metrics
        }
        
        return combined_metrics
    
    def get_performance_report(self) -> str:
        """
        Generate a comprehensive performance report
        
        Returns:
            Formatted performance report string
        """
        metrics = self.get_performance_metrics()
        optimizer_report = self.performance_optimizer.get_performance_report()
        
        report = []
        report.append("=" * 80)
        report.append("WEBSITE RENDERER DETECTOR PERFORMANCE REPORT")
        report.append("=" * 80)
        
        # Detection metrics
        report.append("DETECTION PERFORMANCE:")
        report.append(f"  Total Requests:        {metrics.get('total_requests', 0)}")
        report.append(f"  Successful Requests:   {metrics.get('successful_requests', 0)}")
        report.append(f"  Failed Requests:       {metrics.get('failed_requests', 0)}")
        
        if metrics.get('total_requests', 0) > 0:
            success_rate = (metrics.get('successful_requests', 0) / metrics.get('total_requests', 1)) * 100
            report.append(f"  Success Rate:          {success_rate:.1f}%")
        
        report.append(f"  Average Processing:    {metrics.get('average_processing_time', 0):.2f}s")
        report.append(f"  Requests Per Second:   {metrics.get('requests_per_second', 0):.2f}")
        report.append(f"  Total Processing Time: {metrics.get('total_processing_time', 0):.1f}s")
        report.append("")
        
        # Add optimizer report
        report.append(optimizer_report)
        
        return "\n".join(report)
    
    def optimize_worker_count(self) -> int:
        """
        Get optimized worker count based on current performance
        
        Returns:
            Recommended worker count
        """
        return self.performance_optimizer.get_worker_count()
    
    def cleanup_performance_resources(self) -> None:
        """
        Clean up all performance-related resources
        """
        self.performance_optimizer.cleanup_resources()
        
        # Reset performance metrics
        self.performance_metrics = {
            'total_processing_time': 0.0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_processing_time': 0.0,
            'requests_per_second': 0.0
        }

if __name__ == "__main__":
    # Example usage
    detector = WebsiteRendererDetector()
    detector.process_websites('websites.csv', 'rendering_results.csv')
