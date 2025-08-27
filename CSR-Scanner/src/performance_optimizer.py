"""
Performance optimization and resource management for the Website Rendering Detector
"""

import os
import time
import psutil
import threading
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from urllib.parse import urlparse

from models import DetectorConfig, BrowserConfig
from interfaces import IPerformanceOptimizer


class PerformanceOptimizer(IPerformanceOptimizer):
    """
    Performance optimization and resource management for browser instances
    """
    
    def __init__(self, config: DetectorConfig):
        """
        Initialize the performance optimizer
        
        Args:
            config: Detector configuration
        """
        self.config = config
        self.ua = UserAgent()
        
        # Browser instance management
        self._browser_pool: List[webdriver.Chrome] = []
        self._browser_usage_count: Dict[int, int] = {}
        self._browser_creation_time: Dict[int, float] = {}
        self._browser_lock = threading.Lock()
        
        # Resource monitoring
        self._process = psutil.Process()
        self._initial_memory = self._process.memory_info().rss
        self._max_memory_threshold = 2 * 1024 * 1024 * 1024  # 2GB
        self._browser_restart_threshold = 50  # Restart browser after 50 uses
        self._browser_max_age = 3600  # 1 hour max age for browser instances
        
        # Performance metrics
        self._metrics = {
            'browsers_created': 0,
            'browsers_reused': 0,
            'browsers_restarted': 0,
            'memory_cleanups': 0,
            'total_requests': 0
        }
        
        # Worker thread management
        self._max_workers = min(config.max_workers, 20)  # Cap at 20
        self._current_workers = 0
        self._worker_lock = threading.Lock()
        
    def get_optimized_browser(self, url: str) -> webdriver.Chrome:
        """
        Get an optimized browser instance for the given URL
        
        Args:
            url: URL that will be processed
            
        Returns:
            Configured WebDriver instance
        """
        with self._browser_lock:
            self._metrics['total_requests'] += 1
            
            # Try to reuse existing browser
            browser = self._get_reusable_browser()
            if browser:
                self._metrics['browsers_reused'] += 1
                return browser
            
            # Create new browser if none available
            browser = self._create_optimized_browser(url)
            self._metrics['browsers_created'] += 1
            
            # Add to pool
            browser_id = id(browser)
            self._browser_pool.append(browser)
            self._browser_usage_count[browser_id] = 0
            self._browser_creation_time[browser_id] = time.time()
            
            return browser
    
    def _get_reusable_browser(self) -> Optional[webdriver.Chrome]:
        """
        Get a reusable browser from the pool
        
        Returns:
            WebDriver instance if available, None otherwise
        """
        current_time = time.time()
        
        for browser in self._browser_pool[:]:  # Create copy to avoid modification during iteration
            browser_id = id(browser)
            
            # Check if browser is still alive
            try:
                browser.current_url  # Simple check to see if browser is responsive
            except Exception:
                # Browser is dead, remove from pool
                self._remove_browser_from_pool(browser)
                continue
            
            # Check usage count and age
            usage_count = self._browser_usage_count.get(browser_id, 0)
            creation_time = self._browser_creation_time.get(browser_id, current_time)
            age = current_time - creation_time
            
            # Skip if browser has been used too much or is too old
            if usage_count >= self._browser_restart_threshold or age >= self._browser_max_age:
                self._remove_browser_from_pool(browser)
                continue
            
            # Browser is reusable
            self._browser_usage_count[browser_id] = usage_count + 1
            return browser
        
        return None
    
    def _create_optimized_browser(self, url: str) -> webdriver.Chrome:
        """
        Create a new optimized browser instance
        
        Args:
            url: URL for context-specific optimizations
            
        Returns:
            Configured WebDriver instance
        """
        options = self._get_optimized_chrome_options(url)
        
        try:
            # Use undetected-chromedriver for better stealth
            browser = uc.Chrome(
                options=options,
                use_subprocess=True,
                driver_executable_path=chromedriver_autoinstaller.install()
            )
            
            # Set timeouts
            browser.set_page_load_timeout(self.config.timeouts.browser_load)
            browser.set_script_timeout(self.config.timeouts.javascript_wait)
            
            # Set window size for consistency
            browser.set_window_size(
                self.config.browser.window_width,
                self.config.browser.window_height
            )
            
            return browser
            
        except Exception as e:
            raise RuntimeError(f"Failed to create optimized browser: {str(e)}")
    
    def _get_optimized_chrome_options(self, url: str) -> Options:
        """
        Get optimized Chrome options based on configuration and URL
        
        Args:
            url: URL for context-specific optimizations
            
        Returns:
            Configured Chrome options
        """
        options = uc.ChromeOptions()
        
        # Basic stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        
        # Performance optimizations
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # Memory optimizations
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        
        # Headless mode
        if self.config.browser.headless:
            options.add_argument('--headless=new')
        
        # User agent rotation
        if self.config.browser.user_agent_rotation:
            user_agent = self.ua.random
            options.add_argument(f'user-agent={user_agent}')
        
        # Content preferences for performance
        prefs = {
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.notifications": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        
        # Conditional resource blocking based on configuration
        if self.config.browser.disable_images:
            prefs["profile.managed_default_content_settings.images"] = 2
        
        if self.config.browser.disable_css:
            prefs["profile.managed_default_content_settings.stylesheets"] = 2
        
        # JavaScript is needed for detection, so don't disable it
        prefs["profile.managed_default_content_settings.javascript"] = 1
        
        options.add_experimental_option("prefs", prefs)
        
        # Site-specific optimizations based on URL
        try:
            domain = urlparse(url).netloc.lower()
            
            # Known heavy sites - more aggressive optimization
            heavy_sites = ['facebook.com', 'twitter.com', 'instagram.com', 'youtube.com']
            if any(site in domain for site in heavy_sites):
                options.add_argument('--aggressive-cache-discard')
                options.add_argument('--disable-plugins')
        except Exception:
            # If URL parsing fails, continue with default options
            pass
        
        return options
    
    def monitor_resources(self) -> Dict[str, float]:
        """
        Monitor current resource usage
        
        Returns:
            Dictionary with resource usage metrics
        """
        try:
            # Memory usage
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self._process.memory_percent()
            
            # CPU usage
            cpu_percent = self._process.cpu_percent(interval=0.1)
            
            # Browser pool statistics
            active_browsers = len(self._browser_pool)
            
            # Thread count
            thread_count = self._process.num_threads()
            
            metrics = {
                'memory_mb': memory_mb,
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'active_browsers': active_browsers,
                'thread_count': thread_count,
                'browsers_created': self._metrics['browsers_created'],
                'browsers_reused': self._metrics['browsers_reused'],
                'browsers_restarted': self._metrics['browsers_restarted'],
                'memory_cleanups': self._metrics['memory_cleanups'],
                'total_requests': self._metrics['total_requests']
            }
            
            return metrics
            
        except Exception as e:
            return {
                'error': f"Resource monitoring failed: {str(e)}",
                'memory_mb': 0.0,
                'memory_percent': 0.0,
                'cpu_percent': 0.0,
                'active_browsers': len(self._browser_pool),
                'thread_count': 0
            }
    
    def restart_browser_if_needed(self) -> None:
        """
        Restart browser instances if resource usage is too high
        """
        with self._browser_lock:
            current_memory = self._process.memory_info().rss
            
            # Check if memory usage is too high
            if current_memory > self._max_memory_threshold:
                self._cleanup_old_browsers()
                self._metrics['memory_cleanups'] += 1
            
            # Check for browsers that need restart
            current_time = time.time()
            browsers_to_restart = []
            
            for browser in self._browser_pool[:]:
                browser_id = id(browser)
                usage_count = self._browser_usage_count.get(browser_id, 0)
                creation_time = self._browser_creation_time.get(browser_id, current_time)
                age = current_time - creation_time
                
                # Mark for restart if overused or too old
                if usage_count >= self._browser_restart_threshold or age >= self._browser_max_age:
                    browsers_to_restart.append(browser)
            
            # Restart marked browsers
            for browser in browsers_to_restart:
                self._remove_browser_from_pool(browser)
                self._metrics['browsers_restarted'] += 1
    
    def _cleanup_old_browsers(self) -> None:
        """
        Clean up old or overused browser instances
        """
        current_time = time.time()
        browsers_to_remove = []
        
        for browser in self._browser_pool[:]:
            browser_id = id(browser)
            usage_count = self._browser_usage_count.get(browser_id, 0)
            creation_time = self._browser_creation_time.get(browser_id, current_time)
            age = current_time - creation_time
            
            # Remove if overused, too old, or if we have too many browsers
            if (usage_count >= self._browser_restart_threshold or 
                age >= self._browser_max_age or 
                len(self._browser_pool) > self._max_workers):
                browsers_to_remove.append(browser)
        
        # Remove oldest browsers first if we still have too many
        if len(self._browser_pool) > self._max_workers:
            # Sort by creation time and remove oldest
            sorted_browsers = sorted(
                self._browser_pool,
                key=lambda b: self._browser_creation_time.get(id(b), current_time)
            )
            
            excess_count = len(self._browser_pool) - self._max_workers
            browsers_to_remove.extend(sorted_browsers[:excess_count])
        
        # Remove duplicates and clean up
        for browser in set(browsers_to_remove):
            self._remove_browser_from_pool(browser)
    
    def _remove_browser_from_pool(self, browser: webdriver.Chrome) -> None:
        """
        Safely remove a browser from the pool
        
        Args:
            browser: Browser instance to remove
        """
        try:
            browser_id = id(browser)
            
            # Remove from pool
            if browser in self._browser_pool:
                self._browser_pool.remove(browser)
            
            # Clean up tracking dictionaries
            self._browser_usage_count.pop(browser_id, None)
            self._browser_creation_time.pop(browser_id, None)
            
            # Close browser
            try:
                browser.quit()
            except Exception:
                # Browser might already be closed
                pass
                
        except Exception as e:
            # Log error but don't raise to avoid breaking the pool cleanup
            pass
    
    def get_intelligent_timeout(self, url: str, attempt: int = 1) -> Dict[str, int]:
        """
        Get intelligent timeout values based on site characteristics and attempt number
        
        Args:
            url: URL being processed
            attempt: Current attempt number (for retry scenarios)
            
        Returns:
            Dictionary with timeout values
        """
        base_timeouts = {
            'http_request': self.config.timeouts.http_request,
            'browser_load': self.config.timeouts.browser_load,
            'javascript_wait': self.config.timeouts.javascript_wait
        }
        
        try:
            domain = urlparse(url).netloc.lower()
            
            # Known slow sites get longer timeouts
            slow_sites = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com']
            if any(site in domain for site in slow_sites):
                base_timeouts['http_request'] += 10
                base_timeouts['browser_load'] += 15
                base_timeouts['javascript_wait'] += 5
            
            # Known fast sites can use shorter timeouts
            fast_sites = ['google.com', 'github.com', 'stackoverflow.com']
            if any(site in domain for site in fast_sites):
                base_timeouts['http_request'] = max(5, base_timeouts['http_request'] - 5)
                base_timeouts['browser_load'] = max(10, base_timeouts['browser_load'] - 5)
        
        except Exception:
            # If URL parsing fails, use base timeouts
            pass
        
        # Increase timeouts for retry attempts
        if attempt > 1:
            multiplier = 1 + (attempt - 1) * 0.5  # 50% increase per retry
            for key in base_timeouts:
                base_timeouts[key] = int(base_timeouts[key] * multiplier)
        
        return base_timeouts
    
    def get_worker_count(self) -> int:
        """
        Get optimal worker count based on current system resources
        
        Returns:
            Recommended worker count
        """
        try:
            # Get system resources
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Base worker count on CPU cores
            base_workers = min(cpu_count, self.config.max_workers)
            
            # Adjust based on current resource usage
            if cpu_percent > 80 or memory_percent > 80:
                # High resource usage - reduce workers
                base_workers = max(1, base_workers // 2)
            elif cpu_percent < 50 and memory_percent < 50:
                # Low resource usage - can increase workers
                base_workers = min(self.config.max_workers, base_workers + 2)
            
            # Ensure we don't exceed configured maximum
            return min(base_workers, self._max_workers)
            
        except Exception:
            # If resource monitoring fails, use configured default
            return min(self.config.max_workers, 5)
    
    def cleanup_resources(self) -> None:
        """
        Clean up all allocated resources
        """
        with self._browser_lock:
            # Close all browsers in pool
            for browser in self._browser_pool[:]:
                self._remove_browser_from_pool(browser)
            
            # Clear all tracking data
            self._browser_pool.clear()
            self._browser_usage_count.clear()
            self._browser_creation_time.clear()
            
            # Reset metrics
            self._metrics = {
                'browsers_created': 0,
                'browsers_reused': 0,
                'browsers_restarted': 0,
                'memory_cleanups': 0,
                'total_requests': 0
            }
    
    def get_performance_report(self) -> str:
        """
        Generate a performance report
        
        Returns:
            Formatted performance report string
        """
        metrics = self.monitor_resources()
        
        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE OPTIMIZER REPORT")
        report.append("=" * 60)
        
        # Resource usage
        report.append("RESOURCE USAGE:")
        memory_mb = metrics.get('memory_mb', 0)
        memory_percent = metrics.get('memory_percent', 0)
        cpu_percent = metrics.get('cpu_percent', 0)
        active_browsers = metrics.get('active_browsers', 0)
        thread_count = metrics.get('thread_count', 0)
        
        # Handle potential mock objects
        try:
            report.append(f"  Memory Usage:        {float(memory_mb):.1f} MB ({float(memory_percent):.1f}%)")
            report.append(f"  CPU Usage:           {float(cpu_percent):.1f}%")
            report.append(f"  Active Browsers:     {int(active_browsers)}")
            report.append(f"  Thread Count:        {int(thread_count)}")
        except (TypeError, ValueError):
            report.append(f"  Memory Usage:        {memory_mb} MB ({memory_percent}%)")
            report.append(f"  CPU Usage:           {cpu_percent}%")
            report.append(f"  Active Browsers:     {active_browsers}")
            report.append(f"  Thread Count:        {thread_count}")
        report.append("")
        
        # Browser management statistics
        report.append("BROWSER MANAGEMENT:")
        browsers_created = metrics.get('browsers_created', 0)
        browsers_reused = metrics.get('browsers_reused', 0)
        browsers_restarted = metrics.get('browsers_restarted', 0)
        memory_cleanups = metrics.get('memory_cleanups', 0)
        total_requests = metrics.get('total_requests', 0)
        
        try:
            report.append(f"  Browsers Created:    {int(browsers_created)}")
            report.append(f"  Browsers Reused:     {int(browsers_reused)}")
            report.append(f"  Browsers Restarted:  {int(browsers_restarted)}")
            report.append(f"  Memory Cleanups:     {int(memory_cleanups)}")
            report.append(f"  Total Requests:      {int(total_requests)}")
        except (TypeError, ValueError):
            report.append(f"  Browsers Created:    {browsers_created}")
            report.append(f"  Browsers Reused:     {browsers_reused}")
            report.append(f"  Browsers Restarted:  {browsers_restarted}")
            report.append(f"  Memory Cleanups:     {memory_cleanups}")
            report.append(f"  Total Requests:      {total_requests}")
        report.append("")
        
        # Efficiency metrics
        total_browsers = metrics.get('browsers_created', 0)
        reused_browsers = metrics.get('browsers_reused', 0)
        try:
            total_browsers = int(total_browsers)
            reused_browsers = int(reused_browsers)
            if total_browsers > 0:
                reuse_rate = (reused_browsers / (total_browsers + reused_browsers)) * 100
                report.append("EFFICIENCY METRICS:")
                report.append(f"  Browser Reuse Rate:  {reuse_rate:.1f}%")
                report.append("")
        except (TypeError, ValueError):
            # Skip efficiency metrics if values are not numeric
            pass
        
        # Configuration
        report.append("CONFIGURATION:")
        report.append(f"  Max Workers:         {self._max_workers}")
        report.append(f"  Restart Threshold:   {self._browser_restart_threshold} uses")
        report.append(f"  Max Browser Age:     {self._browser_max_age} seconds")
        report.append(f"  Memory Threshold:    {self._max_memory_threshold / (1024**3):.1f} GB")
        report.append("=" * 60)
        
        return "\n".join(report)