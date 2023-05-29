import json

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


def index(request):
    return render(request, "index.html")


@csrf_exempt
def post_map(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            print(data)

            return HttpResponse("Success")
        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON data", status=400)

    return HttpResponse("Method not allowed", status=405)


def live(request):
    return render(request, "live.html")


def race(request):
    return render(request, "race.html")


def races(request):
    return render(request, "races.html")
