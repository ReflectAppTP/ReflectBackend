from django.shortcuts import render
from django.http import JsonResponse
#api

def hello_world(request):
    return JsonResponse({"message": "Hello world lol"})