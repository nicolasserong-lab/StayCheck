import sys
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def reset_password(username, new_password):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Error: No se encontró al usuario '{username}'")
            return
        
        user.password = generate_password_hash(new_password)
        db.session.commit()
        print(f"¡Éxito! La contraseña de '{username}' ha sido actualizada.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python reset_password.py <nombre_usuario> <nueva_contraseña>")
        print("Ejemplo: python reset_password.py superadmin mi_nueva_clave_123")
    else:
        user_to_reset = sys.argv[1]
        password_to_set = sys.argv[2]
        reset_password(user_to_reset, password_to_set)
