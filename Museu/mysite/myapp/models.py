from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator

# Create your models here.
class Artista(models.Model):
    nombre = models.TextField(verbose_name='Nombre')
      
    def __str__(self):
        return self.nombre
    
class Museo(models.Model):
    nombre = models.TextField(verbose_name='Nombre')
      
    def __str__(self):
        return self.nombre
    
class Obra(models.Model):
    nombre = models.TextField(verbose_name='Nombre')
    fecha = models.TextField(verbose_name='Fecha')
    tipo = models.TextField(verbose_name='Tipo')
    dimensiones = models.TextField(verbose_name='Dimensiones')
    lugar = models.TextField(verbose_name='Lugar')
    artista = models.TextField(verbose_name='Artista')
    expuesto = models.TextField(verbose_name='Expuesto')
    imagen = models.ImageField(verbose_name='Imagen')
    imagenTarjeta = models.ImageField(verbose_name='Imagen Tarjeta')
    descripcion = models.TextField(verbose_name='Descripción')
    tecnica = models.TextField(verbose_name='Técnica')
      
    def __str__(self):
        return self.nombre 

class Rating(models.Model):
    museo = models.ForeignKey(Museo, on_delete=models.CASCADE)
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    def __str__(self):
        return str(self.rating)