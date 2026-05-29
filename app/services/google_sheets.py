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
        
        # Helper para convertir número de columna a letra de Excel (ej: 1 -> A, 27 -> AA)
        def col_num_to_letter(n):
            string = ""
            while n > 0:
                n, remainder = divmod(n - 1, 26)
                string = chr(65 + remainder) + string
            return string

        # 1. Obtener cabeceras actuales en la primera fila de la hoja
        existing_headers = worksheet.row_values(1)
        base_headers = ["Fecha", "Hora", "Usuario", "Propiedad", "Checklist", "Estado", "Observación"]
        
        if not existing_headers or not existing_headers[0]:
            updated_headers = list(base_headers)
        else:
            updated_headers = list(existing_headers)
            
        # 2. Obtener los ítems del checklist ordenados
        sorted_items = sorted(checklist.items, key=lambda x: x.id)
        non_header_items = [i for i in sorted_items if i.tipo_respuesta != 'header']
        
        # 3. Detectar dinámicamente si hay nuevas tareas para agregar como columnas
        has_new = False
        if not existing_headers or not existing_headers[0]:
            has_new = True
            
        for item in non_header_items:
            # Limpiar opciones del nombre de la tarea (si tiene formato "Tarea|Opciones")
            clean_name = item.texto.split('|')[0] if '|' in item.texto else item.texto
            if clean_name not in updated_headers:
                updated_headers.append(clean_name)
                has_new = True
                
        # 4. Si hay nuevas columnas o la hoja estaba vacía, actualizar la cabecera (Fila 1) en un solo viaje
        if has_new:
            worksheet.update([updated_headers], 'A1')
            # Aplicar formato estético a toda la fila de cabecera en Negrita y fondo verde pastel premium
            last_col_letter = col_num_to_letter(len(updated_headers))
            worksheet.format(f"A1:{last_col_letter}1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.88, "green": 0.95, "blue": 0.88}
            })
            existing_headers = updated_headers
            
        # Crear mapa de índices de las columnas (cabecera -> índice)
        header_indices = {header: idx for idx, header in enumerate(existing_headers)}
        
        # 5. Inicializar la fila de datos con valores vacíos coincidiendo con la longitud de las columnas
        row_data = [""] * len(existing_headers)
        
        # Rellenar datos base de la inspección
        row_data[header_indices["Fecha"]] = execution.fecha
        row_data[header_indices["Hora"]] = execution.hora
        row_data[header_indices["Usuario"]] = user.nombre
        row_data[header_indices["Propiedad"]] = prop.nombre
        row_data[header_indices["Checklist"]] = checklist.titulo
        row_data[header_indices["Estado"]] = execution.status
        row_data[header_indices["Observación"]] = execution.observations or ""
        
        # Rellenar cada una de las respuestas en su celda e ítem correspondiente
        for item in non_header_items:
            clean_name = item.texto.split('|')[0] if '|' in item.texto else item.texto
            
            # Obtener la respuesta guardada
            raw_resp = execution.responses.get(str(item.id))
            
            # Formatear la respuesta de manera elegante y comprensible para el usuario
            if raw_resp is None:
                respuesta_str = "Sin responder"
            elif isinstance(raw_resp, bool):
                respuesta_str = "Sí" if raw_resp else "No"
            else:
                # Normalizar booleanos en formato string
                val_lower = str(raw_resp).strip().lower()
                if val_lower == "true":
                    respuesta_str = "Sí"
                elif val_lower == "false":
                    respuesta_str = "No"
                else:
                    respuesta_str = str(raw_resp)
            
            # Insertar la respuesta en la celda/columna correcta
            if clean_name in header_indices:
                row_data[header_indices[clean_name]] = respuesta_str
                
        # 6. Registrar la fila completa en Google Sheets
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        print(f"Error sincronizando con Google Sheets: {e}")
        return False
