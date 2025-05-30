from django.urls import path
from . import views

app_name = "pedidos"

urlpatterns = [
    path('', views.lista_pedidos, name="lista_pedidos"),
    path("recuperar/<int:pedido_id>/", views.recuperar_pedido, name="recuperar_pedido"),
    path('crear/', views.crear_pedido, name="crear_pedido"),
    path("confirmar-bc/", views.confirmar_pedidos_bc, name="confirmar_pedidos_bc"),

]
