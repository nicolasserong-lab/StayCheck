from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.routes.users import admin_required
from app.extensions import db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    if request.method == 'POST':
        sheet_id = request.form.get('google_sheet_id', '').strip()
        # Limpieza automática: Si pegan la URL completa o el ID con /edit...
        if '/d/' in sheet_id:
            sheet_id = sheet_id.split('/d/')[1].split('/')[0]
        elif '/' in sheet_id:
            sheet_id = sheet_id.split('/')[0]
            
        current_user.google_sheet_id = sheet_id
        current_user.google_json = request.form.get('google_credentials_json', '').strip()
        
        db.session.commit()
        flash('Configuración de Google Drive/Sheets actualizada.', 'success')
        return redirect(url_for('settings.index'))
        
    return render_template('settings/index.html')
