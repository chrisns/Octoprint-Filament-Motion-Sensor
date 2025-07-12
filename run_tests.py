#!/usr/bin/env python3
"""
Test runner for OctoPrint Filament Motion Sensor Plugin
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description or ' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0

def install_dependencies():
    """Install test dependencies"""
    print("Installing test dependencies...")
    
    # Install test requirements
    cmd = [sys.executable, "-m", "pip", "install", "-r", "test-requirements.txt"]
    if not run_command(cmd, "Installing test dependencies"):
        return False
    
    # Install plugin in development mode
    cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
    if not run_command(cmd, "Installing plugin in development mode"):
        return False
    
    return True

def run_tests(test_type="all", verbose=False, coverage=True):
    """Run tests based on type"""
    
    base_cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        base_cmd.append("-v")
    
    if coverage:
        base_cmd.extend([
            "--cov=octoprint_filamentmotionsensor",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    if test_type == "unit":
        base_cmd.extend(["-m", "unit", "tests/"])
    elif test_type == "integration":
        base_cmd.extend(["-m", "integration", "tests/"])
    elif test_type == "fast":
        base_cmd.extend(["-m", "not slow", "tests/"])
    elif test_type == "all":
        base_cmd.append("tests/")
    else:
        # Run specific test file or pattern
        base_cmd.append(test_type)
    
    return run_command(base_cmd, f"Running {test_type} tests")

def run_linting():
    """Run code linting"""
    print("Running code linting...")
    
    # Check if flake8 is available
    try:
        import flake8
        cmd = [sys.executable, "-m", "flake8", "octoprint_filamentmotionsensor/", "tests/"]
        if not run_command(cmd, "Running flake8 linting"):
            return False
    except ImportError:
        print("flake8 not available, skipping linting")
    
    return True

def generate_coverage_report():
    """Generate coverage report"""
    print("Generating coverage report...")
    
    cmd = [sys.executable, "-m", "coverage", "html"]
    if run_command(cmd, "Generating HTML coverage report"):
        print("Coverage report generated in htmlcov/index.html")
        return True
    
    return False

def main():
    parser = argparse.ArgumentParser(description="Test runner for OctoPrint Filament Motion Sensor Plugin")
    
    parser.add_argument("--install", action="store_true", 
                       help="Install test dependencies")
    parser.add_argument("--type", choices=["all", "unit", "integration", "fast"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--test", type=str, help="Specific test file or pattern to run")
    parser.add_argument("--no-coverage", action="store_true", 
                       help="Skip coverage reporting")
    parser.add_argument("--lint", action="store_true", 
                       help="Run linting checks")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--coverage-report", action="store_true", 
                       help="Generate HTML coverage report")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    success = True
    
    # Install dependencies if requested
    if args.install:
        success &= install_dependencies()
    
    # Run linting if requested
    if args.lint:
        success &= run_linting()
    
    # Run tests
    if args.test:
        success &= run_tests(args.test, args.verbose, not args.no_coverage)
    else:
        success &= run_tests(args.type, args.verbose, not args.no_coverage)
    
    # Generate coverage report if requested
    if args.coverage_report and not args.no_coverage:
        success &= generate_coverage_report()
    
    if success:
        print("\n✅ All operations completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some operations failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 