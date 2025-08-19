"""
Performance testing configuration and utilities
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any

# Test scenarios configuration
SCENARIOS = {
    "light_load": {
        "description": "Light load testing with normal user patterns",
        "users": 10,
        "spawn_rate": 2,
        "run_time": "5m",
        "user_class": "AIWorkOSUser"
    },
    "normal_load": {
        "description": "Normal production load simulation",
        "users": 50,
        "spawn_rate": 5,
        "run_time": "10m",
        "user_class": "AIWorkOSUser"
    },
    "high_load": {
        "description": "High load stress testing",
        "users": 100,
        "spawn_rate": 10,
        "run_time": "10m",
        "user_class": "HighLoadUser"
    },
    "spike_test": {
        "description": "Spike testing with sudden load increase",
        "users": 200,
        "spawn_rate": 50,
        "run_time": "5m",
        "user_class": "APIStressUser"
    },
    "read_heavy": {
        "description": "Read-heavy workload testing",
        "users": 80,
        "spawn_rate": 8,
        "run_time": "8m",
        "user_class": "ReadOnlyUser"
    },
    "write_heavy": {
        "description": "Write-heavy workload testing",
        "users": 30,
        "spawn_rate": 3,
        "run_time": "10m",
        "user_class": "WriteHeavyUser"
    }
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "response_time_95th": 2000,  # 95th percentile response time in ms
    "response_time_avg": 500,    # Average response time in ms
    "error_rate": 0.01,          # Maximum error rate (1%)
    "throughput_min": 50,        # Minimum requests per second
    "availability": 0.999        # Minimum availability (99.9%)
}

# API endpoints to monitor
ENDPOINTS = {
    "/healthz": {"method": "GET", "expected_status": 200},
    "/health/detailed": {"method": "GET", "expected_status": 200},
    "/status": {"method": "GET", "expected_status": 200},
    "/tasks": {"method": "GET", "expected_status": 200},
    "/ingest": {"method": "POST", "expected_status": 200, "requires_auth": True},
    "/ask": {"method": "POST", "expected_status": 200, "requires_auth": True}
}

def get_test_config(scenario_name: str) -> Dict[str, Any]:
    """Get configuration for a specific test scenario"""
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(SCENARIOS.keys())}")
    
    config = SCENARIOS[scenario_name].copy()
    config["timestamp"] = datetime.now().isoformat()
    config["host"] = os.getenv("TARGET_HOST", "http://localhost:8000")
    config["api_key"] = os.getenv("API_KEY", "test-api-key")
    
    return config

def generate_locust_command(scenario_name: str) -> str:
    """Generate Locust command for a specific scenario"""
    config = get_test_config(scenario_name)
    
    cmd = [
        "locust",
        f"--users={config['users']}",
        f"--spawn-rate={config['spawn_rate']}",
        f"--run-time={config['run_time']}",
        f"--host={config['host']}",
        "--headless",
        "--csv=results/performance_results",
        "--html=results/performance_report.html"
    ]
    
    return " ".join(cmd)

def create_performance_report(results: Dict[str, Any]) -> Dict[str, Any]:
    """Create a performance test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_duration": results.get("test_duration", 0),
        "total_requests": results.get("total_requests", 0),
        "failed_requests": results.get("failed_requests", 0),
        "error_rate": results.get("failed_requests", 0) / max(results.get("total_requests", 1), 1),
        "average_response_time": results.get("average_response_time", 0),
        "min_response_time": results.get("min_response_time", 0),
        "max_response_time": results.get("max_response_time", 0),
        "rps": results.get("total_requests", 0) / max(results.get("test_duration", 1), 1),
        "thresholds_met": {},
        "recommendations": []
    }
    
    # Check against thresholds
    thresholds_met = True
    
    if report["average_response_time"] > PERFORMANCE_THRESHOLDS["response_time_avg"]:
        thresholds_met = False
        report["recommendations"].append(
            f"Average response time ({report['average_response_time']:.2f}ms) exceeds threshold "
            f"({PERFORMANCE_THRESHOLDS['response_time_avg']}ms)"
        )
    
    if report["error_rate"] > PERFORMANCE_THRESHOLDS["error_rate"]:
        thresholds_met = False
        report["recommendations"].append(
            f"Error rate ({report['error_rate']:.3f}) exceeds threshold "
            f"({PERFORMANCE_THRESHOLDS['error_rate']:.3f})"
        )
    
    if report["rps"] < PERFORMANCE_THRESHOLDS["throughput_min"]:
        thresholds_met = False
        report["recommendations"].append(
            f"Throughput ({report['rps']:.2f} RPS) below minimum threshold "
            f"({PERFORMANCE_THRESHOLDS['throughput_min']} RPS)"
        )
    
    report["thresholds_met"]["overall"] = thresholds_met
    
    if thresholds_met:
        report["recommendations"].append("All performance thresholds met successfully!")
    
    return report

# Sample test data generators
def generate_sample_documents(count: int = 100) -> List[Dict[str, str]]:
    """Generate sample documents for testing"""
    templates = [
        "Meeting on {date}: {person} needs to {action} by {deadline}. Blocker: {blocker}.",
        "Email from {person}: Please {action} by {deadline}. Priority: {priority}.",
        "Standup update: {person} is working on {action}. Status: {status}.",
        "Project note: Need to {action} for {project} by {deadline}.",
        "Customer feedback: {feedback}. Action required: {action}."
    ]
    
    people = ["John", "Sarah", "Mike", "Lisa", "Alex", "Maria", "David", "Emma"]
    actions = [
        "complete database migration", "review UI mockups", "fix authentication bug",
        "deploy to staging", "update documentation", "test payment integration",
        "optimize API performance", "implement rate limiting"
    ]
    blockers = [
        "waiting for production access", "dependency on external API",
        "missing requirements", "resource constraints"
    ]
    projects = ["Auth System", "Payment Gateway", "Dashboard", "Mobile App", "API"]
    
    import random
    from datetime import timedelta
    
    documents = []
    for i in range(count):
        template = random.choice(templates)
        date = (datetime.now() + timedelta(days=random.randint(-30, 30))).strftime("%Y-%m-%d")
        
        doc = {
            "text": template.format(
                date=date,
                person=random.choice(people),
                action=random.choice(actions),
                deadline=f"{random.randint(1, 7)} days",
                blocker=random.choice(blockers),
                priority=random.choice(["High", "Medium", "Low"]),
                status=random.choice(["In Progress", "Pending", "Completed"]),
                project=random.choice(projects),
                feedback="System works well but needs performance improvements"
            ),
            "source": random.choice(["email", "meeting", "note", "other"])
        }
        documents.append(doc)
    
    return documents