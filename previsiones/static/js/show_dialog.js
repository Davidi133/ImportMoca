function showDialog(title, message, options = {}) {
  if (window.dialogActivo) return;

  window.dialogActivo = true;

  const dialog = document.getElementById("main-dialog");
  const titleEl = document.getElementById("dialog-title");
  const messageEl = document.getElementById("dialog-message");
  const confirmBtn = document.getElementById("dialog-confirm-btn");
  const cancelBtn = document.getElementById("dialog-cancel-btn");

  titleEl.textContent = title;
  messageEl.textContent = message;

  confirmBtn.textContent = options.confirmText || "Aceptar";
  cancelBtn.textContent = options.cancelText || "Cancelar";

  cancelBtn.style.display = options.type === "confirm" ? "inline-block" : "none";

  confirmBtn.onclick = () => {
    dialog.close();
    window.dialogActivo = false;
    if (typeof options.onConfirm === "function") options.onConfirm();
  };

  cancelBtn.onclick = () => {
    dialog.close();
    window.dialogActivo = false;
  };

  dialog.showModal();
}
