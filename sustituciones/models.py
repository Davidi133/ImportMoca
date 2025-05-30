from django.db import models

# Create your models here.
from django.db import models

class SustitucionArticulo(models.Model):
    identificador_origen = models.CharField(max_length=255)
    identificador_destino = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255, null=True, blank=True)  # descripción del artículo nuevo
    factor_conversion = models.FloatField()
    tipo_operacion = models.CharField(max_length=10, choices=[("DIV", "Dividir"), ("MUL", "Multiplicar")])
    fecha_aplicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.identificador_origen} → {self.identificador_destino} ({self.tipo_operacion} {self.factor_conversion})"
