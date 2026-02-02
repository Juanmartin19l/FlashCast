// Elementos del DOM
const btnEnviar = document.getElementById('btnEnviar');
const btnCancelar = document.getElementById('btnCancelar');
const btnEditar = document.getElementById('btnEditar');
const mensaje = document.getElementById('mensaje');
const logContainer = document.getElementById('log');
const contadorEl = document.getElementById('contador');
const historialEl = document.getElementById('historial');

// Modal
const modalEditar = document.getElementById('modalEditar');
const jsonEditor = document.getElementById('jsonEditor');
const btnGuardar = document.getElementById('btnGuardar');
const btnCancelarEdicion = document.getElementById('btnCancelarEdicion');
const btnCerrarModal = document.getElementById('btnCerrarModal');

let eventSource = null;

// Sistema de notificaciones
function mostrarNotificacion(mensaje, tipo = 'info', duracion = 4000) {
  const notificacion = document.createElement('div');
  notificacion.className = `notificacion notificacion-${tipo}`;
  notificacion.textContent = mensaje;
  document.body.appendChild(notificacion);

  // Trigger animación
  setTimeout(() => notificacion.classList.add('mostrar'), 10);

  // Auto-remover
  setTimeout(() => {
    notificacion.classList.remove('mostrar');
    setTimeout(() => notificacion.remove(), 300);
  }, duracion);
}

// Manejo del Modal
function abrirModalEdicion() {
  fetch('/api/machines')
    .then((res) => res.json())
    .then((data) => {
      jsonEditor.value = JSON.stringify(data, null, 2);
      modalEditar.classList.add('show');
    })
    .catch((err) => {
      mostrarNotificacion('Error al cargar machines.json: ' + err, 'error');
    });
}

function cerrarModalEdicion() {
  modalEditar.classList.remove('show');
}

function guardarMachines() {
  try {
    const machines = JSON.parse(jsonEditor.value);

    fetch('/api/machines', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(machines),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          mostrarNotificacion('Máquinas guardadas correctamente', 'success');
          cerrarModalEdicion();
          // Actualizar contador sin recargar
          fetch('/api/estadisticas')
            .then((res) => res.json())
            .then((stats) => {
              historialEl.textContent = stats.historial_total;
            });
        } else {
          mostrarNotificacion('Error: ' + data.error, 'error');
        }
      })
      .catch((err) => {
        mostrarNotificacion('Error al guardar: ' + err, 'error');
      });
  } catch (e) {
    mostrarNotificacion('JSON inválido: ' + e.message, 'error');
  }
}

// Event Listeners del Modal
btnEditar.addEventListener('click', abrirModalEdicion);
btnCerrarModal.addEventListener('click', cerrarModalEdicion);
btnCancelarEdicion.addEventListener('click', cerrarModalEdicion);
btnGuardar.addEventListener('click', guardarMachines);

// Cerrar modal al hacer click fuera
modalEditar.addEventListener('click', function (e) {
  if (e.target === modalEditar) {
    cerrarModalEdicion();
  }
});

// Cerrar modal con ESC
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    cerrarModalEdicion();
  }
});

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
    mostrarNotificacion('Debes escribir un mensaje', 'error');
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
      mostrarNotificacion('Error: ' + data.error, 'error');
    }
  } catch (error) {
    console.error('Error enviando mensaje:', error);
    mostrarNotificacion('Error al conectar con el servidor', 'error');
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
