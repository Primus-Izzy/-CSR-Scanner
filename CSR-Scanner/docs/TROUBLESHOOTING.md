# Troubleshooting Guide

This guide covers common issues and their solutions when using CSR Scanner.

## Installation Issues

### ChromeDriver Problems

#### Problem: ChromeDriver not found or incompatible version
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solutions:**

1. **Auto-installation (Recommended)**:
   ```python
   # The tool automatically installs compatible ChromeDriver
   # If this fails, try manual installation
   ```

2. **Manual ChromeDriver installation**:
   ```bash
   # Download ChromeDriver from https://chromedriver.chromium.org/
   # Place it in your PATH or specify location:
   export CHROME_DRIVER_PATH=/path/to/chromedriver
   ```

3. **Using webdriver-manager**:
   ```bash
   pip install webdriver-manager
   ```

#### Problem: Chrome browser not found
```
selenium.common.exceptions.WebDriverException: Message: unknown error: cannot find Chrome binary
```

**Solutions:**

1. **Install Chrome browser**:
   - Download from https://www.google.com/chrome/
   - Ensure Chrome is installed in default location

2. **Specify Chrome binary path**:
   ```bash
   export CHROME_BINARY_PATH=/path/to/chrome
   ```

3. **Use Chromium instead**:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install chromium-browser
   
   # On macOS with Homebrew
   brew install --cask chromium
   ```

### Python Dependency Issues

#### Problem: Package installation failures
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solutions:**

1. **Update pip**:
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Use virtual environment**:
   ```bash
   python -m venv csr-scanner-env
   source csr-scanner-env/bin/activate  # Linux/macOS
   # or
   csr-scanner-env\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Install with --user flag**:
   ```bash
   pip install --user -r requirements.txt
   ```

#### Problem: Selenium version conflicts
```
ImportError: cannot import name 'webdriver' from 'selenium'
```

**Solution:**
```bash
pip uninstall selenium
pip install selenium==4.7.2
```

## Runtime Issues

### Memory Problems

#### Problem: Out of memory errors
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. **Reduce concurrent workers**:
   ```bash
   python src/run_analysis.py input.csv --workers 5
   ```

2. **Decrease chunk size**:
   ```bash
   python src/run_analysis.py input.csv --chunk-size 25
   ```

3. **Enable memory optimization**:
   ```bash
   python src/run_analysis.py input.csv --optimize-memory
   ```

4. **Monitor memory usage**:
   ```bash
   # On Linux/macOS
   htop
   
   # On Windows
   tasklist /fi "imagename eq python.exe"
   ```

### Network Issues

#### Problem: DNS resolution failures
```
DNSError: HTTPConnectionPool(host='example.com', port=80): Max retries exceeded
```

**Solutions:**

1. **Check internet connection**:
   ```bash
   ping google.com
   ```

2. **Configure DNS servers**:
   ```bash
   # Use Google DNS
   # Linux: Edit /etc/resolv.conf
   nameserver 8.8.8.8
   nameserver 8.8.4.4
   ```

3. **Use proxy if behind corporate firewall**:
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

#### Problem: Connection timeouts
```
TimeoutError: Request timed out after 30 seconds
```

**Solutions:**

1. **Increase timeout**:
   ```bash
   python src/run_analysis.py input.csv --timeout 60
   ```

2. **Reduce concurrent connections**:
   ```bash
   python src/run_analysis.py input.csv --workers 5
   ```

3. **Check network latency**:
   ```bash
   ping -c 4 target-website.com
   ```

### Browser Issues

#### Problem: Browser crashes frequently
```
selenium.common.exceptions.WebDriverException: Message: unknown error: Chrome failed to start
```

**Solutions:**

1. **Enable headless mode**:
   ```bash
   python src/run_analysis.py input.csv --headless
   ```

2. **Increase browser memory**:
   ```bash
   # Add Chrome arguments in config
   "chrome_options": [
       "--memory-pressure-off",
       "--max_old_space_size=4096"
   ]
   ```

3. **Disable extensions**:
   ```bash
   "chrome_options": [
       "--disable-extensions",
       "--disable-plugins"
   ]
   ```

#### Problem: Browser automation detected
```
selenium.common.exceptions.WebDriverException: Message: unknown error: cannot determine loading status
```

**Solutions:**

1. **Use undetected ChromeDriver**:
   ```python
   # This is already included in the tool
   import undetected_chromedriver as uc
   ```

2. **Enable user agent rotation**:
   ```bash
   python src/run_analysis.py input.csv --rotate-user-agents
   ```

3. **Add random delays**:
   ```python
   config = {
       "browser": {
           "human_like_delays": True,
           "random_delay_range": [1, 3]
       }
   }
   ```

## Performance Issues

### Slow Processing Speed

#### Problem: Processing is slower than expected

**Diagnostic steps:**

1. **Check system resources**:
   ```bash
   # CPU usage
   top  # Linux/macOS
   wmic cpu get loadpercentage /value  # Windows
   
   # Memory usage
   free -h  # Linux
   vm_stat  # macOS
   wmic computersystem get TotalPhysicalMemory /value  # Windows
   ```

2. **Monitor network bandwidth**:
   ```bash
   # Install and use iftop, nload, or similar tools
   iftop -i eth0
   ```

