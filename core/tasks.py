from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import User
from companies.models import Company
from projects.models import Project
from tasks.models import Task
from audit.models import AuditLog
import logging

logger = logging.getLogger(__name__)


# task assignment email notification to assigned user only

@shared_task
def send_task_assignment_email(task_id, assigned_to_email, assigned_by_email, task_title, project_name, company_id=None):
    
    try:
        subject = f"New Task Assigned: {task_title}"
        message = f"""
        Hello,

        You have been assigned a new task:

        Task: {task_title}
        Project: {project_name}
        Assigned by: {assigned_by_email}

        Please log in to view and work on this task.

        Thank you,
        Task Management System
        """
        
        # Send only to the assigned user
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assigned_to_email], 
            fail_silently=False,
        )
        
        logger.info(f"Task assignment email sent to {assigned_to_email} for task {task_id}")
        return f"Email sent to {assigned_to_email}"
        
        
    except Exception as e:
        logger.error(f"Failed to send task assignment email: {str(e)}")
        return f"Error: {str(e)}"


# welcome email message to users
@shared_task
def send_welcome_email(user_email, company_name, user_name, user_role=None):
    
    try:
        
        if user_role == 'admin':
            role_title = "ADMIN"
            role_message = """
            As an ADMIN, you have full access to:
            • Manage all users in your company
            • Create and delete projects
            • View all tasks and audit logs
            • Assign tasks to any user
            """
        elif user_role == 'manager':
            role_title = "MANAGER"
            role_message = """
            As a MANAGER, you can:
            • Create and manage projects
            • Assign tasks to employees
            • Track project progress
            • View team performance
            """
        else: 
            role_title = "EMPLOYEE"
            role_message = """
            As an EMPLOYEE, you can:
            • View tasks assigned to you
            • Update task status (pending → in_progress → completed)
            • Collaborate with your team
            • View your assigned projects
            """
        
        subject = f"Welcome to {company_name} - Task Management System ({role_title})"
        message = f"""
        Hello {user_name},

        Welcome to {company_name}'s Task Management System!

        Your account has been successfully created with role: {role_title}

        {role_message}

        Login credentials:
        Email: {user_email}
        Password: (the password you set during account creation)

        Get started by logging in and exploring your dashboard.

        Thank you,
        Task Management System Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user_email} (role: {user_role})")
        return f"Welcome email sent to {user_email}"
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return f"Error: {str(e)}"
    
# project assignment email notification to assigned user only 
    
@shared_task
def send_project_assignment_email(project_id, assigned_to_email, assigned_by_email, project_name, company_name):

    try:
        subject = f"You have been assigned to a new project: {project_name}"
        message = f"""
        Hello,

        You have been assigned to a new project:

        Project: {project_name}
        Company: {company_name}
        Assigned by: {assigned_by_email}

        You can now view and work on tasks within this project.

        Please log in to view the project.

        Thank you,
        Project Management System
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assigned_to_email],
            fail_silently=False,
        )
        
        logger.info(f"Project assignment email sent to {assigned_to_email} for project {project_id}")
        return f"Email sent to {assigned_to_email}"
        
    except Exception as e:
        logger.error(f"Failed to send project assignment email: {str(e)}")
        return f"Error: {str(e)}"

# background logging 

@shared_task
def log_user_activity_async(user_id, action, model_name, object_id, object_repr, changes=None, ip_address=None):
    
    try:
        from accounts.models import User
        from companies.models import Company
        
        user = User.objects.get(id=user_id)
        
        AuditLog.objects.create(
            company=user.company,
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes or {},
            ip_address=ip_address,
            created_at=timezone.now()
        )
        
        logger.info(f"Background log created for user {user_id}: {action} on {model_name}")
        return f"Logged: {action} on {model_name}"
        
    except Exception as e:
        logger.error(f"Background logging failed: {str(e)}")
        return f"Error: {str(e)}"


# daily summary email

@shared_task
def send_daily_summary_emails():
    
    try:
        # Get all companies
        companies = Company.objects.all()
        summary_count = 0
        
        for company in companies:
            # Get all managers in this company
            managers = User.objects.filter(company=company, role='manager')
            
            if not managers:
                continue
            
            # Calculate task statistics for this company
            today = timezone.now().date()
            start_of_day = timezone.make_aware(
                datetime.combine(today, datetime.min.time())
            )
            end_of_day = timezone.make_aware(
                datetime.combine(today, datetime.max.time())
            )
            
            # Tasks created today
            tasks_created_today = Task.objects.filter(
                company=company,
                created_at__range=(start_of_day, end_of_day)
            ).count()
            
            # Tasks completed today
            tasks_completed_today = Task.objects.filter(
                company=company,
                status='completed',
                updated_at__range=(start_of_day, end_of_day)
            ).count()
            
            # Overall task statistics
            total_tasks = Task.objects.filter(company=company).count()
            pending_tasks = Task.objects.filter(company=company, status='pending').count()
            in_progress_tasks = Task.objects.filter(company=company, status='in_progress').count()
            completed_tasks = Task.objects.filter(company=company, status='completed').count()
            
            # Projects statistics
            total_projects = Project.objects.filter(company=company).count()
            total_users = User.objects.filter(company=company).count()
            
            # Send email to each manager
            for manager in managers:
                subject = f"Daily Task Summary - {company.name} - {today}"
                message = f"""
                Daily Task Summary Report
                ========================
                Company: {company.name}
                Date: {today}
                
                TODAY'S ACTIVITY:
                - Tasks created today: {tasks_created_today}
                - Tasks completed today: {tasks_completed_today}
                
                OVERALL STATISTICS:
                - Total Projects: {total_projects}
                - Total Team Members: {total_users}
                - Total Tasks: {total_tasks}
                
                TASK BREAKDOWN:
                - Pending Tasks: {pending_tasks}
                - In Progress Tasks: {in_progress_tasks}
                - Completed Tasks: {completed_tasks}
                
                COMPLETION RATE:
                - {int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0}% Complete
                
                Log in to your dashboard for more details.
                
                Thank you,
                Task Management System
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[manager.email],
                    fail_silently=False,
                )
                
                summary_count += 1
                logger.info(f"Daily summary sent to {manager.email}")
        
        logger.info(f"Daily summaries sent to {summary_count} managers")
        return f"Sent {summary_count} daily summary emails"
        
    except Exception as e:
        logger.error(f"Daily summary task failed: {str(e)}")
        return f"Error: {str(e)}"

# task status update notification
@shared_task
def send_task_status_update_notification(task_id, task_title, new_status, updated_by_email, assigned_to_email):
    
    try:
        subject = f"Task Status Updated: {task_title}"
        message = f"""
        Task Status Update Notification
        
        Task: {task_title}
        New Status: {new_status.upper()}
        Updated by: {updated_by_email}
        
        Please log in to view the updated task.
        
        Thank you,
        Task Management System
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assigned_to_email],
            fail_silently=False,
        )
        
        logger.info(f"Task status update notification sent for task {task_id}")
        return f"Notification sent for task {task_id}"
        
    except Exception as e:
        logger.error(f"Failed to send status update notification: {str(e)}")
        return f"Error: {str(e)}"