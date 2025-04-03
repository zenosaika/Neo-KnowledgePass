from django.urls import path
from . import views

urlpatterns = [
    path('', views.learning_path, name='learning_path'),
]