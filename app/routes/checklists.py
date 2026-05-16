from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.routes.users import admin_required
from app.models.checklist import (
    get_all_checklists_by_admin, get_checklist_by_id, 
    add_checklist, update_checklist, delete_checklist, update_checklist_items
)

checklists_bp = Blueprint('checklists', __name__)

@checklists_bp.route('/')
@login_required
@admin_required
def index():
    # El Admin solo ve sus checklists
    checklists = get_all_checklists_by_admin(current_user.id)
    return render_template('checklists/index.html', checklists=checklists)

@checklists_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        horas_bloqueo = request.form.get('horas_bloqueo', 24, type=int)
        
        # Asociar al Admin actual
        chk = add_checklist(titulo, descripcion, current_user.id, horas_bloqueo=horas_bloqueo)
        
        # Procesar items dinámicos
        textos = request.form.getlist('item_texto[]')
        tipos = request.form.getlist('item_tipo[]')
        
        items_data = []
        for i in range(len(textos)):
            if textos[i].strip() != '':
                items_data.append({'texto': textos[i].strip(), 'tipo': tipos[i]})
                
        update_checklist_items(chk.id, items_data)
        
        flash('Checklist creado exitosamente.', 'success')
        return redirect(url_for('checklists.index'))
        
    return render_template('checklists/create.html')

@checklists_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    chk = get_checklist_by_id(id)
    if not chk or chk.admin_id != current_user.id:
        flash('Checklist no encontrado o sin acceso.', 'danger')
        return redirect(url_for('checklists.index'))
        
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        estado = request.form.get('estado')
        horas_bloqueo = request.form.get('horas_bloqueo', 24, type=int)
        
        update_checklist(id, titulo, descripcion, estado, horas_bloqueo=horas_bloqueo)
        
        # Procesar items dinámicos
        textos = request.form.getlist('item_texto[]')
        tipos = request.form.getlist('item_tipo[]')
        
        items_data = []
        for i in range(len(textos)):
            if textos[i].strip() != '':
                items_data.append({'texto': textos[i].strip(), 'tipo': tipos[i]})
                
        update_checklist_items(chk.id, items_data)
        
        flash('Checklist actualizado exitosamente.', 'success')
        return redirect(url_for('checklists.index'))
        
    return render_template('checklists/edit.html', chk=chk)

@checklists_bp.route('/delete/<id>', methods=['POST'])
@login_required
@admin_required
def delete(id):
    if delete_checklist(id):
        flash('Checklist eliminado exitosamente.', 'success')
    else:
        flash('Checklist no encontrado.', 'danger')
    return redirect(url_for('checklists.index'))
