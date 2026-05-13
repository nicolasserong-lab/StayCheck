from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.routes.users import admin_required
from app.models.property import (
    get_all_properties_by_admin, get_property_by_id, 
    add_property, update_property, delete_property
)

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('/')
@login_required
@admin_required
def index():
    # El Admin solo ve sus propiedades
    properties = get_all_properties_by_admin(current_user.id)
    return render_template('properties/index.html', properties=properties)

@properties_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        tipo = request.form.get('tipo')
        
        # Asociar automáticamente al Admin logueado
        add_property(nombre, direccion, tipo, current_user.id)
        flash('Propiedad creada exitosamente.', 'success')
        return redirect(url_for('properties.index'))
        
    return render_template('properties/create.html')

@properties_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    prop = get_property_by_id(id)
    if not prop or prop.admin_id != current_user.id:
        flash('Propiedad no encontrada o sin acceso.', 'danger')
        return redirect(url_for('properties.index'))
        
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        tipo = request.form.get('tipo')
        estado = request.form.get('estado')
        
        update_property(id, nombre, direccion, tipo, estado)
        flash('Propiedad actualizada exitosamente.', 'success')
        return redirect(url_for('properties.index'))
        
    return render_template('properties/edit.html', prop=prop)

@properties_bp.route('/delete/<id>', methods=['POST'])
@login_required
@admin_required
def delete(id):
    if delete_property(id):
        flash('Propiedad eliminada exitosamente.', 'success')
    else:
        flash('Propiedad no encontrada.', 'danger')
    return redirect(url_for('properties.index'))
