"""Dependency injection container using dependency-injector framework."""

from dependency_injector import containers, providers
from config import Settings, settings as default_settings
from utility.logging import  setup_logging
from utility.api_manager import APIManager


class Container(containers.DeclarativeContainer):
    """
    Dependency injection container for managing application dependencies.
    
    Uses the dependency-injector framework for professional-grade DI with
    support for factories, singletons, and lifecycle management.
    """
    
    # Configuration provider
    config = providers.Singleton(lambda: default_settings)
    
    # Logger provider - lazy singleton initialization
    logger = providers.Singleton(
        setup_logging,
        name=__name__,
        config=config
    )
    
    # API Manager provider - lazy singleton initialization
    api_manager = providers.Singleton(
        APIManager,
        apis_config=config.provided.apis
    )


# Create a function to initialize the container with custom settings if needed
def create_container(settings: Settings = None) -> Container:
    """
    Create and configure the dependency injection container.
    
    Args:
        settings: Optional custom Settings instance. Defaults to default_settings.
        
    Returns:
        Container: Configured DI container
    """
    container = Container()
    
    if settings:
        # Override config provider with custom settings
        container.config = providers.Singleton(lambda: settings)
        
        # Re-initialize dependent providers
        container.logger = providers.Singleton(
            setup_logging,
            name=__name__,
            config=container.config
        )
        container.api_manager = providers.Singleton(
            APIManager,
            apis_config=container.config.provided.apis
        )
    
    return container


# Global container instance
_container: Container = None


def get_container(settings: Settings = None) -> Container:
    """
    Get the global dependency container instance.
    
    Implements the singleton pattern for the DI container.
    
    Args:
        settings: Optional Settings instance for initialization.
        
    Returns:
        Container: The global container instance
    """
    global _container
    if _container is None:
        _container = create_container(settings)
    return _container


def reset_container() -> None:
    """
    Reset the global container instance.
    
    Useful for testing or when settings need to be reloaded.
    """
    global _container
    if _container:
        _container.shutdown_resources()
    _container = None


async def init_container_dependencies(container: Container = None) -> None:
    """
    Initialize all async dependencies in the container.
    
    Should be called during application startup.
    
    Args:
        container: Optional container instance. Defaults to global container.
    """
    if container is None:
        container = get_container()
    
    # Initialize API Manager (async operation)
    api_mgr = container.api_manager()
    logger = container.logger()
    
    logger.info("Initializing container dependencies...")
    await api_mgr.initialize()
    logger.info("Container dependencies initialized successfully")


async def shutdown_container_dependencies(container: Container = None) -> None:
    """
    Shutdown all async dependencies in the container.
    
    Should be called during application shutdown.
    
    Args:
        container: Optional container instance. Defaults to global container.
    """
    if container is None:
        container = get_container()
    
    logger = container.logger()
    logger.info("Shutting down container dependencies...")
    
    api_mgr = container.api_manager()
    await api_mgr.close_all()
    
    logger.info("Container dependencies shutdown complete")

