from django.urls import path
from . import views

urlpatterns = [
    path('', views.graph_rag, name='graph_rag'),
]