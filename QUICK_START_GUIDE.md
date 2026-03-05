# Quick Start Guide: FastMCP Server with Dependency Injection

## Overview
This guide helps you set up and run the FastMCP server with **dependency injection**, **environment-based configuration**, and **multi-API support**. The server uses a modern architecture with the `dependency-injector` framework for clean dependency management.

---

## Prerequisites

- Python 3.11 or higher
- pip or pip3
- Virtual environment (recommended)
- Docker (optional, for containerized deployment)

---

## Step 1: Clone and Set Up

```bash
# Clone the repository (if not already done)
cd FastMcpServer

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

---

## Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Key dependencies installed:**
- `fastmcp` - FastMCP framework
- `dependency-injector` - Dependency injection framework
- `httpx` - Async HTTP client
- `pydantic-settings` - Configuration management
- `tenacity` - Retry logic
- `uvicorn` - ASGI server

---

## Step 3: Set Up Configuration

All configuration is managed through environment variables. The server loads settings from a `.env` file or system environment variables.

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env for your environment
nano .env  # or use your preferred editor
```

### Required Configuration

```bash
# Application Metadata
APP_NAME=FastMCP-Server
APP_VERSION=1.0.0
ENVIRONMENT=development  # Options: development, staging, production

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Performance & Resilience
REQUEST_TIMEOUT=30  # seconds
MAX_CONNECTIONS=100
API_TIMEOUT=10  # Global timeout for all APIs
API_MAX_RETRIES=3  # Global retry count for all APIs

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60  # seconds

# External APIs (Petstore example)
PETSTORE_API_NAME=petstore
PETSTORE_BASE_URL=https://petstore.swagger.io/v2
PETSTORE_ENABLED=true
```

### Adding More APIs

To add additional external APIs, follow this pattern:

```bash
# API Configuration Template
{API_NAME}_API_NAME={api_name}
{API_NAME}_BASE_URL=https://api.example.com
{API_NAME}_ENABLED=true

# Example: Adding a Weather API
WEATHER_API_NAME=weather
WEATHER_BASE_URL=https://api.openweathermap.org/data/2.5
WEATHER_ENABLED=true
```

The `APIManager` will automatically discover and initialize all configured APIs using the dependency injection container.

---

## Step 4: Understanding the Architecture

The server uses **dependency injection** for clean architecture:

```
Container (Dependency Injection)
├── Config (Environment Variables)
├── Logger (File-based Logging)
└── APIManager (Multi-API Client Management)
    └── HTTPClientManager (per API)
        ├── Circuit Breaker
        ├── Connection Pooling
        └── Retry Logic
```

### Key Components

1. **Container** (`src/container.py`):
   - Manages all dependencies using `dependency-injector`
   - Provides singleton instances of config, logger, and api_manager
   - Handles initialization and cleanup

2. **Config** (`src/config.py`):
   - Loads all settings from environment variables
   - Validates configuration using Pydantic
   - Provides type-safe access to settings

3. **APIManager** (`src/utility/api_manager.py`):
   - Manages multiple HTTP clients (one per external API)
   - Provides centralized health checking
   - Handles lifecycle management

4. **HTTPClientManager** (`src/utility/http_client.py`):
   - Per-API HTTP client with connection pooling
   - Circuit breaker pattern for resilience
   - Automatic retry with exponential backoff

---

## Step 5: Run the Server

### Start the Server
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/Mac

# Create logs directory
mkdir -p logs

# Run the server
python -m src.main

# Or with uvicorn directly
uvicorn src.main:mcp.app --host 0.0.0.0 --port 8000 --log-level info
```

The server will:
1. Initialize the dependency container
2. Load configuration from environment variables
3. Set up the logger
4. Initialize API clients (Petstore, etc.)
5. Register MCP tools
6. Start the HTTP server

---

## Step 6: Test the Server

### Health Check Endpoints
```bash
# Basic health check
curl http://localhost:8000/health

# API health check (checks all external APIs)
curl http://localhost:8000/health/apis

# Response example:
# {
#   "status": "healthy",
#   "apis": {
#     "petstore": "healthy"
#   }
# }
```

### Test MCP Tools

The server exposes MCP tools through the `/mcp` endpoint:

```bash
# List available tools
curl -X POST http://localhost:8000/mcp/v1/tools \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# Call find_pets_by_status tool
curl -X POST http://localhost:8000/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "find_pets_by_status",
      "arguments": {
        "status": "available"
      }
    }
  }'
```

### Watch Logs

```bash
# Follow the log file
tail -f logs/app.log

# Filter for errors
tail -f logs/app.log | grep ERROR

# Filter by request ID
tail -f logs/app.log | grep "request_id"
```

---

## Step 7: Using Docker

### Build the Docker Image

```bash
# Build with default settings
docker-compose build

# Or build manually
docker build -t fastmcp-server:latest .
```

### Run with Docker Compose

```bash
# Start the server
docker-compose up -d

# View logs
docker-compose logs -f mcp-server

# Stop the server
docker-compose down
```

### Environment-Specific Docker Images

Create environment-specific images using build args:

```bash
# Development image
docker build \
  --build-arg APP_NAME=FastMCP-Dev \
  --build-arg ENVIRONMENT=development \
  --build-arg LOG_LEVEL=DEBUG \
  -t fastmcp-server:dev .

# Production image
docker build \
  --build-arg APP_NAME=FastMCP-Prod \
  --build-arg ENVIRONMENT=production \
  --build-arg LOG_LEVEL=WARNING \
  --build-arg API_TIMEOUT=5 \
  -t fastmcp-server:prod .
```

Or use environment variables at runtime:

```bash
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=WARNING \
  -e API_TIMEOUT=5 \
  -e PETSTORE_BASE_URL=https://petstore.swagger.io/v2 \
  fastmcp-server:latest
