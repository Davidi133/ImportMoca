from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin_importmoca/', admin.site.urls),
    path('', include('previsiones.urls')),
    path('pedidos/', include('pedidos.urls')),
    path("setup/", include("sustituciones.urls")),
    path("clientes/", include("clientes.urls")),
]

