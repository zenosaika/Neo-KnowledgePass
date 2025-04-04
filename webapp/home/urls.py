from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('learning_path_home/', views.learning_path_home, name='learning_path_home'),
    path('graph_rag_home/', views.graph_rag_home, name='graph_rag_home'),
]