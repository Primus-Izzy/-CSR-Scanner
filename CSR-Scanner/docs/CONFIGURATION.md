# Configuration Guide

This guide provides detailed information about configuring CSR Scanner for optimal performance and customization.

## Configuration Methods

CSR Scanner supports multiple configuration methods, listed in order of precedence:

1. **Command Line Arguments** (highest priority)
2. **Environment Variables**
3. **Configuration Files** (JSON)
4. **Default Values** (lowest priority)

## Command Line Configuration

### Basic Options

```bash
python src/run_analysis.py input.csv [OPTIONS]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `input_file` | str | required | Path to input CSV file |
| `--output` | str | `rendering_results.csv` | Output file path |
| `--config-file` | str | None | JSON configuration file path |

### Performance Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--workers` | int | 10 | Number of concurrent workers |
| `--chunk-size` | int | 50 | URLs processed per chunk |
| `--timeout` | int | 30 | Request timeout (seconds) |
| `--browser-timeout` | int | 25 | Browser timeout (seconds) |
| `--save-interval` | int | 10 | Save progress every N chunks |
| `--max-retries` | int | 2 | Maximum retry attempts |
| `--memory-limit` | int | 4096 | Memory limit in MB |

### Browser Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--headless` | bool | True | Run browser in headless mode |
| `--disable-images` | bool | True | Disable image loading |
| `--disable-css` | bool | False | Disable CSS loading |
| `--user-agent-rotation` | bool | True | Rotate user agents |
| `--window-width` | int | 1920 | Browser window width |
| `--window-height` | int | 1080 | Browser window height |

### Detection Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--wait-time` | float | 5.0 | Wait time for page load |
| `--framework-detection` | bool | True | Enable framework detection |
| `--scroll-detection` | bool | True | Enable scroll-based detection |
| `--content-change-detection` | bool | True | Detect content changes |
| `--min-content-length` | int | 100 | Minimum content length |

### Logging Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--verbose` | bool | False | Enable verbose logging |
| `--debug` | bool | False | Enable debug mode |
| `--log-file` | str | None | Log file path |
| `--log-level` | str | INFO | Log level (DEBUG, INFO, WARNING, ERROR) |

## Environment Variables

Set environment variables to configure default behavior:

### Browser Configuration
```bash
# Browser binary and driver paths
export CHROME_BINARY_PATH="/usr/bin/google-chrome"
export CHROME_DRIVER_PATH="/usr/local/bin/chromedriver"
export BROWSER_HEADLESS="true"

# Window settings
export WINDOW_WIDTH="1920"
export WINDOW_HEIGHT="1080"
```

### Performance Settings
```bash
# Concurrency and timeouts
export DEFAULT_WORKERS="10"
export DEFAULT_TIMEOUT="30"
export DEFAULT_CHUNK_SIZE="50"
export MAX_MEMORY_MB="4096"

# Retry settings
export MAX_RETRIES="2"
export RETRY_DELAY="1.0"
export SAVE_INTERVAL="10"
```

### Detection Settings
```bash
# Feature flags
export FRAMEWORK_DETECTION="true"
export SCROLL_DETECTION="true"
export CONTENT_CHANGE_DETECTION="true"

# Timing settings
export WAIT_TIME="5.0"
export FRAMEWORK_TIMEOUT="10.0"
```

### Network Settings
```bash
# Proxy configuration
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1"

# User agent settings
export USER_AGENT_ROTATION="true"
export CUSTOM_USER_AGENT="CSR-Scanner/1.0"
```

### Output Settings
```bash
# File paths and formats
export DEFAULT_OUTPUT_DIR="./results"
export ENABLE_BACKUPS="true"
export COMPRESSION="false"

# Screenshot settings
export CAPTURE_SCREENSHOTS="false"
export SCREENSHOT_DIR="./screenshots"
export SCREENSHOT_FORMAT="png"
```

