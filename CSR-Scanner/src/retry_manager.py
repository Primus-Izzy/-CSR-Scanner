"""
Retry mechanism with exponential backoff for Website Rendering Detector
"""

import time
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from models import ErrorCategory, RetryConfig
from interfaces import IRetryManager, IErrorHandler


@dataclass
class RetryAttempt:
    """Information about a single retry attempt"""
    attempt_number: int
    timestamp: datetime
    error_category: ErrorCategory
    error_message: str
    delay_before_attempt: float


@dataclass
class RetryHistory:
    """Complete history of retry attempts for a single operation"""
    url: str
    total_attempts: int
    success: bool
    final_error: Optional[str] = None
    attempts: List[RetryAttempt] = field(default_factory=list)
    total_retry_time: float = 0.0
    
    def add_attempt(self, attempt: RetryAttempt) -> None:
        """Add a retry attempt to the history"""
        self.attempts.append(attempt)
        self.total_retry_time += attempt.delay_before_attempt


class RetryManager(IRetryManager):
    """
    Intelligent retry mechanism with exponential backoff
    """
    
    def __init__(self, config: RetryConfig, error_handler: IErrorHandler, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize RetryManager
        
        Args:
            config: Retry configuration
            error_handler: Error handler for categorizing exceptions
            logger: Optional logger instance
        """
        self.config = config
        self.error_handler = error_handler
        self.logger = logger or self._setup_default_logger()
        self.retry_histories: Dict[str, RetryHistory] = {}
    
    def _setup_default_logger(self) -> logging.Logger:
        """Setup default logger for retry operations"""
        logger = logging.getLogger('retry_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic and exponential backoff
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result if successful
            
        Raises:
            Final exception if all retries are exhausted
        """
        # Extract URL for tracking (assume first arg is URL if available)
        url = args[0] if args and isinstance(args[0], str) else "unknown"
        
        # Initialize retry history
        history = RetryHistory(url=url, total_attempts=0, success=False)
        self.retry_histories[url] = history
        
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            history.total_attempts = attempt
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Success - update history and return result
                history.success = True
                if attempt > 1:
                    self.logger.info(f"Success on attempt {attempt} for {url}")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_category = self.error_handler.categorize_error(e, url)
                error_message = str(e)
                
                # Log the error
                self.error_handler.log_error(
                    url=url,
                    error_category=error_category,
                    error_message=error_message,
                    details={
                        "attempt": attempt,
                        "max_attempts": self.config.max_attempts
                    }
                )
                
                # Record the attempt (always record failed attempts)
                retry_attempt = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    error_category=error_category,
                    error_message=error_message,
                    delay_before_attempt=0  # Will be updated if we retry
                )
                
                # Check if we should retry
                if not self.should_retry(error_category, attempt):
                    self.logger.info(
                        f"Not retrying {url} due to {error_category.value} "
                        f"(attempt {attempt}/{self.config.max_attempts})"
                    )
                    history.add_attempt(retry_attempt)
                    history.final_error = f"{error_category.value}: {error_message}"
                    break
                
                # If this was the last attempt, don't wait
                if attempt >= self.config.max_attempts:
                    self.logger.warning(
                        f"All {self.config.max_attempts} attempts exhausted for {url}. "
                        f"Final error: {error_category.value}"
                    )
                    history.add_attempt(retry_attempt)
                    history.final_error = f"{error_category.value}: {error_message}"
                    break
                
                # Calculate backoff delay for next attempt
                delay = self.get_backoff_delay(attempt)
                retry_attempt.delay_before_attempt = delay
                history.add_attempt(retry_attempt)
                
                # Wait before next attempt
                if delay > 0:
                    self.logger.info(
                        f"Retrying {url} in {delay:.1f}s (attempt {attempt + 1}/{self.config.max_attempts}) "
                        f"after {error_category.value}"
                    )
                    time.sleep(delay)
        
        # All retries exhausted - raise the last exception
        if last_exception:
            raise last_exception
        
        # This should never happen, but just in case
        raise RuntimeError(f"Unexpected error in retry logic for {url}")
    
    def get_backoff_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay for given attempt number
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds before next attempt
        """
        if attempt <= 0:
            return 0.0
        
        # Use the config's backoff calculation
        return self.config.get_backoff_delay(attempt)
    
    def should_retry(self, error_category: ErrorCategory, attempt: int) -> bool:
        """
        Determine if an error should trigger a retry
        
        Args:
            error_category: The categorized error
            attempt: Current attempt number
            
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if we've reached max attempts
        if attempt >= self.config.max_attempts:
            return False
        
        # Don't retry non-retryable errors
        if error_category in self.config.non_retryable_errors:
            return False
        
        # Use error handler's retry logic for additional checks
        return self.error_handler.should_retry(error_category)
    
    def get_retry_history(self, url: str) -> Optional[RetryHistory]:
        """
        Get retry history for a specific URL
        
        Args:
            url: URL to get history for
            
        Returns:
            RetryHistory if available, None otherwise
        """
        return self.retry_histories.get(url)
    
    def get_all_retry_histories(self) -> Dict[str, RetryHistory]:
        """
        Get all retry histories
        
        Returns:
            Dictionary mapping URLs to their retry histories
        """
        return self.retry_histories.copy()
    
    def clear_history(self) -> None:
        """Clear all retry histories"""
        self.retry_histories.clear()
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about retry operations
        
        Returns:
            Dictionary with retry statistics
        """
        if not self.retry_histories:
            return {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "operations_requiring_retry": 0,
                "average_attempts": 0.0,
                "total_retry_time": 0.0,
                "error_breakdown": {}
            }
        
        total_ops = len(self.retry_histories)
        successful_ops = sum(1 for h in self.retry_histories.values() if h.success)
        failed_ops = total_ops - successful_ops
        ops_requiring_retry = sum(1 for h in self.retry_histories.values() if h.total_attempts > 1)
        
        total_attempts = sum(h.total_attempts for h in self.retry_histories.values())
        average_attempts = total_attempts / total_ops if total_ops > 0 else 0.0
        
        total_retry_time = sum(h.total_retry_time for h in self.retry_histories.values())
        
        # Error breakdown
        error_breakdown = {}
        for history in self.retry_histories.values():
            for attempt in history.attempts:
                error_cat = attempt.error_category.value
                error_breakdown[error_cat] = error_breakdown.get(error_cat, 0) + 1
        
        return {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "operations_requiring_retry": ops_requiring_retry,
            "average_attempts": round(average_attempts, 2),
            "total_retry_time": round(total_retry_time, 2),
            "error_breakdown": error_breakdown
        }
    
    def format_retry_summary(self, url: str) -> str:
        """
        Format a human-readable summary of retry attempts for a URL
        
        Args:
            url: URL to format summary for
            
        Returns:
            Formatted summary string
        """
        history = self.retry_histories.get(url)
        if not history:
            return f"No retry history found for {url}"
        
        if history.total_attempts == 1:
            return f"{url}: Success on first attempt"
        
        summary = f"{url}: {history.total_attempts} attempts"
        
        if history.success:
            summary += " (eventually successful)"
        else:
            summary += f" (failed - {history.final_error})"
        
        if history.attempts:
            error_types = [attempt.error_category.value for attempt in history.attempts]
            summary += f" - Errors: {', '.join(error_types)}"
        
        if history.total_retry_time > 0:
            summary += f" - Total retry time: {history.total_retry_time:.1f}s"
        
        return summary