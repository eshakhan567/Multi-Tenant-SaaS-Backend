
# Multi-Tenant SaaS Backend - Complete Inline Documentation

## Project Overview
This is a production-ready multi-tenant SaaS backend system where multiple companies can use the same platform while keeping their data completely isolated.

### Tech Stack
- Django 6.0.4 - Web framework
- Django REST Framework - API framework
- PostgreSQL - Database
- JWT - Authentication
- Celery + Redis - Background tasks
- WhiteNoise - Static files serving

---

## 1. Project Structure

```
multitenant_backend/
├── manage.py                 # Django CLI entry point
├── multitenant_backend/      # Project settings
│   ├── __init__.py          # Celery initialization
│   ├── celery_app.py        # Celery configuration
│   ├── settings.py          # Project settings
│   └── urls.py              # Main URL routing
├── accounts/                 # User authentication app
├── companies/               # Tenant management app
├── projects/                # Project management app
├── tasks/                   # Task management app
├── audit/                   # Audit logging app
└── core/                    # Shared utilities
```

---

## 2. Settings Configuration (`multitenant_backend/settings.py`)

### Database Configuration (Works locally AND on cloud)
```python
# Automatically switches between local PostgreSQL and cloud database
if os.environ.get('DATABASE_URL'):
    DATABASES = {'default': dj_database_url.config(default=os.environ['DATABASE_URL'])}
else:
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

### JWT Authentication Settings
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # Short-lived for security
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # Long-lived for convenience
    'ROTATE_REFRESH_TOKENS': True,                   # New refresh token on each refresh
    'BLACKLIST_AFTER_ROTATION': True,                # Old tokens become invalid
}
```

### Rate Limiting (Protects from API abuse)
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',      # Anonymous users
        'user': '120/minute',     # Authenticated users
        'login': '5/minute',      # Login attempts (prevent brute force)
        'register': '10/hour',    # Registration (prevent spam)
    }
}
```

### Celery (Background Tasks)
```python
CELERY_BROKER_URL = os.environ.get('REDIS_URL')  # Redis as message queue
CELERY_BEAT_SCHEDULE = {
    'send-daily-summary': {
        'task': 'core.tasks.send_daily_summary_emails',
        'schedule': crontab(hour=17, minute=0),  # 5:00 PM daily
    },
}
```

---

## 3. Models Documentation

### Company Model (`companies/models.py`)
```python
class Company(models.Model):
    """Tenant model - each company is isolated"""
    id = models.AutoField(primary_key=True)           # Unique identifier
    name = models.CharField(max_length=255, unique=True)  # Company name
    slug = models.SlugField(unique=True, blank=True)  # URL-friendly version
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Auto-generates slug from name (e.g., "Google Inc" → "google-inc")
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
```

### User Model (`accounts/models.py`)
```python
class User(AbstractBaseUser):
    """Custom user model - uses email instead of username"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),      # Full access to everything
        ('manager', 'Manager'),  # Can create projects/tasks
        ('employee', 'Employee'),# Limited to assigned tasks
    ]
    
    email = models.EmailField(unique=True)  # Login credential
    company = models.ForeignKey(Company)    # Tenant isolation
    role = models.CharField(choices=ROLE_CHOICES)
    
    USERNAME_FIELD = 'email'  # Login with email, not username
```

### Project Model (`projects/models.py`)
```python
class Project(models.Model):
    """Project - belongs to a company"""
    company = models.ForeignKey(Company)        # Tenant isolation
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User)        # Who created
    members = models.ManyToManyField(User)      # Assigned users
    is_deleted = models.BooleanField(default=False)  # Soft delete flag
    deleted_at = models.DateTimeField(null=True)     # When deleted
    
    # Soft delete methods
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()
```

### Task Model (`tasks/models.py`)
```python
class Task(models.Model):
    """Task - belongs to a project"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    project = models.ForeignKey(Project)         # Parent project
    company = models.ForeignKey(Company)         # Direct tenant isolation
    title = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(User)        # Who is responsible
    status = models.CharField(choices=STATUS_CHOICES, default='pending')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    
    # Soft delete methods
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()
```

### AuditLog Model (`audit/models.py`)
```python
class AuditLog(models.Model):
    """Tracks every important action in the system"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]
    
    company = models.ForeignKey(Company)         # Which tenant
    user = models.ForeignKey(User)               # Who performed action
    action = models.CharField(choices=ACTION_CHOICES)  # What action
    model_name = models.CharField(max_length=100)      # Which table
    object_repr = models.CharField(max_length=255)     # Human-readable name
    changes = models.JSONField(default=dict)           # Before/after values
    ip_address = models.GenericIPAddressField()        # Where from
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 4. Custom Managers for Soft Delete

```python
class ActiveManager(models.Manager):
    """Returns only active (non-deleted) records"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class AllObjectsManager(models.Manager):
    """Returns ALL records (including deleted)"""
    def get_queryset(self):
        return super().get_queryset()

