from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'login.html')

@login_required
def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect('login')
