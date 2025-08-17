# Flask Helpdesk System - Comprehensive API Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Authentication System](#authentication-system)
4. [Database Models](#database-models)
5. [Core APIs](#core-apis)
   - [User Management APIs](#user-management-apis)
   - [Task Management APIs](#task-management-apis)
   - [Notification System APIs](#notification-system-apis)
   - [Post Management APIs](#post-management-apis)
6. [External Integrations](#external-integrations)
   - [Redmine Integration](#redmine-integration)
   - [Oracle ERP Integration](#oracle-erp-integration)
7. [Utility Functions](#utility-functions)
8. [WebSocket Events](#websocket-events)
9. [Configuration](#configuration)
10. [Examples & Usage](#examples--usage)

---

## 🔍 Overview

The Flask Helpdesk System is a comprehensive task management and ticketing platform built with Flask. It integrates with external systems like Redmine and Oracle ERP to provide a unified interface for managing tasks, notifications, and user interactions.

### Key Features
- **User Authentication & Authorization** - Role-based access control with LDAP integration
- **Task Management** - Full CRUD operations with Kanban board interface
- **Real-time Notifications** - Browser push notifications and WebSocket support
- **External Integrations** - Seamless integration with Redmine and Oracle ERP
- **Multi-database Support** - SQLite for local data, MySQL for Redmine integration
- **Modern UI** - Responsive design with progressive web app features

### Technology Stack
- **Backend**: Flask 2.3.3, SQLAlchemy, Flask-Login
- **Database**: SQLite (local), MySQL (Redmine), Oracle (ERP)
- **Real-time**: Flask-SocketIO, WebSocket
- **Notifications**: pywebpush for browser notifications
- **Scheduling**: APScheduler for background tasks
- **Authentication**: Flask-Bcrypt, LDAP integration

---

## 🚀 Installation & Setup

### Prerequisites
```bash
Python 3.8+
MySQL Server (for Redmine integration)
Oracle Client (for ERP integration)
```

### Installation Steps

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
# Create .flaskenv file
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
```

4. **Configure database connections**
```ini
# config.ini
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

5. **Initialize database**
```bash
python -c "from blog import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

6. **Run the application**
```bash
python app.py
```

The application will be available at:
- http://localhost:5000
- http://localhost:5000/tasks/my-tasks (main dashboard)
- http://localhost:5000/users/login (login page)

---

## 🔐 Authentication System

### User Model
The authentication system is built around the `User` model with comprehensive user management features.

```python
# blog/models.py
class User(db.Model, UserMixin):
    """User model with authentication and authorization features"""
    
    # Basic user information
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)  # Bcrypt hashed
    
    # Profile information
    full_name = db.Column(db.String(255))
    department = db.Column(db.String(120))
    position = db.Column(db.String(120))
    office = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    
    # System permissions
    is_admin = db.Column(db.Boolean, default=False)
    is_redmine_user = db.Column(db.Boolean, default=False)
    can_access_quality_control = db.Column(db.Boolean, default=False)
    can_access_contact_center_moscow = db.Column(db.Boolean, default=False)
    
    # Notification preferences
    browser_notifications_enabled = db.Column(db.Boolean, default=False)
    notifications_widget_enabled = db.Column(db.Boolean, default=True)
    
    # Activity tracking
    last_seen = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    online = db.Column(db.Boolean, default=False)
    last_notification_check = db.Column(db.DateTime)
```

### Authentication Routes

#### Login
```python
# POST /users/login
# Content-Type: application/x-www-form-urlencoded

{
    "username": "user@example.com",
    "password": "user_password",
    "remember": true  # Optional
}
```

**Response:**
```json
{
    "success": true,
    "message": "Вход выполнен успешно",
    "redirect": "/tasks/my-tasks"
}
```

#### Registration
```python
# POST /users/register
# Content-Type: application/x-www-form-urlencoded

{
    "username": "newuser",
    "email": "newuser@example.com", 
    "password": "secure_password",
    "confirm_password": "secure_password",
    "full_name": "John Doe",
    "department": "IT",
    "position": "Developer"
}
```

#### Logout
```python
# GET /users/logout
# Requires authentication
```

### Authentication Decorators

```python
from flask_login import login_required, current_user
from functools import wraps

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def redmine_user_required(f):
    """Decorator to require Redmine access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_redmine_user:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

---

## 🗄️ Database Models

### Core Models

#### User Model
Comprehensive user management with role-based permissions and external system integration.

```python
class User(db.Model, UserMixin):
    """
    User model with authentication, authorization, and external system integration
    
    Attributes:
        id (int): Primary key
        username (str): Unique username (max 20 chars)
        email (str): Unique email address (max 120 chars)
        password (str): Bcrypt hashed password (60 chars)
        full_name (str): Full display name (max 255 chars)
        department (str): User department (max 120 chars)
        position (str): Job position (max 120 chars)
        office (str): Office location (max 120 chars)
        phone (str): Phone number (max 30 chars)
        is_admin (bool): Administrative privileges
        is_redmine_user (bool): Redmine system access
        can_access_quality_control (bool): Quality control module access
        can_access_contact_center_moscow (bool): Contact center access
        browser_notifications_enabled (bool): Push notification preference
        notifications_widget_enabled (bool): In-app notification preference
        last_seen (datetime): Last activity timestamp
        online (bool): Current online status
        redmine_username (str): Redmine login if different from username
        redmine_api_key (str): Personal Redmine API key
    
    Relationships:
        posts: One-to-many relationship with Post model
        push_subscriptions: One-to-many with PushSubscription model
    """
    
    def get_active_tasks(self):
        """Get user's active tasks from Redmine"""
        pass
    
    def __repr__(self):
        return f"User({self.id}, {self.username}, {self.email})"
```

#### Post Model
Content management for announcements and updates.

```python
class Post(db.Model):
    """
    Post model for announcements and content
    
    Attributes:
        id (int): Primary key
        title (str): Post title (max 100 chars)
        content (str): Post content (Text field)
        date_posted (datetime): Creation timestamp
        image_post (str): Optional image filename (max 30 chars)
        user_id (int): Foreign key to User model
    
    Relationships:
        author: Many-to-one relationship with User model
    """
    
    def __repr__(self):
        return f"Post({self.title}, {self.date_posted})"
```

#### Notifications Model
System for tracking task and system notifications.

```python
class Notifications(db.Model):
    """
    Notification model for task status changes
    
    Attributes:
        id (int): Primary key
        user_id (int): Target user ID
        issue_id (int): Related task/issue ID
        old_status (str): Previous status text
        new_status (str): New status text
        old_subj (str): Task subject/title
        date_created (datetime): Notification timestamp
        is_read (bool): Read status flag
    """
    
    def __init__(self, user_id, issue_id, old_status, new_status, old_subj, date_created):
        self.user_id = user_id
        self.issue_id = issue_id
        self.old_status = old_status
        self.new_status = new_status
        self.old_subj = old_subj
        self.date_created = date_created
        self.is_read = False
```

#### PushSubscription Model
Browser push notification subscriptions.

```python
class PushSubscription(db.Model):
    """
    Browser push notification subscription model
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User model
        endpoint (str): Push service endpoint URL
        p256dh (str): Public key for encryption
        auth (str): Authentication secret
        created_at (datetime): Subscription creation time
        last_used (datetime): Last successful push time
        is_active (bool): Subscription status
    
    Relationships:
        user: Many-to-one relationship with User model
    """
```

---

## 🔌 Core APIs

### User Management APIs

#### Get User Profile
```python
# GET /users/profile/<username>
# Requires: login_required

@users.route("/profile/<string:username>")
@login_required
def user_posts(username):
    """
    Get user profile and posts
    
    Parameters:
        username (str): Username to lookup
        
    Returns:
        HTML: User profile page with posts
        
    Raises:
        404: User not found
    """
```

**Example Usage:**
```python
import requests

response = requests.get(
    'http://localhost:5000/users/profile/johndoe',
    cookies={'session': 'your_session_cookie'}
)
```

#### Update User Profile
```python
# POST /users/account
# Requires: login_required
# Content-Type: multipart/form-data

def account():
    """
    Update user account information
    
    Form Data:
        username (str): New username
        email (str): New email address
        full_name (str): Full display name
        department (str): Department name
        position (str): Job position
        office (str): Office location
        phone (str): Phone number
        picture (file): Profile picture upload
        
    Returns:
        JSON: Success/error response
        Redirect: To account page on success
    """
```

**Example Usage:**
```python
import requests

data = {
    'username': 'newusername',
    'email': 'newemail@example.com',
    'full_name': 'John Doe Updated',
    'department': 'Engineering',
    'position': 'Senior Developer'
}

files = {
    'picture': ('avatar.jpg', open('avatar.jpg', 'rb'), 'image/jpeg')
}

response = requests.post(
    'http://localhost:5000/users/account',
    data=data,
    files=files,
    cookies={'session': 'your_session_cookie'}
)
```

### Task Management APIs

#### Get Task by ID
```python
# GET /tasks/api/task/<int:task_id>
# Requires: login_required, redmine_user_required
# Content-Type: application/json

@api_bp.route("/task/<int:task_id>", methods=["GET"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def get_task_by_id(task_id):
    """
    Get detailed task information by ID
    
    Parameters:
        task_id (int): Redmine task ID
        
    Returns:
        JSON: Task details with status, priority, assignments
        
    Response Format:
        {
            "success": true,
            "data": {
                "id": 12345,
                "subject": "Task title",
                "description": "Task description",
                "status_id": 1,
                "status_name": "New",
                "priority_id": 2,
                "priority_name": "Normal",
                "project_id": 1,
                "project_name": "Project Name",
                "assigned_to_id": 5,
                "assigned_to_name": "John Doe",
                "start_date": "2024-01-15",
                "due_date": "2024-01-30",
                "created_on": "2024-01-10T10:00:00Z",
                "updated_on": "2024-01-12T14:30:00Z"
            },
            "execution_time": 0.245
        }
        
    Errors:
        403: Access denied (not Redmine user)
        404: Task not found
        500: Connection or authentication error
    """
```

**Example Usage:**
```python
import requests

response = requests.get(
    'http://localhost:5000/tasks/api/task/12345',
    cookies={'session': 'your_session_cookie'}
)

if response.status_code == 200:
    task_data = response.json()
    print(f"Task: {task_data['data']['subject']}")
    print(f"Status: {task_data['data']['status_name']}")
```

#### Update Task Status
```python
# PUT /tasks/api/task/<int:task_id>/status
# Requires: login_required, redmine_user_required
# Content-Type: application/json

@api_bp.route("/task/<int:task_id>/status", methods=["PUT"])
@csrf.exempt
@login_required
def update_task_status(task_id):
    """
    Update task status with optional comment
    
    Parameters:
        task_id (int): Redmine task ID
        
    Request Body:
        {
            "status_id": 3,
            "comment": "Work completed and tested",
            "notify_users": true
        }
        
    Returns:
        JSON: Success confirmation with updated task info
        
    Response Format:
        {
            "success": true,
            "message": "Статус задачи обновлен",
            "data": {
                "task_id": 12345,
                "old_status": "In Progress",
                "new_status": "Resolved",
                "comment_added": true,
                "notifications_sent": 3
            },
            "execution_time": 0.892
        }
    """
```

**Example Usage:**
```python
import requests
import json

data = {
    "status_id": 3,
    "comment": "Task completed successfully. All tests passed.",
    "notify_users": True
}

response = requests.put(
    'http://localhost:5000/tasks/api/task/12345/status',
    data=json.dumps(data),
    headers={'Content-Type': 'application/json'},
    cookies={'session': 'your_session_cookie'}
)

if response.status_code == 200:
    result = response.json()
    print(f"Status updated: {result['data']['new_status']}")
```

#### Get User Tasks
```python
# GET /tasks/my-tasks
# Requires: login_required, redmine_user_required
# Query Parameters: page, per_page, status, priority, project

@tasks.route("/my-tasks")
@login_required
@redmine_user_required
def my_tasks():
    """
    Get current user's assigned tasks with filtering and pagination
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 25)
        status (str): Filter by status name
        priority (str): Filter by priority name
        project (str): Filter by project name
        search (str): Search in task subjects
        
    Returns:
        HTML: Rendered task list page
        JSON: Task data (if Accept: application/json)
        
    Response Format (JSON):
        {
            "tasks": [
                {
                    "id": 12345,
                    "subject": "Fix login issue",
                    "status": "In Progress",
                    "priority": "High",
                    "project": "Web Application",
                    "due_date": "2024-01-30",
                    "assigned_to": "John Doe"
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 25,
                "total": 150,
                "pages": 6
            },
            "filters": {
                "status": "In Progress",
                "priority": null,
                "project": null
            }
        }
    """
```

**Example Usage:**
```python
import requests

# Get first page of high priority tasks
response = requests.get(
    'http://localhost:5000/tasks/my-tasks',
    params={
        'page': 1,
        'per_page': 10,
        'priority': 'High',
        'status': 'In Progress'
    },
    headers={'Accept': 'application/json'},
    cookies={'session': 'your_session_cookie'}
)

tasks = response.json()['tasks']
for task in tasks:
    print(f"{task['id']}: {task['subject']} ({task['status']})")
```

#### Create New Task
```python
# POST /tasks/api/task
# Requires: login_required, redmine_user_required
# Content-Type: application/json

@api_bp.route("/task", methods=["POST"])
@csrf.exempt
@login_required
def create_task():
    """
    Create a new task in Redmine
    
    Request Body:
        {
            "subject": "Task title",
            "description": "Detailed task description",
            "project_id": 1,
            "status_id": 1,
            "priority_id": 2,
            "assigned_to_id": 5,
            "start_date": "2024-01-15",
            "due_date": "2024-01-30",
            "estimated_hours": 8.0,
            "custom_fields": [
                {"id": 1, "value": "Custom value"}
            ]
        }
        
    Returns:
        JSON: Created task information
        
    Response Format:
        {
            "success": true,
            "message": "Задача создана успешно",
            "data": {
                "task_id": 12346,
                "subject": "Task title",
                "status": "New",
                "assigned_to": "John Doe",
                "project": "Web Application",
                "created_on": "2024-01-15T10:00:00Z"
            }
        }
    """
```

**Example Usage:**
```python
import requests
import json

task_data = {
    "subject": "Implement user dashboard",
    "description": "Create a comprehensive user dashboard with task overview and notifications",
    "project_id": 1,
    "status_id": 1,
    "priority_id": 2,
    "assigned_to_id": 5,
    "due_date": "2024-02-15",
    "estimated_hours": 16.0
}

response = requests.post(
    'http://localhost:5000/tasks/api/task',
    data=json.dumps(task_data),
    headers={'Content-Type': 'application/json'},
    cookies={'session': 'your_session_cookie'}
)

if response.status_code == 201:
    new_task = response.json()
    print(f"Created task #{new_task['data']['task_id']}")
```

### Notification System APIs

#### Get User Notifications
```python
# GET /tasks/api/notifications
# Requires: login_required
# Query Parameters: unread_only, limit, offset

@api_bp.route("/notifications", methods=["GET"])
@csrf.exempt
@login_required
def get_notifications():
    """
    Get user notifications with filtering options
    
    Query Parameters:
        unread_only (bool): Show only unread notifications
        limit (int): Maximum number of notifications (default: 50)
        offset (int): Pagination offset (default: 0)
        type (str): Filter by notification type
        
    Returns:
        JSON: List of notifications
        
    Response Format:
        {
            "success": true,
            "data": {
                "notifications": [
                    {
                        "id": 123,
                        "type": "status_change",
                        "title": "Task Status Changed",
                        "message": "Task #12345 changed from 'In Progress' to 'Resolved'",
                        "issue_id": 12345,
                        "is_read": false,
                        "created_at": "2024-01-15T10:30:00Z",
                        "data": {
                            "old_status": "In Progress",
                            "new_status": "Resolved",
                            "task_subject": "Fix login issue"
                        }
                    }
                ],
                "total_count": 25,
                "unread_count": 8
            }
        }
    """
```

**Example Usage:**
```python
import requests

# Get unread notifications
response = requests.get(
    'http://localhost:5000/tasks/api/notifications',
    params={
        'unread_only': True,
        'limit': 20
    },
    cookies={'session': 'your_session_cookie'}
)

notifications = response.json()['data']['notifications']
print(f"You have {len(notifications)} unread notifications")
```

#### Mark Notification as Read
```python
# PUT /tasks/api/notifications/<int:notification_id>/read
# Requires: login_required

@api_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@csrf.exempt
@login_required
def mark_notification_read(notification_id):
    """
    Mark a specific notification as read
    
    Parameters:
        notification_id (int): Notification ID
        
    Returns:
        JSON: Success confirmation
        
    Response Format:
        {
            "success": true,
            "message": "Notification marked as read"
        }
    """
```

#### Subscribe to Push Notifications
```python
# POST /tasks/api/push-subscribe
# Requires: login_required
# Content-Type: application/json

@api_bp.route("/push-subscribe", methods=["POST"])
@csrf.exempt
@login_required
def subscribe_to_push():
    """
    Subscribe to browser push notifications
    
    Request Body:
        {
            "endpoint": "https://fcm.googleapis.com/fcm/send/...",
            "keys": {
                "p256dh": "public_key_base64",
                "auth": "auth_secret_base64"
            }
        }
        
    Returns:
        JSON: Subscription confirmation
        
    Response Format:
        {
            "success": true,
            "message": "Push subscription created",
            "subscription_id": 456
        }
    """
```

**Example Usage (JavaScript):**
```javascript
// Client-side push subscription
navigator.serviceWorker.ready.then(registration => {
    return registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicVapidKey)
    });
}).then(subscription => {
    return fetch('/tasks/api/push-subscribe', {
        method: 'POST',
        body: JSON.stringify(subscription),
        headers: {
            'Content-Type': 'application/json'
        }
    });
}).then(response => response.json())
.then(data => {
    console.log('Push subscription successful:', data);
});
```

---

## 🔗 External Integrations

### Redmine Integration

The system provides comprehensive integration with Redmine project management system.

#### Redmine Connector Class
```python
# blog/tasks/utils.py

class RedmineConnector:
    """
    Redmine API connector with authentication and caching
    
    Attributes:
        redmine: Redmine API client instance
        user_login (str): Authenticated user login
        connection_pool: Database connection pool
        cache_timeout (int): Cache timeout in seconds
    """
    
    def __init__(self, user_login, password, redmine_url, api_key=None):
        """
        Initialize Redmine connector
        
        Parameters:
            user_login (str): Redmine username
            password (str): User password
            redmine_url (str): Redmine server URL
            api_key (str): Optional API key for admin access
        """
        
    def get_user_tasks(self, user_id=None, status_filter=None, limit=100):
        """
        Get tasks assigned to user
        
        Parameters:
            user_id (int): Target user ID (default: current user)
            status_filter (list): List of status IDs to filter
            limit (int): Maximum number of tasks
            
        Returns:
            list: List of task dictionaries
        """
        
    def update_task_status(self, task_id, status_id, comment=None):
        """
        Update task status with optional comment
        
        Parameters:
            task_id (int): Task ID to update
            status_id (int): New status ID
            comment (str): Optional comment text
            
        Returns:
            dict: Updated task information
            
        Raises:
            RedmineAuthError: Authentication failed
            RedmineNotFoundError: Task not found
        """
        
    def create_task(self, project_id, subject, description=None, **kwargs):
        """
        Create new task in Redmine
        
        Parameters:
            project_id (int): Target project ID
            subject (str): Task title
            description (str): Task description
            **kwargs: Additional task attributes
            
        Returns:
            dict: Created task information
        """
```

**Example Usage:**
```python
from blog.tasks.utils import create_redmine_connector

# Create connector for authenticated user
connector = create_redmine_connector(
    is_redmine_user=True,
    user_login="john.doe",
    password="user_password"
)

# Get user's active tasks
tasks = connector.get_user_tasks(
    status_filter=[1, 2, 3],  # New, In Progress, Feedback
    limit=50
)

# Update task status
result = connector.update_task_status(
    task_id=12345,
    status_id=3,  # Resolved
    comment="Task completed successfully"
)

# Create new task
new_task = connector.create_task(
    project_id=1,
    subject="New feature request",
    description="Implement user dashboard",
    assigned_to_id=5,
    priority_id=2
)
```

#### Redmine Database Integration
```python
# redmine.py

def get_connection(host, user_name, password, name, max_attempts=3):
    """
    Establish MySQL connection to Redmine database
    
    Parameters:
        host (str): MySQL server host
        user_name (str): Database username
        password (str): Database password
        name (str): Database name
        max_attempts (int): Connection retry attempts
        
    Returns:
        pymysql.Connection: Database connection object
        None: If connection fails
        
    Example:
        conn = get_connection(
            host="localhost",
            user_name="redmine",
            password="password",
            name="redmine_production"
        )
    """

def get_localized_status_name(status_id, connection):
    """
    Get localized status name from Redmine database
    
    Parameters:
        status_id (int): Status ID from Redmine
        connection: MySQL connection object
        
    Returns:
        str: Localized status name
        
    Example:
        status_name = get_localized_status_name(1, conn)
        # Returns: "Новая" (for Russian locale)
    """

def get_project_members(project_id, connection):
    """
    Get project team members from Redmine database
    
    Parameters:
        project_id (int): Project ID
        connection: MySQL connection object
        
    Returns:
        list: List of member dictionaries with user info
        
    Example:
        members = get_project_members(1, conn)
        # Returns: [{"user_id": 5, "name": "John Doe", "role": "Developer"}]
    """
```

### Oracle ERP Integration

Integration with Oracle ERP system for user authentication and data synchronization.

#### ERP Connection Manager
```python
# erp_oracle.py

class ERPOracleConnector:
    """
    Oracle ERP database connector for user authentication and data sync
    
    Attributes:
        connection: Oracle database connection
        cursor: Database cursor object
        config: Configuration parser instance
    """
    
    def __init__(self, config_file="config.ini"):
        """
        Initialize Oracle ERP connector
        
        Parameters:
            config_file (str): Path to configuration file
        """
        
    def authenticate_user(self, username, password):
        """
        Authenticate user against ERP system
        
        Parameters:
            username (str): User login name
            password (str): User password
            
        Returns:
            dict: User information if authenticated
            None: If authentication fails
            
        Example:
            user_info = erp.authenticate_user("john.doe", "password")
            if user_info:
                print(f"Welcome {user_info['full_name']}")
        """
        
    def get_user_profile(self, username):
        """
        Get complete user profile from ERP
        
        Parameters:
            username (str): User login name
            
        Returns:
            dict: Complete user profile data
            
        Response Format:
            {
                "username": "john.doe",
                "full_name": "John Doe",
                "email": "john.doe@company.com",
                "department": "IT Department",
                "position": "Senior Developer",
                "office": "Moscow Office",
                "phone": "+7-495-123-4567",
                "manager": "Jane Smith",
                "hire_date": "2020-01-15"
            }
        """
        
    def sync_user_data(self, username):
        """
        Synchronize user data between ERP and local database
        
        Parameters:
            username (str): User to synchronize
            
        Returns:
            bool: True if sync successful, False otherwise
        """
```

**Example Usage:**
```python
from erp_oracle import ERPOracleConnector

# Initialize ERP connector
erp = ERPOracleConnector()

# Authenticate user
user_info = erp.authenticate_user("john.doe", "password")
if user_info:
    # Sync user data to local database
    sync_result = erp.sync_user_data("john.doe")
    if sync_result:
        print("User data synchronized successfully")
```

---

## 🛠️ Utility Functions

### Cache Manager
```python
# blog/utils/cache_manager.py

class CacheManager:
    """
    Application-wide cache management with performance optimization
    
    Features:
        - Memory-based caching with TTL
        - Weekend performance optimization
        - Cache invalidation strategies
        - Performance metrics tracking
    """
    
    def __init__(self, default_timeout=300):
        """
        Initialize cache manager
        
        Parameters:
            default_timeout (int): Default cache timeout in seconds
        """
        
    def get(self, key, default=None):
        """
        Get value from cache
        
        Parameters:
            key (str): Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        
    def set(self, key, value, timeout=None):
        """
        Set value in cache
        
        Parameters:
            key (str): Cache key
            value: Value to cache
            timeout (int): Cache timeout in seconds
        """
        
    def delete(self, key):
        """Delete key from cache"""
        
    def clear(self):
        """Clear all cached values"""

def weekend_performance_optimizer(f):
    """
    Decorator to optimize performance during weekends
    
    Increases cache timeout and reduces database queries
    during low-activity periods.
    
    Usage:
        @weekend_performance_optimizer
        def expensive_function():
            # Function implementation
            pass
    """
```

### Template Helpers
```python
# blog/utils/template_helpers.py

def format_datetime_msk(dt, format_string="%d.%m.%Y %H:%M"):
    """
    Format datetime for Moscow timezone
    
    Parameters:
        dt (datetime): Datetime object to format
        format_string (str): Format string
        
    Returns:
        str: Formatted datetime string
        
    Example:
        formatted = format_datetime_msk(datetime.now())
        # Returns: "15.01.2024 14:30"
    """

def get_status_color(status_name):
    """
    Get Bootstrap color class for task status
    
    Parameters:
        status_name (str): Status name
        
    Returns:
        str: Bootstrap color class
        
    Example:
        color = get_status_color("In Progress")
        # Returns: "warning"
    """

def get_priority_icon(priority_name):
    """
    Get FontAwesome icon class for task priority
    
    Parameters:
        priority_name (str): Priority name
        
    Returns:
        str: FontAwesome icon class
        
    Example:
        icon = get_priority_icon("High")
        # Returns: "fas fa-exclamation-triangle text-danger"
    """

def truncate_text(text, max_length=100, suffix="..."):
    """
    Truncate text to specified length
    
    Parameters:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix for truncated text
        
    Returns:
        str: Truncated text
    """
```

### Email Service
```python
# blog/utils/email_sender.py

class EmailSender:
    """
    Email notification service with template support
    
    Features:
        - HTML and plain text templates
        - Bulk email sending
        - Delivery tracking
        - Error handling and retries
    """
    
    def __init__(self, smtp_server, smtp_port, username, password):
        """Initialize email service with SMTP configuration"""
        
    def send_notification(self, to_email, subject, template, context=None):
        """
        Send notification email using template
        
        Parameters:
            to_email (str): Recipient email address
            subject (str): Email subject
            template (str): Template name
            context (dict): Template context variables
            
        Returns:
            bool: True if sent successfully
            
        Example:
            email_service.send_notification(
                to_email="user@example.com",
                subject="Task Status Update",
                template="task_notification",
                context={
                    "task_id": 12345,
                    "task_subject": "Fix login issue",
                    "old_status": "In Progress",
                    "new_status": "Resolved"
                }
            )
        """
        
    def send_bulk_notifications(self, recipients, subject, template, context=None):
        """
        Send bulk email notifications
        
        Parameters:
            recipients (list): List of email addresses
            subject (str): Email subject
            template (str): Template name
            context (dict): Template context variables
            
        Returns:
            dict: Delivery results with success/failure counts
        """
```

### Connection Monitor
```python
# blog/utils/connection_monitor.py

class ConnectionMonitor:
    """
    Monitor and manage external system connections
    
    Features:
        - Health check endpoints
        - Connection pooling
        - Automatic reconnection
        - Performance metrics
    """
    
    def check_redmine_connection(self):
        """
        Check Redmine system connectivity
        
        Returns:
            dict: Connection status and metrics
            
        Response Format:
            {
                "status": "healthy",
                "response_time": 0.245,
                "last_check": "2024-01-15T10:30:00Z",
                "error": null
            }
        """
        
    def check_oracle_connection(self):
        """Check Oracle ERP connectivity"""
        
    def get_system_health(self):
        """
        Get overall system health status
        
        Returns:
            dict: Complete system health report
            
        Response Format:
            {
                "overall_status": "healthy",
                "services": {
                    "redmine": {"status": "healthy", "response_time": 0.245},
                    "oracle": {"status": "healthy", "response_time": 0.156},
                    "database": {"status": "healthy", "response_time": 0.012}
                },
                "last_updated": "2024-01-15T10:30:00Z"
            }
        """
```

---

## 🔄 WebSocket Events

The application uses Flask-SocketIO for real-time communication.

### Client Events

#### Connect to Notifications
```javascript
// Client-side connection
const socket = io('/notifications');

socket.on('connect', function() {
    console.log('Connected to notification service');
    
    // Join user's notification room
    socket.emit('join_notifications', {
        user_id: currentUserId
    });
});
```

#### Receive Real-time Notifications
```javascript
socket.on('new_notification', function(data) {
    console.log('New notification received:', data);
    
    // Update notification counter
    updateNotificationCounter(data.unread_count);
    
    // Show notification popup
    showNotificationPopup({
        title: data.title,
        message: data.message,
        type: data.type,
        issue_id: data.issue_id
    });
});
```

#### Task Status Updates
```javascript
socket.on('task_status_changed', function(data) {
    console.log('Task status changed:', data);
    
    // Update task in UI if visible
    updateTaskStatus(data.task_id, data.new_status);
    
    // Show status change notification
    showStatusChangeNotification(data);
});
```

### Server Events

#### Broadcasting Task Updates
```python
# blog/notification_service.py

from flask_socketio import emit, join_room, leave_room

def broadcast_task_update(task_id, old_status, new_status, affected_users):
    """
    Broadcast task status change to affected users
    
    Parameters:
        task_id (int): Updated task ID
        old_status (str): Previous status
        new_status (str): New status
        affected_users (list): List of user IDs to notify
    """
    
    for user_id in affected_users:
        socketio.emit('task_status_changed', {
            'task_id': task_id,
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': datetime.now().isoformat()
        }, room=f'user_{user_id}')

def send_notification_to_user(user_id, notification_data):
    """
    Send real-time notification to specific user
    
    Parameters:
        user_id (int): Target user ID
        notification_data (dict): Notification payload
    """
    
    socketio.emit('new_notification', notification_data, room=f'user_{user_id}')
```

#### Room Management
```python
@socketio.on('join_notifications')
def handle_join_notifications(data):
    """
    Handle user joining notification room
    
    Parameters:
        data (dict): Contains user_id
    """
    user_id = data.get('user_id')
    if user_id and current_user.is_authenticated:
        join_room(f'user_{user_id}')
        emit('joined_notifications', {'status': 'success'})

@socketio.on('leave_notifications')
def handle_leave_notifications(data):
    """Handle user leaving notification room"""
    user_id = data.get('user_id')
    if user_id:
        leave_room(f'user_{user_id}')
        emit('left_notifications', {'status': 'success'})
```

---

## ⚙️ Configuration

### Environment Configuration
```python
# blog/settings.py

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///blog.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'blog/static/profile_pics'
    
    # Notification settings
    PUSH_NOTIFICATIONS_ENABLED = True
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
    VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL')
    
    # External API settings
    REDMINE_URL = os.environ.get('REDMINE_URL')
    REDMINE_API_KEY = os.environ.get('REDMINE_API_KEY')
    
    # Scheduler settings
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Europe/Moscow'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

### Database Configuration
```ini
# config.ini

[database]
db_path = blog/db/blog.db

[mysql]
host = localhost
port = 3306
database = redmine_production
user = redmine_user
password = redmine_password

[oracle]
host = oracle.company.com
port = 1521
service_name = ERP
user = erp_user
password = erp_password

[redmine]
url = https://redmine.company.com
api_key = your_admin_api_key_here
anonymous_user_id = 4

[email]
smtp_server = smtp.company.com
smtp_port = 587
username = notifications@company.com
password = email_password
use_tls = true

[push_notifications]
vapid_public_key = your_vapid_public_key
vapid_private_key = your_vapid_private_key
vapid_claim_email = admin@company.com
```

---

## 📚 Examples & Usage

### Complete Task Management Workflow

```python
import requests
import json
from datetime import datetime, timedelta

class HelpDeskClient:
    """Client wrapper for Helpdesk API"""
    
    def __init__(self, base_url, session_cookie):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.cookies.set('session', session_cookie)
    
    def login(self, username, password):
        """Authenticate with the system"""
        response = self.session.post(f'{self.base_url}/users/login', data={
            'username': username,
            'password': password
        })
        return response.status_code == 200
    
    def get_my_tasks(self, status_filter=None, limit=25):
        """Get current user's tasks"""
        params = {'limit': limit}
        if status_filter:
            params['status'] = status_filter
            
        response = self.session.get(
            f'{self.base_url}/tasks/my-tasks',
            params=params,
            headers={'Accept': 'application/json'}
        )
        return response.json() if response.status_code == 200 else None
    
    def update_task_status(self, task_id, status_id, comment=None):
        """Update task status"""
        data = {'status_id': status_id}
        if comment:
            data['comment'] = comment
            
        response = self.session.put(
            f'{self.base_url}/tasks/api/task/{task_id}/status',
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'}
        )
        return response.json() if response.status_code == 200 else None
    
    def create_task(self, project_id, subject, description, **kwargs):
        """Create new task"""
        task_data = {
            'project_id': project_id,
            'subject': subject,
            'description': description,
            **kwargs
        }
        
        response = self.session.post(
            f'{self.base_url}/tasks/api/task',
            data=json.dumps(task_data),
            headers={'Content-Type': 'application/json'}
        )
        return response.json() if response.status_code == 201 else None
    
    def get_notifications(self, unread_only=True):
        """Get user notifications"""
        params = {'unread_only': unread_only}
        response = self.session.get(
            f'{self.base_url}/tasks/api/notifications',
            params=params
        )
        return response.json() if response.status_code == 200 else None

# Usage example
client = HelpDeskClient('http://localhost:5000', 'your_session_cookie')

# Login
if client.login('john.doe', 'password'):
    print("Logged in successfully")
    
    # Get active tasks
    tasks = client.get_my_tasks(status_filter='In Progress')
    print(f"Found {len(tasks['tasks'])} active tasks")
    
    # Update first task status
    if tasks['tasks']:
        task = tasks['tasks'][0]
        result = client.update_task_status(
            task_id=task['id'],
            status_id=3,  # Resolved
            comment="Task completed and tested"
        )
        if result['success']:
            print(f"Task {task['id']} status updated")
    
    # Create new task
    new_task = client.create_task(
        project_id=1,
        subject="Implement new feature",
        description="Add user preferences management",
        priority_id=2,
        due_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    )
    if new_task['success']:
        print(f"Created new task #{new_task['data']['task_id']}")
    
    # Check notifications
    notifications = client.get_notifications(unread_only=True)
    if notifications['data']['unread_count'] > 0:
        print(f"You have {notifications['data']['unread_count']} unread notifications")
```

### Real-time Notification Integration

```javascript
// Client-side notification handling
class NotificationManager {
    constructor(userId) {
        this.userId = userId;
        this.socket = null;
        this.initializeSocket();
        this.initializePushNotifications();
    }
    
    initializeSocket() {
        this.socket = io('/notifications');
        
        this.socket.on('connect', () => {
            console.log('Connected to notification service');
            this.socket.emit('join_notifications', {
                user_id: this.userId
            });
        });
        
        this.socket.on('new_notification', (data) => {
            this.handleNewNotification(data);
        });
        
        this.socket.on('task_status_changed', (data) => {
            this.handleTaskStatusChange(data);
        });
    }
    
    async initializePushNotifications() {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                const subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
                });
                
                // Send subscription to server
                await fetch('/tasks/api/push-subscribe', {
                    method: 'POST',
                    body: JSON.stringify(subscription),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                console.log('Push notifications enabled');
            } catch (error) {
                console.error('Failed to enable push notifications:', error);
            }
        }
    }
    
    handleNewNotification(data) {
        // Update notification counter
        const counter = document.querySelector('#notification-counter');
        if (counter) {
            counter.textContent = data.unread_count;
            counter.style.display = data.unread_count > 0 ? 'inline' : 'none';
        }
        
        // Add notification to dropdown
        this.addNotificationToUI(data);
        
        // Show browser notification if supported
        if (Notification.permission === 'granted') {
            new Notification(data.title, {
                body: data.message,
                icon: '/static/img/notification-icon.png',
                tag: `notification-${data.id}`
            });
        }
    }
    
    handleTaskStatusChange(data) {
        // Update task status in UI if task is visible
        const taskElement = document.querySelector(`[data-task-id="${data.task_id}"]`);
        if (taskElement) {
            const statusElement = taskElement.querySelector('.task-status');
            if (statusElement) {
                statusElement.textContent = data.new_status;
                statusElement.className = `task-status badge badge-${this.getStatusColor(data.new_status)}`;
            }
        }
        
        // Show status change notification
        this.showToast(`Task #${data.task_id} status changed to ${data.new_status}`);
    }
    
    addNotificationToUI(notification) {
        const notificationsList = document.querySelector('#notifications-list');
        if (notificationsList) {
            const notificationElement = document.createElement('div');
            notificationElement.className = 'notification-item';
            notificationElement.innerHTML = `
                <div class="notification-content">
                    <h6>${notification.title}</h6>
                    <p>${notification.message}</p>
                    <small class="text-muted">${this.formatDate(notification.created_at)}</small>
                </div>
                <button class="btn btn-sm btn-outline-primary" onclick="this.markAsRead(${notification.id})">
                    Mark as Read
                </button>
            `;
            notificationsList.insertBefore(notificationElement, notificationsList.firstChild);
        }
    }
    
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/tasks/api/notifications/${notificationId}/read`, {
                method: 'PUT'
            });
            
            if (response.ok) {
                // Remove notification from UI
                const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (notificationElement) {
                    notificationElement.remove();
                }
                
                // Update counter
                this.updateNotificationCounter();
            }
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    }
    
    showToast(message, type = 'info') {
        // Create and show toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-body">
                ${message}
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
    
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
}

// Initialize notification manager
document.addEventListener('DOMContentLoaded', () => {
    if (typeof currentUserId !== 'undefined') {
        const notificationManager = new NotificationManager(currentUserId);
    }
});
```

### Batch Operations Example

```python
# Bulk task operations
from blog.tasks.utils import create_redmine_connector
from blog.notification_service import BrowserPushService
from concurrent.futures import ThreadPoolExecutor
import time

def bulk_task_operations():
    """Example of bulk task operations with notification"""
    
    # Initialize services
    connector = create_redmine_connector(
        is_redmine_user=True,
        user_login="admin",
        password="admin_password"
    )
    
    notification_service = BrowserPushService()
    
    # Tasks to update
    task_updates = [
        {"task_id": 12345, "status_id": 3, "comment": "Batch update - resolved"},
        {"task_id": 12346, "status_id": 2, "comment": "Batch update - in progress"},
        {"task_id": 12347, "status_id": 5, "comment": "Batch update - closed"},
    ]
    
    def update_single_task(update_data):
        """Update single task"""
        try:
            result = connector.update_task_status(
                task_id=update_data["task_id"],
                status_id=update_data["status_id"],
                comment=update_data["comment"]
            )
            
            # Send notification to assigned user
            if result and result.get("assigned_to_id"):
                notification_service.send_task_notification(
                    user_id=result["assigned_to_id"],
                    task_id=update_data["task_id"],
                    notification_type="status_change",
                    old_status=result.get("old_status"),
                    new_status=result.get("new_status")
                )
            
            return {"task_id": update_data["task_id"], "success": True, "result": result}
        except Exception as e:
            return {"task_id": update_data["task_id"], "success": False, "error": str(e)}
    
    # Execute updates in parallel
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(update_single_task, task_updates))
    
    execution_time = time.time() - start_time
    
    # Process results
    successful_updates = [r for r in results if r["success"]]
    failed_updates = [r for r in results if not r["success"]]
    
    print(f"Bulk update completed in {execution_time:.2f} seconds")
    print(f"Successful updates: {len(successful_updates)}")
    print(f"Failed updates: {len(failed_updates)}")
    
    # Send summary notification to admin
    notification_service.send_admin_notification(
        title="Bulk Task Update Complete",
        message=f"Updated {len(successful_updates)} tasks successfully, {len(failed_updates)} failed",
        data={
            "successful_count": len(successful_updates),
            "failed_count": len(failed_updates),
            "execution_time": execution_time
        }
    )
    
    return results

# Run bulk operations
if __name__ == "__main__":
    results = bulk_task_operations()
```

---

## 🔧 Advanced Configuration

### Custom Middleware

```python
# blog/middleware.py

class RequestLoggingMiddleware:
    """Middleware for request logging and performance monitoring"""
    
    def __init__(self, app):
        self.app = app
        self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())
        
        logger.info(f"[{g.request_id}] {request.method} {request.url} - User: {getattr(current_user, 'username', 'Anonymous')}")
    
    def after_request(self, response):
        execution_time = time.time() - g.start_time
        
        logger.info(f"[{g.request_id}] Response: {response.status_code} - Time: {execution_time:.3f}s")
        
        # Add performance headers
        response.headers['X-Response-Time'] = f"{execution_time:.3f}s"
        response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    def teardown_request(self, exception=None):
        if exception:
            logger.error(f"[{g.request_id}] Request failed with exception: {exception}")
```

### Error Handling

```python
# blog/error_handlers.py

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.is_json:
        return jsonify({
            'error': 'Resource not found',
            'message': 'The requested resource was not found on this server.',
            'status_code': 404
        }), 404
    
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    if request.is_json:
        return jsonify({
            'error': 'Access forbidden',
            'message': 'You do not have permission to access this resource.',
            'status_code': 403
        }), 403
    
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    
    if request.is_json:
        return jsonify({
            'error': 'Internal server error',
            'message': 'An internal server error occurred.',
            'status_code': 500
        }), 500
    
    return render_template('errors/500.html'), 500

class APIException(Exception):
    """Custom API exception class"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

@app.errorhandler(APIException)
def handle_api_exception(error):
    """Handle custom API exceptions"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
```

### Performance Monitoring

```python
# blog/monitoring.py

class PerformanceMonitor:
    """Application performance monitoring"""
    
    def __init__(self, app=None):
        self.metrics = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        g.start_time = time.time()
    
    def after_request(self, response):
        execution_time = time.time() - g.start_time
        endpoint = request.endpoint or 'unknown'
        
        # Update metrics
        if endpoint not in self.metrics:
            self.metrics[endpoint] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf')
            }
        
        metric = self.metrics[endpoint]
        metric['count'] += 1
        metric['total_time'] += execution_time
        metric['avg_time'] = metric['total_time'] / metric['count']
        metric['max_time'] = max(metric['max_time'], execution_time)
        metric['min_time'] = min(metric['min_time'], execution_time)
        
        return response
    
    def get_metrics(self):
        """Get performance metrics"""
        return self.metrics
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {}

# Usage in app factory
def create_app():
    app = Flask(__name__)
    
    # Initialize performance monitoring
    performance_monitor = PerformanceMonitor(app)
    
    @app.route('/admin/metrics')
    @admin_required
    def performance_metrics():
        return jsonify(performance_monitor.get_metrics())
    
    return app
```

---

This comprehensive API documentation covers all major components, functions, and usage patterns of the Flask Helpdesk System. The documentation includes detailed examples, configuration options, and best practices for integrating with and extending the system.