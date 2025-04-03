from django.urls import path
from . import views

urlpatterns = [
    path('', views.recommendation_result, name='recommendation_result'),
]