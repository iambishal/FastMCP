"""HTTP client utilities with resilience patterns.

This module provides reusable HTTP client components with:
- Circuit breaker pattern for fault tolerance
- Connection pooling for performance
- Retry logic with exponential backoff
- HTTP/2 support
"""

import asyncio
from typing import Optional
from datetime import datetime, timedelta
from functools import wraps

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


class CircuitBreaker:
    """
    Simple circuit breaker pattern implementation.
    
    The circuit breaker prevents cascading failures by stopping requests
    to a failing service after a threshold is reached.
    
    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Service is failing, requests are blocked
        - HALF_OPEN: Testing if service has recovered
    
    Args:
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before attempting recovery (half-open state)
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func):
        """
        Decorator to apply circuit breaker to async functions.
        
        Args:
            func: Async function to protect
            
        Returns:
            Wrapped function with circuit breaker logic
            
        Raises:
            Exception: If circuit is OPEN or underlying function fails
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                self.on_success()
                return result
            except Exception as e:
                self.on_failure()
                raise e
        
        return wrapper
    
    def on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """Handle failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def reset(self):
        """Manually reset the circuit breaker."""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None


class HTTPClientManager:
    """
    Centralized HTTP client manager with connection pooling and resilience patterns.
    
    Features:
        - Connection pooling (reuses connections)
        - HTTP/2 support for better performance
        - Circuit breaker for fault tolerance
        - Automatic retries with exponential backoff
        - Configurable timeouts
    
    Args:
        base_url: Base URL for all requests
        timeout: Request timeout in seconds
        max_connections: Maximum number of concurrent connections
    
    Example:
        >>> client = HTTPClientManager("https://api.example.com", timeout=10)
        >>> result = await client.get("/endpoint", params={"key": "value"})
        >>> await client.close()
    """
    
    def __init__(self, base_url: str, timeout: int = 10, max_connections: int = 100):
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self.limits = httpx.Limits(
            max_keepalive_connections=max_connections,
            max_connections=max_connections,
            keepalive_expiry=30
        )
        self.circuit_breaker = CircuitBreaker()
    
    async def get_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client instance.
        
        Returns:
            Configured AsyncClient instance
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                limits=self.limits,
                http2=True,  # Enable HTTP/2
                follow_redirects=True
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client and cleanup resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def get(self, endpoint: str, params: Optional[dict] = None, **kwargs) -> dict:
        """
        Make GET request with retry logic and circuit breaker.
        
        Args:
            endpoint: API endpoint path (relative to base_url)
            params: Query parameters
            **kwargs: Additional arguments passed to httpx.get()
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If request fails after retries
            Exception: If circuit breaker is open
        """
        client = await self.get_client()
        
        @self.circuit_breaker.call
        async def _make_request():
            response = await client.get(endpoint, params=params, **kwargs)
            response.raise_for_status()
            return response.json()
        
        return await _make_request()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def post(
        self, 
        endpoint: str, 
        data: Optional[dict] = None, 
        json: Optional[dict] = None,
        **kwargs
    ) -> dict:
        """
        Make POST request with retry logic and circuit breaker.
        
        Args:
            endpoint: API endpoint path (relative to base_url)
            data: Form data
            json: JSON data
            **kwargs: Additional arguments passed to httpx.post()
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If request fails after retries
            Exception: If circuit breaker is open
        """
        client = await self.get_client()
        
        @self.circuit_breaker.call
        async def _make_request():
            response = await client.post(endpoint, data=data, json=json, **kwargs)
            response.raise_for_status()
            return response.json()
        
        return await _make_request()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def put(
        self, 
        endpoint: str, 
        data: Optional[dict] = None, 
        json: Optional[dict] = None,
        **kwargs
    ) -> dict:
        """
        Make PUT request with retry logic and circuit breaker.
        
        Args:
            endpoint: API endpoint path (relative to base_url)
            data: Form data
            json: JSON data
            **kwargs: Additional arguments passed to httpx.put()
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If request fails after retries
            Exception: If circuit breaker is open
        """
        client = await self.get_client()
        
        @self.circuit_breaker.call
        async def _make_request():
            response = await client.put(endpoint, data=data, json=json, **kwargs)
            response.raise_for_status()
            return response.json()
        
        return await _make_request()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def delete(self, endpoint: str, **kwargs) -> dict:
        """
        Make DELETE request with retry logic and circuit breaker.
        
        Args:
            endpoint: API endpoint path (relative to base_url)
            **kwargs: Additional arguments passed to httpx.delete()
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If request fails after retries
            Exception: If circuit breaker is open
        """
        client = await self.get_client()
        
        @self.circuit_breaker.call
        async def _make_request():
            response = await client.delete(endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        
        return await _make_request()
    
    async def __aenter__(self):
        """Support for async context manager."""
        await self.get_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting async context manager."""
        await self.close()
