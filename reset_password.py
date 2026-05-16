import sys
from app import create_app
from app.extensions import db
from app.models.user import User

def reset_password(username, new_password):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Error: No se encontró al usuario '{username}'")
            return
        
        # Usamos el método set_password que ya gestiona el hashing correctamente
        user.set_password(new_password)
        db.session.commit()
        print(f"¡Éxito! La contraseña de '{username}' ha sido actualizada.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python reset_password.py <nombre_usuario> <nueva_contraseña>")
        print("Ejemplo: python reset_password.py superadmin super123")
    else:
        user_to_reset = sys.argv[1]
        password_to_set = sys.argv[2]
        reset_password(user_to_reset, password_to_set)
