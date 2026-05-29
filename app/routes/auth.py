from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_babel import _
from app.extensions import db
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import get_user_by_username

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        
        if user and user.check_password(password):
            if user.estado != 'Activo':
                flash(_('Tu cuenta está inactiva. Contacta al administrador.'), 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            
            # Sincronizar idioma de sesión con el perfil del usuario
            if 'idioma' in session:
                user.idioma = session['idioma']
                db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash(_('Usuario o contraseña incorrectos.'), 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['es', 'en']:
        session['idioma'] = lang
        if current_user.is_authenticated:
            current_user.idioma = lang
            db.session.commit()
    
    # Volver a la página anterior o al dashboard
    return redirect(request.referrer or url_for('dashboard.index'))
