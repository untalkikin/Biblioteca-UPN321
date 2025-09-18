from django.urls import path
from . import views

# Espacio de nombres para las URLs de la app `catalog`.
app_name = "catalog"

# Rutas principales para el catálogo de la biblioteca:
# - list: lista y filtros
# - detail: detalle de registro
# - new/edit: creación y edición (restringidas en vistas por permisos)
urlpatterns = [
    path("", views.record_list, name="record_list"),
    path("<int:pk>/", views.record_detail, name="record_detail"),
    path("new/", views.record_create, name="record_create"),
    path("<int:pk>/edit/", views.record_update, name="record_update"),
]