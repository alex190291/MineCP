"""
Audit logging utilities for tracking security-relevant actions.
"""
from typing import Optional, Dict, Any
from flask import request, current_app
from flask_jwt_extended import get_jwt_identity
from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
):
    """
    Log a security-relevant action.

    Args:
        action: Action performed (e.g., 'create', 'delete', 'login', 'password_change')
        resource_type: Type of resource (e.g., 'server', 'user', 'auth', 'file')
        resource_id: ID of the resource affected (if applicable)
        details: Additional context about the action
        user_id: User ID (if not available from JWT context)
    """
    try:
        # Get user ID from JWT if not provided
        if user_id is None:
            try:
                user_id = get_jwt_identity()
            except:
                user_id = None  # Not authenticated

        # Don't log if no user (system actions)
        if not user_id:
            return

        # Get IP address from request
        ip_address = request.remote_addr if request else None

        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            action=f"{resource_type}.{action}",
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address
        )

        db.session.add(audit_log)
        db.session.commit()

        current_app.logger.info(
            f"Audit: {audit_log.action} by user {user_id} on {resource_type} {resource_id or '(none)'}"
        )

    except Exception as e:
        current_app.logger.error(f"Failed to create audit log: {e}")
        # Don't fail the request if audit logging fails
        try:
            db.session.rollback()
        except:
            pass


# Convenience functions for common actions

def log_login(user_id: str, success: bool, details: Optional[Dict] = None):
    """Log authentication attempt."""
    action = 'login_success' if success else 'login_failure'
    log_action(action, 'auth', user_id=user_id, details=details)


def log_logout(user_id: str):
    """Log user logout."""
    log_action('logout', 'auth', user_id=user_id)


def log_password_change(user_id: str, target_user_id: str):
    """Log password change."""
    details = {'target_user_id': target_user_id}
    log_action('password_change', 'user', resource_id=target_user_id, details=details, user_id=user_id)


def log_server_create(server_id: str, server_name: str):
    """Log server creation."""
    log_action('create', 'server', resource_id=server_id, details={'name': server_name})


def log_server_delete(server_id: str, server_name: str):
    """Log server deletion."""
    log_action('delete', 'server', resource_id=server_id, details={'name': server_name})


def log_server_start(server_id: str):
    """Log server start."""
    log_action('start', 'server', resource_id=server_id)


def log_server_stop(server_id: str):
    """Log server stop."""
    log_action('stop', 'server', resource_id=server_id)


def log_file_write(server_id: str, file_path: str):
    """Log file write operation."""
    log_action('write', 'file', resource_id=server_id, details={'path': file_path})


def log_file_delete(server_id: str, file_path: str):
    """Log file deletion."""
    log_action('delete', 'file', resource_id=server_id, details={'path': file_path})


def log_file_upload(server_id: str, file_name: str):
    """Log file upload."""
    log_action('upload', 'file', resource_id=server_id, details={'filename': file_name})


def log_mod_install(server_id: str, mod_name: str, source: str):
    """Log mod installation."""
    log_action('install', 'mod', resource_id=server_id, details={'mod_name': mod_name, 'source': source})


def log_mod_delete(server_id: str, mod_name: str):
    """Log mod deletion."""
    log_action('delete', 'mod', resource_id=server_id, details={'mod_name': mod_name})


def log_backup_create(server_id: str, backup_id: str):
    """Log backup creation."""
    log_action('create', 'backup', resource_id=backup_id, details={'server_id': server_id})


def log_backup_restore(server_id: str, backup_id: str):
    """Log backup restore."""
    log_action('restore', 'backup', resource_id=backup_id, details={'server_id': server_id})


def log_backup_delete(backup_id: str):
    """Log backup deletion."""
    log_action('delete', 'backup', resource_id=backup_id)


def log_user_create(created_user_id: str, username: str):
    """Log user creation."""
    log_action('create', 'user', resource_id=created_user_id, details={'username': username})


def log_user_delete(deleted_user_id: str, username: str):
    """Log user deletion."""
    log_action('delete', 'user', resource_id=deleted_user_id, details={'username': username})


def log_user_update(updated_user_id: str, fields_changed: list):
    """Log user update."""
    log_action('update', 'user', resource_id=updated_user_id, details={'fields': fields_changed})


def log_permission_denied(resource_type: str, resource_id: Optional[str] = None):
    """Log permission denied (access control violation)."""
    log_action('permission_denied', resource_type, resource_id=resource_id)


def log_config_change(config_type: str, details: Optional[Dict] = None):
    """Log configuration change."""
    log_action('update', 'config', details={'config_type': config_type, **(details or {})})
