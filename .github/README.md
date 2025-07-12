# CI/CD Pipeline Documentation

This directory contains the continuous integration and continuous deployment (CI/CD) configuration for the OctoPrint Filament Motion Sensor Plugin.

## 🔄 Workflows

### 1. Pull Request Check (`pr-check.yml`)
**Triggers**: On pull request open, synchronize, or reopen  
**Purpose**: Fast validation of pull requests

#### What it does:
- ✅ Runs unit and integration tests
- ✅ Checks code coverage (minimum 80%)
- ✅ Validates code formatting (Black, isort)
- ✅ Runs linting (flake8)
- ✅ Performs security scanning (bandit, safety)
- ✅ Validates plugin imports
- ✅ Comments coverage report on PR

#### Status checks:
- **Tests**: Must pass (blocking)
- **Code Quality**: Non-blocking but reported

### 2. Test Suite (`test.yml`)
**Triggers**: On push to main/master, pull requests  
**Purpose**: Comprehensive testing across multiple environments

#### What it does:
- 🐍 Tests on Python 3.7, 3.8, 3.9, 3.10, 3.11
- 🖥️ Tests on Ubuntu, Windows, macOS
- 📊 Uploads coverage reports to Codecov/Codacy
- 🔒 Runs security scanning
- 📁 Archives test artifacts

#### Matrix Strategy:
```yaml
python-version: ["3.7", "3.8", "3.9", "3.10", "3.11"]
os: [ubuntu-latest, windows-latest, macos-latest]
```

### 3. Release (`release.yml`)
**Triggers**: On version tags (`v*`) or manual dispatch  
**Purpose**: Automated release process

#### What it does:
- ✅ Runs full test suite
- 📦 Builds distribution packages
- 🏷️ Creates GitHub releases
- 📋 Extracts release notes
- 📤 Uploads release assets

#### Triggering a release:
```bash
git tag v2.2.0
git push origin v2.2.0
```

## 🔧 Dependency Management

### Dependabot (`dependabot.yml`)
**Schedule**: Weekly on Mondays at 9:00 AM  
**Purpose**: Automatic dependency updates

#### Monitors:
- 🐍 Python dependencies (`pip`)
- ⚡ GitHub Actions versions
- 📝 Auto-assigns to @chrisns
- 🏷️ Labels: `dependencies`, `python`, `github-actions`

#### Settings:
- Maximum 10 Python PRs open
- Maximum 5 GitHub Actions PRs open
- Ignores major version updates for stable tools

## 🎯 Quality Gates

### Required Checks for PR Merge:
1. **Tests Pass**: All unit and integration tests must pass
2. **Coverage**: Minimum 80% code coverage required
3. **Import Validation**: Plugin must import without errors

### Optional Checks (Reported but Non-blocking):
1. **Code Formatting**: Black and isort compliance
2. **Linting**: flake8 compliance
3. **Security**: bandit and safety scans
4. **Type Checking**: mypy analysis

## 📊 Coverage Reports

### Automatic Coverage Reporting:
- 📝 **PR Comments**: Coverage diff commented on each PR
- 🌐 **Codecov**: Detailed coverage analysis
- 📈 **Codacy**: Code quality metrics
- 💾 **Artifacts**: HTML coverage reports archived

### Coverage Thresholds:
- 🟢 **Green**: ≥80% coverage
- 🟠 **Orange**: 70-79% coverage
- 🔴 **Red**: <70% coverage

## 🏃‍♂️ Running Tests Locally

### Quick Start:
```bash
# Install and run all tests
python run_tests.py --install

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type fast

# Run with linting
python run_tests.py --lint

# Generate coverage report
python run_tests.py --coverage-report
```

### Code Quality Tools:
```bash
# Format code
black octoprint_filamentmotionsensor/ tests/
isort octoprint_filamentmotionsensor/ tests/

# Check formatting
black --check octoprint_filamentmotionsensor/ tests/
isort --check-only octoprint_filamentmotionsensor/ tests/

# Lint code
flake8 octoprint_filamentmotionsensor/ tests/

# Type checking
mypy octoprint_filamentmotionsensor/

# Security scanning
bandit -r octoprint_filamentmotionsensor/
safety check
```

## 🔒 Security Features

### Automated Security Scanning:
- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- **Trivy**: Comprehensive vulnerability scanner
- **SARIF Reports**: Security findings uploaded to GitHub Security tab

### Security Workflow:
1. Scans run on every PR and push
2. Results uploaded to GitHub Security tab
3. Non-blocking but reported for review
4. Critical vulnerabilities flagged for immediate attention

## 🎨 Code Style

### Formatting Standards:
- **Line Length**: 120 characters
- **Code Style**: Black formatter
- **Import Sorting**: isort with Black profile
- **Linting**: flake8 with custom configuration

### Configuration Files:
- `.flake8`: Linting configuration
- `pyproject.toml`: Black, isort, mypy, coverage configuration
- `pytest.ini`: Test configuration (deprecated in favor of pyproject.toml)

## 📁 Artifacts and Reports

### Generated Artifacts:
- 📊 **Test Results**: JUnit XML format
- 📈 **Coverage Reports**: HTML and XML formats
- 🔒 **Security Reports**: JSON format
- 📦 **Build Artifacts**: Distribution packages

### Artifact Retention:
- **Test artifacts**: 30 days
- **Coverage reports**: 30 days
- **Security reports**: 90 days
- **Release builds**: Permanent

## 🚀 Performance Optimizations

### Caching Strategy:
- 📦 **pip cache**: Cached by Python version and requirements hash
- ⚡ **Fast execution**: Parallel job execution
- 🔄 **Smart updates**: Only rebuild when dependencies change

### Execution Times:
- **PR Check**: ~3-5 minutes
- **Full Test Suite**: ~10-15 minutes
- **Release Build**: ~8-12 minutes

## 🔧 Maintenance

### Weekly Tasks (Automated):
- Dependency updates via Dependabot
- Security vulnerability scanning
- Test execution across all supported environments

### Manual Tasks:
- Review and merge dependency updates
- Update Python version matrix as needed
- Review security scan results
- Update CI configuration as project evolves

## 📚 Additional Resources

### GitHub Actions Documentation:
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file)

### Testing Resources:
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Plugin Test Documentation](tests/README.md)

This CI/CD setup ensures high code quality, security, and reliability for the OctoPrint Filament Motion Sensor Plugin. All workflows are designed to be fast, comprehensive, and maintainable. 