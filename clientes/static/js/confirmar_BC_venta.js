function confirmarPedidoBC() {
    const almacen = document.getElementById("almacen").value.trim();
    const tabla = document.getElementById("cuerpo-tabla-articulos");
    const filas = tabla.querySelectorAll("tr");

    const customerId = window.CUSTOMER_ID;
    const paymentTermsId = "de6543ef-6aca-ee11-9d01-005056a6b8c3";
    const sellToName = window.SELL_TO_NAME;
    const sellToAddressLine1 = window.SELL_TO_ADDRESS;
    const sellToCity = window.SELL_TO_CITY;
    const sellToPostCode = window.SELL_TO_POSTCODE;
    const sellToCountry = "ES";

    const articulos = [];

    filas.forEach((fila) => {
        const inputCantidad = fila.querySelector("input[name='cantidad']");
        const cantidad = parseFloat(inputCantidad?.value?.replace(",", "."));
        const codigo = inputCantidad?.dataset.codigo;
        const descripcion = fila.children[1]?.textContent.trim();

        const articulo = window.TODOS_ARTICULOS.find(a => a.codigo === codigo);
        const itemId = articulo?.identificacion?.trim();

        if (itemId && cantidad > 0) {
            articulos.push({
                itemId,
                descripcion,
                cantidad
            });
        }
    });

    if (articulos.length === 0) {
        showDialog("Error", "No hay artículos con cantidades válidas para confirmar.", {
            confirmText: "Aceptar",
            type: "alert"
        });
        return;
    }

    showDialog("¿Confirmar pedido?", "¿Deseas confirmar el pedido con los artículos seleccionados?", {
        confirmText: "Sí, confirmar",
        cancelText: "Cancelar",
        type: "confirm",
        onConfirm: async () => {
            const payload = {
                customerId,
                almacen,
                paymentTermsId,
                sellToName,
                sellToAddressLine1,
                sellToCity,
                sellToPostCode,
                sellToCountry,
                articulos
            };

            try {
                mostrarLoader();
                const resp = await fetch("/importmoca/clientes/crear-pedido-venta/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCSRFToken()
                    },
                    body: JSON.stringify(payload)
                });

                const data = await resp.json();
                ocultarLoader();

                if (data.resultado === "ok" && data.numero) {
                    // Crear el HTML manualmente con negrita
                    const mensajeHTML = `Pedido <strong>${data.numero}</strong> confirmado correctamente.`;

                    showDialog("Resultado de la confirmación", "Cargando...", {
                        confirmText: "Aceptar",
                        type: "alert",
                    });

                    setTimeout(() => {
                        const messageEl = document.getElementById("dialog-message");
                        if (messageEl) messageEl.innerHTML = mensajeHTML;
                    }, 30);

                } else if (Array.isArray(data.mensajes)) {
                    const erroresHTML = data.mensajes.map(m => `<span style="color:red;">${m}</span>`).join("<br>");

                    showDialog("Errores al crear el pedido", "Cargando...", {
                        confirmText: "Aceptar",
                        type: "alert"
                    });

                    setTimeout(() => {
                        const messageEl = document.getElementById("dialog-message");
                        if (messageEl) messageEl.innerHTML = erroresHTML;
                    }, 30);
                } else {
                    const fallback = data.mensaje || "No se pudo confirmar el pedido.";
                    showDialog("Error", fallback, {
                        confirmText: "Aceptar",
                        type: "alert"
                    });
                }


            } catch (e) {
                ocultarLoader();
                console.error(e);
                showDialog("Error de conexión", "No se pudo conectar con el servidor.", {
                    confirmText: "Aceptar",
                    type: "alert"
                });
            }
        }
    });
}

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
