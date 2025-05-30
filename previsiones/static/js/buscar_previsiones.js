document.addEventListener('DOMContentLoaded', function () {
  const familiaSelect = document.getElementById('familia');
  const articuloSelect = document.getElementById('articulo');
  const inputPorcentaje = document.getElementById('porcentaje-masivo');

  // Inicializar Choices para familia
  const familiaChoices = new Choices(familiaSelect, {
    removeItemButton: true,
    placeholder: true,
    searchPlaceholderValue: 'Buscar familia...'
  });

  // Inicializar Choices para artículo
  const articuloChoices = new Choices(articuloSelect, {
    removeItemButton: true,
    placeholder: true,
    searchPlaceholderValue: 'Buscar artículo...'
  });

  // Obtener parámetros desde contexto (inyectado por Django en base.html o la vista)
  const seleccionadosDesdeContexto = window.ARTICULOS_SELECCIONADOS || [];

  // Función para actualizar artículos según la familia seleccionada
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

        // Limpiar y establecer nuevas opciones
        articuloChoices.setChoices(
          articulos.map(a => ({
            value: `${a.codigo}|||${a.descripcion}`,
            label: `${a.descripcion || '(Sin nombre)'} - ${a.codigo}`,
            selected: seleccionadosDesdeContexto.includes(a.codigo)
          })),
          'value',
          'label',
          true
        );
      })
      .catch(error => {
        console.error('Error al cargar artículos:', error);
      });
  }

  // Event listeners para cambios en la selección de familia
  familiaSelect.addEventListener('change', actualizarArticulosPorFamilia);

  // Llamar a la función al cargar la página
  actualizarArticulosPorFamilia();
});

document.getElementById("form-pedido").addEventListener("submit", function (e) {
  const filas = document.querySelectorAll("#tabla-resultados tbody tr");
  const datos = [];

  filas.forEach(fila => {
    const articulo = fila.cells[0]?.textContent?.trim();
    const familia = fila.cells[1]?.textContent?.trim();
    const cantidad = fila.cells[2]?.querySelector("input")?.value;

    if (articulo && cantidad) {
      datos.push({
        articulo,
        familia,
        cantidad: Number(cantidad)
      });
    }
  });

  document.getElementById("datos_tabla").value = JSON.stringify(datos);
});
