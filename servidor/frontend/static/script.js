// Elementos del DOM
const btnEnviar = document.getElementById('btnEnviar');
const btnCancelar = document.getElementById('btnCancelar');
const mensaje = document.getElementById('mensaje');
const departamentoInput = document.getElementById('departamento');
const chipDestino = document.getElementById('chipDestino');
const contadorCaracteres = document.getElementById('contadorCaracteres');
// const logContainer = document.getElementById('log');
// const contadorEl = document.getElementById('contador');
// const historialEl = document.getElementById('historial');
const archivoInput = document.getElementById('archivo');
const archivoNombre = document.getElementById('archivo-nombre');
const MAX_BYTES = 2048;

function contarBytes(texto) {
  return new TextEncoder().encode(texto).length;
}

function actualizarContador() {
  const bytes = contarBytes(mensaje.value);
  contadorCaracteres.textContent = bytes;

  if (bytes > MAX_BYTES) {
    contadorCaracteres.style.color = 'var(--accent-danger)';
  } else {
    contadorCaracteres.style.color = 'inherit';
  }
}

function actualizarDestino() {
  const destino = departamentoInput.value;
  chipDestino.textContent = destino
    ? `Destino: ${destino}`
    : 'Destino: Toda la red';
}

function setSendingState(isSending) {
  btnEnviar.disabled = isSending;
  btnEnviar.textContent = isSending ? 'Enviando...' : 'Enviar mensaje';
  btnCancelar.style.display = isSending ? 'block' : 'none';

  if (!isSending) {
    btnCancelar.disabled = false;
    btnCancelar.textContent = 'Cancelar envío';
  }
}

function cargarDepartamentos() {
  fetch('/api/departamentos')
    .then((res) => res.json())
    .then((data) => {
      if (!data.success || !Array.isArray(data.data)) {
        throw new Error(
          data.error || 'No se pudieron cargar los departamentos',
        );
      }

      const departamentos = data.data;
      for (const departamento of departamentos) {
        const option = document.createElement('option');
        option.value = departamento;
        option.textContent = departamento;
        departamentoInput.appendChild(option);
      }

      actualizarDestino();
    })
    .catch((err) => {
      mostrarNotificacion(
        'No se pudieron cargar departamentos: ' + err,
        'warning',
      );
    });
}

function limpiarFormularioEnvio() {
  mensaje.value = '';
  departamentoInput.value = '';
  archivoInput.value = '';
  archivoNombre.textContent = 'Ningún archivo seleccionado';
  actualizarContador();
  actualizarDestino();
  mensaje.focus();
}

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

// Enviar mensaje
btnEnviar.addEventListener('click', async function () {
  const mensajeTexto = mensaje.value.trim();
  const archivo = archivoInput.files[0];
  const departamento = departamentoInput.value.trim();
  const bytes = contarBytes(mensajeTexto);

  if (!mensajeTexto) {
    mostrarNotificacion('Debes escribir un mensaje', 'error');
    return;
  }

  if (bytes > MAX_BYTES) {
    mostrarNotificacion(
      `El mensaje supera el limite de ${MAX_BYTES} bytes`,
      'error',
    );
    return;
  }

  setSendingState(true);

  if (archivo) {
    try {
      // Subir archivo primero
      const formData = new FormData();
      formData.append('file', archivo);

      const uploadRes = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const uploadData = await uploadRes.json();

      if (!uploadData.success) {
        mostrarNotificacion(
          'Error al subir archivo: ' +
            (uploadData.error || 'Error desconocido'),
          'error',
        );
        return;
      }

      mostrarNotificacion('Archivo subido correctamente', 'success');
      await enviarMensaje(mensajeTexto, uploadData.filename, departamento);
    } catch (err) {
      mostrarNotificacion('Error al subir archivo: ' + err, 'error');
    } finally {
      setSendingState(false);
    }
  } else {
    try {
      // Solo enviar mensaje
      await enviarMensaje(mensajeTexto, null, departamento);
    } finally {
      setSendingState(false);
    }
  }
});

async function enviarMensaje(mensaje, archivoNombre = null, departamento = '') {
  const payload = { mensaje };
  if (archivoNombre) {
    payload.archivo = archivoNombre;
  }
  if (departamento) {
    payload.departamento = departamento;
  }
  const res = await fetch('/api/enviar', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (data.success) {
    const detalle = departamento ? ` a ${departamento}` : '';
    mostrarNotificacion('Mensaje enviado correctamente' + detalle, 'success');
    limpiarFormularioEnvio();
    return;
  }

  mostrarNotificacion('Error: ' + (data.error || data.message), 'error');
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
// conectarStream(); // Eliminado

// Focus en el textarea al cargar
mensaje.focus();
cargarDepartamentos();
actualizarContador();
actualizarDestino();

mensaje.addEventListener('input', actualizarContador);
departamentoInput.addEventListener('change', actualizarDestino);

// Actualizar el nombre del archivo seleccionado
archivoInput.addEventListener('change', function () {
  if (archivoInput.files.length > 0) {
    archivoNombre.textContent = archivoInput.files[0].name;
  } else {
    archivoNombre.textContent = 'Ningún archivo seleccionado';
  }
});
