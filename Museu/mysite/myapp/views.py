# encoding:utf-8
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup
from .models import Artista, Obra, Museo, Rating
from django.shortcuts import render, get_object_or_404
from .forms import *
import shelve
from .recommendations import  transformPrefs, calculateSimilarItems, getRecommendations, getRecommendedItems, topMatches

def obras_por_artista(request):
    formulario = ObraPorArtistaForm()
    obras=[]
    totalObras=[]
    busq = ""
    if request.method=='POST':
        formulario = ObraPorArtistaForm(request.POST)
        if formulario.is_valid():
            busq = formulario.cleaned_data['artistas']

    directorio = 'Index'
    ix = open_dir(directorio)
    with ix.searcher() as searcher:
        artista = "'" + busq + "'"
        query = QueryParser("artista", ix.schema).parse(artista)
        totalObras =  searcher.search(query)
        for obra in totalObras:
            ob= Obra.objects.get(nombre=obra['nombre'])
            if ob not in obras:
                obras.append(ob)
        return render(request, 'obrasPorArtista.html', {'formulario':formulario, 'obras':obras, 'artista':artista})

def obras_por_museo(request):
    formulario = ObraPorMuseoForm()
    obras=[]
    totalObras=[]
    busq = ""
    exp = []
    if request.method=='POST':
        formulario = ObraPorMuseoForm(request.POST)
        if formulario.is_valid():
            busq = formulario.cleaned_data['Museos']
            exp = request.POST.getlist('expuesto')

    directorio = 'Index'
    ix = open_dir(directorio)
    with ix.searcher() as searcher:
        museo = "'" + busq + "'"
        query = QueryParser("museo", ix.schema).parse(museo)
        totalObras = searcher.search(query, limit=None)
        for obra in totalObras:
            ob= Obra.objects.get(nombre=obra['nombre'])
            if ob not in obras:
                if exp:
                    if("Sala" in ob.expuesto):
                        obras.append(ob)  
                else:
                    obras.append(ob)
        return render(request, 'obrasPorMuseo.html', {'formulario':formulario, 'obras':obras})

def obras_por_nombre_tecnica(request):
    formulario = ObraPorMuseoTecnicaForm()
    obras=[]
    totalObras=[]
    busq = ""
    
    if request.method=='POST':
        formulario = ObraPorMuseoTecnicaForm(request.POST)
        if formulario.is_valid():
            busq = formulario.cleaned_data['Museo_Tecnica']
     
    directorio = 'Index'
    ix = open_dir(directorio)
    with ix.searcher() as searcher:
        busq = "'" + busq + "'"
        query = MultifieldParser(["nombre","tecnica"], ix.schema, group=OrGroup).parse(busq)
        totalObras = searcher.search(query, limit=None)
        for obra in totalObras:
            ob= Obra.objects.get(nombre=obra['nombre'])
            if ob not in obras:
                obras.append(ob)
        return render(request, 'obrasPorNombreTecnica.html', {'formulario':formulario, 'obras':obras})
    
def obras_similares(request):
    if request.method=='POST':
        form = ObraSimilarForm(request.POST)
        if form.is_valid():
            idObra = form.cleaned_data['Similar_Obra']
            obra = get_object_or_404(Obra, pk=idObra)
            shelf = shelve.open("dataRS.dat")
            ItemsPrefs = shelf['ItemsPrefs']
            shelf.close()
            recommended = topMatches(ItemsPrefs, int(idObra),n=3)
            obras = []
            similar = []
            for re in recommended:
                obras.append(Obra.objects.get(pk=re[1]))
                similar.append(re[0])
            items= zip(obras,similar)
            return render(request,'obrasSimilares.html', {'obra': obra,'items': items})
    else:
        form = ObraSimilarForm()
    return render(request,'buscarObrasSimilares.html', {'formulario': form})

def list_obras(request):
    obras = Obra.objects.all().order_by('nombre')
    return render(request, 'obras.html', {'obras':obras})

def list_artistas(request):
    artistas = Artista.objects.all().order_by('nombre')
    return render(request, 'artistas.html', {'artistas':artistas})

def list_museos(request):
    museos = Museo.objects.all().order_by('nombre')
    return render(request, 'museos.html', {'museos':museos})

def detallesObra(request, id):
    obra = Obra.objects.get(id = id)
    return render(request, 'detallesObra.html', {'obra':obra})

def inicio(request):
    return render(request, 'index.html')

#Sistema de Recomendación
def loadDict():
    Prefs={}   # matriz de usuarios y puntuaciones a cada a items
    shelf = shelve.open("dataRS.dat")
    ratings = Rating.objects.all()
    for ra in ratings:
        user = int(ra.museo.id)
        itemid = int(ra.obra.id)
        rating = float(ra.rating)
        Prefs.setdefault(user, {})
        Prefs[user][itemid] = rating
    shelf['Prefs']=Prefs
    shelf['ItemsPrefs']=transformPrefs(Prefs)
    shelf['SimItems']=calculateSimilarItems(Prefs, n=10)
    shelf.close()
    
def loadRS(request):
    loadDict()
    return render(request,'loadRS.html')
