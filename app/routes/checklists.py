from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_babel import _
import pandas as pd
import io
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
        
        flash(_('Checklist creado exitosamente.'), 'success')
        return redirect(url_for('checklists.index'))
        
    return render_template('checklists/create.html')

@checklists_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    chk = get_checklist_by_id(id)
    if not chk or chk.admin_id != current_user.id:
        flash(_('Checklist no encontrado o sin acceso.'), 'danger')
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
        
        flash(_('Checklist actualizado exitosamente.'), 'success')
        return redirect(url_for('checklists.index'))
        
    return render_template('checklists/edit.html', chk=chk)

@checklists_bp.route('/delete/<id>', methods=['POST'])
@login_required
@admin_required
def delete(id):
    if delete_checklist(id):
        flash(_('Checklist eliminado exitosamente.'), 'success')
    else:
        flash(_('Checklist no encontrado.'), 'danger')
    return redirect(url_for('checklists.index'))

@checklists_bp.route('/template')
@login_required
@admin_required
def template():
    # Crear un Excel de ejemplo en memoria
    data = {
        'Sección': ['Dormitorios', 'Dormitorios', 'Cocina', 'Estado General'],
        'Tarea / Item': ['Hacer camas', 'Revisar almohadas', 'Limpiar horno', 'Evaluación Propiedad'],
        'Tipo': ['checkbox', 'checkbox', 'checkbox', 'select'],
        'Opciones (solo para select)': ['', '', '', 'Excelente, Buena, Regular, Requiere Mantención']
    }
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Plantilla')
    
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                     as_attachment=True, download_name='plantilla_staycheck.xlsx')

@checklists_bp.route('/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_excel():
    if request.method == 'POST':
        file = request.files.get('file')
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        horas_bloqueo = request.form.get('horas_bloqueo', 24, type=int)
        
        if not file or not titulo:
            flash(_('Faltan datos obligatorios.'), 'danger')
            return redirect(url_for('checklists.import_excel'))
            
        try:
            df = pd.read_excel(file)
            # Validar columnas
            expected_cols = ['Sección', 'Tarea / Item', 'Tipo']
            for col in expected_cols:
                if col not in df.columns:
                    flash(_('Error: El archivo debe contener la columna "%(col)s"', col=col), 'danger')
                    return redirect(url_for('checklists.import_excel'))
            
            # Crear el checklist base
            chk = add_checklist(titulo, descripcion, current_user.id, horas_bloqueo=horas_bloqueo)
            
            items_data = []
            current_section = None
            
            for idx, row in df.iterrows():
                section = str(row['Sección']).strip() if pd.notna(row['Sección']) else None
                tarea = str(row['Tarea / Item']).strip()
                tipo = str(row['Tipo']).strip().lower()
                opciones = str(row.get('Opciones (solo para select)', '')).strip() if pd.notna(row.get('Opciones (solo para select)')) else ''

                # Si cambia la sección, añadir un header
                if section and section != current_section:
                    items_data.append({'texto': section, 'tipo': 'header'})
                    current_section = section
                
                # Procesar el item
                final_texto = tarea
                if tipo == 'select' and opciones:
                    final_texto = f"{tarea}|{opciones}"
                
                items_data.append({'texto': final_texto, 'tipo': tipo})
            
            update_checklist_items(chk.id, items_data)
            flash(_('Checklist "%(titulo)s" importado exitosamente con %(count)s items.', titulo=titulo, count=len(items_data)), 'success')
            return redirect(url_for('checklists.index'))
            
        except Exception as e:
            flash(_('Error al procesar el archivo: %(error)s', error=str(e)), 'danger')
            return redirect(url_for('checklists.import_excel'))
            
    return render_template('checklists/import.html')
