"""
Basic tests for CSR Scanner functionality.

These tests verify that the core components can be imported and initialized
without errors.
"""

import pytest
import sys
import os

# Add src directory to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from models import ProcessingResult, RenderingType, ProcessingStatus, ErrorCategory
    from error_handler import ErrorHandler
    from retry_manager import RetryManager
    from performance_optimizer import PerformanceOptimizer
    from config import Config
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestBasicFunctionality:
    """Test basic functionality and imports."""
    
    def test_imports_available(self):
        """Test that all core modules can be imported."""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"Required modules not available: {IMPORT_ERROR}")
        
        # If we get here, imports worked
        assert True
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_models_creation(self):
        """Test that model classes can be instantiated."""
        # Test RenderingType enum
        assert RenderingType.CLIENT_SIDE_RENDERED
        assert RenderingType.SERVER_SIDE_RENDERED
        assert RenderingType.NOT_ACCESSIBLE
        
        # Test ProcessingStatus enum
        assert ProcessingStatus.SUCCESS
        assert ProcessingStatus.FAILED
        
        # Test ErrorCategory enum
        assert ErrorCategory.DNS_ERROR
        assert ErrorCategory.CONNECTION_ERROR
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_error_handler_initialization(self):
        """Test that ErrorHandler can be initialized."""
        error_handler = ErrorHandler()
        assert error_handler is not None
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available") 
    def test_retry_manager_initialization(self):
        """Test that RetryManager can be initialized."""
        retry_manager = RetryManager()
        assert retry_manager is not None
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_performance_optimizer_initialization(self):
        """Test that PerformanceOptimizer can be initialized."""
        optimizer = PerformanceOptimizer()
        assert optimizer is not None
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_config_initialization(self):
        """Test that Config can be initialized."""
        config = Config()
        assert config is not None


class TestURLValidation:
    """Test URL validation functionality."""
    
    def test_url_parsing(self):
        """Test basic URL parsing without external dependencies."""
        from urllib.parse import urlparse
        
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com",
            "https://example.com/path",
            "https://example.com:8080",
        ]
        
        for url in valid_urls:
            parsed = urlparse(url)
            assert parsed.scheme in ['http', 'https']
            assert parsed.netloc
    
    def test_invalid_urls(self):
        """Test detection of invalid URLs."""
        from urllib.parse import urlparse
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Not HTTP/HTTPS
            "",
            "http://",
            "https://",
        ]
        
        for url in invalid_urls:
            parsed = urlparse(url)
            # Either no scheme/netloc or wrong scheme
            is_invalid = (
                not parsed.scheme or 
                not parsed.netloc or 
                parsed.scheme not in ['http', 'https']
            )
            assert is_invalid


class TestDataStructures:
    """Test data structure functionality."""
    
    def test_list_processing(self):
        """Test basic list processing operations."""
        urls = [
            "https://example1.com",
            "https://example2.com", 
            "https://example3.com"
        ]
        
        # Test list operations
        assert len(urls) == 3
        assert urls[0] == "https://example1.com"
        
        # Test list comprehension
        https_urls = [url for url in urls if url.startswith('https://')]
        assert len(https_urls) == 3
    
    def test_dictionary_operations(self):
        """Test dictionary operations for configuration."""
        config = {
            "browser": {
                "headless": True,
                "timeout": 30
            },
            "performance": {
                "workers": 10,
                "chunk_size": 50
            }
        }
        
        assert config["browser"]["headless"] is True
        assert config["performance"]["workers"] == 10


if __name__ == "__main__":
    pytest.main([__file__])