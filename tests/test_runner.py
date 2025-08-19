"""Test runner with coverage and reporting"""

import sys
import pytest
import subprocess
from pathlib import Path

def main():
    """Run tests with different configurations"""
    project_root = Path(__file__).parent.parent
    
    # Change to project root
    import os
    os.chdir(project_root)
    
    # Test configurations
    configs = {
        "unit": {
            "path": "tests/unit/",
            "description": "Unit tests only"
        },
        "integration": {
            "path": "tests/test_acceptance.py",
            "description": "Integration tests only"
        },
        "all": {
            "path": "tests/",
            "description": "All tests"
        },
        "coverage": {
            "path": "tests/",
            "description": "All tests with coverage report",
            "extra_args": ["--cov=src", "--cov-report=html", "--cov-report=term-missing"]
        },
        "fast": {
            "path": "tests/unit/",
            "description": "Fast unit tests only",
            "extra_args": ["-x", "--tb=short"]
        }
    }
    
    # Parse command line argument
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if test_type not in configs:
        print(f"Available test types: {', '.join(configs.keys())}")
        sys.exit(1)
    
    config = configs[test_type]
    
    print(f"\n🧪 Running {config['description']}")
    print("=" * 50)
    
    # Build pytest command
    cmd = ["pytest", config["path"], "-v"]
    
    if "extra_args" in config:
        cmd.extend(config["extra_args"])
    
    # Add any additional arguments passed to the script
    if len(sys.argv) > 2:
        cmd.extend(sys.argv[2:])
    
    # Run tests
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print(f"\n✅ {config['description']} passed!")
        else:
            print(f"\n❌ {config['description']} failed!")
        
        # Show coverage report location if generated
        if "coverage" in test_type:
            coverage_html = project_root / "htmlcov" / "index.html"
            if coverage_html.exists():
                print(f"\n📊 Coverage report: {coverage_html}")
        
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()