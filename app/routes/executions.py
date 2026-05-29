from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_babel import _
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.routes.users import admin_required
from app.models.property import get_all_properties_by_admin, get_property_by_id
from app.models.checklist import get_all_checklists_by_admin, get_checklist_by_id
from app.models.execution import add_execution, save_execution_responses, get_execution_by_id, get_all_executions_by_admin
from app.models.user import get_user_by_id
from app.services.google_sheets import sync_execution_to_sheet

executions_bp = Blueprint('executions', __name__)

@executions_bp.route('/history')
@login_required
def history():
    # Si es operador, redirigir a su historial personal
    if current_user.is_operator():
        return redirect(url_for('executions.my_history'))
        
    from app.models.execution import Execution
    from app.models.property import Property
    from app.models.checklist import Checklist
    from app.models.user import User
    from app.extensions import db

    # El Admin ve solo sus reportes, traemos todo en una sola consulta SQL optimizada con JOIN
    results = db.session.query(Execution, Property, Checklist, User)\
        .join(Property, Execution.property_id == Property.id)\
        .join(Checklist, Execution.checklist_id == Checklist.id)\
        .join(User, Execution.user_id == User.id)\
        .filter(Execution.admin_id == current_user.id)\
        .order_by(Execution.fecha.desc(), Execution.hora.desc())\
        .all()

    history_data = []
    for ex, prop, chk, usr in results:
        history_data.append({
            'execution': ex,
            'property': prop,
            'checklist': chk,
            'user': usr
        })
    return render_template('executions/history.html', history=history_data)

@executions_bp.route('/my-history')
@login_required
def my_history():
    from app.models.execution import Execution
    from app.models.property import Property
    from app.models.checklist import Checklist
    from app.extensions import db

    # El Operador ve solo sus reportes, traemos todo en una sola consulta SQL optimizada con JOIN
    results = db.session.query(Execution, Property, Checklist)\
        .join(Property, Execution.property_id == Property.id)\
        .join(Checklist, Execution.checklist_id == Checklist.id)\
        .filter(Execution.user_id == current_user.id)\
        .order_by(Execution.fecha.desc(), Execution.hora.desc())\
        .all()

    history_data = []
    for ex, prop, chk in results:
        history_data.append({
            'execution': ex,
            'property': prop,
            'checklist': chk
        })
    return render_template('executions/my_history.html', history=history_data)

