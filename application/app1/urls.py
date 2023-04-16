from django.urls import path
from . import views

urlpatterns = [ 
    path('app/',views.affichage,name = 'app'),
]