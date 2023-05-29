import json
import os
import hashlib
import hmac

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from dotenv import load_dotenv

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

DEV_FILE = os.path.join(CURRENT_PATH, "dev.env")

load_dotenv(DEV_FILE)
DATA_TELEGRAM_LOGIN = os.getenv("DATA_TELEGRAM_LOGIN")
DATA_AUTH_URL = os.getenv("DATA_AUTH_URL")
AUTH_BOT_TOKEN = os.getenv("AUTH_BOT_TOKEN")


def index(request):
    return render(
        request,
        "index.html",
        {"data_telegram_login": DATA_TELEGRAM_LOGIN, "data_auth_url": DATA_AUTH_URL},
    )


def login(request):
    query = request.GET
    sorted_keys = sorted(query.keys())
    received_hash = query["hash"]

    data_check_string = "\n".join(
        [f"{key}={query[key]}" for key in sorted_keys if key != "hash"]
    )

    print(data_check_string)

    secret_key = hashlib.sha256(AUTH_BOT_TOKEN.encode()).digest()
    signature = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if signature == received_hash:
        print("Верификация успешна!")
    else:
        print("Верификация не удалась!")

    return HttpResponse("success")

    # return render(request, "login.html")


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
