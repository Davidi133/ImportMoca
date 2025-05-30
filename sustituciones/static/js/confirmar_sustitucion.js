async function aplicarSustitucion() {
  const identificadorViejo = document.getElementById("identificador-original").value.trim();
  const identificadorNuevo = document.getElementById("nuevo-identificador").value.trim();
  const operacion = document.getElementById("operacion").value;
  const factor = document.getElementById("factor").value.trim();

  if (!identificadorViejo || !identificadorNuevo || !factor) {
    showDialog("Campos requeridos", "Por favor, completa todos los campos antes de aplicar la sustitución.");
    return;
  }

  showDialog(
    "Confirmar sustitución",
    `¿Deseas aplicar la sustitución del artículo ${identificadorViejo} por ${identificadorNuevo} con factor ${factor} (${operacion})?`,
    {
      type: "confirm",
      confirmText: "Aplicar",
      cancelText: "Cancelar",
      onConfirm: async () => {
        try {
          const response = await fetch("/importmoca/setup/aplicar-sustitucion/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({
              identificador_viejo: identificadorViejo,
              identificador_nuevo: identificadorNuevo,
              operacion: operacion,
              factor: factor
            })
          });

          const result = await response.json();

          if (result.success) {
            showDialog("Sustitución aplicada", "Se ha ejecutado correctamente el cambio.");
          } else {
            showDialog("Error", result.error || "Error desconocido al aplicar la sustitución.");
          }
        } catch (error) {
          console.error(error);
          showDialog("Error inesperado", "No se pudo aplicar la sustitución.");
        }
      },
      onCancel: () => {
        showDialog("Cancelado", "No se ha realizado ninguna modificación.");
      }
    }
  );
}

function getCSRFToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}
