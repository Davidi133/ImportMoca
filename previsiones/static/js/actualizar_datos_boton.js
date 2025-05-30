document.getElementById("btn-recargar-familias").addEventListener("click", () => {
  showDialog("Confirmar actualización", "¿Quieres importar previsiones desde Business Central?", {
    type: "confirm",
    confirmText: "Sí, importar",
    cancelText: "Cancelar",
    onConfirm: () => {
      mostrarLoader();
      fetch("/importmoca/api/importar_bc/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "Content-Type": "application/json"
        }
      })
      .then(res => res.json())
      .then(data => {
        ocultarLoader();
        if (data.ok) {
          showDialog("Actualización completada", `Se han importado ${data.total} registros.`);
        } else {
          showDialog("Error", "La actualización no se completó correctamente.");
        }
      })
      .catch(err => {
        ocultarLoader();
        console.error("Error en importar_bc:", err);
        showDialog("Error", "Ocurrió un error al ejecutar la actualización.");
      });
    }
  });
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function mostrarLoader() {
  document.getElementById("loader").style.display = "flex";
}

function ocultarLoader() {
  document.getElementById("loader").style.display = "none";
}
