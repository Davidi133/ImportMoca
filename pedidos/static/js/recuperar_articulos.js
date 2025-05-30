document.addEventListener("DOMContentLoaded", function () {
  const articuloSelect = document.getElementById("articulo");
  const familiaSelect = document.getElementById("familia");

  if (!articuloSelect || !familiaSelect) return;

  // Guardar artículos seleccionados del pedido original
  let codigosSeleccionados = new Set(
    Array.from(articuloSelect.selectedOptions).map(opt => String(opt.value))
  );

  // Inicializar Choices para familia
  if (!familiaSelect.choices) {
    familiaSelect.choices = new Choices(familiaSelect, {
      removeItemButton: true,
      placeholder: true,
      searchPlaceholderValue: "Buscar familia..."
    });
  }

  // Función para cargar artículos por familias seleccionadas
  function cargarArticulos(familiasSeleccionadas) {
    fetch(`/importmoca/api/articulos/?familias=${familiasSeleccionadas.join(",")}`)
      .then(response => response.json())
      .then(data => {
        const articulos = data.articulos || [];

        // Eliminar duplicados
        const vistos = new Set();
        const articulosUnicos = articulos.filter(a => {
          const key = String(a.codigo);
          if (vistos.has(key)) return false;
          vistos.add(key);
          return true;
        });

        // Destruir instancia anterior si existe
        if (articuloSelect.choicesInstance) {
          articuloSelect.choicesInstance.destroy();
        }

        // Limpiar opciones previas
        articuloSelect.innerHTML = "";

        // Crear nueva instancia de Choices con selección conservada
        const instance = new Choices(articuloSelect, {
          removeItemButton: true,
          placeholder: true,
          searchPlaceholderValue: "Buscar artículo...",
          choices: articulosUnicos.map(a => ({
            value: String(a.codigo),
            label: `${a.descripcion || "(Sin nombre)"} – ${a.codigo}`,
            selected: codigosSeleccionados.has(String(a.codigo))
          }))
        });

        articuloSelect.choicesInstance = instance;
      })
      .catch(err => {
        console.error("Error al cargar artículos:", err);
      });
  }

  // Cargar artículos al cargar la página con familias iniciales
  const familiasIniciales = Array.from(familiaSelect.options)
    .filter(opt => opt.selected)
    .map(opt => opt.value);
  cargarArticulos(familiasIniciales);

  // Recargar artículos cada vez que cambian las familias
  familiaSelect.addEventListener("change", function () {
    const nuevasFamilias = Array.from(familiaSelect.options)
      .filter(opt => opt.selected)
      .map(opt => opt.value);

    // Actualizar lista de artículos seleccionados actuales
    codigosSeleccionados = new Set(
      articuloSelect.choicesInstance?.getValue(true) || []
    );

    cargarArticulos(nuevasFamilias);
  });
});
