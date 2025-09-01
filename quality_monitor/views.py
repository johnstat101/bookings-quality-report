from django.shortcuts import render
from django.http import HttpResponse

# home page view
def home_view(request):
    return render(request, "home.html")