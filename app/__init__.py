from flask import Flask, redirect, url_for, session
from flask_login import LoginManager, current_user
from datetime import timedelta
from app.config.settings import Config
from app.extensions import db, babel
from flask import request
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
    
    # Configuración de Babel
    def get_locale():
        # 1. Si el usuario está logueado, usar su idioma guardado
        if current_user.is_authenticated and current_user.idioma:
            return current_user.idioma
        # 2. Si no, intentar leer de la sesión (para usuarios no logueados que cambian idioma)
        if 'idioma' in session:
            return session['idioma']
        # 3. Por último, lo que diga el navegador o español por defecto
        return request.accept_languages.best_match(['es', 'en']) or 'es'

    babel.init_app(app, locale_selector=get_locale)
    
    # Hacer disponible get_locale en los templates
    app.jinja_env.globals.update(get_locale=get_locale)
    
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

    @app.before_request
    def manage_session_timeout():
        # Hacer que la sesión sea permanente para que respete el Lifetime
        session.permanent = True
        
        # Si el usuario está autenticado, ajustar el tiempo según su rol
        if current_user.is_authenticated:
            if current_user.rol == 'operador':
                app.permanent_session_lifetime = timedelta(minutes=20)
            else:
                # SuperAdmin y Admin
                app.permanent_session_lifetime = timedelta(minutes=10)
    
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))

    @app.route('/sw.js')
    def serve_sw():
        return app.send_static_file('js/sw.js')

    @app.route('/manifest.json')
    def serve_manifest():
        return app.send_static_file('manifest.json')

    # Crear tablas e inicializar datos si es necesario
    with app.app_context():
        from app.models.user import init_db_data
        from app.models.property import init_db_properties
        from app.models.checklist import init_db_checklists
        
        # 1. Asegurar que las tablas existan
        db.create_all()
        
        # 2. Migración automática (self-healing) para agregar columnas nuevas si ya existía la tabla
        from sqlalchemy import text
        for col_name, col_type in [
            ("idioma", "VARCHAR(5) DEFAULT 'es'"),
            ("google_json", "TEXT NULL"),
            ("google_sheet_id", "VARCHAR(100) NULL")
        ]:
            try:
                # Intentar agregar la columna usando sintaxis de PostgreSQL (soporta IF NOT EXISTS)
                db.session.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                db.session.commit()
            except Exception:
                db.session.rollback()
                try:
                    # Intentar agregar la columna usando sintaxis estándar/SQLite (no soporta IF NOT EXISTS)
                    db.session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    # Ya existe o falló, continuar pacíficamente
                    pass
        
        # Verificar si la base de datos está vacía (especialmente para PostgreSQL en Render)
        if User.query.first() is None:
            print("Base de datos vacía detectada. Inicializando datos por primera vez...")
            init_db_data()
            init_db_properties()
            init_db_checklists()
        else:
            print("Datos detectados en la base de datos. Respetando persistencia.")

    return app
