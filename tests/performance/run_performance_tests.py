#!/usr/bin/env python3
"""
Performance testing runner for AI Work OS
"""

import os
import sys
import subprocess
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import requests

from performance_config import SCENARIOS, generate_locust_command, create_performance_report

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import locust
        print("✓ Locust is installed")
    except ImportError:
        print("❌ Locust not found. Install with: pip install locust")
        sys.exit(1)

def check_target_server(host: str, api_key: str):
    """Check if target server is running and accessible"""
    try:
        # Check health endpoint
        response = requests.get(f"{host}/healthz", timeout=5)
        if response.status_code == 200:
            print(f"✓ Server is running at {host}")
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
        
        # Check API key by testing a protected endpoint
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        test_payload = {"text": "Test connection", "source": "other"}
        
        response = requests.post(f"{host}/ingest", json=test_payload, headers=headers, timeout=5)
        if response.status_code in [200, 201]:
            print("✓ API key is valid")
        elif response.status_code == 401:
            print("❌ Invalid API key")
            return False
        else:
            print(f"⚠️  API test returned status {response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def setup_results_directory():
    """Create results directory if it doesn't exist"""
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    return results_dir

def run_scenario(scenario_name: str, host: str, api_key: str) -> bool:
    """Run a specific performance test scenario"""
    if scenario_name not in SCENARIOS:
        print(f"❌ Unknown scenario: {scenario_name}")
        print(f"Available scenarios: {', '.join(SCENARIOS.keys())}")
        return False
    
    scenario = SCENARIOS[scenario_name]
    print(f"\n🚀 Running scenario: {scenario_name}")
    print(f"Description: {scenario['description']}")
    print(f"Users: {scenario['users']}, Spawn rate: {scenario['spawn_rate']}, Duration: {scenario['run_time']}")
    
    # Set environment variables
    env = os.environ.copy()
    env["API_KEY"] = api_key
    env["TARGET_HOST"] = host
    
    # Generate timestamp for unique file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_prefix = f"results/{scenario_name}_{timestamp}"
    html_report = f"results/{scenario_name}_{timestamp}.html"
    
    # Build Locust command
    cmd = [
        "locust",
        "-f", "locustfile.py",
        f"--users={scenario['users']}",
        f"--spawn-rate={scenario['spawn_rate']}",
        f"--run-time={scenario['run_time']}",
        f"--host={host}",
        "--headless",
        f"--csv={csv_prefix}",
        f"--html={html_report}",
        "--only-summary"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("Starting test...")
    
    start_time = time.time()
    
    try:
        # Run the test
        result = subprocess.run(
            cmd,
            cwd="tests/performance",
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✓ Test completed successfully in {duration:.1f} seconds")
            print(f"📊 HTML report: {html_report}")
            print(f"📈 CSV data: {csv_prefix}_stats.csv")
            
            # Print summary from output
            if result.stdout:
                print("\nTest Summary:")
                print(result.stdout[-1000:])  # Last 1000 chars
            
            return True
        else:
            print(f"❌ Test failed with exit code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def list_scenarios():
    """List all available test scenarios"""
    print("\nAvailable performance test scenarios:")
    print("=" * 50)
    for name, config in SCENARIOS.items():
        print(f"\n{name}:")
        print(f"  Description: {config['description']}")
        print(f"  Users: {config['users']}")
        print(f"  Duration: {config['run_time']}")
        print(f"  User class: {config['user_class']}")

def main():
    parser = argparse.ArgumentParser(description="Run performance tests for AI Work OS")
    parser.add_argument("scenario", nargs="?", help="Test scenario name (or 'list' to see all)")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host URL")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--check-only", action="store_true", help="Only check server connectivity")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    
    args = parser.parse_args()
    
    # Get API key from environment if not provided
    api_key = args.api_key or os.getenv("API_KEY")
    if not api_key:
        print("❌ API key required. Set API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    print("AI Work OS Performance Testing")
    print("=" * 40)
    
    # Check dependencies
    check_dependencies()
    
    # Setup results directory
    setup_results_directory()
    
    # List scenarios if requested
    if args.scenario == "list":
        list_scenarios()
        return
    
    # Check server connectivity
    print(f"\nChecking server at {args.host}...")
    if not check_target_server(args.host, api_key):
        print("❌ Server check failed. Please ensure the server is running and API key is correct.")
        sys.exit(1)
    
    if args.check_only:
        print("✓ Server check passed")
        return
    
    # Run tests
    if args.all:
        print("\n🏃 Running all scenarios...")
        failed_scenarios = []
        
        for scenario_name in SCENARIOS.keys():
            success = run_scenario(scenario_name, args.host, api_key)
            if not success:
                failed_scenarios.append(scenario_name)
            time.sleep(5)  # Brief pause between tests
        
        # Summary
        print(f"\n📋 Test Summary:")
        print(f"Total scenarios: {len(SCENARIOS)}")
        print(f"Successful: {len(SCENARIOS) - len(failed_scenarios)}")
        print(f"Failed: {len(failed_scenarios)}")
        
        if failed_scenarios:
            print(f"Failed scenarios: {', '.join(failed_scenarios)}")
            sys.exit(1)
        else:
            print("✓ All scenarios passed!")
    
    elif args.scenario:
        success = run_scenario(args.scenario, args.host, api_key)
        if not success:
            sys.exit(1)
    else:
        print("❌ Please specify a scenario name or use --all")
        print("Use 'list' to see available scenarios")
        sys.exit(1)

if __name__ == "__main__":
    main()