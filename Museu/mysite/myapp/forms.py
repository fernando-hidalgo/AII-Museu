from django import forms

class ObraPorArtistaForm(forms.Form):
    artistas = forms.CharField(label="Artista", widget=forms.TextInput(), required=True)

class ObraPorMuseoForm(forms.Form):
    Museos = forms.CharField(label="Museos", widget=forms.TextInput(), required=True)
    
class ObraPorMuseoTecnicaForm(forms.Form):
    Museo_Tecnica = forms.CharField(label="Museo o Tecnica", widget=forms.TextInput(), required=True)
    
class ObraSimilarForm(forms.Form):
    Similar_Obra = forms.CharField(label="Obra", widget=forms.TextInput(), required=True)