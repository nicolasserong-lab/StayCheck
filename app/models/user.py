from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from app.extensions import db

# Tabla intermedia para asignar propiedades a operadores
user_properties = db.Table('user_properties',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('property_id', db.Integer, db.ForeignKey('properties.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False) # Cambio: correo -> username
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False) # 'superadmin', 'admin', 'operator'
    
    # Jerarquía: Para saber a qué Admin pertenece este usuario (si es operador)
    # Si es superadmin o admin, este campo puede ser nulo o apuntar a sí mismo
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    estado = db.Column(db.String(20), default="Activo")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Configuración de Google Cloud (Individual por Administrador)
    google_json = db.Column(db.Text, nullable=True)
    google_sheet_id = db.Column(db.String(100), nullable=True)
    
    # Propiedades asignadas (Muchos a Muchos)
    assigned_properties = db.relationship('Property', secondary=user_properties, 
                                          backref=db.backref('assigned_users', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_superadmin(self):
        return self.rol == "superadmin"

    def is_admin(self):
        return self.rol == "admin"

    def is_operator(self):
        return self.rol == "operator"

def get_user_by_id(user_id):
    return User.query.get(int(user_id))

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_all_users_for_admin(admin_id):
    # Un admin solo ve sus operadores
    return User.query.filter_by(admin_id=admin_id, rol='operator').all()

def get_all_admins():
    # El superadmin ve a sus administradores
    return User.query.filter_by(rol='admin').all()

def add_user(nombre, username, password_hash, rol, admin_id=None, estado="Activo"):
    user = User(nombre=nombre, username=username, password_hash=password_hash, rol=rol, admin_id=admin_id, estado=estado)
    db.session.add(user)
    db.session.commit()
    return user

def delete_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False

def update_user(user_id, nombre=None, username=None, rol=None, estado=None, password_hash=None):
    user = User.query.get(int(user_id))
    if user:
        if nombre: user.nombre = nombre
        if username: user.username = username
        if rol: user.rol = rol
        if estado: user.estado = estado
        if password_hash: user.password_hash = password_hash
        db.session.commit()
        return True
    return False

def init_db_data():
    # Creamos el Super Administrador inicial (Tú)
    if not User.query.filter_by(username="superadmin").first():
        superadmin = User(
            nombre="Super Administrador",
            username="superadmin",
            rol="superadmin",
            estado="Activo"
        )
        superadmin.set_password("super123")
        db.session.add(superadmin)
        db.session.commit()
