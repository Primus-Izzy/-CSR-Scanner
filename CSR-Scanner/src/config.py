"""
Enhanced Configuration Management for the Website Rendering Detector

This module provides comprehensive configuration management with support for:
- Environment variables
- Command line arguments
- Configuration validation
- Default value handling
- Verbose logging and debugging options
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from models import DetectorConfig, TimeoutConfig, RetryConfig, BrowserConfig, ErrorCategory


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors"""
    pass


class ConfigLoader:
    """Enhanced utility class for loading and managing configuration"""
    
    # Default configuration values
    DEFAULT_VALUES = {
        'max_workers': 10,
        'chunk_size': 100,
        'save_progress_interval': 10,
        'http_timeout': 15,
        'browser_timeout': 20,
        'javascript_timeout': 5,
        'max_retries': 3,
        'backoff_base': 1.0,
        'headless': True,
        'disable_images': True,
        'disable_css': True,
        'user_agent_rotation': True,
        'window_width': 1280,
        'window_height': 800
    }
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        'DETECTOR_MAX_WORKERS': ('max_workers', int),
        'DETECTOR_CHUNK_SIZE': ('chunk_size', int),
        'DETECTOR_SAVE_INTERVAL': ('save_progress_interval', int),
        'DETECTOR_TIMEOUT_HTTP': ('http_timeout', int),
        'DETECTOR_TIMEOUT_BROWSER': ('browser_timeout', int),
        'DETECTOR_TIMEOUT_JAVASCRIPT': ('javascript_timeout', int),
        'DETECTOR_MAX_RETRIES': ('max_retries', int),
        'DETECTOR_BACKOFF_BASE': ('backoff_base', float),
        'DETECTOR_HEADLESS': ('headless', lambda x: x.lower() == 'true'),
        'DETECTOR_DISABLE_IMAGES': ('disable_images', lambda x: x.lower() == 'true'),
        'DETECTOR_DISABLE_CSS': ('disable_css', lambda x: x.lower() == 'true'),
        'DETECTOR_USER_AGENT_ROTATION': ('user_agent_rotation', lambda x: x.lower() == 'true'),
        'DETECTOR_WINDOW_WIDTH': ('window_width', int),
        'DETECTOR_WINDOW_HEIGHT': ('window_height', int),
        'DETECTOR_VERBOSE': ('verbose', lambda x: x.lower() == 'true'),
        'DETECTOR_DEBUG': ('debug', lambda x: x.lower() == 'true')
    }
    
    @staticmethod
    def load_from_environment() -> DetectorConfig:
        """Load configuration from environment variables with enhanced error handling"""
        config = DetectorConfig()
        
        # Process environment variables using mappings
        for env_var, (config_key, converter) in ConfigLoader.ENV_MAPPINGS.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    converted_value = converter(env_value)
                    ConfigLoader._set_config_value(config, config_key, converted_value)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(
                        f"Invalid value for environment variable {env_var}: {env_value}. "
                        f"Expected {converter.__name__ if hasattr(converter, '__name__') else 'valid value'}. "
                        f"Error: {e}"
                    )
        
        # Calculate total processing timeout
        config.timeouts.total_processing = (
            config.timeouts.http_request + 
            config.timeouts.browser_load + 
            config.timeouts.javascript_wait + 10  # Buffer
        )
        
        return config
    
    @staticmethod
    def _set_config_value(config: DetectorConfig, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        if key in ['max_workers', 'chunk_size', 'save_progress_interval']:
            setattr(config, key, value)
        elif key in ['http_timeout', 'browser_timeout', 'javascript_timeout']:
            timeout_key = key.replace('_timeout', '_request') if 'http' in key else key.replace('_timeout', '_load') if 'browser' in key else key.replace('_timeout', '_wait')
            setattr(config.timeouts, timeout_key, value)
        elif key in ['max_retries', 'backoff_base']:
            retry_key = 'max_attempts' if key == 'max_retries' else key
            setattr(config.retry, retry_key, value)
        elif key in ['headless', 'disable_images', 'disable_css', 'user_agent_rotation', 'window_width', 'window_height']:
            setattr(config.browser, key, value)
    
    @staticmethod
    def create_argument_parser() -> argparse.ArgumentParser:
        """Create enhanced argument parser with comprehensive configuration options"""
        parser = argparse.ArgumentParser(
            description='Enhanced Website Rendering Analysis Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic usage
  python run_analysis.py input.csv --output results.csv --workers 10
  
  # Performance tuning
  python run_analysis.py input.csv --workers 15 --timeout 30 --browser-timeout 25
  
  # Retry configuration
  python run_analysis.py input.csv --max-retries 5 --backoff-base 2.0
  
  # Browser customization
  python run_analysis.py input.csv --headless false --disable-images false --window-size 1920x1080
  
  # Debugging
  python run_analysis.py input.csv --verbose --debug --log-file debug.log
  
  # Environment variables (alternative to CLI args):
  export DETECTOR_MAX_WORKERS=15
  export DETECTOR_TIMEOUT_HTTP=30
  export DETECTOR_VERBOSE=true
  python run_analysis.py input.csv
            """
        )
        
        # Input/Output arguments
        parser.add_argument('input_file', nargs='?', default='input_websites.csv',
                          help='Path to input CSV/Excel file (default: input_websites.csv)')
        parser.add_argument('--output', '-o', default='rendering_results.csv',
                          help='Output CSV file path (default: rendering_results.csv)')
        
        # Performance settings
        performance_group = parser.add_argument_group('Performance Settings')
        performance_group.add_argument('--workers', '-w', type=int, 
                                     help=f'Number of concurrent workers (default: {ConfigLoader.DEFAULT_VALUES["max_workers"]}, max: 20)')
        performance_group.add_argument('--chunk', type=int, 
                                     help=f'Number of URLs to process before saving (default: {ConfigLoader.DEFAULT_VALUES["chunk_size"]})')
        performance_group.add_argument('--save-interval', type=int, 
                                     help=f'Save progress every N processed URLs (default: {ConfigLoader.DEFAULT_VALUES["save_progress_interval"]})')
        
        # Timeout settings
        timeout_group = parser.add_argument_group('Timeout Settings')
        timeout_group.add_argument('--timeout', type=int, 
                                 help=f'HTTP request timeout in seconds (default: {ConfigLoader.DEFAULT_VALUES["http_timeout"]})')
        timeout_group.add_argument('--browser-timeout', type=int, 
                                 help=f'Browser load timeout in seconds (default: {ConfigLoader.DEFAULT_VALUES["browser_timeout"]})')
        timeout_group.add_argument('--js-timeout', type=int, 
                                 help=f'JavaScript execution timeout in seconds (default: {ConfigLoader.DEFAULT_VALUES["javascript_timeout"]})')
        
        # Retry settings
        retry_group = parser.add_argument_group('Retry Settings')
        retry_group.add_argument('--max-retries', type=int, 
                               help=f'Maximum retry attempts for failed requests (default: {ConfigLoader.DEFAULT_VALUES["max_retries"]})')
        retry_group.add_argument('--backoff-base', type=float, 
                               help=f'Base delay for exponential backoff in seconds (default: {ConfigLoader.DEFAULT_VALUES["backoff_base"]})')
        retry_group.add_argument('--no-retry-dns', action='store_true',
                               help='Disable retries for DNS resolution errors (default: disabled)')
        retry_group.add_argument('--no-retry-ssl', action='store_true',
                               help='Disable retries for SSL certificate errors (default: disabled)')
        
        # Browser settings
        browser_group = parser.add_argument_group('Browser Settings')
        browser_group.add_argument('--headless', type=str, choices=['true', 'false'],
                                 help='Run browser in headless mode (default: true)')
        browser_group.add_argument('--disable-images', type=str, choices=['true', 'false'],
                                 help='Disable image loading for faster processing (default: true)')
        browser_group.add_argument('--disable-css', type=str, choices=['true', 'false'],
                                 help='Disable CSS loading for faster processing (default: true)')
        browser_group.add_argument('--user-agent-rotation', type=str, choices=['true', 'false'],
                                 help='Rotate user agents to avoid detection (default: true)')
        browser_group.add_argument('--window-size', type=str, 
                                 help='Browser window size in WIDTHxHEIGHT format (default: 1280x800)')
        
        # Logging and debugging
        logging_group = parser.add_argument_group('Logging and Debugging')
        logging_group.add_argument('--verbose', '-v', action='store_true',
                                 help='Enable verbose logging (INFO level)')
        logging_group.add_argument('--debug', '-d', action='store_true',
                                 help='Enable debug mode with detailed logging (DEBUG level)')
        logging_group.add_argument('--quiet', '-q', action='store_true',
                                 help='Suppress all output except errors')
        logging_group.add_argument('--log-file', type=str,
                                 help='Write logs to specified file in addition to console')
        
        # Configuration management
        config_group = parser.add_argument_group('Configuration Management')
        config_group.add_argument('--config-file', type=str,
                                help='Load configuration from JSON file')
        config_group.add_argument('--save-config', type=str,
                                help='Save current configuration to JSON file')
        config_group.add_argument('--show-config', action='store_true',
                                help='Display current configuration and exit')
        config_group.add_argument('--validate-config', action='store_true',
                                help='Validate configuration and exit')
        
        return parser
    
    @staticmethod
    def load_from_args(args: argparse.Namespace) -> DetectorConfig:
        """Load configuration from parsed command line arguments with enhanced validation"""
        # Start with environment configuration
        config = ConfigLoader.load_from_environment()
        
        # Load from config file if specified (this will override environment values)
        if hasattr(args, 'config_file') and args.config_file:
            if os.path.exists(args.config_file):
                config = ConfigLoader.load_from_file(args.config_file, config)
            else:
                raise ConfigurationError(f"Configuration file not found: {args.config_file}")
        
        # Override with command line arguments
        if hasattr(args, 'workers') and args.workers is not None:
            config.max_workers = args.workers  # Don't cap here, let validation handle it
        
        if hasattr(args, 'chunk') and args.chunk is not None:
            config.chunk_size = args.chunk
        
        if hasattr(args, 'save_interval') and args.save_interval is not None:
            config.save_progress_interval = args.save_interval
        
        # Timeout settings
        if hasattr(args, 'timeout') and args.timeout is not None:
            config.timeouts.http_request = args.timeout
        
        if hasattr(args, 'browser_timeout') and args.browser_timeout is not None:
            config.timeouts.browser_load = args.browser_timeout
        
        if hasattr(args, 'js_timeout') and args.js_timeout is not None:
            config.timeouts.javascript_wait = args.js_timeout
        
        # Calculate total processing timeout
        config.timeouts.total_processing = (
            config.timeouts.http_request + 
            config.timeouts.browser_load + 
            config.timeouts.javascript_wait + 10  # Buffer
        )
        
        # Retry settings
        if hasattr(args, 'max_retries') and args.max_retries is not None:
            config.retry.max_attempts = args.max_retries
        
        if hasattr(args, 'backoff_base') and args.backoff_base is not None:
            config.retry.backoff_base = args.backoff_base
        
        # Handle retry exclusions
        if hasattr(args, 'no_retry_dns') and args.no_retry_dns:
            if ErrorCategory.DNS_ERROR not in config.retry.non_retryable_errors:
                config.retry.non_retryable_errors.append(ErrorCategory.DNS_ERROR)
        
        if hasattr(args, 'no_retry_ssl') and args.no_retry_ssl:
            if ErrorCategory.SSL_ERROR not in config.retry.non_retryable_errors:
                config.retry.non_retryable_errors.append(ErrorCategory.SSL_ERROR)
        
        # Browser settings
        if hasattr(args, 'headless') and args.headless is not None:
            config.browser.headless = args.headless.lower() == 'true'
        
        if hasattr(args, 'disable_images') and args.disable_images is not None:
            config.browser.disable_images = args.disable_images.lower() == 'true'
        
        if hasattr(args, 'disable_css') and args.disable_css is not None:
            config.browser.disable_css = args.disable_css.lower() == 'true'
        
        if hasattr(args, 'user_agent_rotation') and args.user_agent_rotation is not None:
            config.browser.user_agent_rotation = args.user_agent_rotation.lower() == 'true'
        
        # Parse window size
        if hasattr(args, 'window_size') and args.window_size:
            try:
                width, height = args.window_size.split('x')
                config.browser.window_width = int(width)
                config.browser.window_height = int(height)
            except (ValueError, AttributeError):
                raise ConfigurationError(f"Invalid window size format: {args.window_size}. Expected format: WIDTHxHEIGHT (e.g., 1920x1080)")
        
        return config
    
    @staticmethod
    def load_from_file(config_file: str, base_config: Optional[DetectorConfig] = None) -> DetectorConfig:
        """Load configuration from JSON file"""
        import json
        
        if base_config is None:
            base_config = DetectorConfig()
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Apply configuration from file
            for key, value in config_data.items():
                if hasattr(base_config, key):
                    if key == 'timeouts':
                        for timeout_key, timeout_value in value.items():
                            if hasattr(base_config.timeouts, timeout_key):
                                setattr(base_config.timeouts, timeout_key, timeout_value)
                    elif key == 'retry':
                        for retry_key, retry_value in value.items():
                            if hasattr(base_config.retry, retry_key):
                                setattr(base_config.retry, retry_key, retry_value)
                    elif key == 'browser':
                        for browser_key, browser_value in value.items():
                            if hasattr(base_config.browser, browser_key):
                                setattr(base_config.browser, browser_key, browser_value)
                    else:
                        setattr(base_config, key, value)
            
            return base_config
            
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {config_file}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file {config_file}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration file {config_file}: {e}")
    
    @staticmethod
    def save_to_file(config: DetectorConfig, config_file: str) -> None:
        """Save configuration to JSON file"""
        import json
        
        config_dict = {
            'max_workers': config.max_workers,
            'chunk_size': config.chunk_size,
            'save_progress_interval': config.save_progress_interval,
            'timeouts': {
                'http_request': config.timeouts.http_request,
                'browser_load': config.timeouts.browser_load,
                'javascript_wait': config.timeouts.javascript_wait,
                'total_processing': config.timeouts.total_processing
            },
            'retry': {
                'max_attempts': config.retry.max_attempts,
                'backoff_base': config.retry.backoff_base,
                'backoff_multiplier': config.retry.backoff_multiplier,
                'non_retryable_errors': [error.value for error in config.retry.non_retryable_errors]
            },
            'browser': {
                'headless': config.browser.headless,
                'disable_images': config.browser.disable_images,
                'disable_css': config.browser.disable_css,
                'disable_javascript': config.browser.disable_javascript,
                'user_agent_rotation': config.browser.user_agent_rotation,
                'window_width': config.browser.window_width,
                'window_height': config.browser.window_height
            }
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            raise ConfigurationError(f"Error saving configuration to {config_file}: {e}")
    
    @staticmethod
    def validate_config(config: DetectorConfig) -> Dict[str, str]:
        """Comprehensive configuration validation with detailed error messages"""
        errors = {}
        
        # Performance settings validation
        if config.max_workers < 1 or config.max_workers > 20:
            errors['max_workers'] = 'Must be between 1 and 20 workers'
        
        if config.chunk_size < 1 or config.chunk_size > 10000:
            errors['chunk_size'] = 'Must be between 1 and 10,000 URLs per chunk'
        
        if config.save_progress_interval < 1 or config.save_progress_interval > 1000:
            errors['save_progress_interval'] = 'Must be between 1 and 1,000 URLs'
        
        # Timeout validation
        if config.timeouts.http_request < 5 or config.timeouts.http_request > 300:
            errors['http_timeout'] = 'Must be between 5 and 300 seconds'
        
        if config.timeouts.browser_load < 5 or config.timeouts.browser_load > 300:
            errors['browser_timeout'] = 'Must be between 5 and 300 seconds'
        
        if config.timeouts.javascript_wait < 1 or config.timeouts.javascript_wait > 60:
            errors['javascript_timeout'] = 'Must be between 1 and 60 seconds'
        
        # Check for reasonable timeout relationships
        if config.timeouts.browser_load < config.timeouts.http_request:
            errors['timeout_relationship'] = 'Browser timeout should be >= HTTP timeout'
        
        # Retry settings validation
        if config.retry.max_attempts < 0 or config.retry.max_attempts > 10:
            errors['max_retries'] = 'Must be between 0 and 10 attempts'
        
        if config.retry.backoff_base < 0.1 or config.retry.backoff_base > 30.0:
            errors['backoff_base'] = 'Must be between 0.1 and 30.0 seconds'
        
        if config.retry.backoff_multiplier < 1.0 or config.retry.backoff_multiplier > 5.0:
            errors['backoff_multiplier'] = 'Must be between 1.0 and 5.0'
        
        # Browser settings validation
        if config.browser.window_width < 800 or config.browser.window_width > 3840:
            errors['window_width'] = 'Must be between 800 and 3840 pixels'
        
        if config.browser.window_height < 600 or config.browser.window_height > 2160:
            errors['window_height'] = 'Must be between 600 and 2160 pixels'
        
        # Logical validation
        if config.save_progress_interval > config.chunk_size:
            errors['save_interval_chunk'] = 'Save interval should not exceed chunk size'
        
        return errors
    
    @staticmethod
    def get_validation_warnings(config: DetectorConfig) -> List[str]:
        """Get configuration warnings for potentially suboptimal settings"""
        warnings = []
        
        # Performance warnings
        if config.max_workers > 15:
            warnings.append("High worker count (>15) may cause resource contention")
        
        if config.chunk_size > 5000:
            warnings.append("Large chunk size may increase memory usage")
        
        # Timeout warnings
        if config.timeouts.http_request > 60:
            warnings.append("Long HTTP timeout may slow processing of failed sites")
        
        if config.timeouts.browser_load > 60:
            warnings.append("Long browser timeout may slow processing significantly")
        
        # Retry warnings
        if config.retry.max_attempts > 5:
            warnings.append("High retry count may significantly slow processing")
        
        if config.retry.backoff_base > 5.0:
            warnings.append("High backoff base may cause very long retry delays")
        
        # Browser warnings
        if not config.browser.headless:
            warnings.append("Non-headless mode will be slower and use more resources")
        
        if not config.browser.disable_images:
            warnings.append("Loading images will slow processing and use more bandwidth")
        
        if not config.browser.disable_css:
            warnings.append("Loading CSS will slow processing and use more bandwidth")
        
        return warnings
    
    @staticmethod
    def print_config(config: DetectorConfig, show_warnings: bool = True) -> None:
        """Print current configuration in a comprehensive, readable format"""
        print("=" * 80)
        print("WEBSITE RENDERING DETECTOR CONFIGURATION".center(80))
        print("=" * 80)
        
        # Performance settings
        print("PERFORMANCE SETTINGS:")
        print(f"  Max Workers:           {config.max_workers:>3} (concurrent processing threads)")
        print(f"  Chunk Size:            {config.chunk_size:>3} (URLs processed before saving)")
        print(f"  Save Interval:         {config.save_progress_interval:>3} (save progress every N URLs)")
        print()
        
        # Timeout settings
        print("TIMEOUT SETTINGS:")
        print(f"  HTTP Request:          {config.timeouts.http_request:>3}s (initial page fetch)")
        print(f"  Browser Load:          {config.timeouts.browser_load:>3}s (full page load with JS)")
        print(f"  JavaScript Wait:       {config.timeouts.javascript_wait:>3}s (wait for dynamic content)")
        print(f"  Total Processing:      {config.timeouts.total_processing:>3}s (maximum per URL)")
        print()
        
        # Retry settings
        print("RETRY SETTINGS:")
        print(f"  Max Attempts:          {config.retry.max_attempts:>3} (including initial attempt)")
        print(f"  Backoff Base:          {config.retry.backoff_base:>3.1f}s (initial retry delay)")
        print(f"  Backoff Multiplier:    {config.retry.backoff_multiplier:>3.1f}x (delay increase factor)")
        print(f"  Non-retryable Errors:  {', '.join([e.value for e in config.retry.non_retryable_errors])}")
        print()
        
        # Browser settings
        print("BROWSER SETTINGS:")
        print(f"  Headless Mode:         {'[X]' if config.browser.headless else '[ ]'} ({'Enabled' if config.browser.headless else 'Disabled'})")
        print(f"  Disable Images:        {'[X]' if config.browser.disable_images else '[ ]'} ({'Enabled' if config.browser.disable_images else 'Disabled'})")
        print(f"  Disable CSS:           {'[X]' if config.browser.disable_css else '[ ]'} ({'Enabled' if config.browser.disable_css else 'Disabled'})")
        print(f"  Disable JavaScript:    {'[X]' if config.browser.disable_javascript else '[ ]'} ({'Enabled' if config.browser.disable_javascript else 'Disabled'})")
        print(f"  User Agent Rotation:   {'[X]' if config.browser.user_agent_rotation else '[ ]'} ({'Enabled' if config.browser.user_agent_rotation else 'Disabled'})")
        print(f"  Window Size:           {config.browser.window_width}x{config.browser.window_height} pixels")
        print()
        
        # Configuration validation
        errors = ConfigLoader.validate_config(config)
        if errors:
            print("ERROR: CONFIGURATION ERRORS:")
            for field, error in errors.items():
                print(f"  {field}: {error}")
            print()
        
        # Configuration warnings
        if show_warnings:
            warnings = ConfigLoader.get_validation_warnings(config)
            if warnings:
                print("WARNING: CONFIGURATION WARNINGS:")
                for warning in warnings:
                    print(f"  • {warning}")
                print()
        
        # Performance estimates
        print("ESTIMATED PERFORMANCE:")
        estimated_speed = ConfigLoader._estimate_processing_speed(config)
        print(f"  Estimated Speed:       ~{estimated_speed:.1f} URLs/minute")
        print(f"  Memory Usage:          ~{config.max_workers * 50}MB (approximate)")
        
        print("=" * 80)
    
    @staticmethod
    def _estimate_processing_speed(config: DetectorConfig) -> float:
        """Estimate processing speed based on configuration"""
        # Base processing time per URL (seconds)
        base_time = (config.timeouts.http_request + config.timeouts.browser_load) / 2
        
        # Adjust for retry overhead
        retry_overhead = config.retry.max_attempts * 0.1
        
        # Adjust for browser optimizations
        optimization_factor = 1.0
        if config.browser.disable_images:
            optimization_factor *= 0.8
        if config.browser.disable_css:
            optimization_factor *= 0.9
        if config.browser.headless:
            optimization_factor *= 0.9
        
        # Calculate URLs per minute
        time_per_url = (base_time + retry_overhead) * optimization_factor
        urls_per_minute = (60 / time_per_url) * min(config.max_workers, 10)  # Cap concurrency benefit
        
        return urls_per_minute
    
    @staticmethod
    def setup_logging(verbose: bool = False, debug: bool = False, quiet: bool = False, 
                     log_file: Optional[str] = None) -> None:
        """Setup logging configuration based on arguments"""
        # Determine log level
        if debug:
            log_level = logging.DEBUG
        elif verbose:
            log_level = logging.INFO
        elif quiet:
            log_level = logging.ERROR
        else:
            log_level = logging.WARNING
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if not quiet:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)  # Always debug level for file
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not setup log file {log_file}: {e}")
        
        # Set specific logger levels
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)