### Logging Configuration
```bash
# Log settings
export LOG_LEVEL="INFO"
export LOG_FILE="csr_scanner.log"
export ENABLE_CONSOLE_LOGGING="true"
export LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## JSON Configuration Files

Create detailed configuration files in JSON format:

### Complete Configuration Example

```json
{
  "browser": {
    "headless": true,
    "binary_path": null,
    "driver_path": null,
    "disable_images": true,
    "disable_css": false,
    "disable_javascript": false,
    "user_agent_rotation": true,
    "custom_user_agent": null,
    "window_size": {
      "width": 1920,
      "height": 1080
    },
    "chrome_options": [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--disable-extensions",
      "--disable-plugins",
      "--disable-images",
      "--disable-javascript",
      "--memory-pressure-off"
    ],
    "prefs": {
      "profile.default_content_setting_values.notifications": 2,
      "profile.default_content_settings.popups": 0,
      "profile.managed_default_content_settings.images": 2
    }
  },
  "performance": {
    "workers": 10,
    "chunk_size": 50,
    "timeout": 30,
    "browser_timeout": 25,
    "save_interval": 10,
    "max_retries": 2,
    "retry_delay": 1.0,
    "backoff_factor": 1.5,
    "memory_limit_mb": 4096,
    "cpu_limit_percent": 90,
    "delay_between_requests": 0.1,
    "max_concurrent_browsers": 20
  },
  "detection": {
    "wait_time": 5.0,
    "framework_timeout": 10.0,
    "scroll_detection": true,
    "framework_detection": true,
    "dom_analysis": true,
    "javascript_execution_detection": true,
    "content_change_detection": true,
    "minimum_content_length": 100,
    "scroll_pause_time": 1.0,
    "max_scroll_attempts": 3,
    "framework_patterns": {
      "react": [
        "React",
        "_reactRootContainer",
        "__REACT_DEVTOOLS_GLOBAL_HOOK__"
      ],
      "vue": [
        "Vue",
        "__VUE__",
        "_isVue"
      ],
      "angular": [
        "ng-version",
        "getAllAngularRootElements",
        "angular"
      ]
    }
  },
  "output": {
    "format": "csv",
    "compression": false,
    "include_screenshots": false,
    "include_html_snapshots": false,
    "include_network_logs": false,
    "detailed_errors": true,
    "screenshot_settings": {
      "enabled": false,
      "directory": "./screenshots",
      "format": "png",
      "quality": 90,
      "full_page": false
    }
  },
  "logging": {
    "level": "INFO",
    "file": null,
    "console": true,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "rotation": {
      "enabled": false,
      "max_bytes": 10485760,
      "backup_count": 5
    }
  },
  "network": {
    "proxy": {
      "enabled": false,
      "http": null,
      "https": null,
      "rotation": false,
      "proxy_list": []
    },
    "ssl": {
      "verify": false,
      "cert_file": null,
      "key_file": null
    },
    "headers": {
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.5",
      "Accept-Encoding": "gzip, deflate",
      "DNT": "1",
      "Connection": "keep-alive"
    }
  }
}
```

### Minimal Configuration Example

```json
{
  "performance": {
    "workers": 5,
    "timeout": 60
  },
  "browser": {
    "headless": false,
    "disable_images": false
  },
  "detection": {
    "wait_time": 10,
    "framework_detection": false
  }
}
```

## Configuration Profiles

### Development Profile

Optimized for debugging and development:

```json
{
  "browser": {
    "headless": false,
    "disable_images": false,
    "disable_css": false,
    "chrome_options": [
      "--start-maximized",
      "--disable-web-security"
    ]
  },
  "performance": {
    "workers": 1,
    "timeout": 120,
    "max_retries": 0
  },
  "detection": {
    "wait_time": 10,
    "scroll_detection": true
  },
  "logging": {
    "level": "DEBUG",
    "console": true,
    "file": "debug.log"
  }
}
```

### Production Profile

Optimized for high-performance processing:

```json
{
  "browser": {
    "headless": true,
    "disable_images": true,
    "disable_css": true,
    "chrome_options": [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--memory-pressure-off"
    ]
  },
  "performance": {
    "workers": 20,
    "chunk_size": 100,
    "timeout": 15,
    "save_interval": 5,
    "memory_limit_mb": 8192
  },
  "detection": {
    "wait_time": 3,
    "framework_detection": true,
    "scroll_detection": false
  },
  "logging": {
    "level": "WARNING",
    "console": false,
    "file": "production.log"
  }
}
```

### Memory-Optimized Profile

For systems with limited RAM:

```json
{
  "browser": {
    "headless": true,
    "disable_images": true,
    "disable_css": true,
    "chrome_options": [
      "--memory-pressure-off",
      "--max_old_space_size=512",
      "--single-process"
    ]
  },
  "performance": {
    "workers": 3,
    "chunk_size": 10,
    "memory_limit_mb": 1024,
    "save_interval": 2
  },
  "detection": {
    "wait_time": 2,
    "framework_detection": false
  }
}
```

## Advanced Configuration

### Custom Framework Detection

Add custom framework detection patterns:

```json
{
  "detection": {
    "framework_patterns": {
      "custom_framework": [
        "CustomFramework",
        "__CUSTOM_FW__",
        "window.CustomFramework"
      ],
      "htmx": [
        "htmx",
        "hx-get",
        "_hyperscript"
      ]
    }
  }
}
```

### Proxy Configuration

Configure proxy settings for corporate environments:

```json
{
  "network": {
    "proxy": {
      "enabled": true,
      "http": "http://proxy.company.com:8080",
      "https": "http://proxy.company.com:8080",
      "rotation": true,
      "proxy_list": [
        "http://proxy1.company.com:8080",
        "http://proxy2.company.com:8080",
        "http://proxy3.company.com:8080"
      ]
    }
  }
}
```

### Custom Headers

Set custom HTTP headers:

```json
{
  "network": {
    "headers": {
      "User-Agent": "CSR-Scanner/1.0",
      "Accept": "text/html,application/xhtml+xml",
      "Accept-Language": "en-US,en;q=0.9",
      "Accept-Encoding": "gzip, deflate, br",
      "Cache-Control": "no-cache",
      "X-Custom-Header": "custom-value"
    }
  }
}
```

## Configuration Validation

Validate your configuration file:

```bash
python -c "
import json
import sys

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    print('✅ Configuration is valid JSON')
    
    # Basic validation
    required_sections = ['browser', 'performance', 'detection']
    for section in required_sections:
        if section in config:
            print(f'✅ {section} section found')
        else:
            print(f'⚠️  {section} section missing (will use defaults)')
            