@executions_bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    execution = get_execution_by_id(id)
    if not execution:
        flash(_('Ejecución no encontrada.'), 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Solo el autor o su admin pueden editar
    if execution.user_id != current_user.id and current_user.id != execution.admin_id:
        flash(_('No tienes permiso para editar este reporte.'), 'danger')
        return redirect(url_for('dashboard.index'))
    
    prop = get_property_by_id(execution.property_id)
    chk = get_checklist_by_id(execution.checklist_id)
    
    if request.method == 'POST':
        responses = {}
        for item in chk.items:
            val = request.form.get(f'item_{item.id}')
            responses[item.id] = val
        
        observations = request.form.get('observations', '')
        save_execution_responses(id, responses, observations)
        
        # Re-sincronizar con Google Sheets para actualizar el registro existente
        sync_execution_to_sheet(execution, prop, chk, current_user)
        
        flash(_('Reporte actualizado y sincronizado exitosamente.'), 'success')
        return redirect(url_for('executions.my_history'))
    
    return render_template('executions/fill.html', execution=execution, property=prop, checklist=chk, is_edit=True)

@executions_bp.route('/detail/<id>')
@login_required
def detail(id):
    ex = get_execution_by_id(id)
    if not ex or (current_user.rol == 'admin' and ex.admin_id != current_user.id):
        flash(_('Ejecución no encontrada o sin acceso.'), 'danger')
        return redirect(url_for('dashboard.index'))
    
    prop = get_property_by_id(ex.property_id)
    chk = get_checklist_by_id(ex.checklist_id)
    user = get_user_by_id(ex.user_id)
    
    return render_template('executions/detail.html', execution=ex, property=prop, checklist=chk, user=user)

@executions_bp.route('/select-property')
@login_required
def select_property():
    # Si es operador, solo ve las propiedades que se le asignaron específicamente
    if current_user.is_operator():
        properties = [p for p in current_user.assigned_properties if p.estado == 'Activa']
    else:
        # El admin sigue viendo todas sus propiedades
        owner_id = current_user.id
        properties = [p for p in get_all_properties_by_admin(owner_id) if p.estado == 'Activa']
        
    return render_template('executions/select_property.html', properties=properties)

@executions_bp.route('/select-checklist/<property_id>')
@login_required
def select_checklist(property_id):
    prop = get_property_by_id(property_id)
    owner_id = current_user.admin_id if current_user.is_operator() else current_user.id
    
    if not prop or prop.admin_id != owner_id:
        flash(_('Propiedad no encontrada.'), 'danger')
        return redirect(url_for('dashboard.index'))
    
    checklists = [c for c in get_all_checklists_by_admin(owner_id) if c.estado == 'Activo']
    
    # Lógica de bloqueo de 24 horas para operadores
    from app.models.execution import Execution
    lockouts = {}
    
    for chk in checklists:
        # Buscar la última ejecución COMPLETADA de este checklist para esta propiedad por este usuario
        last_ex = Execution.query.filter_by(
            property_id=property_id,
            checklist_id=chk.id,
            user_id=current_user.id,
            status='Completado'
        ).order_by(Execution.fecha.desc(), Execution.hora.desc()).first()
        
        if last_ex:
            # Convertir los strings de la base de datos a objetos datetime
            try:
                last_dt = datetime.strptime(f"{last_ex.fecha} {last_ex.hora}", "%Y-%m-%d %H:%M:%S")
                # Usar el valor configurado en el checklist (chk.horas_bloqueo)
                next_available = last_dt + timedelta(hours=chk.horas_bloqueo)
                now = datetime.now()
                
                if now < next_available:
                    remaining = next_available - now
                    lockouts[chk.id] = {
                        'is_locked': True,
                        'seconds_left': int(remaining.total_seconds()),
                        'next_available': next_available.strftime('%H:%M')
                    }
                else:
                    lockouts[chk.id] = {'is_locked': False}
            except Exception as e:
                print(f"Error al procesar fecha: {e}")
                lockouts[chk.id] = {'is_locked': False}
        else:
            lockouts[chk.id] = {'is_locked': False}

    return render_template('executions/select_checklist.html', 
                           property=prop, 
                           checklists=checklists, 
                           lockouts=lockouts)

@executions_bp.route('/start/<property_id>/<checklist_id>', methods=['POST'])
@login_required
def start(property_id, checklist_id):
    # El reporte hereda el admin_id del usuario actual
    owner_id = current_user.admin_id if current_user.is_operator() else current_user.id
    execution = add_execution(property_id, checklist_id, current_user.id, owner_id)
    
    # Si viene de una tarea asignada, pasar el task_id
    task_id = request.form.get('task_id')
    return redirect(url_for('executions.fill', id=execution.id, task_id=task_id))

@executions_bp.route('/fill/<id>', methods=['GET', 'POST'])
@login_required
def fill(id):
    execution = get_execution_by_id(id)
    task_id = request.args.get('task_id') # Viene del redirect de start
    
    if not execution:
        flash(_('Ejecución no encontrada.'), 'danger')
        return redirect(url_for('dashboard.index'))
    
    prop = get_property_by_id(execution.property_id)
    chk = get_checklist_by_id(execution.checklist_id)
    
    if request.method == 'POST':
        responses = {}
        for item in chk.items:
            val = request.form.get(f'item_{item.id}')
            responses[item.id] = val
        
        observations = request.form.get('observations', '')
        save_execution_responses(id, responses, observations)
        
        # Sincronización automática con Google Sheets
        sync_execution_to_sheet(execution, prop, chk, current_user)
        

        
        flash(_('Checklist finalizado exitosamente y sincronizado con la nube.'), 'success')
        return redirect(url_for('executions.select_checklist', property_id=execution.property_id))
    
    return render_template('executions/fill.html', execution=execution, property=prop, checklist=chk, task_id=task_id)

@executions_bp.route('/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    from app.models.execution import Execution
    from app.extensions import db
    
    # Solo superadmin o admin pueden eliminar
    if current_user.rol not in ['superadmin', 'admin']:
        flash(_('No tienes permisos para eliminar registros.'), 'danger')
        return redirect(url_for('executions.history'))
        
    execution = Execution.query.get(id)
    if not execution:
        flash(_('Registro no encontrado.'), 'danger')
        return redirect(url_for('executions.history'))
    
    # Validar que pertenece a este admin (el admin original o el superadmin de esos admins)
    if current_user.rol == 'admin' and execution.admin_id != current_user.id:
        flash(_('No tienes permiso para eliminar este registro.'), 'danger')
        return redirect(url_for('executions.history'))
        
    db.session.delete(execution)
    db.session.commit()
    
    flash(_('Registro de checklist eliminado exitosamente del historial.'), 'success')
    return redirect(url_for('executions.history'))

@executions_bp.route('/cancel/<id>')
@login_required
def cancel(id):
    from app.models.execution import Execution
    from app.extensions import db
    
    execution = Execution.query.get(id)
    property_id = None
    
    if execution:
        property_id = execution.property_id
        # Solo borrar si está en estado 'Iniciado' (no completado) y pertenece al usuario
        if execution.status == 'Iniciado' and execution.user_id == current_user.id:
            db.session.delete(execution)
            db.session.commit()
    
    # Si tenemos el property_id, regresamos a la selección de checklists de esa propiedad
    if property_id:
        return redirect(url_for('executions.select_checklist', property_id=property_id))
        
    return redirect(url_for('dashboard.index'))
