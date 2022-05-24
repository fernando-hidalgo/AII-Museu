from bs4 import BeautifulSoup
import urllib.request
from whoosh.index import create_in
from whoosh.fields import KEYWORD, Schema, TEXT, NUMERIC
from django.shortcuts import render, redirect
import os, shutil
from .models import Artista, Obra, Museo, Rating
import random
import shelve
from .recommendations import  transformPrefs, calculateSimilarItems

# lineas para evitar error SSL
import ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

#URLs, una para cada museo a cargar. Notar que no está el valor de la página
urlThyssen = "https://www.museothyssen.org/buscador/coleccion/41/tipo/obra?key=&fecha_inicio=&fecha_inicio_actuales=&fecha_fin_actuales=&fecha_fin_pasadas=&sort=search_api_relevance&order=desc&page="
urlSofia = "https://www.museoreinasofia.es/buscar?bundle=obra&f%5B0%5D=obra_en_exposicion%3Atrue&f%5B1%5D=con_imagen%3Atrue&f%5B100%5D=&fecha=&items_per_page=15&keyword=&sort=rel&page="

def get_obras_Thyssen():
    listaObras= []
    #Queremos paginas 0 y 1, por eso range requiere usar 0,2
    for i in range(0,2):
        openURL = urllib.request.urlopen(urlThyssen+str(i))
        bsPagina = BeautifulSoup(openURL, "lxml")
        
        datos = bsPagina.find("div", class_="row row--abajo").find_all("div", class_="col-md-6 col-lg-4 u-mb@xs")
        for c in datos:
            urlObra = c.find("a")['href']
            imagenTarjeta = c.find("a", class_="snippet__media js-snippet-link").find("img")['src']
            openObra = urllib.request.urlopen(urlObra)
            bsObra = BeautifulSoup(openObra, "lxml")
            
            info = bsObra.find("div", class_="page-header__description")
            nombre = info.find("h1", class_="leading u-mb--@xs").find("span").getText()
            fecha = info.find("div", class_="leading u-mb-@xs").getText().replace("h","H")
            tecnica = list(info.find_all("div", class_="u-mb-@xs")[1].stripped_strings)[0]
            dimensiones = info.find_all("div", class_="u-display-inline")[1].getText()
            museo = info.find_all("div", class_="u-display-inline")[2].getText()
            expuesto = info.find_all("div", class_="u-display-inline")[5].getText()
            desc = bsObra.find("div", class_="long-description is-collapsed u-mb-@xs")
            if desc is not None:
                descripcion = bsObra.find("div", class_="long-description is-collapsed u-mb-@xs").find("div").find("p").getText()
            else:
                descripcion = bsObra.find("div", class_="col-md-5 col-md-pull-3").find("div", class_="u-display-inline").getText()
            try:
               imagen = bsObra.find("div", class_="col-md-4 col-md-pull-3").find("a")['data-href']
            except KeyError:
                imagen = "https://www.museothyssen.org"+bsObra.find_all("img", class_="u-mb@print img-fluid img-print")[0]['src']
            artista = bsObra.find("h2", class_="page-header__title").find("a").getText()
            
            listaObras.append((nombre,fecha,dimensiones,museo,descripcion,artista,imagen,expuesto,tecnica,imagenTarjeta))
    return listaObras

