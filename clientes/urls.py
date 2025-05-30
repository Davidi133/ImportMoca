from django.urls import path
from . import views

app_name = 'clientes'
urlpatterns = [
    path("", views.buscar_clientes, name="buscar_clientes"),
    path("pedidos/<str:cliente_id>/", views.ver_pedidos_cliente, name="ver_pedidos_cliente"),
    path("api/buscar-clientes/", views.api_buscar_clientes, name="api_buscar_clientes"),
    path("pedido/<str:pedido_id>/", views.ver_pedido_detalle, name="ver_pedido_detalle"),
    path("crear-pedido-venta/", views.crear_pedido_venta_bc, name="crear_pedido_venta_bc"),
    path("crear/", views.crear_pedido_desde_cero, name="crear_pedido"),

]
