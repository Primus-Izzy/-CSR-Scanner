# Contributing to CSR Scanner

Thank you for your interest in contributing to CSR Scanner! This document provides guidelines and information for contributors.

## Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/Primus-Izzy/CSR-Scanner.git
   cd CSR-Scanner
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv csr-scanner-dev
   source csr-scanner-dev/bin/activate  # Linux/macOS
   # or
   csr-scanner-dev\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Verify Installation**
   ```bash
   python src/run_analysis.py examples/sample_input.csv --output test_output.csv
   ```

### Development Dependencies

Create `requirements-dev.txt` for development tools:

```
pytest>=6.0
pytest-cov>=2.0
pytest-mock>=3.6
black>=21.0
flake8>=3.8
mypy>=0.800
isort>=5.0
pre-commit>=2.15
sphinx>=4.0
sphinx-rtd-theme>=0.5
```

## Code Standards

### Code Style

We use Black for code formatting and follow PEP 8 standards:

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/
```

### Type Hints

Use type hints for better code documentation and IDE support:

```python
from typing import List, Dict, Optional, Union
from src.models import ProcessingResult

def analyze_urls(urls: List[str], config: Optional[Dict] = None) -> List[ProcessingResult]:
    """Analyze multiple URLs and return results."""
    pass
```

### Documentation Strings

Use comprehensive docstrings:

```python
def analyze_url(self, url: str, timeout: Optional[int] = None) -> ProcessingResult:
    """
    Analyze a single URL to determine rendering type.
    
    Args:
        url: The URL to analyze
        timeout: Optional timeout override in seconds
        
    Returns:
        ProcessingResult containing analysis details
        
    Raises:
        ValueError: If URL is invalid
        TimeoutError: If analysis times out
        
    Example:
        >>> renderer = WebsiteRenderer()
        >>> result = renderer.analyze_url("https://example.com")
        >>> print(result.rendering_type)
        RenderingType.SERVER_SIDE_RENDERED
    """
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_renderer.py

# Run with verbose output
pytest -v
```

### Writing Tests

Create comprehensive tests for new features:

```python
# tests/test_new_feature.py
import pytest
from src.website_renderer import WebsiteRenderer
from src.models import RenderingType

class TestNewFeature:
    def setup_method(self):
        """Setup for each test method."""
        self.renderer = WebsiteRenderer()
    
    def test_feature_success(self):
        """Test successful feature operation."""
        # Arrange
        url = "https://example.com"
        
        # Act
        result = self.renderer.analyze_url(url)
        
        # Assert
        assert result.status == ProcessingStatus.SUCCESS
        assert result.url == url
    
    @pytest.mark.parametrize("url,expected_type", [
        ("https://react-app.com", RenderingType.CLIENT_SIDE_RENDERED),
        ("https://static-site.com", RenderingType.SERVER_SIDE_RENDERED),
    ])
    def test_rendering_detection(self, url, expected_type):
        """Test rendering type detection for various sites."""
        result = self.renderer.analyze_url(url)
        assert result.rendering_type == expected_type
```

### Test Coverage

Maintain high test coverage (>90%):

- Unit tests for core functionality
- Integration tests for end-to-end workflows
- Performance tests for optimization validation
- Edge case tests for error handling

## Contribution Types

### Bug Fixes

1. **Create Issue**: Describe the bug with reproduction steps
2. **Write Test**: Create a failing test that reproduces the bug
3. **Fix Bug**: Implement the fix
4. **Verify**: Ensure the test passes and no regressions occur

### New Features

1. **Discuss First**: Create an issue to discuss the feature
2. **Design**: Plan the implementation approach
3. **Implement**: Write code following our standards
4. **Test**: Add comprehensive tests
5. **Document**: Update relevant documentation

### Documentation Improvements

- Fix typos and grammar
- Add examples and clarifications
- Update configuration guides
- Improve API documentation

### Performance Optimizations

1. **Benchmark**: Establish baseline performance
2. **Profile**: Identify bottlenecks
3. **Optimize**: Implement improvements
4. **Measure**: Verify performance gains
5. **Test**: Ensure no functionality regressions

## Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
   ```bash
   pytest
   ```

2. **Check Code Quality**: 
   ```bash
   black --check src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

3. **Update Documentation**: Update relevant docs and examples

4. **Test Manually**: Test your changes with real data

### PR Guidelines

1. **Clear Title**: Use descriptive titles
   - ✅ "Add support for Vue.js framework detection"
   - ❌ "Fix stuff"

2. **Detailed Description**: Include:
   - What changes were made
   - Why the changes were necessary
   - How to test the changes
   - Any breaking changes

3. **Link Issues**: Reference related issues with "Fixes #123"

4. **Small PRs**: Keep PRs focused and reasonably sized

### PR Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing with sample data

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

## Code Review Process

### For Contributors

- Respond to feedback promptly
- Make requested changes in new commits (don't force push)
- Ask questions if feedback is unclear
- Be open to suggestions and improvements

### For Reviewers

- Be constructive and specific in feedback
- Explain the "why" behind suggestions
- Approve when code meets standards
- Request changes when necessary improvements are needed

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes (2.0.0)
- **Minor**: New features, backward compatible (1.1.0)
- **Patch**: Bug fixes, backward compatible (1.0.1)

### Changelog

Update `CHANGELOG.md` with:

```markdown
## [1.1.0] - 2024-01-15

### Added
- Support for Vue.js framework detection
- New configuration options for timeout handling

### Changed
- Improved error handling for network timeouts
- Updated default browser timeout to 25 seconds

### Fixed
- Fixed issue with CSS detection on certain sites
- Resolved memory leak in batch processing

### Deprecated
- Old configuration format (will be removed in 2.0.0)
```

## Development Workflow

### Branch Naming

Use descriptive branch names:

- `feature/vue-js-detection`
- `bugfix/memory-leak-batch-processing`
- `docs/api-documentation-update`
- `perf/optimize-dom-analysis`

### Commit Messages

Write clear commit messages:

```
feat: add Vue.js framework detection

- Add detection patterns for Vue.js applications
- Include support for Vue 2 and Vue 3
- Add tests for Vue.js detection scenarios

Closes #123
```

### Pre-commit Hooks

Set up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: local
    hooks:
      - id: tests
        name: tests
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Code Review**: Direct feedback on pull requests

### Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Testing with pytest](https://docs.pytest.org/)

## Recognition

Contributors will be:

- Listed in the CONTRIBUTORS.md file
- Mentioned in release notes for significant contributions
- Given credit in documentation updates

Thank you for contributing to CSR Scanner! 🎉