"""
Error handling and categorization system for Website Rendering Detector
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
import requests
import socket
import ssl
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, NoSuchElementException,
    ElementNotInteractableException, InvalidSessionIdException,
    SessionNotCreatedException, UnexpectedAlertPresentException
)
from urllib3.exceptions import SSLError as Urllib3SSLError
from requests.exceptions import (
    RequestException, Timeout, ConnectionError, HTTPError,
    SSLError as RequestsSSLError, TooManyRedirects, InvalidURL,
    InvalidSchema, MissingSchema
)

from models import ErrorCategory
from interfaces import IErrorHandler


class ErrorHandler(IErrorHandler):
    """
    Comprehensive error handling and categorization system
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize ErrorHandler
        
        Args:
            logger: Optional logger instance, creates default if None
        """
        self.logger = logger or self._setup_default_logger()
        
        # Define non-retryable error patterns
        self.non_retryable_patterns = {
            ErrorCategory.DNS_ERROR: [
                "Name or service not known",
                "nodename nor servname provided",
                "getaddrinfo failed",
                "No address associated with hostname"
            ],
            ErrorCategory.SSL_ERROR: [
                "certificate verify failed",
                "SSL certificate problem",
                "SSL: CERTIFICATE_VERIFY_FAILED",
                "certificate has expired",
                "hostname doesn't match"
            ]
        }
    
    def _setup_default_logger(self) -> logging.Logger:
        """Setup default logger for error handling"""
        logger = logging.getLogger('error_handler')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def categorize_error(self, exception: Exception, url: str = "") -> ErrorCategory:
        """
        Categorize an exception into a standardized error category
        
        Args:
            exception: The exception to categorize
            url: Optional URL context for the error
            
        Returns:
            ErrorCategory enum value
        """
        error_message = str(exception).lower()
        exception_type = type(exception).__name__
        
        # DNS errors (highest priority - most specific)
        if self._is_dns_error(exception, error_message):
            return ErrorCategory.DNS_ERROR
        
        # SSL/TLS errors (high priority)
        if self._is_ssl_error(exception, error_message):
            return ErrorCategory.SSL_ERROR
        
        # Timeout errors (high priority)
        if self._is_timeout_error(exception, error_message):
            return ErrorCategory.TIMEOUT_ERROR
        
        # Browser/WebDriver errors (before HTTP to catch selenium exceptions)
        if self._is_browser_error(exception, error_message):
            return ErrorCategory.BROWSER_ERROR
        
        # HTTP errors
        if self._is_http_error(exception, error_message):
            return ErrorCategory.HTTP_ERROR
        
        # Parse errors
        if self._is_parse_error(exception, error_message):
            return ErrorCategory.PARSE_ERROR
        
        # Network errors (lower priority - more general)
        if self._is_network_error(exception, error_message):
            return ErrorCategory.NETWORK_ERROR
        
        # Default to unknown error
        self.logger.warning(f"Unknown error type: {exception_type} - {error_message}")
        return ErrorCategory.UNKNOWN_ERROR
    
    def _is_timeout_error(self, exception: Exception, error_message: str) -> bool:
        """Check if exception is a timeout error"""
        timeout_indicators = [
            "timeout", "timed out", "read timeout", "connection timeout",
            "request timeout", "response timeout"
        ]
        
        return (
            isinstance(exception, (Timeout, TimeoutException, socket.timeout)) or
            any(indicator in error_message for indicator in timeout_indicators)
        )
    
    def _is_http_error(self, exception: Exception, error_message: str) -> bool:
        """Check if exception is an HTTP error"""
        http_indicators = [
            "http error", "status code", "404", "403", "500", "502", "503", "504",
            "bad request", "unauthorized", "forbidden", "not found",
            "internal server error", "bad gateway", "service unavailable"
        ]
        
        return (
            isinstance(exception, (HTTPError, requests.HTTPError)) or
            any(indicator in error_message for indicator in http_indicators) or
            re.search(r'\b[4-5]\d{2}\b', error_message)  # HTTP status codes 4xx, 5xx
        )
    
    def _is_ssl_error(self, exception: Exception, error_message: str) -> bool:
        """Check if exception is an SSL/TLS error"""
        ssl_indicators = [
            "ssl", "certificate", "tls", "handshake", "verify failed",
            "certificate_verify_failed", "ssl certificate problem",
            "certificate has expired", "hostname doesn't match"
        ]
        
        return (
            isinstance(exception, (ssl.SSLError, RequestsSSLError, Urllib3SSLError)) or
            any(indicator in error_message for indicator in ssl_indicators)
        )
    
    def _is_network_error(self, exception: Exception, error_message: str) -> bool:
        """Check if exception is a network connectivity error"""
        network_indicators = [
            "connection error", "network error", "connection refused",
            "connection reset", "connection aborted", "network unreachable",
            "host unreachable", "no route to host"
        ]
        
        return (
            isinstance(exception, (ConnectionError, socket.error)) or
            any(indicator in error_message for indicator in network_indicators)
        )
    
    def _is_browser_error(self, exception: Exception, error_message: str) -> bool:
        """Check if exception is a browser/WebDriver error"""
        browser_indicators = [
            "webdriver", "selenium", "chrome", "browser", "driver",
            "session not created", "invalid session", "element not found",
            "element not interactable", "unexpected alert"
        ]
        
        return (
            isinstance(exception, (
                WebDriverException, NoSuchElementException,
                ElementNotInteractableException, InvalidSessionIdException,
                SessionNotCreatedException, UnexpectedAlertPresentException
            )) or
            any(indicator in error_message for indicator in browser_indicators)
        )
    
    def _is_parse_error(self, exception: Exception, error_message: str) -> bool:
        """Check if exception is a parsing error"""
        parse_indicators = [
            "parse error", "parsing", "invalid json", "decode error",
            "encoding error", "unicode error", "malformed", "failed to parse"
        ]
        
        return (
            isinstance(exception, (ValueError, UnicodeError, UnicodeDecodeError)) or
            any(indicator in error_message for indicator in parse_indicators)
        )
    
    def _is_dns_error(self, exception: Exception, error_message: str) -> bool:
        """Check if exception is a DNS resolution error"""
        dns_indicators = [
            "name or service not known", "nodename nor servname provided",
            "getaddrinfo failed", "no address associated with hostname",
            "dns", "name resolution", "hostname"
        ]
        
        return (
            isinstance(exception, socket.gaierror) or
            any(indicator in error_message for indicator in dns_indicators)
        )
    
    def should_retry(self, error_category: ErrorCategory) -> bool:
        """
        Determine if an error should trigger a retry
        
        Args:
            error_category: The categorized error
            
        Returns:
            True if the error is retryable, False otherwise
        """
        # Non-retryable errors
        non_retryable = {
            ErrorCategory.DNS_ERROR,
            ErrorCategory.SSL_ERROR,
            ErrorCategory.PARSE_ERROR
        }
        
        return error_category not in non_retryable
    
    def log_error(self, url: str, error_category: ErrorCategory, 
                  error_message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error with structured information
        
        Args:
            url: URL where error occurred
            error_category: Categorized error type
            error_message: Human-readable error message
            details: Optional additional error details
        """
        log_data = {
            "url": url,
            "error_category": error_category.value,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
        }
        
        if details:
            log_data.update(details)
        
        # Log at appropriate level based on error category
        if error_category in [ErrorCategory.DNS_ERROR, ErrorCategory.SSL_ERROR]:
            self.logger.warning(f"Non-retryable error: {log_data}")
        elif error_category == ErrorCategory.TIMEOUT_ERROR:
            self.logger.warning(f"Timeout error (retryable): {log_data}")
        elif error_category == ErrorCategory.HTTP_ERROR:
            status_code = details.get('http_status_code') if details else None
            if status_code and 400 <= status_code < 500:
                self.logger.info(f"Client error (non-retryable): {log_data}")
            else:
                self.logger.warning(f"Server error (retryable): {log_data}")
        else:
            self.logger.error(f"Error occurred: {log_data}")
    
    def get_error_details(self, exception: Exception, url: str = "") -> Dict[str, Any]:
        """
        Extract detailed information from an exception
        
        Args:
            exception: The exception to analyze
            url: Optional URL context
            
        Returns:
            Dictionary with error details
        """
        details = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "url": url
        }
        
        # Extract HTTP status code if available
        if hasattr(exception, 'response') and exception.response:
            details["http_status_code"] = exception.response.status_code
            details["response_headers"] = dict(exception.response.headers)
        
        # Extract WebDriver specific details
        if isinstance(exception, WebDriverException):
            if hasattr(exception, 'msg'):
                details["webdriver_message"] = exception.msg
            if hasattr(exception, 'screen'):
                details["has_screenshot"] = exception.screen is not None
        
        return details
    
    def is_retryable_http_status(self, status_code: int) -> bool:
        """
        Determine if an HTTP status code indicates a retryable error
        
        Args:
            status_code: HTTP status code
            
        Returns:
            True if retryable, False otherwise
        """
        # 5xx server errors are generally retryable
        if 500 <= status_code < 600:
            return True
        
        # 429 Too Many Requests is retryable
        if status_code == 429:
            return True
        
        # 408 Request Timeout is retryable
        if status_code == 408:
            return True
        
        # 4xx client errors are generally not retryable
        if 400 <= status_code < 500:
            return False
        
        # Other status codes (2xx, 3xx) shouldn't be errors
        return False
    
    def format_error_for_output(self, error_category: ErrorCategory, 
                               error_message: str, details: Optional[Dict[str, Any]] = None) -> str:
        """
        Format error information for CSV output
        
        Args:
            error_category: Categorized error type
            error_message: Error message
            details: Optional error details
            
        Returns:
            Formatted error string for CSV
        """
        formatted = f"{error_category.value}: {error_message}"
        
        if details:
            if "http_status_code" in details:
                formatted += f" (HTTP {details['http_status_code']})"
            
            if "exception_type" in details:
                formatted += f" [{details['exception_type']}]"
        
        # Truncate if too long for CSV
        if len(formatted) > 200:
            formatted = formatted[:197] + "..."
        
        return formatted