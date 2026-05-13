# StayCheck - SaaS Property Management & Checklist Platform

**StayCheck** es una plataforma profesional diseñada para administradores de propiedades, departamentos y hoteles que necesitan un control riguroso sobre sus procesos operativos y de limpieza.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Flask](https://img.shields.io/badge/framework-Flask-lightgrey.svg)

## 🚀 Características Principales
- **Arquitectura SaaS:** Soporte para múltiples empresas (Administradores) con aislamiento total de datos.
- **Jerarquía de Roles:** SuperAdmin (Dueño), Administrador (Cliente) y Operador (Personal).
- **Checklists Dinámicos:** Crea y personaliza plantillas de inspección con campos ilimitados.
- **Sincronización Cloud:** Envío automático de reportes a **Google Sheets** y almacenamiento en **Google Drive**.
- **Diseño Mobile-First:** Interfaz optimizada para móviles con visualización de historiales mediante tarjetas.
- **Edición Histórica:** Los operadores pueden corregir sus reportes enviados directamente desde la plataforma.

## 🛠️ Requisitos
- Python 3.10 o superior.
- Cuenta de Google Cloud (para sincronización con Sheets).

## 📦 Instalación y Uso

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/TU_USUARIO/StayCheck.git
   cd StayCheck
   ```

2. **Crear y activar entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación:**
   ```bash
   python run.py
   ```
   *El sistema creará automáticamente la base de datos `staycheck.db` en la primera ejecución.*

## 🔒 Seguridad
Las contraseñas se almacenan de forma segura utilizando hashing (PBKDF2). Para recuperación de acceso, el administrador dispone de un script de utilidad `reset_password.py`.

## 📄 Licencia
Este proyecto está bajo la licencia MIT.
