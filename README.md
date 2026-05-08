
# Multi-Tenant SaaS Backend

A production-ready, multi-tenant SaaS backend system built with Django REST Framework. This system allows multiple companies (tenants) to use the same platform while keeping their data completely isolated and secure.

## 🚀 Features

### Core Features
- ✅ **Multi-Tenant Architecture** - Complete data isolation between companies
- ✅ **JWT Authentication** - Secure token-based authentication with refresh tokens
- ✅ **Role-Based Access Control** - Admin, Manager, and Employee roles with API-level permissions
- ✅ **Company Management** - Register companies with automatic admin account creation
- ✅ **User Management** - Create, list, and delete users within each company
- ✅ **Project Management** - Full CRUD operations for projects
- ✅ **Task Management** - Create, assign, update status, and track tasks
- ✅ **Audit Logging** - Track all user actions with timestamps and IP addresses

### Advanced Features
- ✅ **API Rate Limiting** - 120 requests/minute for authenticated users, 30 for anonymous
- ✅ **Soft Delete** - Recycle bin functionality for projects and tasks with restore capability
- ✅ **Background Jobs** - Celery + Redis for async email notifications and task processing
- ✅ **Email Notifications** - Project assignment, Task assignment, Status updates, and Daily summary emails
- ✅ **Data Isolation** - Enforced at database and API levels

## 🛠️ Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 6.0.4 | Web framework |
| Django REST Framework | 3.15+ | API framework |
| PostgreSQL | 16+ | Production database |
| Celery | 5.3+ | Background task queue |
| Redis | 7.0+ | Message broker for Celery |
| JWT | SimpleJWT | Authentication |

## 📋 Prerequisites

- Python 3.12 or higher
- PostgreSQL 16 or higher
- Redis Server 7.0 or higher
- pip (Python package manager)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Multi-Tenant\ SaaS\ Backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### Requirements File (`requirements.txt`)

```txt
Django==6.0.4
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
psycopg2-binary==2.9.9
celery==5.3.6
redis==5.0.1
django-celery-beat==2.6.0
django-extensions==3.2.3
pydotplus==2.0.2
```

### 4. Configure Database

Create PostgreSQL database:

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE multitenant_db;
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE multitenant_db TO postgres;
\q
```

### 5. Configure Environment Variables

Create `.env` file in project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=multitenant_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 6. Update `settings.py`

Update the database configuration in `multitenant_backend/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'multitenant_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 7. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createcachetable
```

## 🚀 Running the Application

### Start All Services

You need **4 terminals** running simultaneously:

#### Terminal 1: Redis Server
```bash
redis-server
```

#### Terminal 2: Celery Worker (Background Tasks)
```bash
cd ~/Downloads/Multi-Tenant\ SaaS\ Backend/multitenant_backend
source .venv/bin/activate
celery -A multitenant_backend.celery_app worker --loglevel=info
```

#### Terminal 3: Celery Beat (Scheduled Tasks - Optional)
```bash
cd ~/Downloads/Multi-Tenant\ SaaS\ Backend/multitenant_backend
source .venv/bin/activate
celery -A multitenant_backend.celery_app beat --loglevel=info
```

#### Terminal 4: Django Server
```bash
cd ~/Downloads/Multi-Tenant\ SaaS\ Backend/multitenant_backend
source .venv/bin/activate
python manage.py runserver
```

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/companies/register/` | Register new company with admin account |
| POST | `/api/auth/login/` | Login and get JWT tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/auth/logout/` | Logout (blacklists token) |

### User Management (Admin only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/` | List all users in company |
| POST | `/api/users/` | Create new user (manager/employee) |
| DELETE | `/api/users/{id}/` | Delete user |

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/` | List projects (filtered by role) |
| POST | `/api/projects/` | Create new project |
| GET | `/api/projects/{id}/` | Get project details |
| PUT | `/api/projects/{id}/` | Update project |
| DELETE | `/api/projects/{id}/` | Soft delete project |
| POST | `/api/projects/{id}/assign/` | Assign user to project |
| POST | `/api/projects/{id}/restore/` | Restore soft-deleted project |
| GET | `/api/projects/deleted/` | List deleted projects |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/{id}/tasks/` | List tasks in project |
| POST | `/api/projects/{id}/tasks/` | Create task |
| GET | `/api/projects/{id}/tasks/{tid}/` | Get task details |
| PUT | `/api/projects/{id}/tasks/{tid}/` | Update task |
| DELETE | `/api/projects/{id}/tasks/{tid}/` | Soft delete task |
| POST | `/api/tasks/{id}/assign/` | Assign task to user |
| POST | `/api/tasks/{id}/restore/` | Restore soft-deleted task |
| GET | `/api/tasks/deleted/` | List deleted tasks |

### Audit Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit-logs/` | View all audit logs (Admin only) |
| GET | `/api/my-activity/` | View user's own activity |

## 🧪 Testing with Postman

### 1. Register a Company

```http
POST {{base_url}}/api/companies/register/
Content-Type: application/json

{
    "company_name": "Tech Corp",
    "admin_email": "admin@techcorp.com",
    "admin_password": "AdminPass123"
}
```

### 2. Login as Admin

