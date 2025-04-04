from django.shortcuts import render

def homepage(request):
    return render(request, 'home/homepage.html')

def learning_path_home(request):
    return render(request, 'home/learning_path_home.html')

def graph_rag_home(request):
    return render(request, 'home/graph_rag_home.html')