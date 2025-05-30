document.addEventListener("DOMContentLoaded", function () {
  const btnConfirmar = document.getElementById("btn-confirmar-pago");

  if (!btnConfirmar) return;

  btnConfirmar.addEventListener("click", function (e) {
    e.preventDefault();
    showDialog("¿Confirmar pedido?", "¿Deseas confirmar el pedido con los artículos seleccionados?", {
      confirmText: "Sí, confirmar",
      cancelText: "Cancelar",
      type: "confirm",
      onConfirm: () => confirmarPedido()
    });
  });
});


function confirmarPedido() {
    const filas = document.querySelectorAll("#cuerpo-tabla-articulos tr");
    const articulos = [];

    filas.forEach(fila => {
        const input = fila.querySelector("input[name='cantidad']");
        const codigo = input?.dataset.codigo?.trim();
        const cantidadRaw = input?.value?.replace(",", ".").trim();
        const cantidad = parseFloat(cantidadRaw);

        if (codigo && !isNaN(cantidad) && cantidad > 0) {
            articulos.push({ codigo, cantidad });
        }
    });


    if (articulos.length === 0) {
        showDialog("Error", "No hay artículos con cantidades válidas para confirmar.", {
            confirmText: "Aceptar",
            type: "alert"
        });
        return;
    }

    const almacen = document.getElementById("almacen")?.value;
    const fecha_prevision = document.getElementById("fecha")?.value;
    const familias = document.getElementById("familia")
        ? Array.from(document.getElementById("familia").selectedOptions).map(opt => opt.value)
        : [];

    // 1. Confirmación previa antes de enviar
    showDialog("Confirmar pedido", "¿Deseas confirmar este pedido?", {
        confirmText: "Sí, confirmar",
        cancelText: "Cancelar",
        type: "confirm",
        onConfirm: () => {
            // 2. Si el usuario confirma, se envía el pedido
            mostrarLoader();
            fetch("/importmoca/pedidos/crear/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({ articulos, almacen, fecha_prevision, familias })
            })
            .then(response => {
                ocultarLoader();
                if (response.ok) {
                    showDialog("Pedido guardado correctamente", "El pedido ha sido registrado en el sistema.", {
                        confirmText: "Aceptar",
                        type: "alert"
                    });
                } else {
                    return response.json().then(data => {
                        showDialog("Error al guardar", data.error || "Ocurrió un error inesperado.", {
                            confirmText: "Aceptar",
                            type: "alert"
                        });
                    });
                }
            })
            .catch(() => {
                ocultarLoader();
                showDialog("Error de conexión", "No se pudo conectar con el servidor.", {
                    confirmText: "Aceptar",
                    type: "alert"
                });
            });
        }
    });
}

// Extrae CSRF desde las cookies
function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : "";
}

function mostrarLoader() {
document.getElementById("loader").style.display = "flex";
}

function ocultarLoader() {
document.getElementById("loader").style.display = "none";
}
