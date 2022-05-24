from django.contrib import admin
from django.urls import path
from myapp import views, populate

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio),
    path('cargarBD/', populate.carga),
    path('cargarWhoosh/', populate.cargaWhoosh),
    path('cargarRS/', views.loadRS),
    path('obras/', views.list_obras),
    path('artistas/', views.list_artistas),
    path('museos/', views.list_museos),
    path('detallesObra/<int:id>', views.detallesObra),
    path('obrasPorMuseo/', views.obras_por_museo),
    path('obrasPorArtista/', views.obras_por_artista),
    path('obrasPorNombreTecnica/', views.obras_por_nombre_tecnica),
    path('obrasSimilares/', views.obras_similares),
]