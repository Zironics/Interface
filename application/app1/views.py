from django.shortcuts import render
from django.shortcuts import render,redirect
from .forms import *
from django.http.response import HttpResponse
from django.http import HttpResponse 
from .functions import *
from .decomposition import *
import os

# Create your views here.


def affichage(request):
    if request.method == "POST":
        form = parametre(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['image_id']
            method = form.cleaned_data['method']
            seuil = form.cleaned_data['seuil']
            nb_obj = form.cleaned_data['nb_obj']
            nb_rel = form.cleaned_data['nb_rel']
            nb_att = form.cleaned_data['nb_att']
            algo = form.cleaned_data['algo']

            id = str(file).split('.')[0]
            app_directory = os.path.dirname(os.path.dirname( __file__ ))
            file_dir = os.path.join(app_directory, f'image_data/{str(file)}')
            if os.path.isfile(file_dir):
                photo = f'All_images/{id}.jpg'
                if algo == "arbre":
                    s = sentence(image_id = str(file),method = method,seuil = seuil,nb_obj = nb_obj,nb_rel = nb_rel,nb_attr = nb_att)
                else :
                    s = generate_sentence(image_id = str(file),method = method ,nb_obj = nb_obj, nb_rel = nb_rel,nb_att=nb_att,seuil = seuil)
                img = ET.parse(os.path.join(app_directory, f'image_data/{str(file)}')).getroot()
                captions = []
                for cap in img.iter('caption'):
                    captions.append(cap.text)
                
                form = parametre(initial={
                'image_id': file, 
                'method':method,
                'seuil':seuil,
                'nb_obj':nb_obj,
                'nb_rel':nb_rel,
                })  
                return render(request,"caption.html",{"result":s,"img":photo,'captions':captions,'form':form})
            else :
                #error
                pass
        
    form = parametre()
    return render(request,"index.html",{'form':form})