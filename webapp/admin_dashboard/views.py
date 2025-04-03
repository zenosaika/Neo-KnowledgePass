from django.shortcuts import render

def admin_dashboard(request):
    return render(request, 'admin_dashboard/admin_dashboard.html')