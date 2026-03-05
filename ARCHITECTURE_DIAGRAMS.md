# FastMCP Server - Architecture Diagrams

This document contains all visual architecture diagrams for the FastMCP Server project.

---

## 1. System Architecture Diagram

Shows the complete layered architecture from clients through the ASGI server, FastMCP framework, dependency injection container, and down to the infrastructure layer with HTTP clients and resilience patterns.

```mermaid
graph TB
    subgraph "External World"
        Client[MCP Client<br/>VS Code, etc.]
        API1[Petstore API<br/>petstore.swagger.io]
        API2[Future APIs<br/>weather, etc.]
    end

    subgraph "ASGI Server Layer"
        Uvicorn[Uvicorn ASGI Server<br/>:8000]
    end

    subgraph "FastMCP Application"
        FastMCP[FastMCP Framework<br/>mcp.app]
        
        subgraph "Starlette Layer"
            Middleware[Middleware<br/>Custom Processing]
            ExceptionHandlers[Exception Handlers<br/>404, 405, 422, 500]
            Routes[HTTP Routes<br/>/health, /health/apis]
        end
        
        MCPProtocol[MCP Protocol Handler<br/>JSON-RPC over HTTP]
    end

    subgraph "Application Core"
        Container[Dependency Injection Container<br/>DeclarativeContainer]
        
        subgraph "Providers"
            ConfigProvider[Config Provider<br/>Singleton]
            LoggerProvider[Logger Provider<br/>Singleton]
            APIManagerProvider[APIManager Provider<br/>Singleton]
        end
        
        Lifespan[Lifespan Manager<br/>Asynccontextmanager]
    end

    subgraph "Business Logic Layer"
        Tools[MCP Tools<br/>find_pets_by_status]
        Registry[Tool Registry<br/>Dependency Injection]
    end

    subgraph "Infrastructure Layer"
        Config[Config<br/>Environment Variables]
        Logger[Logger<br/>File + Console]
        APIManager[API Manager<br/>Multi-API Orchestration]
        
        subgraph "HTTP Clients"
            PetstoreClient[Petstore Client<br/>HTTPClientManager]
            FutureClient[Future Clients<br/>HTTPClientManager]
        end
        
        subgraph "Resilience"
            CircuitBreaker[Circuit Breaker<br/>5 failures / 60s]
            RetryLogic[Retry Logic<br/>Exponential Backoff]
            ConnectionPool[Connection Pool<br/>Max 100 connections]
        end
    end

    Client -->|HTTP POST /mcp| Uvicorn
    Uvicorn --> FastMCP
    FastMCP --> Middleware
    Middleware --> ExceptionHandlers
    ExceptionHandlers --> Routes
    Routes --> MCPProtocol
    MCPProtocol -->|Call Tool| Tools
    
    Tools -->|Request Dependency| Registry
    Registry -->|Resolve| Container
    Container --> ConfigProvider
    Container --> LoggerProvider
    Container --> APIManagerProvider
    
    ConfigProvider --> Config
    LoggerProvider --> Logger
    APIManagerProvider --> APIManager
    
    APIManager --> PetstoreClient
    APIManager --> FutureClient
    
    PetstoreClient --> CircuitBreaker
    PetstoreClient --> RetryLogic
    PetstoreClient --> ConnectionPool
    
    CircuitBreaker -->|HTTP Request| API1
    FutureClient -->|HTTP Request| API2
    
    Lifespan -.->|Startup| Container
    Lifespan -.->|Shutdown| APIManager

    style Container fill:#e1f5ff
    style Config fill:#fff4e1
    style Logger fill:#fff4e1
    style APIManager fill:#fff4e1
    style CircuitBreaker fill:#ffe1e1
    style RetryLogic fill:#ffe1e1
    style ConnectionPool fill:#ffe1e1
```

**Key Features**:
- Clean layered architecture (Server → Application → Core → Business Logic → Infrastructure)
- Color-coded components (Blue: Container, Yellow: Config/Logger/APIManager, Red: Resilience)
- Complete dependency flow from external APIs through to clients
- Lifecycle management integration

---

## 2. Request Flow - Tool Call Lifecycle

Sequence diagram showing the complete flow of a tool request from client through all layers and back.

