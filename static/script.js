// Elementos del DOM
const btnEnviar = document.getElementById('btnEnviar');
const btnCancelar = document.getElementById('btnCancelar');
const mensaje = document.getElementById('mensaje');
const estado = document.getElementById('estado');
const logContainer = document.getElementById('log');
const contadorEl = document.getElementById('contador');
const historialEl = document.getElementById('historial');

let eventSource = null;

// Conectar a Server-Sent Events para actualizaciones en tiempo real
function conectarStream() {
  eventSource = new EventSource('/api/stream');

  eventSource.onmessage = function (event) {
    const data = JSON.parse(event.data);

    if (data.heartbeat) {
      return; // Ignorar heartbeats
    }

    // Agregar log
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${data.tipo}`;
    logEntry.textContent = data.texto;
    logContainer.appendChild(logEntry);

    // Auto-scroll al final
    logContainer.scrollTop = logContainer.scrollHeight;
  };

  eventSource.onerror = function () {
    console.error('Error en la conexión SSE. Reconectando...');
    setTimeout(conectarStream, 3000);
  };
}

// Actualizar estadísticas
function actualizarEstadisticas() {
  fetch('/api/estadisticas')
    .then((response) => response.json())
    .then((data) => {
      contadorEl.textContent = data.contador;
      historialEl.textContent = data.historial_total;

      if (data.enviando) {
        btnEnviar.disabled = true;
        btnEnviar.textContent = '⏳ ENVIANDO...';
        btnCancelar.style.display = 'block';
        btnCancelar.disabled = false;
        btnCancelar.textContent = '🛑 CANCELAR ENVÍO';
        estado.className = 'estado enviando';
        estado.innerHTML =
          '<span class="status-icon">⏳</span><span class="status-text">Enviando mensajes a la red...</span>';
      } else {
        btnEnviar.disabled = false;
        btnEnviar.textContent = '📤 ENVIAR MENSAJE A TODA LA RED';
        btnCancelar.style.display = 'none';
        estado.className = 'estado success';
        estado.innerHTML =
          '<span class="status-icon">✓</span><span class="status-text">Listo para enviar</span>';
      }
    })
    .catch((error) => console.error('Error actualizando estadísticas:', error));
}

// Enviar mensaje
btnEnviar.addEventListener('click', async function () {
  const textoMensaje = mensaje.value.trim();

  if (!textoMensaje) {
    estado.className = 'estado error';
    estado.innerHTML =
      '<span class="status-icon">❌</span><span class="status-text">Debes escribir un mensaje</span>';
    return;
  }

  try {
    const response = await fetch('/api/enviar', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ mensaje: textoMensaje }),
    });

    const data = await response.json();

    if (response.ok) {
      // Limpiar log anterior
      logContainer.innerHTML = '';

      btnEnviar.disabled = true;
      btnEnviar.textContent = '⏳ ENVIANDO...';
      btnCancelar.style.display = 'block';
      estado.className = 'estado enviando';
      estado.innerHTML =
        '<span class="status-icon">⏳</span><span class="status-text">Enviando mensajes a la red...</span>';
    } else {
      estado.className = 'estado error';
      estado.innerHTML = `<span class="status-icon">❌</span><span class="status-text">${data.error}</span>`;
    }
  } catch (error) {
    console.error('Error enviando mensaje:', error);
    estado.className = 'estado error';
    estado.innerHTML =
      '<span class="status-icon">❌</span><span class="status-text">Error al conectar con el servidor</span>';
  }
});

// Cancelar envío
btnCancelar.addEventListener('click', async function () {
  try {
    const response = await fetch('/api/cancelar', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (response.ok) {
      btnCancelar.disabled = true;
      btnCancelar.textContent = '⏳ CANCELANDO...';
      estado.className = 'estado error';
      estado.innerHTML =
        '<span class="status-icon">⚠️</span><span class="status-text">Cancelando envío...</span>';
    } else {
      console.error('Error cancelando:', data.error);
    }
  } catch (error) {
    console.error('Error cancelando:', error);
  }
});

// Inicializar
conectarStream();
actualizarEstadisticas();
setInterval(actualizarEstadisticas, 500); // Actualizar cada 500ms

// Focus en el textarea al cargar
mensaje.focus();
