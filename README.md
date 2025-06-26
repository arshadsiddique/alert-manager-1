# Grafana-JSM Alert Manager v2.0

A comprehensive alert management system that automatically syncs alerts from Grafana to Jira Service Management (JSM) using the latest JSM API endpoints.

## 🚀 Key Features

- **JSM API Integration**: Uses the current JSM API endpoints (not deprecated Opsgenie)
- **Intelligent Alert Matching**: Multiple matching strategies (alias, tags, content, time-proximity)
- **Real-time Sync**: Configurable cron jobs for automatic synchronization
- **Web Dashboard**: Modern React interface with Ant Design components
- **Bulk Operations**: Acknowledge or resolve multiple alerts simultaneously
- **Production Filtering**: Automatically filters out non-production alerts

## 🏗️ Architecture

### Backend
- **FastAPI** with SQLAlchemy ORM
- **PostgreSQL** database
- **APScheduler** for cron jobs
- **JSM API v1** integration with proper authentication

### Frontend
- **React 18** with hooks
- **Ant Design** component library
- **Axios** for API communication
- **Moment.js** for date handling

### Database Schema
- Comprehensive alert model with JSM fields
- Alert matching metadata (confidence scores, match types)
- Legacy Jira compatibility fields
- Optimized indexes for performance

## 📋 Prerequisites

- Docker and Docker Compose
- Grafana instance with API access
- Jira Service Management with API access
- JSM Cloud ID (auto-retrieved from tenant info)

## 🔧 Quick Setup

### 1. Clone and Configure

```bash
git clone <repository-url>
cd grafana-jsm-alert-manager

# Copy environment configuration
cp .env.example .env
```

### 2. Update Environment Variables

Edit `.env` with your actual values:

```bash
# Grafana Configuration
GRAFANA_API_URL="https://grafana.observability.devo.com"
GRAFANA_API_KEY="your_actual_grafana_api_key"

# JSM Configuration (NEW FORMAT)
JIRA_URL="https://devoinc.atlassian.net"
JIRA_USER_EMAIL="your-email@devo.com"
JIRA_API_TOKEN="your_actual_jira_api_token"
JSM_CLOUD_ID="cfe6e1fe-26bb-4354-9cf1-fffaf23319db"  # Your actual cloud ID
```

### 3. Start the Application

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Backend API (port 8000)
- Frontend web app (port 3000)

### 4. Access the Application

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔄 How It Works

### Alert Matching Process

1. **Fetch from Sources**: Gets active alerts from Grafana and JSM
2. **Multi-Strategy Matching**:
   - **Alias Matching** (95% confidence): SHA256 hash of alert characteristics
   - **Tag Matching** (70-90% confidence): alertname, instance, cluster correlation
   - **Content Similarity** (70-85% confidence): Summary/description word matching
   - **Time Proximity** (50-70% confidence): Alerts created within time window

3. **Database Storage**: Stores matched alerts with confidence scores
4. **Status Sync**: Bidirectional status updates between systems

### JSM API Integration

- **Authentication**: Basic Auth with email:API_token
- **Rate Limiting**: Built-in rate limiting (100 requests/minute)
- **Async Operations**: Proper handling of JSM's async operation model
- **Error Handling**: Exponential backoff retry logic

## 📊 UI Features

### Alert Dashboard
- Real-time alert display with auto-refresh
- Advanced filtering (severity, status, match type, cluster)
- Bulk operations (acknowledge/resolve multiple alerts)
- JSM integration status indicators

### Alert Details
- Complete alert information from both Grafana and JSM
- Match confidence and type display
- Direct links to Grafana dashboards and JSM alerts
- Action history tracking

### Configuration Panel
- Cron job management for sync schedules
- Real-time job status monitoring
- Easy schedule modifications

## 🔧 Configuration

### Alert Matching Settings

```bash
# Confidence threshold for auto-matching
ALERT_MATCH_CONFIDENCE_THRESHOLD=50.0

# Time window for proximity matching
ALERT_MATCH_TIME_WINDOW_MINUTES=15

# Alert filtering
FILTER_NON_PROD_ALERTS=true
EXCLUDED_CLUSTERS=["stage", "dev", "test"]
EXCLUDED_ENVIRONMENTS=["devo-stage-eu"]
```

### Sync Configuration

```bash
# Sync intervals (seconds)
GRAFANA_SYNC_INTERVAL_SECONDS=300
JSM_SYNC_INTERVAL_SECONDS=300

# Feature flags
USE_JSM_MODE=true
ENABLE_AUTO_CLOSE=true
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose down && docker-compose up -d --build

# Reset database
docker-compose down -v && docker-compose up -d
```

## 🔍 Monitoring

### Health Endpoints
- `/health` - Overall system health
- `/api/info` - API capabilities and statistics
- `/api/alerts/sync/summary` - Sync statistics

### Logging
- Structured logging with correlation IDs
- JSM API request/response logging
- Alert matching decision logging
- Performance metrics

## 🛠️ Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## 🔧 Troubleshooting

### Common Issues

1. **JSM Authentication Errors**
   - Verify API token and email are correct
   - Check Cloud ID is properly set
   - Ensure user has JSM permissions

2. **Alert Matching Issues**
   - Check match confidence thresholds
   - Review excluded environments/clusters
   - Verify Grafana alert format

3. **Database Connection Issues**
   - Ensure PostgreSQL container is running
   - Check database credentials in environment variables

### Debug Mode
Set `DEBUG=true` in environment variables for detailed logging.

## 📈 Performance

### Optimizations
- Database indexes on frequently queried fields
- Connection pooling for API requests
- Efficient alert matching algorithms
- Frontend virtualization for large datasets

### Scaling Considerations
- Horizontal scaling with multiple backend instances
- Database partitioning for large alert volumes
- Redis caching for frequent lookups
- Load balancing for high availability

## 🔒 Security

- Environment variable configuration for sensitive data
- API rate limiting
- Input validation and sanitization
- CORS configuration
- Database connection encryption

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue in the repository

---

**Migration Status**: ✅ Successfully migrated from deprecated Opsgenie API to JSM API v1
**Version**: 2.0.0
**Last Updated**: June 2025
