"""Enhanced logging module with Application Insights support."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.azure import metrics_exporter
    from azure.monitor.opentelemetry import configure_azure_monitor
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class StructuredFormatter(logging.Formatter):
    """Custom formatter with structured logging support."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with additional context."""
        # Add custom fields
        if not hasattr(record, 'request_id'):
            record.request_id = 'N/A'
        if not hasattr(record, 'user_id'):
            record.user_id = 'N/A'
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'N/A'
            
        return super().format(record)


class LoggerManager:
    """Centralized logger management with Application Insights support."""
    
    _instances = {}
    _azure_handler: Optional[logging.Handler] = None
    _metrics_exporter = None
    
    @classmethod
    def setup_azure_logging(cls, connection_string: str) -> None:
        """
        Set up Azure Application Insights logging.
        
        Args:
            connection_string: Application Insights connection string
        """
        if not AZURE_AVAILABLE:
            logging.warning(
                "Azure monitoring packages not installed. "
                "Install with: pip install opencensus-ext-azure azure-monitor-opentelemetry"
            )
            return
        
        try:
            # Configure OpenTelemetry with Azure Monitor
            configure_azure_monitor(
                connection_string=connection_string,
                logging_enabled=True,
                metrics_enabled=True,
                traces_enabled=True
            )
            
            # Create Azure log handler
            cls._azure_handler = AzureLogHandler(connection_string=connection_string)
            cls._azure_handler.setFormatter(StructuredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
            ))
            
            # Set up metrics exporter
            cls._metrics_exporter = metrics_exporter.new_metrics_exporter(
                connection_string=connection_string
            )
            
            logging.info("Azure Application Insights logging configured successfully")
        except Exception as e:
            logging.error(f"Failed to configure Azure Application Insights: {e}", exc_info=True)
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        log_max_bytes: int = 10485760,
        log_backup_count: int = 5,
        enable_azure: bool = False
    ) -> logging.Logger:
        """
        Get or create a logger instance with proper configuration.
        
        Args:
            name: Logger name
            log_level: Logging level
            log_file: Optional log file path
            log_max_bytes: Maximum log file size
            log_backup_count: Number of backup files
            enable_azure: Enable Azure Application Insights logging
            
        Returns:
            Configured logger instance
        """
        # Return existing logger if already configured
        if name in cls._instances:
            return cls._instances[name]
        
        logger = logging.getLogger(name)
        
        # Clear any existing handlers
        logger.handlers.clear()
        logger.setLevel(log_level)
        
        # Create structured formatter
        formatter = StructuredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] [%(correlation_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler with color support
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
        
        # File handler with rotation (for local/development)
        if log_file:
            try:
                log_file_path = Path(log_file)
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=log_max_bytes,
                    backupCount=log_backup_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(log_level)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.error(f"Failed to create file handler: {e}")
        
        # Azure Application Insights handler (for production)
        if enable_azure and cls._azure_handler:
            logger.addHandler(cls._azure_handler)
            logger.info("Azure Application Insights handler added to logger")
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        cls._instances[name] = logger
        return logger


def setup_logging(
    name: str,
    config=None
) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name
        config: Optional settings object
        
    Returns:
        Configured logger instance
    """
    if config is None:
        # Fallback to environment variables
        import os
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_file = os.getenv("LOG_FILE", "logs/app.log")
        log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
        log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        enable_azure = False
        connection_string = None
    else:
        log_level = config.log_level
        log_file = config.log_file if not config.is_production else None
        log_max_bytes = config.log_max_bytes
        log_backup_count = config.log_backup_count
        enable_azure = config.enable_telemetry and config.is_production
        connection_string = config.applicationinsights_connection_string
    
    # Set up Azure logging if enabled
    if enable_azure and connection_string:
        LoggerManager.setup_azure_logging(connection_string)
    
    return LoggerManager.get_logger(
        name=name,
        log_level=log_level,
        log_file=log_file,
        log_max_bytes=log_max_bytes,
        log_backup_count=log_backup_count,
        enable_azure=enable_azure
    )