**Solutions:**

1. **Optimize worker count**:
   ```bash
   # Start with CPU core count
   python src/run_analysis.py input.csv --workers 8
   ```

2. **Tune timeouts**:
   ```bash
   # Reduce timeout for faster processing
   python src/run_analysis.py input.csv --timeout 15
   ```

3. **Disable unnecessary features**:
   ```bash
   python src/run_analysis.py input.csv --disable-images --disable-css
   ```

4. **Use SSD storage**:
   - Ensure output files are written to SSD
   - Use fast storage for Chrome cache

### High CPU Usage

#### Problem: 100% CPU usage for extended periods

**Solutions:**

1. **Reduce worker count**:
   ```bash
   python src/run_analysis.py input.csv --workers 4
   ```

2. **Add processing delays**:
   ```python
   config = {
       "performance": {
           "delay_between_requests": 0.5
       }
   }
   ```

3. **Enable CPU throttling**:
   ```python
   config = {
       "performance": {
           "cpu_limit_percent": 80
       }
   }
   ```

## Data Issues

### Invalid Input Data

#### Problem: CSV parsing errors
```
pandas.errors.ParserError: Error tokenizing data
```

**Solutions:**

1. **Check CSV format**:
   ```bash
   head -5 input.csv
   # Should show proper CSV headers
   ```

2. **Fix CSV encoding**:
   ```python
   import pandas as pd
   df = pd.read_csv('input.csv', encoding='utf-8')
   df.to_csv('fixed_input.csv', index=False, encoding='utf-8')
   ```

3. **Validate URLs**:
   ```python
   import pandas as pd
   from urllib.parse import urlparse
   
   df = pd.read_csv('input.csv')
   valid_urls = []
   
   for url in df['url']:
       try:
           result = urlparse(str(url))
           if result.scheme and result.netloc:
               valid_urls.append(url)
       except:
           pass
   
   valid_df = pd.DataFrame({'url': valid_urls})
   valid_df.to_csv('valid_input.csv', index=False)
   ```

### Output Issues

#### Problem: Incomplete or corrupted output files
```
pandas.errors.EmptyDataError: No columns to parse from file
```

**Solutions:**

1. **Check disk space**:
   ```bash
   df -h  # Linux/macOS
   dir  # Windows
   ```

2. **Verify write permissions**:
   ```bash
   touch test_output.csv  # Linux/macOS
   echo. > test_output.csv  # Windows
   ```

3. **Use absolute paths**:
   ```bash
   python src/run_analysis.py input.csv --output /full/path/to/results.csv
   ```

4. **Enable backup files**:
   ```bash
   python src/run_analysis.py input.csv --enable-backups
   ```

## Debug Mode

### Enable Debug Mode

For detailed troubleshooting, enable debug mode:

```bash
python src/run_analysis.py input.csv --debug --verbose --log-file debug.log
```

This will provide:
- Detailed error messages
- Processing timestamps
- Memory usage information
- Network request details
- Browser console logs

### Log Analysis

Check log files for specific errors:

```bash
# Search for errors
grep -i error debug.log

# Check memory issues
grep -i "memory" debug.log

# Look for timeout issues
grep -i "timeout" debug.log
```

## Platform-Specific Issues

### Windows Issues

#### Problem: Path length limitations
```
OSError: [Errno 2] No such file or directory
```

**Solution:**
```bash
# Enable long path support in Windows 10/11
# Or use shorter directory names
```

#### Problem: Antivirus interference
```
PermissionError: [WinError 5] Access is denied
```

**Solution:**
- Add Python and Chrome to antivirus exceptions
- Use Windows Defender exclusions

### macOS Issues

#### Problem: Gatekeeper blocking ChromeDriver
```
cannot be opened because the developer cannot be verified
```

**Solution:**
```bash
# Allow ChromeDriver
sudo xattr -r -d com.apple.quarantine /path/to/chromedriver
```

### Linux Issues

#### Problem: Missing system dependencies
```
ImportError: libgtk-3.so.0: cannot open shared object file
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install -y libnss3-dev libgconf-2-4 libxss1 libappindicator1 libindicator7

# CentOS/RHEL
sudo yum install -y liberation-fonts
```

## Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Enable debug mode** and review logs
3. **Test with a small dataset** (5-10 URLs)
4. **Check system requirements** and dependencies
5. **Update to latest version**

### Providing Debug Information

When reporting issues, include:

1. **System information**:
   ```bash
   python --version
   pip list | grep selenium
   google-chrome --version  # or chromium --version
   ```

2. **Error messages** (full stack trace)

3. **Configuration used**

4. **Sample URLs** that cause issues

5. **Log files** (with debug enabled)

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share experiences  
- **Documentation**: Comprehensive guides and examples

## Performance Optimization

### Quick Performance Checklist

- [ ] Use appropriate worker count (CPU cores × 1.5)
- [ ] Optimize timeout values for your network
- [ ] Enable headless mode for production
- [ ] Disable images/CSS if not needed for detection
- [ ] Use SSD storage for better I/O performance
- [ ] Monitor system resources during processing
- [ ] Use batch processing for large datasets
- [ ] Enable memory optimization for large jobs