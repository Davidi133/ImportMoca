from django.db import models
from math import ceil
class ArticuloPrevision(models.Model):
    codigo = models.CharField(max_length=50)
    identificacion = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    almacen = models.CharField(max_length=50)
    proveedor = models.CharField(max_length=255, null=True, blank=True)
    familia = models.CharField(max_length=255)
    anio = models.IntegerField()
    mes = models.IntegerField()
    cantidad_compra = models.FloatField(default=0)
    prevision_venta = models.FloatField(default=0)
    stock_seguridad = models.FloatField(default=0)
    cantidad_stock_final = models.FloatField(default=0)

    class Meta:
        unique_together = ('codigo', 'anio', 'mes', 'almacen', 'identificacion')
        verbose_name = 'Previsión Artículo'
        verbose_name_plural = 'Previsiones Artículos'

    def __str__(self):
        return f"{self.codigo} - {self.anio}/{self.mes}"
