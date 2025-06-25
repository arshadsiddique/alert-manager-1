# Grafana-Jira Alert Manager

A full-stack application that automatically syncs alerts from Grafana to Jira Service Management, enabling seamless incident management workflow.

## 🚀 Features

- **Real-time Alert Sync**: Automatically syncs active alerts from Grafana to Jira Service Management
- **Jira Integration**: Creates incidents, acknowledges, and resolves issues in Jira
- **Alert Management**: View, acknowledge, and resolve alerts through a modern web interface
- **Configurable Sync**: Customizable cron jobs for alert synchronization
- **Status Tracking**: Track alert status across both Grafana and Jira
- **Direct Links**: Quick access to Grafana dashboards and Jira issues

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **Frontend**: React with Ant Design components
- **Database**: PostgreSQL
- **Scheduler**: APScheduler for periodic alert sync
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose
- Grafana instance with API access
- Jira Service Management with API access
- Valid API tokens for both services

## 🔧 Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd grafana-jira-alert-manager
```

### 2. Configure Environment Variables

Copy the example environment file and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Database Configuration
DATABASE_URL="postgresql://user:password@postgres:5432/alertdb"

# Grafana Configuration
GRAFANA_API_URL="https://grafana.observability.devo.com"
GRAFANA_API_KEY="your_actual_grafana_api_key"

# Jira Service Management Configuration
JIRA_URL="https://devoinc.atlassian.net"
JIRA_USER_EMAIL="your-email@domain.com"
JIRA_API_TOKEN="your_actual_jira_api_token"
JIRA_PROJECT_KEY="OP"
JIRA_INCIDENT_ISSUE_TYPE="Incident"
JIRA_ACKNOWLEDGE_TRANSITION_NAME="To Do"
JIRA_RESOLVE_TRANSITION_NAME="Completed"

# Sync Configuration
GRAFANA_SYNC_INTERVAL_SECONDS=600

# Frontend Configuration
REACT_APP_API_BASE_URL="http://localhost:8000"
REACT_APP_JIRA_URL="https://devoinc.atlassian.net"
```

### 3. Obtain API Credentials

#### Grafana API Key
1. Go to your Grafana instance
2. Navigate to Configuration → API Keys
3. Create a new API key with Admin permissions
4. Copy the key to `GRAFANA_API_KEY`

#### Jira API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Copy the token to `JIRA_API_TOKEN`
4. Set your Jira email in `JIRA_USER_EMAIL`

### 4. Configure Jira Workflow

Ensure your Jira project has the correct workflow transitions:
- Update `JIRA_ACKNOWLEDGE_TRANSITION_NAME` with the exact name of your acknowledge transition
- Update `JIRA_RESOLVE_TRANSITION_NAME` with the exact name of your resolve transition

### 5. Start the Application

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Backend API (port 8000)
- Frontend web app (port 3000)

### 6. Access the Application

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📱 Usage

### Alert Management
1. **View Alerts**: The main dashboard shows all alerts with their status
2. **Acknowledge Alerts**: Select alerts and click "Acknowledge in Jira" to transition them
3. **Resolve Alerts**: Select alerts and click "Resolve in Jira" to close them
4. **Sync Alerts**: Click "Sync Alerts" to manually trigger synchronization
5. **View in Jira**: Click on Jira issue links to open issues directly

### Configuration
1. Navigate to the Configuration tab
2. View and modify cron job schedules
3. Enable/disable automatic synchronization

## 🔄 How It Works

1. **Alert Detection**: The system periodically queries Grafana for active alerts
2. **Issue Creation**: New alerts automatically create incidents in Jira with proper labels and priority
3. **Status Sync**: Alert statuses are synchronized between Grafana and Jira
4. **Auto-Resolution**: When alerts are resolved in Grafana, corresponding Jira issues are automatically resolved
5. **Manual Management**: Users can acknowledge and resolve alerts through the web interface

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose down && docker-compose up -d --build

# Reset database
docker-compose down -v && docker-compose up -d
```

## 🔧 API Endpoints

### Alerts
- `GET /api/alerts` - List all alerts
- `GET /api/alerts/{id}` - Get specific alert
- `POST /api/alerts/acknowledge` - Acknowledge alerts
- `POST /api/alerts/resolve` - Resolve alerts
- `POST /api/alerts/sync` - Trigger sync

### Configuration
- `GET /api/config/cron` - List cron configurations
- `POST /api/config/cron` - Create cron job
- `PUT /api/config/cron/{id}` - Update cron job

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

## 🔍 Troubleshooting

### Common Issues

1. **Jira Authentication Errors**
   - Verify API token and email are correct
   - Ensure the user has permissions to create issues in the project

2. **Grafana Connection Issues**
   - Check API key permissions
   - Verify Grafana URL is accessible

3. **Workflow Transition Errors**
   - Verify transition names exactly match your Jira workflow
   - Check that transitions are available for the current issue status

4. **Database Connection Issues**
   - Ensure PostgreSQL container is running
   - Check database credentials in environment variables

### Logs
```bash
# Backend logs
docker-compose logs backend

# Frontend logs
docker-compose logs frontend

# Database logs
docker-compose logs postgres
```

## 📊 Monitoring

The application provides several monitoring endpoints:
- Health check: `/health`
- Metrics: Built-in logging for sync operations
- Status tracking: Real-time alert status in the web interface

## 🚨 Security Considerations

- Store API tokens securely using environment variables
- Use HTTPS in production
- Regularly rotate API tokens
- Implement proper access controls for the web interface
- Consider using secrets management for sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue in the repository