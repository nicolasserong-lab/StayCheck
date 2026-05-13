from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from app.models.user import (
    get_all_users_for_admin, get_all_admins, get_user_by_id, 
    add_user, update_user, delete_user, get_user_by_username
)
from app.models.property import get_all_properties_by_admin, get_property_by_id
from app.extensions import db

users_bp = Blueprint('users', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin() and not current_user.is_superadmin():
            flash('No tienes permisos para acceder a esta área.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@users_bp.route('/')
@login_required
@admin_required
def index():
    if current_user.is_superadmin():
        users = get_all_admins()
    else:
        users = get_all_users_for_admin(current_user.id)
    return render_template('users/index.html', users=users)

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    # Obtener propiedades para asignar (solo si el usuario actual es admin y creará un operador)
    all_properties = []
    if not current_user.is_superadmin():
        all_properties = get_all_properties_by_admin(current_user.id)

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if get_user_by_username(username):
            flash('El nombre de usuario ya está en uso.', 'danger')
        else:
            # Lógica jerárquica
            new_user = None
            if current_user.is_superadmin():
                # El SuperAdmin crea otros Admins
                new_user = add_user(nombre, username, generate_password_hash(password), 'admin', admin_id=None)
            else:
                # El Admin crea sus Operadores
                new_user = add_user(nombre, username, generate_password_hash(password), 'operator', admin_id=current_user.id)
            
            # Asignar propiedades seleccionadas si es un operador
            if new_user and new_user.rol == 'operator':
                selected_property_ids = request.form.getlist('assigned_properties')
                for prop_id in selected_property_ids:
                    prop = get_property_by_id(prop_id)
                    if prop:
                        new_user.assigned_properties.append(prop)
                db.session.commit()
            
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('users.index'))
            
    return render_template('users/create.html', properties=all_properties)

@users_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    user = get_user_by_id(id)
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('users.index'))
    
    # Verificación de privacidad
    if not current_user.is_superadmin() and user.admin_id != current_user.id:
        flash('No tienes permiso para editar este usuario.', 'danger')
        return redirect(url_for('users.index'))
    
    # Obtener propiedades para asignar (solo si el usuario a editar es un operador)
    all_properties = []
    if user.rol == 'operator':
        all_properties = get_all_properties_by_admin(current_user.id)
        
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        username = request.form.get('username')
        estado = request.form.get('estado')
        password = request.form.get('password')
        
        existing_user = get_user_by_username(username)
        if existing_user and str(existing_user.id) != str(id):
            flash('El nombre de usuario ya está en uso.', 'danger')
        else:
            pwd_hash = generate_password_hash(password) if password else None
            update_user(id, nombre, username, user.rol, estado, pwd_hash)
            
            # Sincronizar propiedades asignadas (si es operador)
            if user.rol == 'operator':
                selected_property_ids = request.form.getlist('assigned_properties')
                # Limpiar asignaciones actuales y agregar nuevas
                user.assigned_properties = []
                for prop_id in selected_property_ids:
                    prop = get_property_by_id(prop_id)
                    if prop:
                        user.assigned_properties.append(prop)
                db.session.commit()
                
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('users.index'))
            
    return render_template('users/edit.html', user=user, properties=all_properties)

@users_bp.route('/delete/<id>', methods=['POST'])
@login_required
@admin_required
def delete(id):
    if str(current_user.id) == str(id):
        flash('No puedes eliminar tu propio usuario activo.', 'danger')
    else:
        if delete_user(id):
            flash('Usuario eliminado exitosamente.', 'success')
        else:
            flash('Usuario no encontrado.', 'danger')
    return redirect(url_for('users.index'))

@users_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validar si el username ya existe (y no es el propio)
        existing_user = get_user_by_username(username)
        if existing_user and existing_user.id != current_user.id:
            flash('El nombre de usuario ya está en uso.', 'danger')
        else:
            current_user.nombre = nombre
            current_user.username = username
            if password:
                current_user.set_password(password)
            
            db.session.commit()
            flash('Tus datos han sido actualizados exitosamente.', 'success')
            return redirect(url_for('dashboard.index'))
            
    return render_template('users/profile.html', user=current_user)
