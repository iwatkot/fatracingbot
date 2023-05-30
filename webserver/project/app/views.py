import json
import os


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from .mongo import User as MongoUser
from .utils import validate_login
import globals as g

logger = g.Logger(__name__)

DATA_TELEGRAM_LOGIN = os.getenv("AUTH_BOT_USERNAME")
DATA_AUTH_URL = os.getenv("AUTH_REDIRECT")
ADMINS = [int(admin) for admin in os.getenv("ADMINS").split(",")]


def index(request):
    return render(
        request,
        "index.html",
        {"data_telegram_login": DATA_TELEGRAM_LOGIN, "data_auth_url": DATA_AUTH_URL},
    )


@user_passes_test(lambda u: u.is_superuser)
def admin(request):
    return render(request, "admin.html")


def telegram_login(request):
    query = request.GET

    if not validate_login(query):
        return Http404

    telegram_id = query.get("id")

    logger.debug(f"Trying to log in with telegram id {telegram_id}.")

    mongo_user = MongoUser.objects(telegram_id=telegram_id).first()

    if not mongo_user:
        logger.warning(f"User with telegram id {telegram_id} not found in database.")
        # Todo: page with info about registration.
        return Http404

    logger.debug(
        f"Found user with telegram id {telegram_id} in database. "
        f"Full name: {mongo_user.first_name} {mongo_user.last_name}."
    )

    try:
        user = User.objects.get(username=mongo_user.telegram_id)
    except User.DoesNotExist:
        logger.debug(
            f"User with telegram id {telegram_id} not found in Django database. It will be created."
        )

        if int(telegram_id) in ADMINS:
            user = User.objects.create_superuser(
                username=str(mongo_user.telegram_id),
                password=str(mongo_user.telegram_id),
            )

            logger.info(f"User with telegram id {telegram_id} is superuser.")

        else:
            user = User.objects.create(
                username=str(mongo_user.telegram_id),
                password=str(mongo_user.telegram_id),
            )

    auth_login(request, user)

    logger.debug(f"User with telegram id {telegram_id} logged in.")

    return redirect("/")


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