```http
POST {{base_url}}/api/auth/login/
Content-Type: application/json

{
    "email": "admin@techcorp.com",
    "password": "AdminPass123"
}
```

### 3. Create a Manager

```http
POST {{base_url}}/api/users/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "email": "manager@techcorp.com",
    "password": "ManagerPass123",
    "role": "manager"
}
```

### 4. Create a Project

```http
POST {{base_url}}/api/projects/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "name": "E-Commerce Platform",
    "description": "Build a full-stack e-commerce website"
}
```

### 5. Create a Task

```http
POST {{base_url}}/api/projects/{{project_id}}/tasks/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "title": "Design Database",
    "description": "Create PostgreSQL schema",
    "assigned_to": 3
}
```

### 6. Assign Task (Triggers Email)

```http
POST {{base_url}}/api/tasks/{{task_id}}/assign/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "assigned_to": 2
}
```

### 7. Update Task Status (Employee)

```http
PUT {{base_url}}/api/projects/{{project_id}}/tasks/{{task_id}}/
Authorization: Bearer {{employee_token}}
Content-Type: application/json

{
    "status": "in_progress"
}
```

### 8. Soft Delete Project

```http
DELETE {{base_url}}/api/projects/{{project_id}}/
Authorization: Bearer {{access_token}}
```

### 9. Restore Deleted Project

```http
POST {{base_url}}/api/projects/{{project_id}}/restore/
Authorization: Bearer {{access_token}}
```

### 10. View Audit Logs

```http
GET {{base_url}}/api/audit-logs/
Authorization: Bearer {{access_token}}
```

## 📊 Database Schema (ERD)

Generate ERD diagram:

```bash
# Install dependencies
pip install django-extensions pydotplus
sudo apt-get install graphviz

# Generate ERD
python manage.py graph_models companies accounts projects tasks audit -o erd.png
```

Or use online tool:
1. Run `python manage.py graph_models companies accounts projects tasks audit --dot -o schema.dot`
2. Copy content to https://dreampuf.github.io/GraphvizOnline/
3. Download as PNG

## 🔒 Rate Limiting Configuration

| User Type | Endpoint | Limit |
|-----------|----------|-------|
| Authenticated | All endpoints | 120/minute |
| Anonymous | All endpoints | 30/minute |
| Anyone | Login | 5/minute |
| Anyone | Registration | 10/hour |
| Admin | All endpoints | 300/minute |
| Anyone | Audit Logs | 20/minute |

## 📧 Email Configuration

For email notifications, configure Gmail SMTP:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Generate from Google Account
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

### Generate Gmail App Password

1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Go to App Passwords
4. Select "Mail" and "Other"
5. Copy the 16-character password

## 🔧 Troubleshooting

### Celery Worker Not Starting

```bash
# Check Redis is running
redis-cli ping

# Restart Redis
sudo systemctl restart redis-server

# Restart Celery
celery -A multitenant_backend.celery_app worker --loglevel=info
```

### Email Not Sending

```bash
# Test email configuration
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail('Test', 'Message', 'from@email.com', ['to@email.com'], fail_silently=False)
```

### Rate Limit Not Working

```bash
# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## 📁 Project Structure

```
multitenant_backend/
├── manage.py
├── multitenant_backend/
│   ├── __init__.py
│   ├── celery_app.py      # Celery configuration
│   ├── settings.py         # Project settings
│   └── urls.py             # Main URL routing
├── accounts/               # User authentication
├── audit/                  # Audit logging
├── companies/              # Tenant management
├── core/                   # Shared utilities
│   ├── permissions.py      # RBAC classes
│   ├── tasks.py            # Celery tasks
│   ├── throttles.py        # Rate limiting
│   └── utils.py            # Helper functions
├── projects/               # Project management
└── tasks/                  # Task management
```

## 👥 User Roles & Permissions

| Action | Admin | Manager | Employee |
|--------|-------|---------|----------|
| Manage users | ✅ | ❌ | ❌ |
| Create projects | ✅ | ✅ | ❌ |
| Update projects | ✅ | ✅ | ❌ |
| Delete projects | ✅ | ✅ | ❌ |
| Create tasks | ✅ | ✅ | ❌ |
| Update task status | ✅ | ✅ | ✅ (own tasks) |
| Update task title | ✅ | ✅ | ❌ |
| Delete tasks | ✅ | ✅ | ❌ |
| View audit logs | ✅ | ❌ | ❌ |
| View own activity | ✅ | ✅ | ✅ |

## 📝 License

This project is for educational purposes as part of a Multi-Tenant SaaS Backend implementation.

## 👨‍💻 Author

Isma Ehtisham

## 🙏 Acknowledgments

- Django REST Framework for API capabilities
- Celery for background task processing
- PostgreSQL for reliable database management
```

## Quick Start Command Summary

```bash
# 1. Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Database
sudo -u postgres psql -c "CREATE DATABASE multitenant_db;"
python manage.py migrate

# 3. Run (4 terminals)
redis-server
celery -A multitenant_backend.celery_app worker --loglevel=info
python manage.py runserver

# 4. Test
curl -X POST http://127.0.0.1:8000/api/companies/register/ \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Test","admin_email":"admin@test.com","admin_password":"pass123"}'
```