```

---

## Step 8: Adding Custom Tools

### Create Tool Function

Edit `src/tools/example_tools.py`:

```python
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    """Input schema for my custom tool"""
    param: str = Field(..., description="Parameter description")

async def my_custom_tool(
    param: str,
    http_client,  # Injected by registry
    logger  # Injected by registry
) -> str:
    """
    Description of what this tool does.
    
    Args:
        param: Parameter description
    """
    logger.info(f"Executing my_custom_tool with param: {param}")
    
    try:
        # Use http_client to make API calls
        response = await http_client.get(f"/endpoint/{param}")
        return response.text
    except Exception as e:
        logger.error(f"Error in my_custom_tool: {e}")
        raise
```

### Register the Tool

Edit `src/tools/registry.py`:

```python
from .example_tools import my_custom_tool, MyToolInput

def register_tools(mcp, container):
    # Get dependencies from container
    api_manager = container.api_manager()
    logger = container.logger()
    
    # Get HTTP client for your API
    my_api_client = api_manager.get("myapi")
    
    # Register your tool
    @mcp.tool(input_schema=MyToolInput)
    async def my_custom_tool_wrapper(param: str) -> str:
        return await my_custom_tool(
            param=param,
            http_client=my_api_client,
            logger=logger
        )
```

---

## Step 9: Production Deployment

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastmcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastmcp-server
  template:
    metadata:
      labels:
        app: fastmcp-server
    spec:
      containers:
      - name: mcp-server
        image: fastmcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "WARNING"
        - name: API_TIMEOUT
          value: "10"
        - name: PETSTORE_BASE_URL
          value: "https://petstore.swagger.io/v2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/apis
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Azure Container Apps

```bash
# Create resource group
az group create --name fastmcp-rg --location eastus

# Create container app
az containerapp create \
  --name fastmcp-server \
  --resource-group fastmcp-rg \
  --image fastmcp-server:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    ENVIRONMENT=production \
    LOG_LEVEL=WARNING \
    PETSTORE_BASE_URL=https://petstore.swagger.io/v2
```

---

## Step 10: Monitoring and Troubleshooting

### Check Container Status

```python
# In Python shell or script
from src.container import container

# Access logger
logger = container.logger()
logger.info("Test log message")

# Access API manager
api_manager = container.api_manager()
health = await api_manager.health_check()
print(health)  # {'petstore': 'healthy'}

# List configured APIs
apis = api_manager.list_apis()
print(apis)  # ['petstore']
```

### Common Issues

**Issue: ModuleNotFoundError for dependency_injector**
```bash
# Solution: Install with no-build-isolation
pip uninstall dependency-injector
pip install --no-build-isolation dependency-injector==4.48.3
```

**Issue: Logger not writing to file**
```bash
# Solution: Ensure logs directory exists
mkdir -p logs
chmod 755 logs
```

**Issue: API client returns connection errors**
```bash
# Solution: Check BASE_URL configuration
echo $PETSTORE_BASE_URL
# Verify API is accessible
curl https://petstore.swagger.io/v2/pet/1
```

**Issue: Container initialization fails**
```bash
# Solution: Check environment variables
python -c "from src.config import Settings; print(Settings().model_dump_json(indent=2))"
```

---

## Configuration Reference

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_NAME` | str | FastMCP-Server | Application name |
| `APP_VERSION` | str | 1.0.0 | Application version |
| `ENVIRONMENT` | str | development | Environment name |
| `HOST` | str | 0.0.0.0 | Server host |
| `PORT` | int | 8000 | Server port |
| `LOG_LEVEL` | str | INFO | Logging level |
| `LOG_FILE` | str | logs/app.log | Log file path |
| `API_TIMEOUT` | int | 10 | Global API timeout (seconds) |
| `API_MAX_RETRIES` | int | 3 | Global API retry count |
| `MAX_CONNECTIONS` | int | 100 | Max HTTP connections |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | int | 5 | Circuit breaker threshold |
| `CIRCUIT_BREAKER_TIMEOUT` | int | 60 | Circuit breaker timeout (seconds) |

### API Configuration Pattern

For each external API, define:
- `{API_NAME}_API_NAME` - API identifier (lowercase)
- `{API_NAME}_BASE_URL` - API base URL
- `{API_NAME}_ENABLED` - Enable/disable API

---

## Next Steps

1. ✅ Read [PRODUCTION_REVIEW.md](PRODUCTION_REVIEW.md) for architecture details
2. ✅ Read [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) for comprehensive documentation
3. ✅ Explore the codebase structure
4. ✅ Add your custom tools and APIs
5. ✅ Configure monitoring and alerting
6. ✅ Deploy to your environment

---

## Support & Resources

### Documentation
- FastMCP: https://gofastmcp.com
- dependency-injector: https://python-dependency-injector.ets-labs.org
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings
- HTTPX: https://www.python-httpx.org

### Code Structure
```
src/
├── main.py              # Application entry point
├── container.py         # Dependency injection container
├── config.py            # Configuration management
├── middleware.py        # Custom middleware
├── tools/
│   ├── example_tools.py # Tool implementations
│   └── registry.py      # Tool registration
└── utility/
    ├── api_manager.py   # Multi-API manager
    ├── http_client.py   # HTTP client with resilience
    ├── logging.py       # Logger setup
    └── exception_handlers.py  # Exception handling
```

---

## Success Criteria

After completing this guide, you should have:

✅ Server running on `http://localhost:8000`  
✅ Health endpoints responding  
✅ MCP tools callable  
✅ Logs writing to `logs/app.log`  
✅ External API integration working  
✅ Dependency injection container functioning  

Ready for production deployment! 🚀
