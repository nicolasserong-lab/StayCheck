from flask import Blueprint, render_template, redirect, url_for
from flask_babel import _
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
        return render_template('dashboard/operator.html', tasks=[])
    else:
        return _("Rol no reconocido"), 403
