from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('learning_path_home/', views.learning_path_home, name='learning_path_home'),
]