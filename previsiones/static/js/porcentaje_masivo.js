function aplicarPorcentaje() {
  const inputPorcentaje = document.getElementById('porcentaje-masivo');
  if (!inputPorcentaje) return;

  const porcentaje = parseFloat(inputPorcentaje.value);
  if (isNaN(porcentaje)) return;

  document.querySelectorAll(".input-stock").forEach(input => {
    const base = parseFloat(input.dataset.baseValue || input.value.replace(',', '.'));
    if (!isNaN(base)) {
      input.value = Math.round(base * (porcentaje / 100)).toString();
    }
  });

  // Recalcular el total después de aplicar porcentaje
  if (typeof actualizarTotalPedido === "function") {
    actualizarTotalPedido();
  }
}

function prepararInputPorcentaje() {
  const inputPorcentaje = document.getElementById('porcentaje-masivo');
  if (!inputPorcentaje) return;

  inputPorcentaje.addEventListener("input", () => {
    aplicarPorcentaje();
  });
}

function prepararInputsCantidad() {
  document.querySelectorAll(".input-stock").forEach(input => {
    if (!input.dataset.baseValue) {
      const baseInicial = parseFloat(input.value.replace(',', '.'));
      if (!isNaN(baseInicial)) input.dataset.baseValue = baseInicial;
    }

    input.removeEventListener("input", actualizarBaseValue);
    input.addEventListener("input", actualizarBaseValue);
  });
}

function actualizarBaseValue(e) {
  const val = parseFloat(e.target.value.replace(',', '.'));
  if (!isNaN(val)) e.target.dataset.baseValue = val;
}

document.addEventListener("DOMContentLoaded", () => {
  prepararInputPorcentaje();
  prepararInputsCantidad();

  // Detectar inputs nuevos añadidos a la tabla
  const tabla = document.getElementById("cuerpo-tabla-articulos");
  if (tabla) {
    const observer = new MutationObserver(() => {
      prepararInputsCantidad();
    });

    observer.observe(tabla, {
      childList: true,
      subtree: true
    });
  }
});
