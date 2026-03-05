"""
Load testing script for FastMCP Server using Locust.

Usage:
    # Install locust
    pip install locust

    # Run load test
    locust -f load_test.py --host=http://localhost:8000

    # Or headless mode
    locust -f load_test.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
"""

import random
from locust import HttpUser, task, between, events
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServerUser(HttpUser):
    """Simulates a user interacting with the MCP server."""
    
    # Wait between 1 to 3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user starts."""
        logger.info("Starting new user session")
        self.client.headers.update({
            'Content-Type': 'application/json',
            'X-Correlation-ID': f'load-test-{random.randint(1000, 9999)}'
        })
    
    @task(3)
    def health_check(self):
        """Test health check endpoint (most frequent)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with status {response.status_code}")
    
    @task(2)
    def readiness_check(self):
        """Test readiness check endpoint."""
        with self.client.get("/health/ready", catch_response=True) as response:
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get('status') == 'ready':
                    response.success()
                else:
                    response.failure("Server not ready")
            else:
                response.failure(f"Readiness check failed with status {response.status_code}")
    
    @task(1)
    def liveness_check(self):
        """Test liveness check endpoint."""
        self.client.get("/health/live")
    
    @task(5)
    def find_available_pets(self):
        """Test finding available pets (simulates tool invocation)."""
        # Note: This would need to match your actual MCP endpoint structure
        # Adjust the payload according to your MCP protocol implementation
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "find_pets_by_status",
                "arguments": {
                    "status": "available"
                }
            },
            "id": random.randint(1, 10000)
        }
        
        with self.client.post("/mcp", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Request failed with status {response.status_code}")
    
    @task(2)
    def add_client(self):
        """Test adding a new client."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "add_client",
                "arguments": {
                    "name": f"Test User {random.randint(1, 10000)}",
                    "email": f"user{random.randint(1, 10000)}@example.com",
                    "date_of_birth": "1990-05-15"
                }
            },
            "id": random.randint(1, 10000)
        }
        
        with self.client.post("/mcp", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Request failed with status {response.status_code}")


class StressTestUser(HttpUser):
    """Aggressive stress testing user for circuit breaker and rate limit testing."""
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    @task
    def rapid_requests(self):
        """Make rapid requests to test rate limiting."""
        self.client.get("/health")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts."""
    logger.info("=" * 60)
    logger.info("Starting FastMCP Server Load Test")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops."""
    logger.info("=" * 60)
    logger.info("Load Test Completed")
    logger.info(f"Total Requests: {environment.stats.total.num_requests}")
    logger.info(f"Total Failures: {environment.stats.total.num_failures}")
    logger.info(f"Average Response Time: {environment.stats.total.avg_response_time:.2f}ms")
    logger.info(f"RPS: {environment.stats.total.total_rps:.2f}")
    logger.info("=" * 60)
