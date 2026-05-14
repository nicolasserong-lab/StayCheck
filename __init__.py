from flask import Flask, redirect, url_for
from flask_login import LoginManager
from app.config.settings import Config
from app.extensions import db
import os

login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configuración de la Base de Datos (Soporte para SQLite y PostgreSQL)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Render proporciona 'postgres://', pero SQLAlchemy requiere 'postgresql://'
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback para desarrollo local con SQLite
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'staycheck.db')
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    from app.models.user import get_user_by_id
    
    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    # Registrar Modelos
    from app.models.user import User
    from app.models.property import Property
    from app.models.checklist import Checklist
    from app.models.execution import Execution
    from app.models.task import Task

    # Registro de Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.users import users_bp
    from app.routes.properties import properties_bp
    from app.routes.checklists import checklists_bp
    from app.routes.executions import executions_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(properties_bp, url_prefix='/properties')
    app.register_blueprint(checklists_bp, url_prefix='/checklists')
    app.register_blueprint(executions_bp, url_prefix='/executions')
    app.register_blueprint(settings_bp, url_prefix='/settings')

    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))

    # Crear tablas e inicializar datos si es necesario
    with app.app_context():
        from app.models.user import init_db_data
        from app.models.property import init_db_properties
        from app.models.checklist import init_db_checklists
        
        db.create_all()
        
        # Verificar si la base de datos está vacía (especialmente para PostgreSQL en Render)
        if User.query.first() is None:
            print("Base de datos vacía detectada. Inicializando datos por primera vez...")
            init_db_data()
            init_db_properties()
            init_db_checklists()
        else:
            print("Datos detectados en la base de datos. Respetando persistencia.")

    return app
