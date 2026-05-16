from datetime import datetime
from app.extensions import db

class ChecklistItem(db.Model):
    __tablename__ = 'checklist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklists.id'), nullable=False)
    texto = db.Column(db.String(200), nullable=False)
    tipo_respuesta = db.Column(db.String(50), nullable=False)

class Checklist(db.Model):
    __tablename__ = 'checklists'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(500))
    estado = db.Column(db.String(20), default="Activo")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Nuevo: Cada admin tiene sus propias plantillas
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Nuevo: Bloqueo configurable (en horas)
    horas_bloqueo = db.Column(db.Integer, default=24)
    
    items = db.relationship('ChecklistItem', backref='checklist', lazy=True, cascade="all, delete-orphan")

def get_all_checklists_by_admin(admin_id):
    return Checklist.query.filter_by(admin_id=admin_id).all()

def get_checklist_by_id(chk_id):
    return Checklist.query.get(int(chk_id))

def add_checklist(titulo, descripcion, admin_id, estado="Activo", horas_bloqueo=24):
    chk = Checklist(titulo=titulo, descripcion=descripcion, admin_id=admin_id, estado=estado, horas_bloqueo=horas_bloqueo)
    db.session.add(chk)
    db.session.commit()
    return chk

def update_checklist(chk_id, titulo=None, descripcion=None, estado=None, horas_bloqueo=None):
    chk = Checklist.query.get(int(chk_id))
    if chk:
        if titulo: chk.titulo = titulo
        if descripcion: chk.descripcion = descripcion
        if estado: chk.estado = estado
        if horas_bloqueo is not None: chk.horas_bloqueo = horas_bloqueo
        db.session.commit()
        return True
    return False

def delete_checklist(chk_id):
    chk = Checklist.query.get(int(chk_id))
    if chk:
        db.session.delete(chk)
        db.session.commit()
        return True
    return False

def update_checklist_items(chk_id, items_data):
    chk = Checklist.query.get(int(chk_id))
    if chk:
        ChecklistItem.query.filter_by(checklist_id=chk_id).delete()
        for item in items_data:
            new_item = ChecklistItem(
                checklist_id=chk_id,
                texto=item['texto'],
                tipo_respuesta=item['tipo']
            )
            db.session.add(new_item)
        db.session.commit()
        return True
    return False

def init_db_checklists():
    pass
