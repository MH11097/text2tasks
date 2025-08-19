# Performance Testing

This directory contains performance testing tools and scripts for the AI Work OS application.

## Prerequisites

Install Locust for load testing:

```bash
pip install locust
```

## Quick Start

1. **Start the application**:
```bash
python -m uvicorn src.main:app --reload --port 8000
```

2. **Set your API key**:
```bash
export API_KEY=your-secure-api-key-here
```

3. **Run a basic test**:
```bash
cd tests/performance
python run_performance_tests.py light_load
```

## Available Test Scenarios

| Scenario | Users | Duration | Description |
|----------|-------|----------|-------------|
| `light_load` | 10 | 5m | Light load with normal user patterns |
| `normal_load` | 50 | 10m | Normal production load simulation |
| `high_load` | 100 | 10m | High load stress testing |
| `spike_test` | 200 | 5m | Spike testing with sudden load increase |
| `read_heavy` | 80 | 8m | Read-heavy workload testing |
| `write_heavy` | 30 | 10m | Write-heavy workload testing |

## Running Tests

### List all scenarios:
```bash
python run_performance_tests.py list
```

### Run a specific scenario:
```bash
python run_performance_tests.py normal_load
```

### Run all scenarios:
```bash
python run_performance_tests.py --all
```

### Test against different host:
```bash
python run_performance_tests.py light_load --host http://production-server:8000
```

### Check server connectivity only:
```bash
python run_performance_tests.py --check-only
```

## Manual Locust Testing

For interactive testing with the Locust web UI:

```bash
cd tests/performance
locust -f locustfile.py --host http://localhost:8000
```

Then open http://localhost:8089 in your browser.

## Test Results

Results are saved in the `results/` directory:
- HTML reports: `{scenario}_{timestamp}.html`
- CSV data: `{scenario}_{timestamp}_stats.csv`
- Failure logs: `{scenario}_{timestamp}_failures.csv`

## Performance Thresholds

The tests check against these performance thresholds:
- **Average response time**: < 500ms
- **95th percentile response time**: < 2000ms
- **Error rate**: < 1%
- **Minimum throughput**: > 50 RPS
- **Availability**: > 99.9%

## User Classes

### AIWorkOSUser
- Simulates normal user behavior
- Mixed read/write operations
- Realistic wait times (1-3 seconds)

### HighLoadUser
- Faster request patterns (0.1-0.5 seconds)
- More frequent health checks
- Tests rate limiting

### APIStressUser
- Very fast requests (0-0.1 seconds)
- Stress tests the API limits
- Large payload testing

### ReadOnlyUser
- Only performs read operations
- Tests read scalability
- Good for caching validation

### WriteHeavyUser
- Focuses on write operations
- Tests database performance under load
- Validates write transaction handling

## Monitoring During Tests

During performance tests, monitor:

1. **Application logs** (structured JSON logs)
2. **System resources** (CPU, memory, disk I/O)
3. **Database performance** (if using PostgreSQL)
4. **Rate limiting** (Redis metrics if enabled)

## Example Commands

```bash
# Quick health check
python run_performance_tests.py --check-only

# Light load test
python run_performance_tests.py light_load

# Full test suite
python run_performance_tests.py --all

# Custom host with API key
API_KEY=your-key python run_performance_tests.py normal_load --host https://api.example.com

# Interactive mode
locust -f locustfile.py --host http://localhost:8000
```

## Interpreting Results

### Good Performance Indicators:
- Low error rate (< 1%)
- Consistent response times
- High throughput
- No rate limit violations

### Warning Signs:
- Increasing response times under load
- High error rates
- Rate limit violations
- Memory/CPU spikes

### Common Issues:
- **Slow database queries**: Check indexes and query optimization
- **Rate limiting**: Adjust limits or improve caching
- **Memory leaks**: Monitor memory usage over time
- **Connection pool exhaustion**: Increase pool size

## Troubleshooting

### "Connection refused" errors:
- Ensure the application is running
- Check the host URL
- Verify firewall settings

### "Invalid API key" errors:
- Set the correct API_KEY environment variable
- Check API key format and length

### High response times:
- Check database indexes
- Monitor system resources
- Review application logs

### Rate limiting issues:
- Increase rate limits in configuration
- Implement Redis for distributed rate limiting
- Review rate limiting patterns in tests