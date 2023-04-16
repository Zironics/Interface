from datetime import datetime
from django import forms

class parametre(forms.Form):
    
    choices = [('betweenness','betweenness'),('closeness','closeness'),('degree','degree'),('eigenvector','eigenvector')]
    algo = [('arbre','arbre'),('decomposition','decomposition')]
    image_id = forms.FileField()
    nb_obj = forms.IntegerField(widget=forms.NumberInput(attrs={"class":"form-control"}))
    nb_rel = forms.IntegerField(widget=forms.NumberInput(attrs={"class":"form-control"}))
    nb_att = forms.IntegerField(widget=forms.NumberInput(attrs={"class":"form-control"}))
    seuil = forms.FloatField(widget=forms.NumberInput(attrs={'step': "0.01",'min':0,'max':1}))
    method = forms.ChoiceField(choices = choices)
    algo = forms.ChoiceField(choices=algo)