# Usage in models
objects = ActiveManager()      # Default: hides deleted
all_objects = AllObjectsManager()  # Shows everything
```

---

## 5. Permission Classes (`core/permissions.py`)

```python
class isAdmin(permissions.BasePermission):
    """Only admin users can access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class isManagerOrAdmin(permissions.BasePermission):
    """Managers and admins can access"""
    def has_permission(self, request, view):
        return request.user.role in ['admin', 'manager']

class isSameCompany(permissions.BasePermission):
    """Ensures users only see their company's data (Tenant Isolation)"""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        return False
```

---

## 6. Rate Limiting Throttles (`core/throttles.py`)

```python
class LoginRateThrottle(SimpleRateThrottle):
    """5 login attempts per minute - prevents brute force"""
    scope = 'login'
    rate = '5/minute'
    
    def get_cache_key(self, request, view):
        return f"login_throttle_{self.get_ident(request)}"

class UserListRateThrottle(SimpleRateThrottle):
    """Stricter limit for user list endpoint"""
    scope = 'user_list'
    rate = '30/minute'
    
    def get_cache_key(self, request, view):
        if request.method == 'GET' and request.user.is_authenticated:
            return f"user_list_{request.user.id}"
        return None
```

---

## 7. Celery Tasks (`core/tasks.py`)

### Task Assignment Email
```python
@shared_task
def send_task_assignment_email(task_id, assigned_to_email, assigned_by_email, 
                                task_title, project_name, company_id=None):
    """Sends email ONLY to the assigned user (not admins)"""
    send_mail(
        subject=f"New Task Assigned: {task_title}`",
        message=f"You have been assigned: {task_title}`...",
        recipient_list=[assigned_to_email],  # Only assigned user
    )
```

### Daily Summary Email
```python
@shared_task
def send_daily_summary_emails():
    """Sends daily task summary to managers at 5:00 PM"""
    # Gets all companies
    # Calculates task statistics (pending, in_progress, completed)
    # Sends email to each manager
```

### Welcome Email
```python
@shared_task
def send_welcome_email(user_email, company_name, user_name, user_role):
    """Role-specific welcome email"""
    if user_role == 'admin':
        role_message = "You have full access to manage everything..."
    elif user_role == 'manager':
        role_message = "You can create projects and assign tasks..."
    else:
        role_message = "You can view and update your assigned tasks..."
```

---

## 8. API Endpoints Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/companies/register/` | Register company + admin |
| POST | `/api/auth/login/` | Login (returns JWT tokens) |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/auth/logout/` | Logout |

### User Management (Admin only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/` | List all users |
| POST | `/api/users/` | Create user (manager/employee) |
| DELETE | `/api/users/{id}/` | Delete user |

### Project Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/` | List projects (filtered by role) |
| POST | `/api/projects/` | Create project |
| GET | `/api/projects/{id}/` | Get project details |
| PUT | `/api/projects/{id}/` | Update project |
| DELETE | `/api/projects/{id}/` | Soft delete project |
| POST | `/api/projects/{id}/restore/` | Restore deleted project |
| GET | `/api/projects/deleted/` | List deleted projects |
| POST | `/api/projects/{id}/assign/` | Assign user to project |

