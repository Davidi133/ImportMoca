from django.urls import path
from . import views

urlpatterns = [
    path("", views.sustituir_articulo, name="sustituir_articulo"),
    path("verificar_articulo_db/<str:identificador>/", views.verificar_articulo_db, name="verificar_articulo_db"),
    path("verificar_articulo_bc/<str:codigo>/", views.verificar_articulo_bc, name="verificar_articulo_bc"),
    path('aplicar-sustitucion/', views.aplicar_sustitucion, name='aplicar_sustitucion'),

]