```mermaid
sequenceDiagram
    participant Client
    participant Uvicorn
    participant FastMCP
    participant Middleware
    participant ExceptionHandler
    participant Tool
    participant Registry
    participant Container
    participant APIManager
    participant HTTPClient
    participant CircuitBreaker
    participant ExternalAPI

    Client->>Uvicorn: HTTP POST /mcp/v1/tools/call
    Uvicorn->>FastMCP: ASGI Request
    FastMCP->>Middleware: Process Request
    Middleware->>ExceptionHandler: Error Boundary
    
    ExceptionHandler->>Tool: Execute find_pets_by_status
    Tool->>Registry: Get Dependencies
    Registry->>Container: Resolve api_manager & logger
    Container-->>Registry: Return instances
    Registry-->>Tool: Inject dependencies
    
    Tool->>APIManager: Get "petstore" client
    APIManager-->>Tool: Return HTTPClientManager
    
    Tool->>HTTPClient: GET /pet/findByStatus
    HTTPClient->>CircuitBreaker: Check state
    
    alt Circuit Closed
        CircuitBreaker->>ExternalAPI: HTTP GET
        ExternalAPI-->>CircuitBreaker: 200 OK + Data
        CircuitBreaker-->>HTTPClient: Success
        CircuitBreaker->>CircuitBreaker: Reset failure count
    else Circuit Open
        CircuitBreaker-->>HTTPClient: Fast fail
        HTTPClient-->>Tool: Error: Circuit Open
    end
    
    alt Request Failed
        HTTPClient->>HTTPClient: Exponential backoff retry
        HTTPClient->>CircuitBreaker: Retry request
    end
    
    HTTPClient-->>Tool: API Response
    Tool-->>ExceptionHandler: Tool Result
    ExceptionHandler-->>Middleware: Response
    Middleware-->>FastMCP: HTTP Response
    FastMCP-->>Uvicorn: ASGI Response
    Uvicorn-->>Client: JSON-RPC Response
```

**Key Features**:
- Step-by-step request handling from client to external API
- Dependency injection resolution shown explicitly
- Circuit breaker decision logic (Circuit Closed vs Open)
- Retry mechanism with exponential backoff
- Complete response chain back to client

---

## 3. Circuit Breaker State Machine

State diagram showing the 3-state circuit breaker pattern for protection against cascading failures.

```mermaid
stateDiagram-v2
    [*] --> Closed: Initialize
    
    Closed --> Closed: Success<br/>(reset counter)
    Closed --> Closed: Failure<br/>(increment counter)
    Closed --> Open: Threshold reached<br/>(5 failures)
    
    Open --> Open: All requests<br/>(fast fail)
    Open --> HalfOpen: Timeout expires<br/>(60 seconds)
    
    HalfOpen --> Closed: Test request<br/>succeeds
    HalfOpen --> Open: Test request<br/>fails
    
    note right of Closed
        Normal Operation
        - Allow all requests
        - Track failures
    end note
    
    note right of Open
        Fast Fail Mode
        - Reject all requests
        - No load on failing service
    end note
    
    note right of HalfOpen
        Recovery Test
        - Allow one request
        - Determine if recovered
    end note
```

**Key Features**:
- **CLOSED State**: Normal operation, track failures, reset on success
- **OPEN State**: Fast-fail after 5 consecutive failures, prevent cascading
- **HALF_OPEN State**: Test recovery after 60-second timeout
- Automatic recovery detection and state transitions

---

## 4. Application Lifecycle - Startup & Shutdown

Detailed sequence diagram showing the complete application lifecycle from startup through running to graceful shutdown.

```mermaid
sequenceDiagram
    participant OS
    participant Uvicorn
    participant FastMCP
    participant Lifespan
    participant Container
    participant APIManager
    participant HTTPClients

    OS->>Uvicorn: Start uvicorn
    Uvicorn->>FastMCP: Initialize app
    FastMCP->>Lifespan: Enter lifespan context
    
    Note over Lifespan: Startup Phase (before yield)
    
    Lifespan->>Container: Initialize container
    Container->>Container: Create config singleton
    Container->>Container: Create logger singleton
    Container->>Container: Create api_manager singleton
    
    Lifespan->>Container: init_container_dependencies()
    Container->>APIManager: initialize()
    APIManager->>HTTPClients: Create clients for each API
    HTTPClients-->>APIManager: Clients ready
    APIManager-->>Container: Initialization complete
    
    Container-->>Lifespan: Dependencies initialized
    
    Note over Lifespan: Application Running
    Lifespan->>FastMCP: Ready for requests
    FastMCP->>Uvicorn: Listening on port 8000
    
    Note over Uvicorn: Handle requests...
    
    OS->>Uvicorn: SIGTERM signal
    Uvicorn->>FastMCP: Shutdown signal
    FastMCP->>Lifespan: Exit context
    
    Note over Lifespan: Shutdown Phase (after yield)
    
    Lifespan->>Container: shutdown_container_dependencies()
    Container->>APIManager: close_all()
    APIManager->>HTTPClients: Close all connections
    HTTPClients-->>APIManager: Connections closed
    APIManager-->>Container: Cleanup complete
    
    Container-->>Lifespan: Shutdown complete
    Lifespan-->>FastMCP: Lifespan ended
    FastMCP-->>Uvicorn: Shutdown complete
    Uvicorn-->>OS: Process exit
```

**Key Features**:
- **Startup Phase**: Container initialization, singleton creation, API client setup
- **Running Phase**: Request handling with initialized dependencies
- **Shutdown Phase**: Graceful cleanup, connection closure, resource release
- ASGI lifespan context manager pattern shown explicitly

---

## 5. Kubernetes Deployment Architecture

Complete deployment architecture showing containerization, orchestration, and monitoring integration.

