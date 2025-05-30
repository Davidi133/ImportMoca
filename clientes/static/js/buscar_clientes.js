document.addEventListener("DOMContentLoaded", function () {
  const select = document.getElementById("cliente");
  const choices = new Choices(select, {
    removeItemButton: true,
    maxItemCount: 1,
    placeholderValue: "Buscar cliente...",
    searchPlaceholderValue: "Buscar cliente...",
    searchEnabled: true,
    itemSelectText: "",
    shouldSort: true,
	searchResultLimit: 20,
    noResultsText: "No se encontraron resultados"
  });

  fetch("/importmoca/clientes/api/buscar-clientes/?term=")
    .then(res => res.json())
    .then(data => {
      const opciones = data.results.map(cliente => ({
        value: cliente.id,
        label: cliente.text
      }));
      choices.setChoices(opciones, "value", "label", true);
    })
    .catch(err => {
      console.error("Error al cargar clientes:", err);
      showDialog("Error al cargar clientes", data.error || "No se pudieron cargar los clientes.", {
          confirmText: "Aceptar",
          type: "alert"
      });

    });

  document.getElementById("btn-confirmar-pago").addEventListener("click", function () {
    const clienteId = choices.getValue(true)[0]; // id del cliente seleccionado
    aniadir_venta(clienteId);
  });

  // Al seleccionar un cliente
  select.addEventListener("change", function () {
    const clienteId = choices.getValue(true)[0];  // Único valor seleccionado
    if (!clienteId) return;

    fetch(`/importmoca/clientes/pedidos/${clienteId}/`)
      .then(res => res.json())
      .then(data => {
        const tbody = document.getElementById("tbody-pedidos");
        tbody.innerHTML = "";

        if (data.pedidos.length > 0) {
          data.pedidos.forEach(p => {
            const fila = document.createElement("tr");
            fila.innerHTML = `
              <td>${p.number}</td>
              <td>${p.orderDate || "—"}</td>
              <td>${p.totalAmountIncludingTax?.toFixed(2) || "0.00"} €</td>
              <td><a href="/importmoca/clientes/pedido/${p.id}/" class="btn btn-sm btn-primary">Ver detalles</a></td>
            `;
            tbody.appendChild(fila);
          });
        } else {
          tbody.innerHTML = "<tr><td colspan='5'>No hay pedidos para este cliente.</td></tr>";
        }

        document.getElementById("tabla-pedidos-cliente").style.display = "block";
      })
      .catch(err => {
        console.error("Error al cargar pedidos:", err);
        showDialog("Error al cargar pedidos", data.error || "No se pudieron cargar los pedidos del cliente.", {
          confirmText: "Aceptar",
          type: "alert"
        });

      });
  });
});

