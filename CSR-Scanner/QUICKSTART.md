# Quick Start Guide

Get up and running with CSR Scanner in 5 minutes!

## 1. Installation

### Prerequisites
- Python 3.8 or higher
- Chrome/Chromium browser
- 2GB+ RAM available

### Install CSR Scanner

```bash
# Clone the repository
git clone https://github.com/Primus-Izzy/CSR-Scanner.git
cd CSR-Scanner

# Create virtual environment (recommended)
python -m venv csr-scanner-env
source csr-scanner-env/bin/activate  # Linux/macOS
# or
csr-scanner-env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## 2. Basic Usage

### Create Input File

Create a CSV file with websites to analyze:

```bash
# Create sample input file
echo "url" > my_websites.csv
echo "https://react.dev" >> my_websites.csv
echo "https://vuejs.org" >> my_websites.csv  
echo "https://angular.io" >> my_websites.csv
echo "https://github.com" >> my_websites.csv
echo "https://stackoverflow.com" >> my_websites.csv
```

### Run Analysis

```bash
# Basic analysis
python src/run_analysis.py my_websites.csv --output results.csv

# With custom settings
python src/run_analysis.py my_websites.csv \
  --output results.csv \
  --workers 5 \
  --timeout 30 \
  --verbose
```

### View Results

```bash
# View results in terminal
head -10 results.csv

# Or open in spreadsheet application
```

Expected output columns:
- `url`: Original URL
- `final_url`: Final URL after redirects  
- `rendering_type`: CSR, SSR, or Not Accessible
- `status`: Success/Failed
- `processing_time_sec`: Processing time
- `frameworks`: Detected JS frameworks
- `http_status_code`: HTTP response code

## 3. Common Use Cases

### High-Performance Processing

For large datasets (1000+ URLs):

```bash
python src/run_analysis.py large_dataset.csv \
  --output large_results.csv \
  --workers 15 \
  --chunk-size 100 \
  --timeout 20 \
  --save-interval 5
```

### Debug Mode

For troubleshooting issues:

```bash  
python src/run_analysis.py my_websites.csv \
  --output debug_results.csv \
  --debug \
  --verbose \
  --headless false \
  --max-retries 1
```

### Resource-Constrained Systems

For systems with limited RAM/CPU:

```bash
python src/run_analysis.py my_websites.csv \
  --output constrained_results.csv \
  --workers 3 \
  --chunk-size 10 \
  --timeout 45
```

## 4. Configuration File

For repeated use, create a configuration file:

```json
{
  "performance": {
    "workers": 10,
    "timeout": 25,
    "chunk_size": 50
  },
  "browser": {
    "headless": true,
    "disable_images": true
  },
  "detection": {
    "wait_time": 5,
    "framework_detection": true
  }
}
```

Use with:
```bash
python src/run_analysis.py my_websites.csv --config-file config.json
```

## 5. Understanding Results

### Rendering Types

- **Client-Side Rendered (CSR)**: JavaScript frameworks render content dynamically
- **Server-Side Rendered (SSR)**: Content is pre-rendered on the server
- **Not Accessible**: Site couldn't be reached or analyzed

### Framework Detection

Common frameworks detected:
- React, Vue.js, Angular, Svelte
- Next.js, Nuxt.js, Gatsby
- jQuery, Backbone.js, Ember.js

### Status Codes

- **200**: Successful analysis
- **404**: Page not found
- **500**: Server error
- **0**: Connection/DNS issues

## 6. Performance Tips

### Optimize Workers

Start with CPU core count and adjust:
```bash
# Check CPU cores
python -c "import os; print(f'CPU cores: {os.cpu_count()}')"

# Use cores × 1.5 for workers
python src/run_analysis.py input.csv --workers 12  # for 8-core system
```

### Monitor Resources

While processing, monitor system resources:
```bash
# Linux/macOS
htop

# Windows  
tasklist /fi "imagename eq python.exe"
```

### Batch Processing

For very large datasets, use batch processing:
```bash
# Split large file into batches
python examples/batch_processing.py --input large_file.csv --batch-size 5000
```

## 7. Troubleshooting

### ChromeDriver Issues
```bash
# ChromeDriver will auto-install, but if issues occur:
pip install webdriver-manager --upgrade
```

### Memory Issues
```bash
# Reduce workers and chunk size
python src/run_analysis.py input.csv --workers 3 --chunk-size 15
```

### Network Issues
```bash
# Increase timeout for slow networks
python src/run_analysis.py input.csv --timeout 60
```

### Permission Issues
```bash
# Ensure write permissions for output directory
mkdir -p results/
chmod 755 results/
```

## 8. Next Steps

### Advanced Configuration
- Read [CONFIGURATION.md](docs/CONFIGURATION.md) for detailed options
- See [examples/](examples/) for advanced usage patterns

### API Usage
- Check [docs/API.md](docs/API.md) for programmatic usage
- Integrate with your Python applications

### Performance Tuning  
- Review [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Optimize settings for your specific use case

### Contributing
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Report issues on GitHub

## Sample Output

```csv
url,final_url,rendering_type,status,processing_time_sec,timestamp,frameworks,error_category,error_message,retry_count,http_status_code
https://react.dev,https://react.dev/,Client-Side Rendered,Success,3.45,2025-01-15T10:30:15.123456,React,,,,200
https://github.com,https://github.com/,Server-Side Rendered,Success,2.18,2025-01-15T10:30:18.234567,,,,,200
https://vuejs.org,https://vuejs.org/,Client-Side Rendered,Success,4.12,2025-01-15T10:30:22.345678,Vue.js,,,,200
```

## Support

- **Documentation**: Check the `docs/` directory
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub Discussions for questions
- **Examples**: See `examples/` directory for more usage patterns

Happy analyzing! 🚀