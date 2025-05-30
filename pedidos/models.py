import json

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User


class Pedido(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("procesado", "Procesado"),
        ("cancelado", "Cancelado"),
    ]

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_procesado = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    almacen = models.CharField(max_length=100)
    familias = models.CharField(max_length=255)
    fecha_prevision = models.CharField(max_length=7)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Pedido {self.id} ({self.fecha_creacion.strftime('%Y-%m-%d')})"

class LineaPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='lineas', on_delete=models.CASCADE)
    codigo_producto = models.CharField(max_length=20)
    identificador = models.CharField(max_length=100, blank=True, null=True)

    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_stock_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.codigo_producto} - {self.cantidad}"


class ResumenPedidoBusinessCentral(models.Model):
    pedido = models.OneToOneField("pedidos.Pedido", on_delete=models.CASCADE, related_name="resumen_bc")
    pedidos_bc_ids = models.TextField()  # Guarda JSON: '["id1", "id2"]'
    proveedores = models.TextField()     # Guarda JSON: '["prov1", "prov2"]'
    fecha_creado = models.DateTimeField(auto_now_add=True)

    @property
    def pedidos_bc_ids_list(self):
        try:
            return json.loads(self.pedidos_bc_ids)
        except:
            return []

    @property
    def proveedores_list(self):
        try:
            return json.loads(self.proveedores)
        except:
            return []

    def __str__(self):
        return f"Resumen BC para Pedido {self.pedido.id}"