```mermaid
graph TB
    subgraph "Container Registry"
        Registry[Docker Registry<br/>Docker Hub, ACR, ECR]
    end
    
    subgraph "Build Pipeline"
        Source[Source Code<br/>GitHub, GitLab]
        Build[Docker Build<br/>Multi-stage]
        Tag[Image Tagging<br/>:latest, :v1.0.0]
    end
    
    subgraph "Kubernetes Cluster"
        Ingress[Ingress Controller<br/>NGINX, Traefik]
        Service[Service<br/>ClusterIP]
        
        subgraph "Deployment"
            Pod1[Pod 1<br/>FastMCP Server]
            Pod2[Pod 2<br/>FastMCP Server]
            Pod3[Pod 3<br/>FastMCP Server]
        end
        
        ConfigMap[ConfigMap<br/>Environment Variables]
        Secret[Secret<br/>API Keys]
    end
    
    subgraph "External"
        Client[Clients]
        API1[External APIs]
    end
    
    subgraph "Monitoring"
        Logs[Log Aggregation<br/>ELK, Loki]
        Metrics[Metrics<br/>Prometheus]
        Health[Health Checks<br/>Kubernetes Probes]
    end
    
    Source --> Build
    Build --> Tag
    Tag -->|Push| Registry
    
    Registry -->|Pull| Pod1
    Registry -->|Pull| Pod2
    Registry -->|Pull| Pod3
    
    ConfigMap -.->|Mount| Pod1
    ConfigMap -.->|Mount| Pod2
    ConfigMap -.->|Mount| Pod3
    
    Secret -.->|Mount| Pod1
    Secret -.->|Mount| Pod2
    Secret -.->|Mount| Pod3
    
    Pod1 --> Service
    Pod2 --> Service
    Pod3 --> Service
    
    Service --> Ingress
    Ingress --> Client
    
    Pod1 -->|HTTP| API1
    Pod2 -->|HTTP| API1
    Pod3 -->|HTTP| API1
    
    Pod1 -.->|Logs| Logs
    Pod2 -.->|Logs| Logs
    Pod3 -.->|Logs| Logs
    
    Pod1 -.->|Metrics| Metrics
    Pod2 -.->|Metrics| Metrics
    Pod3 -.->|Metrics| Metrics
    
    Health -.->|Probe| Pod1
    Health -.->|Probe| Pod2
    Health -.->|Probe| Pod3

    style Pod1 fill:#e1f5ff
    style Pod2 fill:#e1f5ff
    style Pod3 fill:#e1f5ff
```

**Key Features**:
- Build pipeline from source to container registry
- Kubernetes deployment with 3 replicas for high availability
- ConfigMap and Secret injection into pods
- Service and Ingress for load balancing
- External API connectivity
- Monitoring integration (logs, metrics, health checks)
- Dashed lines showing configuration/monitoring injection

---

## Diagram Legend

### Colors & Styling

| Color | Meaning | Components |
|-------|---------|-----------|
| **Light Blue** | Dependency Injection | Container, Providers |
| **Light Yellow** | Configuration | Config, Logger, APIManager |
| **Light Red** | Resilience Patterns | Circuit Breaker, Retry Logic, Connection Pool |
| **Cyan** | Application Pods | FastMCP Server instances |

### Line Types

| Line Type | Meaning |
|-----------|---------|
| **Solid Arrow** | Direct dependency/flow |
| **Dashed Arrow** | Configuration/monitoring injection |
| **Bidirectional** | Two-way communication |

---

## How to Use These Diagrams

### For Documentation
1. **System Architecture**: Use as overview in README or architecture docs
2. **Request Flow**: Use to explain how requests are processed
3. **Circuit Breaker**: Use to explain resilience patterns
4. **Lifecycle**: Use to explain startup/shutdown behavior
5. **Deployment**: Use for DevOps and infrastructure documentation

### For Presentations
- Copy diagram code into Mermaid Live Editor (https://mermaid.live)
- Export as PNG/SVG for slides
- Use in architecture review meetings

### For Team Communication
- Share this file with team members
- Reference specific diagrams in pull request descriptions
- Use in architecture decision records (ADRs)

### For Implementation Reference
- Refer to diagrams when adding new features
- Ensure new components follow the layered architecture
- Use dependency flow to understand injection points

---

## Diagram Updates

When the architecture changes:

1. **System Architecture**: Update when adding new layers or major components
2. **Request Flow**: Update when changing tool execution pipeline
3. **Circuit Breaker**: Update if changing failure thresholds/timeouts
4. **Lifecycle**: Update if changing startup/shutdown behavior
5. **Deployment**: Update when changing infrastructure strategy

---

## Related Documentation

- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - Setup and usage guide
- [PRODUCTION_REVIEW.md](PRODUCTION_REVIEW.md) - Architecture and design review
- [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) - Detailed technical documentation

---

**Last Updated**: March 2, 2026  
**FastMCP Version**: 3.0.2  
**Python Version**: 3.11+
