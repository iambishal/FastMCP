"""API Manager for handling multiple external API clients.

This module provides a centralized manager for multiple HTTPClientManager instances,
allowing the application to interact with multiple external APIs efficiently.
"""

from typing import Dict, Optional
from utility.http_client import HTTPClientManager


class APIManager:
    """
    Manages multiple HTTP clients for different external APIs.
    
    Features:
        - Lazy initialization of API clients
        - Connection pooling per API
        - Circuit breaker per API
        - Easy addition of new APIs
    
    Example:
        >>> api_manager = APIManager(apis_config)
        >>> await api_manager.initialize()
        >>> petstore_client = api_manager.get("petstore")
        >>> pets = await petstore_client.get("/pet/findByStatus", params={"status": "available"})
        >>> await api_manager.close()
    """
    
    def __init__(self, apis_config: Dict[str, dict]):
        """
        Initialize API Manager with API configurations.
        
        Args:
            apis_config: Dictionary of API configs
                Example:
                {
                    "petstore": {
                        "base_url": "https://petstore.swagger.io/v2",
                        "timeout": 10,
                        "max_retries": 3
                    },
                    "jsonplaceholder": {
                        "base_url": "https://jsonplaceholder.typicode.com",
                        "timeout": 10
                    }
                }
        """
        self.apis_config = apis_config
        self.clients: Dict[str, HTTPClientManager] = {}
    
    def initialize_sync(self) -> None:
        """
        Initialize all configured API clients synchronously.
        
        This creates HTTPClientManager instances for each API in the config.
        It's safe to call multiple times; existing clients are reused.
        """
        for api_name, config in self.apis_config.items():
            if api_name not in self.clients:
                self.clients[api_name] = HTTPClientManager(
                    base_url=config.get("base_url"),
                    timeout=config.get("timeout", 10),
                    max_connections=config.get("max_connections", 100)
                )
    
    async def initialize(self) -> None:
        """
        Initialize all configured API clients asynchronously.
        
        This creates HTTPClientManager instances for each API in the config.
        It's safe to call multiple times; existing clients are reused.
        """
        self.initialize_sync()
    
    def get(self, api_name: str) -> Optional[HTTPClientManager]:
        """
        Get the HTTP client for a specific API.
        
        Args:
            api_name: Name of the API (key from apis_config)
            
        Returns:
            HTTPClientManager instance or None if not initialized
            
        Raises:
            KeyError: If API name is not configured
        """
        if api_name not in self.apis_config:
            raise KeyError(f"API '{api_name}' not configured. Available: {list(self.apis_config.keys())}")
        
        return self.clients.get(api_name)
    
    def list_apis(self) -> Dict[str, dict]:
        """
        List all configured APIs with their metadata.
        
        Returns:
            Dictionary of API names and their configurations
        """
        return {
            name: {
                "base_url": config.get("base_url"),
                "description": config.get("description", "No description"),
                "status": "initialized" if name in self.clients else "not initialized"
            }
            for name, config in self.apis_config.items()
        }
    
    async def close_all(self) -> None:
        """Close all HTTP clients and cleanup resources."""
        for api_name, client in self.clients.items():
            try:
                await client.close()
            except Exception as e:
                # Log error but continue closing other clients
                print(f"Error closing {api_name} client: {e}")
        self.clients.clear()
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all initialized API clients.
        
        Returns:
            Dictionary mapping API names to their health status (True/False)
        """
        health = {}
        for api_name, client in self.clients.items():
            try:
                if client:
                    http_client = await client.get_client()
                    health[api_name] = not http_client.is_closed
                else:
                    health[api_name] = False
            except Exception:
                health[api_name] = False
        return health
    
    async def __aenter__(self):
        """Support for async context manager."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting async context manager."""
        await self.close_all()
