// Elementos del DOM
const btnEnviar = document.getElementById('btnEnviar');
const btnCancelar = document.getElementById('btnCancelar');
const mensaje = document.getElementById('mensaje');
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

    // Procesar estadísticas
    if (data.type === 'estadisticas') {
      contadorEl.textContent = data.contador;
      historialEl.textContent = data.historial_total;

      if (data.enviando) {
        btnEnviar.disabled = true;
        btnEnviar.textContent = 'Enviando...';
        btnCancelar.style.display = 'block';
        btnCancelar.disabled = false;
        btnCancelar.textContent = 'Cancelar envío';
      } else {
        btnEnviar.disabled = false;
        btnEnviar.textContent = 'Enviar a toda la red';
        btnCancelar.style.display = 'none';
      }
      return;
    }

    // Procesar logs
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

// Enviar mensaje
btnEnviar.addEventListener('click', async function () {
  const textoMensaje = mensaje.value.trim();

  if (!textoMensaje) {
    alert('Debes escribir un mensaje');
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
      btnEnviar.textContent = 'Enviando...';
      btnCancelar.style.display = 'block';
    } else {
      alert(`Error: ${data.error}`);
    }
  } catch (error) {
    console.error('Error enviando mensaje:', error);
    alert('Error al conectar con el servidor');
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
      btnCancelar.textContent = 'Cancelando...';
    } else {
      console.error('Error cancelando:', data.error);
    }
  } catch (error) {
    console.error('Error cancelando:', error);
  }
});

// Inicializar
conectarStream();

// Focus en el textarea al cargar
mensaje.focus();
