// Elementos del DOM
const btnEnviar = document.getElementById('btnEnviar');
const btnCancelar = document.getElementById('btnCancelar');
const mensaje = document.getElementById('mensaje');
const departamentoInput = document.getElementById('departamento');
// const logContainer = document.getElementById('log');
// const contadorEl = document.getElementById('contador');
// const historialEl = document.getElementById('historial');
const archivoInput = document.getElementById('archivo');
const archivoNombre = document.getElementById('archivo-nombre');

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
btnEnviar.addEventListener('click', function () {
  const mensajeTexto = mensaje.value.trim();
  const archivo = archivoInput.files[0];
  const departamento = departamentoInput.value.trim();

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
          enviarMensaje(mensajeTexto, data.filename, departamento);
        } else {
          mostrarNotificacion('Error al subir archivo: ' + data.error, 'error');
        }
      })
      .catch((err) => {
        mostrarNotificacion('Error al subir archivo: ' + err, 'error');
      });
  } else {
    // Solo enviar mensaje
    enviarMensaje(mensajeTexto, null, departamento);
  }
});

function enviarMensaje(mensaje, archivoNombre = null, departamento = '') {
  const payload = { mensaje };
  if (archivoNombre) {
    payload.archivo = archivoNombre;
  }
  if (departamento) {
    payload.departamento = departamento;
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
        const detalle = departamento ? ` a ${departamento}` : '';
        mostrarNotificacion(
          'Mensaje enviado correctamente' + detalle,
          'success',
        );
        limpiarFormularioEnvio();
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
// conectarStream(); // Eliminado

// Focus en el textarea al cargar
mensaje.focus();
cargarDepartamentos();

// Actualizar el nombre del archivo seleccionado
archivoInput.addEventListener('change', function () {
  if (archivoInput.files.length > 0) {
    archivoNombre.textContent = archivoInput.files[0].name;
  } else {
    archivoNombre.textContent = 'Ningún archivo seleccionado';
  }
});
