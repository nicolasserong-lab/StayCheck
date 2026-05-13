from datetime import datetime
from app.extensions import db

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(20), default="Activa")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Nuevo: Pertenece a un Admin específico
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

def get_all_properties_by_admin(admin_id):
    return Property.query.filter_by(admin_id=admin_id).all()

def get_property_by_id(prop_id):
    return Property.query.get(int(prop_id))

def add_property(nombre, direccion, tipo, admin_id, estado="Activa"):
    prop = Property(nombre=nombre, direccion=direccion, tipo=tipo, admin_id=admin_id, estado=estado)
    db.session.add(prop)
    db.session.commit()
    return prop

def update_property(prop_id, nombre=None, direccion=None, tipo=None, estado=None):
    prop = Property.query.get(int(prop_id))
    if prop:
        if nombre: prop.nombre = nombre
        if direccion: prop.direccion = direccion
        if tipo: prop.tipo = tipo
        if estado: prop.estado = estado
        db.session.commit()
        return True
    return False

def delete_property(prop_id):
    prop = Property.query.get(int(prop_id))
    if prop:
        db.session.delete(prop)
        db.session.commit()
        return True
    return False

def init_db_properties():
    # Ya no inicializamos datos fijos globales para evitar contaminación entre admins
    pass
