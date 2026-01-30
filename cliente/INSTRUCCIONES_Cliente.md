# 📋 FlashCast Client - Installation Instructions

## How to Build the Executable (.exe)

If you modify the source code and need to rebuild the executable, follow these steps from the project root:

1. Create a virtual environment (first time only):

   ```powershell
   python -m venv .venv
   ```

2. Activate the virtual environment:

   ```powershell
   # In PowerShell
   .venv\Scripts\Activate.ps1
   # In CMD
   .venv\Scripts\activate.bat
   ```

3. Install PyInstaller (first time only):

   ```powershell
   pip install pyinstaller
   ```

4. Build the executable with FlashCast icon:

   ```powershell
   pyinstaller --onefile --noconsole --icon=frontend/static/flashcast.png cliente/cliente.py
   ```

   **Note:** The FlashCast logo will be embedded as the executable icon.

The generated file will be in the `dist/` folder.

---

## Step 1: Copy to Other PCs and Install Auto-Start

**On the employee's PC:**

1. Copy `cliente.exe`.

2. **Configure auto-start - Quick Option (Recommended):**
   - Press **Win + R**
   - Type `shell:startup` and press **Enter**
   - The Startup folder will open
   - Paste `cliente.exe` there (or create a shortcut)
   - Done: The next time the computer starts, the program will run automatically

3. **Opcional - Crear un acceso directo:**
   - Haz clic derecho en `esclavo.exe` → "Enviar a" → "Escritorio (crear acceso directo)"
   - Luego mueve ese acceso directo a la carpeta de Startup (shell:startup)

## Paso 2: Verificar que funciona

Reinicia la PC y verifica que el servicio está corriendo:

```powershell
# Ver si el proceso está corriendo
Get-Process esclavo -ErrorAction SilentlyContinue
```

O verifica en el Administrador de tareas que `esclavo.exe` está en ejecución.

## Notas Importantes

⚠️ **Puertos**: El ejecutable escucha en `0.0.0.0:5000` por defecto

- Si necesitas cambiar el puerto, edita `.env` y recompila

⚠️ **Privilegios**: El script de autoinicio requiere ejecución como Administrador

⚠️ **Cortafuegos**: Asegúrate que Windows Firewall permite conexiones en el puerto configurado

## Desinstalación

Para remover el autoinicio en una PC:

1. Presiona **Win + R**
2. Escribe: `shell:startup`
3. Elimina el archivo `esclavo.exe` de esa carpeta
