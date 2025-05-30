from django.urls import path
from . import views

urlpatterns = [
    path('', views.buscar_previsiones, name='buscar_previsiones'),
    path('api/articulos/', views.api_articulos_por_familia, name='api_articulos'),
    path('previsiones/api/previsiones-por-articulo/', views.api_previsiones_por_articulo, name='api_previsiones_por_articulo'),
    path("api/importar_bc/", views.ejecutar_importar_bc, name="importar_bc"),



]
