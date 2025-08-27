# CSR Scanner API Documentation

## Core Classes and Methods

### WebsiteRenderer Class

The main class responsible for analyzing websites and detecting rendering types.

#### Constructor
```python
WebsiteRenderer(config: dict = None)
```

**Parameters:**
- `config` (dict, optional): Configuration dictionary containing browser and detection settings

#### Methods

##### `analyze_url(url: str) -> ProcessingResult`

Analyzes a single URL to determine its rendering type.

**Parameters:**
- `url` (str): The URL to analyze

**Returns:**
- `ProcessingResult`: Object containing analysis results

**Example:**
```python
from src.website_renderer import WebsiteRenderer

renderer = WebsiteRenderer()
result = renderer.analyze_url("https://example.com")
print(f"Rendering type: {result.rendering_type}")
```

##### `analyze_urls_batch(urls: List[str]) -> List[ProcessingResult]`

Analyzes multiple URLs in batch with parallel processing.

**Parameters:**
- `urls` (List[str]): List of URLs to analyze

**Returns:**
- `List[ProcessingResult]`: List of analysis results

### Data Models

#### ProcessingResult

Represents the result of analyzing a single URL.

**Attributes:**
- `url` (str): Original URL
- `final_url` (str): Final URL after redirects
- `rendering_type` (RenderingType): CSR, SSR, or Not Accessible
- `status` (ProcessingStatus): Success or Failed
- `processing_time_sec` (float): Time taken to process
- `timestamp` (datetime): When processing occurred
- `frameworks` (List[str]): Detected JavaScript frameworks
- `error_category` (ErrorCategory): Type of error if failed
- `error_message` (str): Detailed error message
- `retry_count` (int): Number of retries attempted
- `http_status_code` (int): HTTP response code

#### RenderingType Enum

- `CLIENT_SIDE_RENDERED`: Website uses client-side rendering
- `SERVER_SIDE_RENDERED`: Website uses server-side rendering  
- `NOT_ACCESSIBLE`: Website is not accessible

#### ProcessingStatus Enum

- `SUCCESS`: Processing completed successfully
- `FAILED`: Processing failed

#### ErrorCategory Enum

- `DNS_ERROR`: DNS resolution failed
- `CONNECTION_ERROR`: Network connection failed
- `TIMEOUT_ERROR`: Request timed out
- `HTTP_ERROR`: HTTP error response
- `BROWSER_ERROR`: Browser automation error
- `PARSING_ERROR`: Content parsing error
- `UNKNOWN_ERROR`: Unknown error occurred

## Configuration Options

### Browser Configuration

```python
browser_config = {
    "headless": True,              # Run browser in headless mode
    "disable_images": True,        # Disable image loading
    "disable_css": False,          # Disable CSS loading
    "user_agent_rotation": True,   # Rotate user agents
    "window_size": {
        "width": 1920,
        "height": 1080
    }
}
```

### Performance Configuration

```python
performance_config = {
    "workers": 10,           # Number of concurrent workers
    "chunk_size": 50,        # URLs processed per chunk
    "timeout": 30,           # Request timeout in seconds
    "browser_timeout": 25,   # Browser timeout in seconds
    "max_retries": 2,        # Maximum retry attempts
    "retry_delay": 1.0       # Delay between retries
}
```

### Detection Configuration

```python
detection_config = {
    "wait_time": 5,                        # Wait time for page load
    "scroll_detection": True,              # Enable scroll-based detection
    "framework_detection": True,           # Enable framework detection
    "content_change_detection": True,      # Detect content changes
    "minimum_content_length": 100          # Minimum content length
}
```

## Usage Examples

### Basic Usage

```python
from src.website_renderer import WebsiteRenderer

# Initialize renderer
renderer = WebsiteRenderer()

# Analyze single URL
result = renderer.analyze_url("https://example.com")
print(f"URL: {result.url}")
print(f"Type: {result.rendering_type}")
print(f"Frameworks: {result.frameworks}")
```

### Batch Processing

```python
from src.website_renderer import WebsiteRenderer
import pandas as pd

# Load URLs from CSV
df = pd.read_csv("input.csv")
urls = df['url'].tolist()

# Configure renderer
config = {
    "performance": {
        "workers": 15,
        "timeout": 25
    },
    "browser": {
        "headless": True,
        "disable_images": True
    }
}

renderer = WebsiteRenderer(config)

# Process batch
results = renderer.analyze_urls_batch(urls)

# Convert to DataFrame
results_df = pd.DataFrame([result.__dict__ for result in results])
results_df.to_csv("results.csv", index=False)
```

### Custom Configuration

