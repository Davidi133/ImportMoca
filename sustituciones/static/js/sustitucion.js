// static/js/sustitucion.js

document.addEventListener("DOMContentLoaded", () => {
  const origenInput = document.querySelector('input[name="identificador_origen"]');
  const destinoInput = document.querySelector('input[name="identificador_destino"]');
  const btnComprobar = document.getElementById("btn-comprobar-identificadores");
  const bloqueValidacion = document.getElementById("info-validacion");
  const infoOrigen = document.getElementById("info-origen");
  const infoDestino = document.getElementById("info-destino");

  const bloqueConversor = document.getElementById("bloque-conversion");

  btnComprobar.addEventListener("click", async (e) => {
    e.preventDefault();
    const idOrigen = origenInput.value.trim();
    const idDestino = destinoInput.value.trim();

    if (!idOrigen || !idDestino) {
      showDialog("Campos requeridos", "Debes introducir ambos identificadores antes de continuar.");
      return;
    }

    let datosOrigen, datosDestino;

    try {
      const res1 = await fetch(`/importmoca/setup/verificar_articulo_db/${idOrigen}/`);
      if (!res1.ok) throw new Error("Origen no encontrado");
      datosOrigen = await res1.json();
    } catch {
      showDialog("Identificador incorrecto", `El identificador original {idOrigen} no existe en la base de datos.`);
      return;
    }

    try {
      const res2 = await fetch(`/importmoca/setup/verificar_articulo_bc/${idDestino}/`);
      if (!res2.ok) throw new Error("Destino no encontrado");
      datosDestino = await res2.json();
    } catch {
      showDialog("Identificador incorrecto", `El nuevo identificador ${idDestino} no existe en Business Central.`);
      return;
    }

    document.getElementById("campo-identificador-origen").textContent = datosOrigen.identificacion;
    document.getElementById("campo-identificador-destino").textContent = datosDestino.id || "N/D";

    document.getElementById("campo-codigo-origen").textContent = datosOrigen.codigo;
    document.getElementById("campo-codigo-destino").textContent = datosDestino.No;

    document.getElementById("campo-descripcion-origen").textContent = datosOrigen.descripcion;
    document.getElementById("campo-descripcion-destino").textContent = datosDestino.Description;

    document.getElementById("campo-familia-origen").textContent = datosOrigen.familia;
    document.getElementById("campo-familia-destino").textContent = datosDestino.GenProdPostingGroup || "N/D";

    document.getElementById("campo-proveedor-origen").textContent = datosOrigen.proveedor || "N/D";
    document.getElementById("campo-proveedor-destino").textContent = datosDestino.VendorNo || "N/D";


    bloqueValidacion.style.display = "block";
    bloqueConversor.style.display = "block";
  });
});