except json.JSONDecodeError as e:
    print(f'❌ Invalid JSON: {e}')
    sys.exit(1)
except FileNotFoundError:
    print('❌ Configuration file not found')
    sys.exit(1)
"
```

## Performance Tuning

### CPU-Intensive Workloads

```json
{
  "performance": {
    "workers": 16,
    "chunk_size": 25,
    "timeout": 20,
    "cpu_limit_percent": 85,
    "delay_between_requests": 0.05
  }
}
```

### Network-Bound Workloads

```json
{
  "performance": {
    "workers": 30,
    "chunk_size": 100,
    "timeout": 45,
    "delay_between_requests": 0,
    "max_concurrent_browsers": 50
  }
}
```

### Memory-Bound Workloads

```json
{
  "performance": {
    "workers": 8,
    "chunk_size": 20,
    "memory_limit_mb": 2048,
    "save_interval": 1,
    "cleanup_interval": 50
  }
}
```

## Configuration Best Practices

### 1. Start with Defaults

Begin with default settings and adjust based on performance:

```bash
# Test with defaults first
python src/run_analysis.py sample.csv --output test.csv

# Then optimize
python src/run_analysis.py sample.csv --workers 15 --timeout 20
```

### 2. Monitor Resource Usage

Use system monitoring to guide configuration:

```bash
# Monitor during processing
htop  # or Task Manager on Windows

# Adjust workers based on CPU usage
# Adjust memory limit based on RAM usage
```

### 3. Test with Small Datasets

Validate configuration with small batches:

```bash
# Create test dataset
head -20 large_input.csv > test_input.csv

# Test configuration
python src/run_analysis.py test_input.csv --config-file config.json
```

### 4. Use Environment-Specific Profiles

```bash
# Development
python src/run_analysis.py input.csv --config-file dev_config.json

# Production
python src/run_analysis.py input.csv --config-file prod_config.json

# Testing
python src/run_analysis.py input.csv --config-file test_config.json
```

### 5. Version Control Configuration

Keep configuration files in version control:

```
configs/
├── development.json
├── production.json
├── testing.json
└── local.json  # .gitignore this file
```

## Configuration Migration

### From Command Line to Config File

Convert command line arguments to JSON configuration:

```bash
# Command line
python src/run_analysis.py input.csv --workers 15 --timeout 25 --verbose

# Equivalent JSON
{
  "performance": {
    "workers": 15,
    "timeout": 25
  },
  "logging": {
    "level": "DEBUG",
    "console": true
  }
}
```

### Updating Configuration

When updating CSR Scanner, check for new configuration options:

1. Review the changelog
2. Check example configurations
3. Validate existing configurations
4. Test with updated settings

## Troubleshooting Configuration

### Common Configuration Errors

1. **Invalid JSON syntax**:
   ```bash
   python -m json.tool config.json
   ```

2. **Missing required values**:
   - Check logs for "Configuration Error" messages
   - Ensure all paths are absolute
   - Verify numeric values are within valid ranges

3. **Performance issues**:
   - Start with conservative settings
   - Gradually increase workers and chunk size
   - Monitor system resources

### Configuration Debugging

Enable configuration debugging:

```json
{
  "logging": {
    "level": "DEBUG",
    "console": true
  },
  "debug": {
    "log_configuration": true,
    "validate_settings": true
  }
}
```

This will log the final merged configuration at startup, helping identify configuration issues.