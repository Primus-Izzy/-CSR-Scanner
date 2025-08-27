"""
CSR Scanner - Client-Side Rendering Detection Tool

A powerful and efficient tool for detecting whether websites use client-side 
rendering (CSR), server-side rendering (SSR), or are not accessible.

Main Features:
- Rendering type detection (CSR/SSR/Not Accessible)
- JavaScript framework identification
- Batch processing with multi-threading
- Comprehensive error handling
- Resume capability
- Performance optimization

Usage:
    from csr_scanner import WebsiteRenderer
    
    renderer = WebsiteRenderer()
    result = renderer.analyze_url("https://example.com")
    print(f"Rendering type: {result.rendering_type}")
"""

__version__ = "1.0.0"
__author__ = "Isreal Oyarinde"
__license__ = "MIT"

# Main imports for easy access
try:
    from .website_renderer import WebsiteRenderer
    from .models import (
        ProcessingResult,
        RenderingType,
        ProcessingStatus,
        ErrorCategory,
        RetryConfig,
        DetectionMetrics,
        DetectorConfig,
        TimeoutConfig,
        BrowserConfig
    )
    from .error_handler import ErrorHandler
    from .retry_manager import RetryManager
    from .performance_optimizer import PerformanceOptimizer
    from .config import Config
    
    __all__ = [
        "WebsiteRenderer",
        "ProcessingResult", 
        "RenderingType",
        "ProcessingStatus",
        "ErrorCategory",
        "RetryConfig",
        "DetectionMetrics", 
        "DetectorConfig",
        "TimeoutConfig",
        "BrowserConfig",
        "ErrorHandler",
        "RetryManager", 
        "PerformanceOptimizer",
        "Config"
    ]
    
except ImportError as e:
    # Handle import errors gracefully for development/testing
    import warnings
    warnings.warn(f"Some CSR Scanner modules could not be imported: {e}")
    __all__ = []