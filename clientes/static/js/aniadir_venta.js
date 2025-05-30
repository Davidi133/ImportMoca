function aniadir_venta(clienteId) {
  if (!clienteId) {
    showDialog("Cliente no seleccionado", "Para crear un pedido, primero debes seleccionar un cliente.", {
      confirmText: "Cerrar",
      type: "alert"
    });
  }
    else {
      // Redirigir con clienteId como parámetro GET
      window.location.href = `/importmoca/clientes/crear/?cliente=${clienteId}`;
    }
}
