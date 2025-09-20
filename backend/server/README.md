# SIEM AI Agent Backend

A sophisticated conversational SIEM assistant built with FastAPI that enables natural language querying of security event data. This backend serves as the API layer for the **Project Sentinel** hackathon solution, addressing the SIH problem statement for "Conversational SIEM Assistant for Investigation and Automated Threat Reporting using NLP."

## 🎯 Project Overview

This system provides an NLP-powered interface that connects with ELK SIEMs (Elastic SIEM/Wazuh) to support:

- **Conversational Investigations**: Multi-turn natural language queries with context preservation
- **Automated Report Generation**: Natural language report requests with charts and summaries
- **Intelligent Query Translation**: Natural language to Elasticsearch DSL/KQL conversion
- **Context Management**: Maintains dialogue history for iterative queries

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Elasticsearch │
│   Interface     │───▶│   Backend       │───▶│   SIEM Data     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   NLP Service   │
                       │   (Person B)    │
                       └─────────────────┘
```

### Core Components

1. **NLP Service** (`nlp_service.py`) - Converts natural language to Elasticsearch DSL
2. **SIEM Connector** (`siem_connector.py`) - Handles Elasticsearch connections and mock data
3. **Context Manager** (`context_manager.py`) - Manages conversation state and multi-turn queries
4. **API Layer** (`main.py`) - FastAPI application with REST endpoints
5. **Data Models** (`models.py`) - Pydantic models for API contracts

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Optional: Elasticsearch/Wazuh instance (falls back to mock data)

### Installation

1. **Clone and navigate to the server directory:**
   ```bash
   cd backend/server
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment (optional):**
   ```bash
   copy .env.example .env
   # Edit .env with your configuration
   ```

5. **Start the server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Verify Installation

Visit http://localhost:8000/docs to access the interactive API documentation.

## 📡 API Endpoints

### Core Endpoints

#### `POST /query` - Natural Language Query
Process natural language security queries with context support.

**Request:**
```json
{
  "question": "Show me failed login attempts from external IPs",
  "session_id": "optional-session-id",
  "context": ["previous queries for context"],
  "time_range": "last 24 hours",
  "max_results": 20
}
```

**Response:**
```json
{
  "summary": "Found 15 security events for 'failed login attempts from external IPs'.",
  "results": [
    {
      "timestamp": "2025-09-20T21:15:00Z",
      "source_ip": "203.0.113.15",
      "user": "admin",
      "rule_description": "sshd: authentication failed.",
      "severity": "medium",
      "details": "SSH authentication failure from external IP"
    }
  ],
  "query_stats": {
    "total_hits": 15,
    "query_time_ms": 125,
    "indices_searched": ["wazuh-alerts-*"]
  },
  "session_id": "session-uuid",
  "suggestions": [
    "Show me successful logins from the same IPs",
    "Filter by high severity events only"
  ]
}
```

#### `POST /report` - Generate Security Reports
Create automated security reports with analysis and visualizations.

**Request:**
```json
{
  "report_type": "malware_summary",
  "time_period": "last_week",
  "include_charts": true,
  "filters": {
    "severity": "high"
  }
}
```

#### `GET /health` - Health Check
Check system health and connectivity status.

### Context Management

#### `GET /context/{session_id}` - Get Session Context
Retrieve conversation history for a session.

#### `DELETE /context/{session_id}` - Clear Session Context
Clear conversation history for a session.

### System Endpoints

#### `GET /siem/status` - SIEM Connection Status
Check Elasticsearch connectivity and data source status.

#### `POST /siem/mock-mode` - Toggle Mock Mode
Enable/disable mock data mode for testing.

#### `GET /metrics` - System Metrics
Get API usage statistics and performance metrics.

## 🔧 Configuration

### Environment Variables

The application supports extensive configuration through environment variables. See `.env.example` for all available options.

**Key Configuration Options:**

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Elasticsearch Configuration
ELASTICSEARCH_HOST=http://localhost:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=changeme

# Development Settings
FORCE_MOCK_DATA=false
DEBUG_MODE=false
```

### Configuration Profiles

The system supports different configuration profiles:

- **Development**: Debug mode, mock data, verbose logging
- **Production**: Security hardened, performance optimized
- **Testing**: Minimal configuration for automated tests

Set the environment with:
```bash
export ENVIRONMENT=production
```

## 🧠 NLP Service Integration

The current implementation includes a sophisticated placeholder for the NLP service that demonstrates expected functionality:

### Query Pattern Recognition
- Authentication events: "failed login", "brute force"
- Network events: "suspicious connection", "external traffic"
- Malware events: "malware detection", "virus scan"
- File events: "file access", "sensitive files"

### Context-Aware Processing
- Multi-turn conversation support
- Query refinement and filtering
- Historical context consideration

### Future Integration Points
The NLP service is designed for easy integration with actual ML models:

```python
# Current interface (placeholder)
def generate_dsl_query(question: str, context: List[str]) -> Dict[str, Any]:
    # Placeholder implementation
    pass

# Future integration point for Person B's work
def generate_dsl_query_ml(question: str, context: List[str]) -> Dict[str, Any]:
    # Actual ML model implementation
    pass
