document.addEventListener("DOMContentLoaded", function () {
  const btnActualizar = document.getElementById("btn-actualizar");
  const selectArticulo = document.getElementById("articulo");
  const selectFamilia = document.getElementById("familia");
  const cuerpoTabla = document.getElementById("cuerpo-tabla-articulos");

  if (!btnActualizar || !selectArticulo || !cuerpoTabla) return;

 btnActualizar.addEventListener("click", function () {
  const codigosSeleccionados = Array.from(selectArticulo.selectedOptions).map(opt => opt.value);
  const codigosVisibles = Array.from(cuerpoTabla.querySelectorAll("input[name='cantidad']")).map(input => input.dataset.codigo);

  codigosVisibles.forEach(codigo => {
    if (!codigosSeleccionados.includes(codigo)) {
      const fila = cuerpoTabla.querySelector(`input[data-codigo="${codigo}"]`)?.closest("tr");
      if (fila) fila.remove();
    }
  });

  const nuevos = codigosSeleccionados.filter(codigo => !codigosVisibles.includes(codigo));
  if (!nuevos.length) {
    actualizarFamiliasDesdeTabla();
    return;
  }

  const almacen = cuerpoTabla.querySelector("tr td:nth-child(5)")?.textContent?.trim();
  if (!almacen) {
    alert("No se pudo determinar el almacén del pedido.");
    return;
  }

  const fechaOriginal = document.getElementById("fecha").value; // YYYY-MM
  let fechaParam = "";
  if (fechaOriginal) {
    const [anioActual, mes] = fechaOriginal.split("-");
    const anio = parseInt(anioActual) - 1;
    fechaParam = `&fecha=${mes}/${anio}`;
  }

  const params = nuevos.map(c => `articulos[]=${encodeURIComponent(c)}`).join("&");
  const url = `/importmoca/previsiones/api/previsiones-por-articulo/?${params}&almacen=${encodeURIComponent(almacen)}${fechaParam}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (!data.articulos) return;

      data.articulos.forEach(art => {
        const fila = document.createElement("tr");

        if (art.descripcion === "(Sin previsión)") {
          const info = TODOS_ARTICULOS.find(a => a.codigo === art.codigo) || {};
          const descripcion = info.descripcion || "Sin descripción";
          const identificacion = info.identificacion || "–";
          const familia = info.familia || "–";

          fila.innerHTML = `
            <td>${art.codigo}</td>
            <th style="display: none;">Identificador</th>
            <td>${descripcion}</td>
            <td>${familia}</td>
            <td>${almacen}</td>
            <td>${fechaOriginal || "–"}</td>
            <td>0</td>
            <td>0</td>
            <td><input type="number" name="cantidad" class="input-stock" value="" data-codigo="${art.codigo}" /></td>
          `;
        } else {
          fila.innerHTML = `
            <td>${art.codigo}</td>
            <td style="display: none;">{{ articulo.identificacion }}</td>
            <td>${art.descripcion}</td>
            <td>${art.familia}</td>
            <td>${art.almacen}</td>
            <td>${fechaOriginal || "–"}</td>
            <td>${Math.ceil(art.stock_seguridad)}</td>
            <td>${Math.ceil(art.prevision_venta)}</td>
            <td>
              <input type="number" name="cantidad" class="input-stock"
                     value="${Math.ceil(art.cantidad_stock_final)}"
                     data-original-value="${Math.ceil(art.cantidad_stock_final)}"
                     data-codigo="${art.codigo}" />
            </td>
          `;
        }

        cuerpoTabla.appendChild(fila);
      });

      actualizarFamiliasDesdeTabla();
    })
    .catch(error => {
      console.error("Error al cargar artículos nuevos:", error);
      alert("Error al actualizar artículos.");
    });
});


  function actualizarFamiliasDesdeTabla() {
    const filas = cuerpoTabla.querySelectorAll("tr");
    const familiasActuales = new Set();

    filas.forEach(fila => {
      const celdas = fila.querySelectorAll("td");
      if (celdas.length >= 4) {
        const familia = celdas[3].textContent.trim();
        if (familia && familia !== "–") {
          familiasActuales.add(familia);
        }
      }
    });

    const familiasPrevias = Array.from(selectFamilia.options).map(opt => opt.value);

    if (selectFamilia.choices && typeof selectFamilia.choices.destroy === "function") {
      selectFamilia.choices.destroy();
    }

    selectFamilia.innerHTML = "";

    Array.from(familiasActuales).forEach(f => {
      const option = new Option(f, f, true, true);
      selectFamilia.appendChild(option);
    });

    familiasPrevias.forEach(f => {
      if (!familiasActuales.has(f)) {
        const option = new Option(f, f, false, false);
        selectFamilia.appendChild(option);
      }
    });

    selectFamilia.choices = new Choices(selectFamilia, {
      removeItemButton: true,
      placeholder: true,
      searchPlaceholderValue: "Buscar familia..."
    });
  }
});
