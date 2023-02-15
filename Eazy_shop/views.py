from django.shortcuts import render

def home (request):
 return render (request,"Eazy_shop/index.html")

def register (request):
 return render (request,"Eazy_shop/register.html")