```

## 🗄️ Data Sources

### Elasticsearch Integration
- **Primary**: Wazuh alerts (`wazuh-alerts-*`)
- **Secondary**: Filebeat logs (`filebeat-*`)
- **Archives**: Wazuh archives (`wazuh-archives-*`)

### Mock Data Mode
When Elasticsearch is unavailable, the system falls back to realistic mock security event data:

- 12 realistic security events covering various attack vectors
- MITRE ATT&CK framework mappings
- Severity levels and geographic data
- Multiple log sources (SSH, DNS, web, file system)

## 🔍 Query Processing Flow

1. **Input Processing**: Parse natural language query and extract intent
2. **Context Retrieval**: Get relevant conversation history
3. **DSL Generation**: Convert to Elasticsearch DSL query
4. **Query Execution**: Execute against SIEM data source
5. **Result Processing**: Format and enrich results
6. **Response Generation**: Create natural language summary
7. **Context Update**: Update conversation history

## 📊 Conversation Context

The system maintains intelligent conversation context to support multi-turn queries:

### Context Features
- **Session Management**: UUID-based session tracking
- **Query History**: Maintains last 10 queries per session
- **Active Filters**: Tracks persistent filters across queries
- **Relevance Scoring**: Identifies relevant previous queries
- **Automatic Cleanup**: Removes expired sessions

### Context-Aware Queries
Users can ask follow-up questions:
- "Show me more details about those events"
- "Filter by the same user"
- "What happened before that?"

## 🔐 Security Considerations

### Authentication & Authorization
- API key support (configurable header)
- CORS configuration for frontend integration
- Input validation and sanitization

### Data Security
- Secure Elasticsearch connection options
- Certificate verification controls
- Environment-based configuration

### Production Hardening
- Rate limiting considerations
- Input size limits
- Error message sanitization

## 🚦 Testing

### Manual Testing
1. **Start the server**: `python main.py`
2. **Visit API docs**: http://localhost:8000/docs
3. **Test queries**: Use the interactive documentation

### Example Test Queries
```bash
# Test basic query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me failed login attempts"}'

# Test health check
curl http://localhost:8000/health

# Test SIEM status
curl http://localhost:8000/siem/status
```

### Unit Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest tests/
```

## 📈 Performance Considerations

### Query Optimization
- Default result limits (20 events)
- Configurable timeouts (30 seconds)
- Index pattern optimization

### Context Management
- Session limit enforcement (1000 sessions)
- Automatic cleanup of expired sessions
- Memory-efficient storage

### Scalability
- Stateless API design
- Horizontal scaling ready
- Database-backed context storage (future)

## 🔄 Integration Points

### Person A (SIEM Setup)
- Elasticsearch endpoint configuration
- Index pattern definitions
- Authentication setup

### Person B (NLP Development)
- Drop-in replacement for `nlp_service.py`
- Standardized function interfaces
- Context-aware query processing

### Frontend Integration
- RESTful API design
- WebSocket support (future)
- Real-time event streaming

## 🐛 Troubleshooting

### Common Issues

**Elasticsearch Connection Failed:**
```
❌ Failed to connect to http://localhost:9200
```
- Verify Elasticsearch is running
- Check network connectivity
- Review authentication credentials
- System falls back to mock data automatically

**Module Import Errors:**
```
ModuleNotFoundError: No module named 'fastapi'
```
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**Permission Denied:**
```
PermissionError: [Errno 13] Permission denied
```
- Check file permissions
- Ensure log directory is writable
- Run with appropriate user permissions

### Debug Mode
Enable debug mode for verbose logging:
```bash
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
```

### Mock Data Testing
Force mock data mode for testing:
```bash
export FORCE_MOCK_DATA=true
```

## 🚀 Deployment

### Development Deployment
```bash
python main.py
# or
uvicorn main:app --reload
```

### Production Deployment
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or use the production configuration
export ENVIRONMENT=production
python main.py
```

### Docker Deployment (Future)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## 📝 API Documentation

The API provides comprehensive documentation through:
- **OpenAPI/Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **JSON Schema**: http://localhost:8000/openapi.json

## 🤝 Contributing

### Code Structure
```
server/
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── nlp_service.py       # NLP query processing
├── siem_connector.py    # Elasticsearch integration
├── context_manager.py   # Conversation context
├── config.py           # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example        # Configuration template
└── mock_siem_data.json # Test data
```

### Development Guidelines
1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include comprehensive docstrings
4. Write unit tests for new features
5. Update API documentation

## 📄 License

This project is part of the SIH hackathon submission for ISRO's SIEM AI Agent challenge.

## 🆘 Support

For technical support or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Examine log output for error details
4. Test with mock data mode for isolation

---

## 🎉 Next Steps for Future Development

### Phase 1: Enhanced NLP Integration
- Replace placeholder NLP service with actual ML models
- Implement entity recognition for security terms
- Add query intent classification
- Support for complex temporal queries

### Phase 2: Advanced Features
- Real-time event streaming
- Automated threat hunting workflows
- Custom alerting and notifications
- Integration with threat intelligence feeds

### Phase 3: AI Agent Capabilities
- Autonomous investigation workflows
- Predictive threat analysis
- Automated response recommendations
- Learning from user interactions

### Phase 4: Enterprise Features
- Multi-tenant support
- Role-based access control
- Audit logging and compliance
- High availability and clustering

The current implementation provides a solid foundation for all these future enhancements while being immediately usable for hackathon demonstration and further development.