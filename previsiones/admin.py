from django.contrib import admin
from .models import ArticuloPrevision

@admin.register(ArticuloPrevision)
class ArticuloPrevisionAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'identificacion', 'descripcion', 'almacen', 'proveedor',
        'familia', 'anio', 'mes',
        'prevision_venta', 'stock_seguridad', 'cantidad_stock_final'
    )
    list_filter = ('anio', 'mes', 'almacen', 'familia', 'proveedor')
    search_fields = ('codigo', 'identificacion', 'descripcion', 'proveedor', 'familia')
