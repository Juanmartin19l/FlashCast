# 📋 Instrucciones - MENSAJE Esclavo (Ejecutable)

## Cómo generar el ejecutable (.exe)

Si modificas el código fuente y necesitas volver a generar el ejecutable, sigue estos pasos desde la raíz del proyecto:

1. Crea un entorno virtual (solo la primera vez):

   ```powershell
   python -m venv .venv
   ```

2. Activa el entorno virtual:

   ```powershell
   # En PowerShell
   .venv\Scripts\Activate.ps1
   # En CMD
   .venv\Scripts\activate.bat
   ```

3. Instala PyInstaller (solo la primera vez):

   ```powershell
   pip install pyinstaller
   ```

4. Genera el ejecutable:

   ```powershell
   pyinstaller --onefile --noconsole --icon=cliente/flashcast.ico cliente/cliente.py
   ```

El archivo generado estará en la carpeta `dist/`.

---

## Paso 1: Copiar a otras PC e Instalar Autoinicio

**En la PC del empleado:**

1. Copia `esclavo.exe`.

2. **Configurar autoinicio - Opción Rápida (Recomendado):**
   - Presiona **Win + R**
   - Escribe `shell:startup` y presiona **Enter**
   - Se abrirá la carpeta de Inicio automático
   - Pega ahí el `esclavo.exe` (o crea un acceso directo)
   - Listo: La próxima vez que prendan la compu, el programa se activa solo

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
