"""
Data models and core interfaces for the Website Rendering Detector
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ErrorCategory(Enum):
    """Standardized error categories for website processing"""
    TIMEOUT_ERROR = "TimeoutError"
    HTTP_ERROR = "HTTPError"
    SSL_ERROR = "SSLError"
    NETWORK_ERROR = "NetworkError"
    BROWSER_ERROR = "BrowserError"
    PARSE_ERROR = "ParseError"
    DNS_ERROR = "DNSError"
    UNKNOWN_ERROR = "UnknownError"


class RenderingType(Enum):
    """Website rendering type classifications"""
    SERVER_SIDE_RENDERED = "Server-Side Rendered"
    CLIENT_SIDE_RENDERED = "Client-Side Rendered"
    NOT_ACCESSIBLE = "Not Accessible"


class ProcessingStatus(Enum):
    """Processing status for website analysis"""
    SUCCESS = "Success"
    FAILED = "Failed"
    RETRYING = "Retrying"


@dataclass
class ProcessingResult:
    """Complete result of website rendering detection"""
    url: str
    final_url: str
    rendering_type: str
    status: str
    processing_time_sec: float
    timestamp: str
    frameworks: List[str] = field(default_factory=list)
    error_category: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    http_status_code: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV output"""
        return {
            'url': self.url,
            'final_url': self.final_url,
            'rendering_type': self.rendering_type,
            'status': self.status,
            'processing_time_sec': self.processing_time_sec,
            'timestamp': self.timestamp,
            'frameworks': ','.join(self.frameworks) if self.frameworks else '',
            'error_category': self.error_category or '',
            'error_message': self.error_message or '',
            'retry_count': self.retry_count,
            'http_status_code': self.http_status_code or ''
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingResult':
        """Create ProcessingResult from dictionary (for resume functionality)"""
        frameworks = []
        if data.get('frameworks') and isinstance(data['frameworks'], str):
            frameworks = [f.strip() for f in data['frameworks'].split(',') if f.strip()]
        
        return cls(
            url=str(data.get('url', '')),
            final_url=str(data.get('final_url', '')),
            rendering_type=str(data.get('rendering_type', '')),
            status=str(data.get('status', '')),
            processing_time_sec=float(data.get('processing_time_sec', 0)),
            timestamp=str(data.get('timestamp', '')),
            frameworks=frameworks,
            error_category=data.get('error_category') if data.get('error_category') else None,
            error_message=data.get('error_message') if data.get('error_message') else None,
            retry_count=int(data.get('retry_count', 0)),
            http_status_code=int(data['http_status_code']) if data.get('http_status_code') and str(data['http_status_code']).isdigit() else None
        )


@dataclass
class DetectionMetrics:
    """Internal metrics for rendering detection analysis"""
    content_size_difference: int
    framework_indicators: List[str] = field(default_factory=list)
    dynamic_content_detected: bool = False
    javascript_execution_time: float = 0.0
    dom_mutation_count: int = 0
    http_response_time: float = 0.0
    browser_load_time: float = 0.0
    
    def get_csr_score(self) -> float:
        """Calculate CSR likelihood score (0-1)"""
        score = 0.0
        
        # Content size difference indicates dynamic rendering
        if self.content_size_difference > 1000:
            score += 0.3
        elif self.content_size_difference > 500:
            score += 0.2
        elif self.content_size_difference > 100:
            score += 0.1
        
        # Framework indicators strongly suggest CSR
        if self.framework_indicators:
            score += 0.4
        
        # Dynamic content detection
        if self.dynamic_content_detected:
            score += 0.2
        
        # DOM mutations indicate client-side rendering
        if self.dom_mutation_count > 10:
            score += 0.2
        elif self.dom_mutation_count > 5:
            score += 0.1
        
        # Long JavaScript execution time suggests CSR
        if self.javascript_execution_time > 2.0:
            score += 0.1
        
        return min(score, 1.0)


@dataclass
class RetryConfig:
    """Configuration for retry mechanism"""
    max_attempts: int = 3
    backoff_base: float = 1.0
    backoff_multiplier: float = 2.0
    non_retryable_errors: List[ErrorCategory] = field(default_factory=lambda: [
        ErrorCategory.DNS_ERROR,
        ErrorCategory.SSL_ERROR
    ])
    
    def get_backoff_delay(self, attempt: int) -> float:
        """Calculate backoff delay for given attempt number"""
        return self.backoff_base * (self.backoff_multiplier ** (attempt - 1))


@dataclass
class TimeoutConfig:
    """Timeout configuration for different operations"""
    http_request: int = 15
    browser_load: int = 20
    javascript_wait: int = 5
    total_processing: int = 45


@dataclass
class BrowserConfig:
    """Browser configuration settings"""
    headless: bool = True
    disable_images: bool = True
    disable_css: bool = True
    disable_javascript: bool = False
    user_agent_rotation: bool = True
    window_width: int = 1280
    window_height: int = 800


@dataclass
class DetectorConfig:
    """Main configuration for the website rendering detector"""
    max_workers: int = 10
    chunk_size: int = 100
    save_progress_interval: int = 10
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    
    @classmethod
    def from_args(cls, args) -> 'DetectorConfig':
        """Create configuration from command line arguments"""
        config = cls()
        
        if hasattr(args, 'workers') and args.workers:
            config.max_workers = args.workers
        if hasattr(args, 'chunk') and args.chunk:
            config.chunk_size = args.chunk
        if hasattr(args, 'timeout') and args.timeout:
            config.timeouts.http_request = args.timeout
            config.timeouts.browser_load = args.timeout + 5
        
        return config


@dataclass
class ProcessingStats:
    """Statistics for processing session"""
    total_urls: int = 0
    processed_urls: int = 0
    successful_urls: int = 0
    failed_urls: int = 0
    ssr_count: int = 0
    csr_count: int = 0
    not_accessible_count: int = 0
    total_processing_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    
    def add_result(self, result: ProcessingResult) -> None:
        """Add a processing result to statistics"""
        self.processed_urls += 1
        self.total_processing_time += result.processing_time_sec
        
        if result.status == ProcessingStatus.SUCCESS.value:
            self.successful_urls += 1
            
            if result.rendering_type == RenderingType.SERVER_SIDE_RENDERED.value:
                self.ssr_count += 1
            elif result.rendering_type == RenderingType.CLIENT_SIDE_RENDERED.value:
                self.csr_count += 1
            elif result.rendering_type == RenderingType.NOT_ACCESSIBLE.value:
                self.not_accessible_count += 1
        else:
            self.failed_urls += 1
            
            if result.error_category:
                self.error_breakdown[result.error_category] = self.error_breakdown.get(result.error_category, 0) + 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.processed_urls == 0:
            return 0.0
        return (self.successful_urls / self.processed_urls) * 100
    
    def get_processing_speed(self) -> float:
        """Calculate URLs processed per second"""
        if not self.start_time or not self.end_time:
            return 0.0
        
        elapsed_seconds = (self.end_time - self.start_time).total_seconds()
        if elapsed_seconds == 0:
            return 0.0
        
        return self.processed_urls / elapsed_seconds
    
    def get_average_processing_time(self) -> float:
        """Calculate average processing time per URL"""
        if self.processed_urls == 0:
            return 0.0
        return self.total_processing_time / self.processed_urls