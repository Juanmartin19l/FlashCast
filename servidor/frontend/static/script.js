// Elementos del DOM
const btnEnviar = document.getElementById('btnEnviar');
const btnCancelar = document.getElementById('btnCancelar');
const btnEditar = document.getElementById('btnEditar');
const mensaje = document.getElementById('mensaje');
const logContainer = document.getElementById('log');
const contadorEl = document.getElementById('contador');
const historialEl = document.getElementById('historial');
const archivoInput = document.getElementById('archivo');
const archivoNombre = document.getElementById('archivo-nombre');
const adjuntarLabel = document.querySelector('.adjuntar-label');

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
btnEnviar.addEventListener('click', function () {
  const mensajeTexto = mensaje.value.trim();
  const archivo = archivoInput.files[0];

  if (!mensajeTexto) {
    mostrarNotificacion('Debes escribir un mensaje', 'error');
    return;
  }

  if (archivo) {
    // Subir archivo primero
    const formData = new FormData();
    formData.append('file', archivo);

    fetch('/api/upload', {
      method: 'POST',
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          mostrarNotificacion('Archivo subido correctamente', 'success');
          // Enviar mensaje junto con nombre del archivo
          enviarMensaje(mensajeTexto, data.filename);
        } else {
          mostrarNotificacion('Error al subir archivo: ' + data.error, 'error');
        }
      })
      .catch((err) => {
        mostrarNotificacion('Error al subir archivo: ' + err, 'error');
      });
  } else {
    // Solo enviar mensaje
    enviarMensaje(mensajeTexto);
  }
});

function enviarMensaje(mensaje, archivoNombre = null) {
  const payload = { mensaje };
  if (archivoNombre) {
    payload.archivo = archivoNombre;
  }
  fetch('/api/enviar', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        mostrarNotificacion('Mensaje enviado correctamente', 'success');
      } else {
        mostrarNotificacion('Error: ' + (data.error || data.message), 'error');
      }
    })
    .catch((err) => {
      mostrarNotificacion('Error al enviar mensaje: ' + err, 'error');
    });
}

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

// Actualizar el nombre del archivo seleccionado
archivoInput.addEventListener('change', function () {
  if (archivoInput.files.length > 0) {
    archivoNombre.textContent = archivoInput.files[0].name;
  } else {
    archivoNombre.textContent = 'Ningún archivo seleccionado';
  }
});
