# 📋 Instrucciones - MENSAJE Esclavo (Ejecutable)

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
