from datetime import datetime
from app.extensions import db

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklists.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Operador asignado
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Admin que asignó
    
    status = db.Column(db.String(20), default='Pendiente') # 'Pendiente', 'Completada'
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones para facilitar la lectura
    property = db.relationship('Property', backref='tasks')
    checklist = db.relationship('Checklist', backref='tasks')
    user = db.relationship('User', foreign_keys=[user_id], backref='assigned_tasks')

def get_pending_tasks_by_user(user_id):
    return Task.query.filter_by(user_id=user_id, status='Pendiente').order_by(Task.fecha_asignacion.desc()).all()

def add_task(property_id, checklist_id, user_id, admin_id):
    task = Task(property_id=property_id, checklist_id=checklist_id, user_id=user_id, admin_id=admin_id)
    db.session.add(task)
    db.session.commit()
    return task
