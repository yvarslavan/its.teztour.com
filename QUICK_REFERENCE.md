# Flask Helpdesk System - Quick Reference Guide

A quick reference for developers working with the Flask Helpdesk System APIs and components.

## 🚀 Quick Start Commands

```bash
# Setup
git clone <repository-url> && cd flask-helpdesk
pip install -r requirements.txt
python -c "from blog import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
python app.py

# Development
pytest                    # Run tests
black blog/ tests/        # Format code
flake8 blog/ tests/       # Lint code
```

## 🔗 Essential API Endpoints

### Authentication
```bash
# Login
POST /users/login
Content-Type: application/x-www-form-urlencoded
Body: username=admin&password=password

# Logout
GET /users/logout
```

### Tasks
```bash
# Get task details
GET /tasks/api/task/{task_id}

# Update task status
PUT /tasks/api/task/{task_id}/status
Content-Type: application/json
Body: {"status_id": 3, "comment": "Task completed"}

# Get user tasks
GET /tasks/my-tasks?status=In%20Progress&limit=25

# Create task
POST /tasks/api/task
Content-Type: application/json
Body: {"subject": "New task", "project_id": 1, "status_id": 1}
```

### Notifications
```bash
# Get notifications
GET /tasks/api/notifications?unread_only=true&limit=20

# Mark as read
PUT /tasks/api/notifications/{notification_id}/read

# Subscribe to push
POST /tasks/api/push-subscribe
Content-Type: application/json
Body: {"endpoint": "...", "keys": {"p256dh": "...", "auth": "..."}}
```

## 💻 Code Examples

### Python API Client
```python
import requests
import json

class HelpDeskAPI:
    def __init__(self, base_url, session_cookie=None):
        self.base_url = base_url
        self.session = requests.Session()
        if session_cookie:
            self.session.cookies.set('session', session_cookie)
    
    def login(self, username, password):
        response = self.session.post(f'{self.base_url}/users/login', data={
            'username': username, 'password': password
        })
        return response.status_code == 200
    
    def get_task(self, task_id):
        response = self.session.get(f'{self.base_url}/tasks/api/task/{task_id}')
        return response.json() if response.status_code == 200 else None
    
    def update_task_status(self, task_id, status_id, comment=None):
        data = {'status_id': status_id}
        if comment:
            data['comment'] = comment
        response = self.session.put(
            f'{self.base_url}/tasks/api/task/{task_id}/status',
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'}
        )
        return response.json() if response.status_code == 200 else None

# Usage
api = HelpDeskAPI('http://localhost:5000')
if api.login('admin', 'password'):
    task = api.get_task(12345)
    print(f"Task: {task['data']['subject']}")
```

### JavaScript WebSocket Client
```javascript
class NotificationClient {
    constructor(userId) {
        this.userId = userId;
        this.socket = io('/notifications');
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to notifications');
            this.socket.emit('join_notifications', { user_id: this.userId });
        });
        
        this.socket.on('new_notification', (data) => {
            this.showNotification(data.title, data.message);
            this.updateCounter(data.unread_count);
        });
        
        this.socket.on('task_status_changed', (data) => {
            this.updateTaskStatus(data.task_id, data.new_status);
        });
    }
    
    showNotification(title, message) {
        if (Notification.permission === 'granted') {
            new Notification(title, { body: message });
        }
    }
    
    updateCounter(count) {
        const counter = document.getElementById('notification-counter');
        if (counter) {
            counter.textContent = count;
            counter.style.display = count > 0 ? 'inline' : 'none';
        }
    }
    
    updateTaskStatus(taskId, newStatus) {
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
        if (taskElement) {
            const statusElement = taskElement.querySelector('.task-status');
            if (statusElement) {
                statusElement.textContent = newStatus;
            }
        }
    }
}

// Initialize
const notificationClient = new NotificationClient(currentUserId);
```

### Flask Route Example
```python
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get task details by ID."""
    try:
        # Your logic here
        task_data = get_task_from_redmine(task_id)
        
        return jsonify({
            'success': True,
            'data': task_data,
            'message': 'Task retrieved successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve task'
        }), 500

@api_bp.route('/tasks/<int:task_id>/status', methods=['PUT'])
@login_required
def update_task_status(task_id):
    """Update task status."""
    data = request.get_json()
    
    try:
        result = update_redmine_task_status(
            task_id=task_id,
            status_id=data['status_id'],
            comment=data.get('comment')
        )
        
        # Send notification
        send_task_notification(task_id, result['old_status'], result['new_status'])
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Task status updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update task status'
        }), 500
```

