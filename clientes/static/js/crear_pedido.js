document.addEventListener("DOMContentLoaded", function () {
  const familiaSelect = document.getElementById("familia");
  const articuloSelect = document.getElementById("articulo");
  const btnActualizar = document.getElementById("btn-actualizar-articulos");
  const cuerpoTabla = document.getElementById("cuerpo-tabla-articulos");

  if (!familiaSelect || !articuloSelect || !btnActualizar || !cuerpoTabla) {
    console.error("Faltan elementos del DOM.");
    return;
  }

  const familiaChoices = new Choices(familiaSelect, {
    removeItemButton: true,
    placeholder: true,
    searchPlaceholderValue: "Buscar familia..."
  });

  const articuloChoices = new Choices(articuloSelect, {
    removeItemButton: true,
    placeholder: true,
    searchPlaceholderValue: "Buscar artículo..."
  });

  function actualizarArticulosPorFamilia() {
    const familiasSeleccionadas = Array.from(familiaSelect.selectedOptions).map(opt => opt.value);
    if (!familiasSeleccionadas.length) {
      articuloChoices.clearStore();
      return;
    }

    fetch(`/importmoca/api/articulos/?familias=${familiasSeleccionadas.join(',')}`)
      .then(response => response.json())
      .then(data => {
        const articulos = data.articulos || [];
        const seleccionadosPrevios = articuloChoices.getValue(true);
        const choices = articulos.map(a => ({
          value: `${a.codigo}|||${a.descripcion}`,
          label: `${a.descripcion || '(Sin nombre)'} - ${a.codigo}`,
          selected: seleccionadosPrevios.includes(a.codigo)
        }));
        articuloChoices.setChoices(choices, 'value', 'label', true);
      })
      .catch(error => {
        console.error('Error al cargar artículos por familia:', error);
      });
  }

  familiaSelect.addEventListener('change', actualizarArticulosPorFamilia);
  actualizarArticulosPorFamilia(); // Inicial

btnActualizar.addEventListener("click", function () {
  const almacenSeleccionado = document.getElementById("almacen")?.value;
  if (!almacenSeleccionado) return;

  let seleccionados = articuloChoices.getValue(true); // ["codigo|||desc", ...]

  // Si no hay artículos seleccionados, añadir todos los visibles en el select
  if (!seleccionados.length) {
    const todasLasOpciones = articuloSelect.querySelectorAll("option");
    seleccionados = Array.from(todasLasOpciones).map(opt => opt.value);
  }

  const codigosSeleccionados = seleccionados.map(val => val.split("|||")[0]);

  const filasActuales = cuerpoTabla.querySelectorAll("tr");

  // Eliminar filas no seleccionadas o que no coincidan con el almacén
  filasActuales.forEach(fila => {
    const input = fila.querySelector("input[name='cantidad']");
    const codigo = input?.dataset.codigo;
    const almacen = fila.children[3]?.textContent?.trim();

    const sigueSeleccionado = codigosSeleccionados.includes(codigo);
    const sigueEnAlmacen = almacen.toUpperCase() === almacenSeleccionado.toUpperCase();

    if (!sigueSeleccionado || !sigueEnAlmacen) {
      fila.remove();
    }
  });

  // Artículos ya visibles después del borrado
  const visibles = Array.from(cuerpoTabla.querySelectorAll("input[name='cantidad']"))
    .map(input => input.dataset.codigo);

  // Añadir nuevos artículos
  codigosSeleccionados.forEach(codigo => {
    if (visibles.includes(codigo)) return;

    const info = TODOS_ARTICULOS.find(a => String(a.codigo) === String(codigo));
    if (!info) return;

    const fila = document.createElement("tr");
    fila.innerHTML = `
      <td>${info.codigo}</td>
      <td>${info.descripcion || "—"}</td>
      <td>${info.familia || "—"}</td>
      <td>${almacenSeleccionado || "—"}</td>
      <td>
        <input type="number" name="cantidad" class="input-stock"
               value="0" data-codigo="${info.codigo}" data-familia="${info.familia}" />
      </td>
    `;
    cuerpoTabla.appendChild(fila);
  });
});
});
