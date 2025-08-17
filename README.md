# Flask Helpdesk System

A comprehensive task management and ticketing platform built with Flask, featuring real-time notifications, external system integrations, and a modern web interface.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.3.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- MySQL Server (for Redmine integration)
- Oracle Client (for ERP integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd flask-helpdesk
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .flaskenv.example .flaskenv
   # Edit .flaskenv with your settings
   ```

4. **Configure database connections**
   ```bash
   cp config.ini.example config.ini
   # Edit config.ini with your database settings
   ```

5. **Initialize database**
   ```bash
   python -c "from blog import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at http://localhost:5000

## 🔗 Quick Links

- **Main Dashboard**: http://localhost:5000/tasks/my-tasks
- **Login Page**: http://localhost:5000/users/login
- **Admin Panel**: http://localhost:5000/admin (admin users only)

## ✨ Key Features

### 🔐 Authentication & Authorization
- **Role-based Access Control** - Admin, Redmine users, department-specific permissions
- **External Authentication** - Integration with Oracle ERP and LDAP systems
- **Session Management** - Secure session handling with Flask-Login

### 📋 Task Management
- **Full CRUD Operations** - Create, read, update, delete tasks through Redmine integration
- **Kanban Board Interface** - Drag-and-drop task management with real-time updates
- **Advanced Filtering** - Filter by status, priority, project, assignee, and custom fields
- **Bulk Operations** - Update multiple tasks simultaneously with progress tracking

### 🔔 Real-time Notifications
- **Browser Push Notifications** - Native browser notifications using Web Push API
- **WebSocket Support** - Real-time updates via Flask-SocketIO
- **Email Notifications** - Configurable email alerts for task changes
- **In-app Notifications** - Live notification feed with read/unread status

### 🔗 External Integrations
- **Redmine Integration** - Full API integration for project management
- **Oracle ERP Integration** - User authentication and profile synchronization
- **MySQL Database** - Direct database access for advanced queries
- **LDAP Support** - Enterprise directory integration

### 🎨 Modern UI/UX
- **Responsive Design** - Mobile-friendly interface with Bootstrap 5
- **Progressive Web App** - Service worker support for offline functionality
- **Dark/Light Theme** - User-configurable theme preferences
- **Accessibility** - WCAG 2.1 compliant interface

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask App     │    │   Databases     │
│                 │    │                 │    │                 │
│ • HTML/CSS/JS   │◄──►│ • Flask 2.3.3   │◄──►│ • SQLite (local)│
│ • Bootstrap 5   │    │ • SQLAlchemy    │    │ • MySQL (Redmine)│
│ • WebSocket     │    │ • Flask-SocketIO│    │ • Oracle (ERP)  │
│ • Service Worker│    │ • APScheduler   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ External APIs   │
                       │                 │
                       │ • Redmine API   │
                       │ • Push Services │
                       │ • Email SMTP    │
                       └─────────────────┘
```

## 📚 API Documentation

For comprehensive API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### Core API Endpoints

#### Authentication
- `POST /users/login` - User authentication
- `POST /users/register` - User registration
- `GET /users/logout` - User logout

#### Task Management
- `GET /tasks/api/task/<id>` - Get task details
- `PUT /tasks/api/task/<id>/status` - Update task status
- `POST /tasks/api/task` - Create new task
- `GET /tasks/my-tasks` - Get user's tasks

#### Notifications
- `GET /tasks/api/notifications` - Get user notifications
- `PUT /tasks/api/notifications/<id>/read` - Mark notification as read
- `POST /tasks/api/push-subscribe` - Subscribe to push notifications

#### WebSocket Events
- `join_notifications` - Join user's notification room
- `new_notification` - Receive real-time notifications
- `task_status_changed` - Receive task status updates

## 🛠️ Configuration

### Environment Variables (.flaskenv)
```bash
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
```

### Database Configuration (config.ini)
```ini
[database]
db_path = blog/db/blog.db

[mysql]
host = localhost
database = redmine_db
user = redmine_user
password = redmine_password

[oracle]
host = oracle_host
service_name = oracle_service
user = erp_user
password = erp_password

[redmine]
url = https://redmine.example.com
api_key = your_admin_api_key
anonymous_user_id = 4
```

### Push Notifications Setup
```ini
[push_notifications]
vapid_public_key = your_vapid_public_key
vapid_private_key = your_vapid_private_key
vapid_claim_email = admin@company.com
```

## 🔧 Development

### Project Structure
```
flask-helpdesk/
├── app.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── config.ini            # Configuration file
├── blog/                 # Main application package
│   ├── __init__.py       # Flask application factory
│   ├── models.py         # Database models
│   ├── settings.py       # Configuration classes
│   ├── tasks/            # Task management module
│   ├── user/             # User management module
│   ├── utils/            # Utility functions
│   ├── templates/        # HTML templates
│   └── static/           # Static assets
├── redmine.py            # Redmine integration
├── erp_oracle.py         # Oracle ERP integration
└── mysql_db.py           # MySQL database utilities
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=blog
```

### Development Server
```bash
# Run development server with auto-reload
python app.py

# Run with specific configuration
FLASK_ENV=development python app.py
```

## 🚀 Deployment

### Production Setup

1. **Configure production environment**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secret-key
   export DATABASE_URL=your-database-url
   ```

2. **Install production dependencies**
   ```bash
   pip install gunicorn
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
   ```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🧪 Testing

### API Testing with curl
```bash
# Login
curl -X POST http://localhost:5000/users/login \
  -d "username=admin&password=password" \
  -c cookies.txt

# Get tasks
curl -X GET http://localhost:5000/tasks/api/task/12345 \
  -b cookies.txt \
  -H "Accept: application/json"

# Update task status
curl -X PUT http://localhost:5000/tasks/api/task/12345/status \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"status_id": 3, "comment": "Task completed"}'
```

### WebSocket Testing
```javascript
// Connect to WebSocket
const socket = io('http://localhost:5000/notifications');

socket.on('connect', () => {
    console.log('Connected to notification service');
    socket.emit('join_notifications', { user_id: 1 });
});

socket.on('new_notification', (data) => {
    console.log('Notification received:', data);
});
```

## 📊 Monitoring & Logging

### Application Metrics
- **Performance Monitoring** - Request/response times, error rates
- **Usage Analytics** - User activity, feature usage statistics
- **System Health** - Database connections, external API status

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use meaningful commit messages

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check MySQL connection
mysql -h localhost -u redmine_user -p redmine_db

# Check Oracle connection
sqlplus erp_user/password@oracle_host:1521/ERP
```

**Push Notification Issues**
```bash
# Verify VAPID keys
python -c "from pywebpush import webpush; print('VAPID keys working')"

# Test notification endpoint
curl -X POST http://localhost:5000/tasks/api/push-subscribe \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "test", "keys": {"p256dh": "test", "auth": "test"}}'
```

**Performance Issues**
```bash
# Check application metrics
curl http://localhost:5000/admin/metrics

# Monitor database queries
tail -f app.log | grep "SQL"
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask** - Web framework
- **Redmine** - Project management integration
- **Bootstrap** - UI framework
- **Socket.IO** - Real-time communication
- **pywebpush** - Push notification support

## 📞 Support

For support and questions:
- **Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Issues**: Create an issue on GitHub
- **Email**: support@company.com

---

**Built with ❤️ using Flask and modern web technologies**