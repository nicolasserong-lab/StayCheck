from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    if current_user.is_superadmin():
        return render_template('dashboard/superadmin.html')
    elif current_user.is_admin():
        return render_template('dashboard/admin.html')
    elif current_user.is_operator():
        from app.models.task import get_pending_tasks_by_user
        tasks = get_pending_tasks_by_user(current_user.id)
        return render_template('dashboard/operator.html', tasks=tasks)
    else:
        return "Rol no reconocido", 403