## 🗄️ Database Models Quick Reference

### User Model
```python
from blog.models import User

# Create user
user = User(
    username='johndoe',
    email='john@example.com',
    password=bcrypt.generate_password_hash('password').decode('utf-8'),
    full_name='John Doe',
    department='IT',
    is_redmine_user=True
)
db.session.add(user)
db.session.commit()

# Query users
admin_users = User.query.filter_by(is_admin=True).all()
redmine_users = User.query.filter_by(is_redmine_user=True).all()
user = User.query.filter_by(username='johndoe').first()
```

### Notifications Model
```python
from blog.models import Notifications

# Create notification
notification = Notifications(
    user_id=1,
    issue_id=12345,
    old_status='In Progress',
    new_status='Resolved',
    old_subj='Fix login issue',
    date_created=datetime.now()
)
db.session.add(notification)
db.session.commit()

# Query notifications
unread = Notifications.query.filter_by(user_id=1, is_read=False).all()
recent = Notifications.query.filter_by(user_id=1).order_by(Notifications.date_created.desc()).limit(10).all()
```

## 🔧 Configuration Quick Reference

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
database = redmine_production
user = redmine_user
password = redmine_password

[redmine]
url = https://redmine.company.com
api_key = your_admin_api_key
anonymous_user_id = 4
```

### Flask Application Configuration
```python
# blog/settings.py
class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///blog.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Notification settings
    PUSH_NOTIFICATIONS_ENABLED = True
    VAPID_PUBLIC_KEY = 'your-vapid-public-key'
    VAPID_PRIVATE_KEY = 'your-vapid-private-key'
    
    # External API settings
    REDMINE_URL = 'https://redmine.company.com'
    REDMINE_API_KEY = 'your-redmine-api-key'
```

## 🧪 Testing Quick Reference

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_models.py

# With coverage
pytest --cov=blog --cov-report=html

# Verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_user"
```

### Test Example
```python
import pytest
from blog import create_app, db
from blog.models import User

@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_user_creation(app):
    with app.app_context():
        user = User(username='test', email='test@example.com', password='hashed')
        db.session.add(user)
        db.session.commit()
        assert user.id is not None

def test_login_api(client):
    response = client.post('/users/login', data={
        'username': 'admin',
        'password': 'password'
    })
    assert response.status_code == 200
```

## 🔄 Common Workflows

### Task Status Update Workflow
```python
# 1. Get task details
task = get_task_by_id(task_id)

# 2. Update status in Redmine
result = update_redmine_task_status(task_id, new_status_id, comment)

# 3. Create local notification
notification = create_notification(user_id, task_id, old_status, new_status)

# 4. Send push notification
send_push_notification(user_id, notification_data)

# 5. Broadcast WebSocket update
broadcast_task_update(task_id, old_status, new_status, affected_users)
```

### User Authentication Workflow
```python
# 1. Validate credentials
user = User.query.filter_by(username=username).first()
if user and bcrypt.check_password_hash(user.password, password):
    # 2. Login user
    login_user(user, remember=remember_me)
    
    # 3. Update last seen
    user.last_seen = datetime.now()
    user.online = True
    db.session.commit()
    
    # 4. Redirect to dashboard
    return redirect('/tasks/my-tasks')
```

## 🚨 Error Handling

### API Error Response Format
```json
{
    "success": false,
    "error": "Resource not found",
    "message": "Task with ID 12345 was not found",
    "status_code": 404,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## 📊 Performance Tips

### Database Optimization
```python
# Use eager loading for relationships
users = User.query.options(joinedload(User.posts)).all()

# Use pagination for large datasets
users = User.query.paginate(page=1, per_page=25, error_out=False)

# Use database indexes
class User(db.Model):
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
```

### Caching
```python
from blog.utils.cache_manager import cache_manager

@cache_manager.cached(timeout=300)
def get_user_tasks(user_id):
    # Expensive database operation
    return tasks

# Cache invalidation
cache_manager.delete(f'user_tasks_{user_id}')
```

## 🔒 Security Checklist

- [ ] CSRF protection enabled
- [ ] SQL injection prevention (SQLAlchemy ORM)
- [ ] XSS protection (template escaping)
- [ ] Authentication required for sensitive endpoints
- [ ] Input validation and sanitization
- [ ] Secure session configuration
- [ ] HTTPS in production
- [ ] Rate limiting for API endpoints

## 📞 Support & Resources

- **Full Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **GitHub Issues**: Create an issue for bugs or questions
- **Email Support**: support@company.com

---

**Need more details? Check the comprehensive [API Documentation](API_DOCUMENTATION.md) for complete information.**