document.addEventListener("DOMContentLoaded", function () {
  const familiaSelect = document.getElementById("familia");
  const articuloSelect = document.getElementById("articulo");
  const cuerpoTabla = document.getElementById("cuerpo-tabla-articulos");
  const btnActualizar = document.getElementById("btn-actualizar");

  if (!familiaSelect || !articuloSelect || !cuerpoTabla || !btnActualizar) return;

  let codigosSeleccionados = new Set(
    Array.from(articuloSelect.selectedOptions).map(opt => String(opt.value))
  );

  if (!familiaSelect.choices) {
    familiaSelect.choices = new Choices(familiaSelect, {
      removeItemButton: true,
      placeholder: true,
      searchPlaceholderValue: "Buscar familia..."
    });
  }

  function cargarArticulos(familias) {
    fetch(`/importmoca/api/articulos/?familias=${familias.join(",")}`)
      .then(r => r.json())
      .then(data => {
        const vistos = new Set();
        const articulos = (data.articulos || []).filter(a => {
          if (vistos.has(a.codigo)) return false;
          vistos.add(a.codigo);
          return true;
        });

        TODOS_ARTICULOS = articulos;

        if (articuloSelect.choicesInstance) articuloSelect.choicesInstance.destroy();
        articuloSelect.innerHTML = "";

        const instance = new Choices(articuloSelect, {
          removeItemButton: true,
          placeholder: true,
          searchPlaceholderValue: "Buscar artículo...",
          choices: articulos.map(a => ({
            value: String(a.codigo),
            label: `${a.descripcion || "(Sin nombre)"} – ${a.codigo}`,
            selected: codigosSeleccionados.has(String(a.codigo))
          }))
        });

        articuloSelect.choicesInstance = instance;
      });
  }

  const familiasIniciales = Array.from(familiaSelect.options).filter(opt => opt.selected).map(opt => opt.value);
  cargarArticulos(familiasIniciales);

  familiaSelect.addEventListener("change", function () {
    const nuevasFamilias = Array.from(familiaSelect.options).filter(opt => opt.selected).map(opt => opt.value);
    codigosSeleccionados = new Set(articuloSelect.choicesInstance?.getValue(true) || []);
    cargarArticulos(nuevasFamilias);
  });

  btnActualizar.addEventListener("click", function () {
    const nuevos = Array.from(articuloSelect.selectedOptions).map(opt => opt.value);
    const actuales = Array.from(cuerpoTabla.querySelectorAll("input[name='cantidad']")).map(i => i.dataset.codigo);

    const nuevosACargar = nuevos.filter(c => !actuales.includes(c));
    const eliminar = actuales.filter(c => !nuevos.includes(c));

    eliminar.forEach(codigo => {
      const fila = cuerpoTabla.querySelector(`input[data-codigo="${codigo}"]`)?.closest("tr");
      if (fila) fila.remove();
    });

    if (!nuevosACargar.length) {
      actualizarFamiliasDesdeTabla();
      return;
    }

    nuevosACargar.forEach(async codigo => {
      const art = TODOS_ARTICULOS.find(a => a.codigo === codigo);
      if (!art) {
        console.warn("Artículo no encontrado en TODOS_ARTICULOS:", codigo);
        return;
      }

      if (!art.familia) {
        console.warn("FAMILIA UNDEFINED para artículo:", art);
      }
      const fechaPedido = document.getElementById("fecha")?.value || "—";
      const almacenPedido = document.getElementById("almacen")?.value || "—";

      const fila = document.createElement("tr");
      fila.innerHTML = `
        <td>${art.codigo}</td>
        <td>${art.descripcion}</td>
        <td>${art.familia || "–"}</td>
        <td class="td-almacen">${almacenPedido}</td>
        <td class="td-fecha">${fechaPedido}</td>
        <td>
          <input type="number"
                 name="cantidad"
                 class="input-stock"
                 value="0"
                 data-original-value="0"
                 data-codigo="${art.codigo}">
        </td>
      `;
      cuerpoTabla.appendChild(fila);
    });

    actualizarFamiliasDesdeTabla();
  });

  function actualizarFamiliasDesdeTabla() {
    const filas = cuerpoTabla.querySelectorAll("tr");
    const familiasActuales = new Set();

    filas.forEach(fila => {
      const celdas = fila.querySelectorAll("td");
      if (celdas.length >= 3) {
        const familia = celdas[2].textContent.trim();
        if (familia && familia !== "–") {
          familiasActuales.add(familia);
        }
      }
    });

    const familiasPrevias = Array.from(familiaSelect.options).map(opt => opt.value);

    if (familiaSelect.choices && typeof familiaSelect.choices.destroy === "function") {
      familiaSelect.choices.destroy();
    }

    familiaSelect.innerHTML = "";

    Array.from(familiasActuales).forEach(f => {
      const option = new Option(f, f, true, true);
      familiaSelect.appendChild(option);
    });

    familiasPrevias.forEach(f => {
      if (!familiasActuales.has(f)) {
        const option = new Option(f, f, false, false);
        familiaSelect.appendChild(option);
      }
    });

    familiaSelect.choices = new Choices(familiaSelect, {
      removeItemButton: true,
      placeholder: true,
      searchPlaceholderValue: "Buscar familia..."
    });
  }
});