def get_obras_Sofia():
    listaObras= []
    #Queremos paginas 0 y 1, por eso range requiere usar 0,2
    for i in range(0,2):
        openURL = urllib.request.urlopen(urlSofia+str(i))
        bsPagina = BeautifulSoup(openURL, "lxml")
        
        datos = bsPagina.find("ul", class_="thumbnails grid").find_all("li", class_="span3")
        for c in datos:
            urlObra = c.find("a")['href']
            imagenTarjeta = c.find("div", class_="miniatura__imagen miniatura__imagen--centrada-vertical").find("img")['src']
            openObra = urllib.request.urlopen('https://www.museoreinasofia.es'+urlObra)
            bsObra = BeautifulSoup(openObra, "lxml")
            
            nombre = bsObra.find("h1", class_="artwork__data-title title3").getText().strip()
            museo = 'Museo Reina Sofia'
            fecha = bsObra.find("div", class_="field field-name-field-obra-datacion-texto field-type-text field-label-inline clearfix").find("div", class_="field-item even").getText()
            tec = bsObra.find("div", class_="field field-name-field-obra-materia field-type-text field-label-inline clearfix")
            if tec is not None:
                tecnica = tec.find("div", class_="field-item even").getText().strip()
            else:
                tecnica = 'No especificada'
            dim = bsObra.find("div", class_="field field-name-field-obra-dimensiones field-type-text field-label-inline clearfix")
            if dim is not None:
                dimensiones = dim.find("div", class_="field-item even").getText().strip()
            else:
                dimensiones = 'No especificadas'
            try:
               expuesto = bsObra.find_all("div", class_="field field-type-text field-label-inline clearfix")[1].find("div", class_="field-items").getText().strip()
            except IndexError:
                expuesto = 'No expuesto'
            artista = bsObra.find("h2", class_="artwork__data-subtitle-primary subtitle3").find("a").getText()
            desc = bsObra.find("div", class_="tabbable")
            if dim is not None:
                descripcion = desc.getText()
            else:
                descripcion = 'No especificada'
            if (len(descripcion)==0):
                descripcion = 'No especificada'
            imagen = bsObra.find("div", class_="artwork__image").find("a")['href']
            
            listaObras.append((nombre,fecha,dimensiones,museo,descripcion,artista,imagen,expuesto,tecnica, imagenTarjeta))
    return listaObras

def get_obras_total():
    listaTotal = get_obras_Thyssen() + get_obras_Sofia()
    return listaTotal

def populateDB():
    #variables para contar el número de registros que vamos a almacenar
    num_obras = 0
    num_artistas = 0
    num_museos = 0
    
    #borramos todas las tablas de la BD
    Artista.objects.all().delete()
    Obra.objects.all().delete()
    Museo.objects.all().delete()

    listaObras= get_obras_total()
    for obra in listaObras:
        if not Obra.objects.filter(nombre=obra[0]).exists():
            
            #Obras
            Obra.objects.create(nombre= obra[0],fecha = obra[1], dimensiones = obra[2], lugar = obra[3], descripcion = obra[4], artista=obra[5], imagen=obra[6], expuesto=obra[7], tecnica=obra[8], imagenTarjeta=obra[9])
            num_obras+=1

            #Artistas
            if not Artista.objects.filter(nombre=obra[5]).exists():
                Artista.objects.create(nombre= obra[5])
                num_artistas+=1
            
            #Museos
            if not Museo.objects.filter(nombre=obra[3]).exists():
                Museo.objects.create(nombre= obra[3])
                num_museos+=1    
    crearRatings()
    return ((num_obras, num_artistas, num_museos))

def crearRatings():
    obras = Obra.objects.all()
    for o in obras:
        print(o.id)
        #m = Museo.objects.filter(nombre=o.lugar)
        museos = Museo.objects.all()
        for m in museos:
            Rating.objects.create(museo = m, obra = o, rating = random.randint(1, 5))
            

#carga los datos desde la web en la BD
def carga(request):
    if request.method=='POST':
        if 'Aceptar' in request.POST:
            num_obras, num_artistas, num_museos = populateDB()
            
            mensaje="Se han almacenado: " + str(num_obras) +" obras, " + str(num_artistas) +" artistas y " + str(num_museos) +" museos"
            return render(request, 'cargaBD.html', {'mensaje':mensaje})
        else:
            return redirect("/")

    return render(request, 'confirmacion.html')


def populateWhoosh():
    schemObras = Schema(idObra = NUMERIC(stored=True), nombre=KEYWORD(stored=True), fecha= TEXT(stored=True), museo=KEYWORD(stored=True), descripcion=TEXT(stored=True), artista = KEYWORD(stored=True), expuesto=TEXT(stored=True), tecnica=KEYWORD(stored=True))

    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    

    ix = create_in("Index", schema=schemObras)
    writer = ix.writer()
    listaObras = get_obras_total()
    numObras=1
    for obra in listaObras:
        writer.update_document(idObra = numObras, nombre= obra[0],fecha = obra[1], museo = obra[3], descripcion = obra[4], artista=obra[5], expuesto=obra[7], tecnica=obra[8])
        numObras+=1
    writer.commit()
    
    return numObras-1

           
def cargaWhoosh(request):
    if request.method=='POST':
        if 'Aceptar' in request.POST:
            numObras = populateWhoosh()

            mensaje="Se han almacenado: " + str(numObras) +" obras."
            return render(request, 'cargaWhoosh.html', {'mensaje':mensaje})
        else:
            return redirect("/")
           
    return render(request, 'confirmacion.html')