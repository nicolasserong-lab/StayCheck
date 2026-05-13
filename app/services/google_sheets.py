import gspread
from google.oauth2.service_account import Credentials
import json
import os
from app.models.user import User

def get_gspread_client(admin_user):
    if not admin_user:
        return None
        
    creds_json = admin_user.google_json
    
    creds_info = None
    
    if not creds_json:
        # Ya no cargamos de archivo local por seguridad multi-tenant
        return None
    else:
        try:
            creds_info = json.loads(creds_json)
        except Exception as e:
            print(f"DEBUG: El JSON de {admin_user.username} no es válido: {e}")
            return None

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        print(f"DEBUG: Error al autorizar con Google para {admin_user.username}: {e}")
        return None

def sync_execution_to_sheet(execution, prop, checklist, user):
    # Obtener el Administrador dueño de esta operación
    # Si el usuario es admin, el admin es él mismo. Si es operador, buscamos su admin_id.
    admin_id = user.id if user.rol == 'admin' else user.admin_id
    admin_user = User.query.get(admin_id)
    
    if not admin_user:
        print("Error: No se encontró el administrador responsable")
        return False
        
    sheet_id = admin_user.google_sheet_id
    
    if not sheet_id:
        print(f"Error: El administrador {admin_user.username} no ha configurado el Google Sheet ID")
        return False
    
    client = get_gspread_client(admin_user)
    if not client:
        print(f"Error: No se pudieron cargar las credenciales de Google de {admin_user.username}")
        return False
    
    try:
        spreadsheet = client.open_by_key(sheet_id)
        
        # 1. Intentar usar 'Registros', si no, usar la primera pestaña disponible
        try:
            worksheet = spreadsheet.worksheet("Registros")
        except gspread.exceptions.WorksheetNotFound:
            # Si no existe 'Registros', usamos la primera pestaña que tenga la hoja
            worksheet = spreadsheet.get_worksheet(0)
            # Opcional: renombrarla a Registros para orden
            try:
                worksheet.update_title("Registros")
            except:
                pass
        
        # 2. Si la hoja está totalmente vacía (no hay nada en A1), poner cabeceras
        if not worksheet.acell('A1').value:
            headers = ["Fecha", "Hora", "Usuario", "Propiedad", "Checklist", "Estado", "Observación", "Detalles JSON"]
            worksheet.append_row(headers)
            # Poner cabeceras en Negrita (Formato premium)
            worksheet.format("A1:H1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
        
        # 3. Preparar fila con los datos
        row = [
            execution.fecha,
            execution.hora,
            user.nombre,
            prop.nombre,
            checklist.titulo,
            execution.status,
            execution.observations,
            json.dumps(execution.responses)
        ]
        
        worksheet.append_row(row)
        return True
    except Exception as e:
        print(f"Error sincronizando con Google Sheets: {e}")
        return False