### Task Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/{id}/tasks/` | List tasks |
| POST | `/api/projects/{id}/tasks/` | Create task |
| GET | `/api/projects/{id}/tasks/{tid}/` | Get task details |
| PUT | `/api/projects/{id}/tasks/{tid}/` | Update task |
| DELETE | `/api/projects/{id}/tasks/{tid}/` | Soft delete task |
| POST | `/api/tasks/{id}/restore/` | Restore deleted task |
| GET | `/api/tasks/deleted/` | List deleted tasks |
| POST | `/api/tasks/{id}/assign/` | Assign task to user |

### Audit Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit-logs/` | View all logs (Admin only) |
| GET | `/api/my-activity/` | View user's own activity |

---

## 9. Role-Based Access Control (RBAC)

| Action | Admin | Manager | Employee |
|--------|-------|---------|----------|
| Manage users | ✅ | ❌ | ❌ |
| Create project | ✅ | ✅ | ❌ |
| Update project | ✅ | ✅ | ❌ |
| Delete project | ✅ | ✅ | ❌ |
| Create task | ✅ | ✅ | ❌ |
| Update task status | ✅ | ✅ | ✅ (own tasks) |
| Update task title | ✅ | ✅ | ❌ |
| Delete task | ✅ | ✅ | ❌ |
| View audit logs | ✅ | ❌ | ❌ |
| View own activity | ✅ | ✅ | ✅ |

---

## 10. Data Isolation (Multi-Tenancy)

### How Data Isolation Works

```python
# Every query automatically filters by company
def get(self, request):
    # User only sees their company's data
    users = User.objects.filter(company=request.user.company)
    
    # Projects filtered by company
    projects = Project.objects.filter(company=request.user.company)
    
    # Tasks filtered by company
    tasks = Task.objects.filter(company=request.user.company)
```

### Database Level Isolation

```sql
-- Foreign keys ensure data belongs to correct company
accounts_user.company_id REFERENCES companies_company(id)
projects_project.company_id REFERENCES companies_company(id)
tasks_task.company_id REFERENCES companies_company(id)
audit_auditlog.company_id REFERENCES companies_company(id)
```

---

## 11. Background Jobs (Celery)

### Starting Celery Services

```bash
# Terminal 1: Redis server
redis-server

# Terminal 2: Celery worker
celery -A multitenant_backend.celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
celery -A multitenant_backend.celery_app beat --loglevel=info

# Terminal 4: Django server
python manage.py runserver
```

### What Runs in Background

| Task | Trigger | Description |
|------|---------|-------------|
| `send_task_assignment_email` | Task assigned | Email to assigned user |
| `send_task_status_update_notification` | Status changed | Notification to task owner |
| `send_welcome_email` | New user created | Role-specific welcome |
| `send_daily_summary_emails` | Daily at 5 PM | Summary to managers |

---

## 12. Soft Delete Implementation

### How Soft Delete Works

```python
# Instead of permanent deletion:
project.delete()  # ❌ Removes from database

# Soft delete (marks as deleted):
project.soft_delete()  # ✅ Sets is_deleted=True, deleted_at=now()

# Restore from trash:
project.restore()  # ✅ Sets is_deleted=False, deleted_at=None
```

### Managers for Soft Delete

```python
# Normal queries - excludes deleted items
Project.objects.all()  # Only active projects

# Admin queries - includes deleted items
Project.all_objects.filter(is_deleted=True)  # Only deleted projects
```

---

## 13. Rate Limiting Protection

| User Type | Limit | Endpoint |
|-----------|-------|----------|
| Anonymous | 30/minute | All endpoints |
| Authenticated | 120/minute | All endpoints |
| Anyone | 5/minute | Login attempts |
| Anyone | 10/hour | Registration |
| Admin | 300/minute | All endpoints |
| Anyone | 20/minute | Audit logs |

