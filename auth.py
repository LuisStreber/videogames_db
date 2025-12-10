from flask_login import UserMixin
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

class Role:
    ADMIN = 'admin'
    EDITOR = 'editor'
    VIEWER = 'viewer'

ROLE_PERMISSIONS = {
    Role.ADMIN: ['view', 'create', 'edit', 'delete', 'manage_users'],
    Role.EDITOR: ['view', 'create', 'edit'],
    Role.VIEWER: ['view']
}

class User(UserMixin):
    """Clase User para Flask-Login"""

    def __init__(self, id, username, password_hash, role='viewer'):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def has_permission(self, permission):
        """Verifica si el usuario tiene permisos especificos"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def is_admin(self):
        """Verifica si el usuario es admin"""
        return self.role == Role.ADMIN

    def is_editor(self):
        """Verifica si el usuario es editor o admin"""
        return self.role in [Role.ADMIN, Role.EDITOR]

    # Métodos auxiliares legibles por el código
    def can_view(self):
        return 'view' in ROLE_PERMISSIONS.get(self.role, [])

    def can_create(self):
        return 'create' in ROLE_PERMISSIONS.get(self.role, [])

    def can_edit(self):
        return 'edit' in ROLE_PERMISSIONS.get(self.role, [])

    def can_delete(self):
        return 'delete' in ROLE_PERMISSIONS.get(self.role, [])

def permission_required(permission):
    """Decorador para requerir permisos especificos"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión', 'error')
                return redirect(url_for('login'))

            if not current_user.has_permission(permission):
                flash('No tienes permisos para realizar esta acción', 'error')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorador para rutas que solo admin puede acceder"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('login'))

        if not current_user.is_admin():
            flash('Solo administradores pueden acceder a esta página', 'error')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function

def editor_required(f):
    """Decorador para rutas que solo admin y editor pueden acceder"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('login'))

        if not current_user.is_editor():
            flash('No tienes permisos para realizar esta acción', 'error')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function
