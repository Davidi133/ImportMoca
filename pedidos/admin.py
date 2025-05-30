from django.contrib import admin
from .models import Pedido, LineaPedido, ResumenPedidoBusinessCentral
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_creacion', 'estado', 'almacen', 'familias', 'fecha_prevision')
    list_filter = ('estado', 'fecha_prevision', 'almacen')

@admin.register(LineaPedido)
class LineaPedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'identificador','codigo_producto', 'cantidad')

@admin.register(ResumenPedidoBusinessCentral)
class ResumenPedidoBCAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "mostrar_ids_bc", "mostrar_proveedores", "fecha_creado")
    readonly_fields = ("pedido", "pedidos_bc_ids", "proveedores", "fecha_creado")

    def mostrar_ids_bc(self, obj):
        return ", ".join(obj.pedidos_bc_ids_list)
    mostrar_ids_bc.short_description = "IDs en BC"

    def mostrar_proveedores(self, obj):
        return ", ".join(obj.proveedores_list)
    mostrar_proveedores.short_description = "Proveedores"