### Rate Limit Response

```json
{
    "detail": "Request was throttled. Expected available in 60 seconds."
}
```

---

## 14. Audit Logging

### What Gets Logged

```python
# Login
log_audit(user, 'LOGIN', 'User', user.id, user.email, {}, request)

# Create project
log_audit(user, 'CREATE', 'Project', project.id, project.name, {...}, request)

# Update task
log_audit(user, 'UPDATE', 'Task', task.id, task.title, {...}, request)

# Soft delete
log_audit(user, 'SOFT_DELETE', 'Project', project.id, project.name, {...}, request)

# Restore
log_audit(user, 'RESTORE', 'Project', project.id, project.name, {...}, request)
```

### Log Entry Example

```json
{
    "id": 1,
    "user": "admin@techcorp.com",
    "action": "CREATE",
    "model_name": "Project",
    "object_repr": "E-Commerce Platform",
    "changes": {"name": "E-Commerce Platform"},
    "ip_address": "127.0.0.1",
    "created_at": "2026-05-11T10:00:00Z"
}
```

---

## 15. Email Configuration

### Gmail SMTP Setup

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')  # App password
```

### Environment Variables (Secrets)

```bash
# Never commit these to GitHub
EMAIL_HOST_PASSWORD=your-16-char-app-password
SECRET_KEY=your-django-secret-key
DEBUG=False
```

---

## 16. Testing Commands

### Register Company
```bash
curl -X POST http://127.0.0.1:8000/api/companies/register/ \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Test Corp","admin_email":"admin@test.com","admin_password":"test123"}'
```

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"test123"}'
```

### Create Project
```bash
curl -X POST http://127.0.0.1:8000/api/projects/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project","description":"Test"}'
```

### Create Task
```bash
curl -X POST http://127.0.0.1:8000/api/projects/1/tasks/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Task","assigned_to":2}'
```

---

## 17. Common Issues & Solutions

### Issue: `ModuleNotFoundError`
```bash
pip install -r requirements.txt
```

### Issue: Database connection failed
```bash
sudo systemctl start postgresql
redis-cli ping  # Should return PONG
```

### Issue: Celery tasks not running
```bash
celery -A multitenant_backend.celery_app worker --loglevel=info
```

### Issue: Emails not sending
- Use Gmail App Password, not regular password
- Check spam folder
- Or use console backend: `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`

---

## 18. Deployment Checklist

- [ ] `DEBUG = False` in production
- [ ] `ALLOWED_HOSTS` set to your domain
- [ ] `SECRET_KEY` in environment variables
- [ ] `EMAIL_HOST_PASSWORD` in environment variables
- [ ] Database using `DATABASE_URL` environment variable
- [ ] Redis using `REDIS_URL` environment variable
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] Migrations applied: `python manage.py migrate`

---

## 19. Git Branches

```bash
# Development branch - active development
git checkout development

# Staging branch - pre-production testing
git checkout staging

# Production branch - live code
git checkout main

# Documentation branch - documentation only
git checkout documentation
```

---

## 20. Project Summary

| Feature | Status | Description |
|---------|--------|-------------|
| Multi-Tenancy | ✅ Complete | Company-based data isolation |
| JWT Auth | ✅ Complete | Secure token authentication |
| RBAC | ✅ Complete | Admin/Manager/Employee roles |
| Rate Limiting | ✅ Complete | 120/minute per user |
| Soft Delete | ✅ Complete | Recycle bin with restore |
| Background Jobs | ✅ Complete | Celery + Redis |
| Email Notifications | ✅ Complete | Task assignment & summary |
| Audit Logging | ✅ Complete | Track all actions |
| PostgreSQL | ✅ Complete | Production database |

---

## Version History

- **v1.0.0** - Initial release with all core features
- **v1.1.0** - Added rate limiting
- **v1.2.0** - Added soft delete functionality
- **v1.3.0** - Added Celery background jobs

---

## License

This project is for educational purposes as part of a Multi-Tenant SaaS Backend implementation.

---

