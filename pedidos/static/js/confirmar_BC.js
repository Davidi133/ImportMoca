document.addEventListener("DOMContentLoaded", () => {
  const checkTodos = document.getElementById("check-todos");
  const checkPedidos = document.querySelectorAll(".check-pedido");
  const botonBC = document.getElementById("btn-confirmar-bc");

  // Selección masiva
  if (checkTodos) {
    checkTodos.addEventListener("change", () => {
      checkPedidos.forEach(cb => cb.checked = checkTodos.checked);
      toggleBoton();
    });
  }

  // Mostrar u ocultar botón según selección
  checkPedidos.forEach(cb => cb.addEventListener("change", toggleBoton));

  function toggleBoton() {
    const algunoMarcado = [...checkPedidos].some(cb => cb.checked);
    if (botonBC) botonBC.style.display = algunoMarcado ? "block" : "none";
  }
});

document.getElementById("filtro-estado").addEventListener("change", function () {
  const estado = this.value;
  const tablaPedidos = document.getElementById("tabla-pedidos");
  const tablaBC = document.getElementById("tabla-bc");

  if (estado === "bc") {
    tablaPedidos.style.display = "none";
    tablaBC.style.display = "block";
  } else {
    tablaPedidos.style.display = "block";
    tablaBC.style.display = "none";

    document.querySelectorAll("#tabla-pedidos tbody tr").forEach(row => {
      const estadoActual = row.getAttribute("data-estado");
      row.style.display = (!estado || estado === estadoActual) ? "" : "none";
    });
  }
});


function confirmarPedidosBC() {
  const pedidosSeleccionados = [...document.querySelectorAll(".check-pedido:checked")]
    .map(cb => cb.value);

  if (pedidosSeleccionados.length === 0) {
    showDialog("Sin selección", "Debes seleccionar al menos un pedido para confirmar.", {
      confirmText: "Cerrar"
    });
    return;
  }

  const mensaje = `¿Confirmar los pedidos ${pedidosSeleccionados.join(", ")} en Business Central?`;
  showDialog("Confirmar pedidos", mensaje, {
    type: "confirm",
    confirmText: "Sí, confirmar",
    cancelText: "Cancelar",
    onConfirm: () => {
      mostrarLoader();
      fetch("/importmoca/pedidos/confirmar-bc/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ pedidos: pedidosSeleccionados })
      })
        .then(response => response.json())
        .then(data => {
          const resultados = data.resultados || [];

          const contenidoHTML = resultados.map(res => {
            if (res.resultado === "ok") {
              return `Pedido <strong>${res.numero}</strong> confirmado correctamente.`;
            } else {
              return res.mensaje; //
            }
          }).join("<br>");

          showDialog("Resultado de confirmación", "Cargando...", {
            confirmText: "Aceptar",
            onConfirm: () => location.reload()
          });

          // Sobrescribe el contenido como HTML una vez abierto el modal
          setTimeout(() => {
            const messageEl = document.getElementById("dialog-message");
            if (messageEl) messageEl.innerHTML = contenidoHTML;
          }, 50);

        })
        .catch(err => {
          showDialog("Error", "Se produjo un error inesperado al confirmar los pedidos.", {
            confirmText: "Cerrar"
          });
        });
    }
  });
}



function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  return parts.length === 2 ? parts.pop().split(";").shift() : "";
}

function mostrarLoader() {
  document.getElementById("loader").style.display = "flex";
}

function ocultarLoader() {
  document.getElementById("loader").style.display = "none";
}