```python
from src.website_renderer import WebsiteRenderer
from src.models import RetryConfig, TimeoutConfig

# Advanced configuration
config = {
    "browser": {
        "headless": False,  # Show browser for debugging
        "disable_images": False,
        "user_agent": "Custom User Agent"
    },
    "detection": {
        "wait_time": 10,
        "framework_detection": True,
        "scroll_detection": False
    },
    "performance": {
        "workers": 5,
        "timeout": 60,
        "max_retries": 1
    }
}

renderer = WebsiteRenderer(config)
result = renderer.analyze_url("https://complex-spa.com")
```

### Error Handling

```python
from src.website_renderer import WebsiteRenderer
from src.models import ProcessingStatus, ErrorCategory

renderer = WebsiteRenderer()

try:
    result = renderer.analyze_url("https://example.com")
    
    if result.status == ProcessingStatus.SUCCESS:
        print(f"Successfully analyzed: {result.rendering_type}")
    else:
        print(f"Analysis failed: {result.error_category}")
        print(f"Error message: {result.error_message}")
        
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Framework Detection

The tool can detect the following JavaScript frameworks and libraries:

### Supported Frameworks

- **React**: Detects React applications
- **Vue.js**: Detects Vue applications  
- **Angular**: Detects Angular applications
- **Svelte**: Detects Svelte applications
- **Next.js**: Detects Next.js applications
- **Nuxt.js**: Detects Nuxt.js applications
- **Gatsby**: Detects Gatsby applications
- **jQuery**: Detects jQuery usage
- **Backbone.js**: Detects Backbone applications
- **Ember.js**: Detects Ember applications

### Framework Detection Process

1. **DOM Analysis**: Examines DOM structure and attributes
2. **Script Analysis**: Analyzes loaded JavaScript files
3. **Global Object Detection**: Checks for framework-specific global objects
4. **Meta Tag Analysis**: Examines HTML meta tags for framework indicators

## Performance Monitoring

### Built-in Metrics

The renderer provides several performance metrics:

```python
# Access processing metrics
print(f"Processing time: {result.processing_time_sec}s")
print(f"Retry count: {result.retry_count}")
print(f"Timestamp: {result.timestamp}")
```

### Memory Management

```python
# Configure memory limits
config = {
    "performance": {
        "memory_limit_mb": 4096,
        "cleanup_interval": 100
    }
}
```

## Error Recovery

### Automatic Retry

The tool automatically retries failed requests with configurable parameters:

```python
retry_config = {
    "max_retries": 3,
    "retry_delay": 2.0,
    "backoff_factor": 1.5,
    "retry_on_errors": [
        "DNS_ERROR",
        "CONNECTION_ERROR", 
        "TIMEOUT_ERROR"
    ]
}
```

### Resume Processing

```python
# Resume from existing results file
renderer = WebsiteRenderer()
existing_results = pd.read_csv("partial_results.csv")
processed_urls = set(existing_results['url'].tolist())

# Filter out already processed URLs
remaining_urls = [url for url in all_urls if url not in processed_urls]
new_results = renderer.analyze_urls_batch(remaining_urls)
```

## Advanced Features

### Proxy Support

```python
proxy_config = {
    "proxy": {
        "http": "http://proxy.example.com:8080",
        "https": "https://proxy.example.com:8080",
        "rotation": True
    }
}
```

### Custom User Agents

```python
user_agent_config = {
    "browser": {
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ],
        "rotation": True
    }
}
```

### Screenshot Capture

```python
screenshot_config = {
    "output": {
        "capture_screenshots": True,
        "screenshot_dir": "./screenshots/",
        "screenshot_format": "png"
    }
}
```

## Integration Examples

### Django Integration

```python
from django.http import JsonResponse
from src.website_renderer import WebsiteRenderer

def analyze_website(request):
    url = request.GET.get('url')
    
    renderer = WebsiteRenderer()
    result = renderer.analyze_url(url)
    
    return JsonResponse({
        'url': result.url,
        'rendering_type': result.rendering_type.value,
        'frameworks': result.frameworks,
        'success': result.status.value == 'SUCCESS'
    })
```

### Flask Integration

```python
from flask import Flask, request, jsonify
from src.website_renderer import WebsiteRenderer

app = Flask(__name__)
renderer = WebsiteRenderer()

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    url = data.get('url')
    
    result = renderer.analyze_url(url)
    
    return jsonify({
        'url': result.url,
        'type': result.rendering_type.value,
        'frameworks': result.frameworks
    })
```

### Celery Integration

```python
from celery import Celery
from src.website_renderer import WebsiteRenderer

app = Celery('csr_scanner')

@app.task
def analyze_url_task(url):
    renderer = WebsiteRenderer()
    result = renderer.analyze_url(url)
    
    return {
        'url': result.url,
        'type': result.rendering_type.value,
        'frameworks': result.frameworks,
        'processing_time': result.processing_time_sec
    }
```