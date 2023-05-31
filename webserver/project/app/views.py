import json
import os


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .mongo import User as MongoUser
from .utils import validate_login
import globals as g

logger = g.Logger(__name__)

DATA_TELEGRAM_LOGIN = os.getenv("AUTH_BOT_USERNAME")
DATA_AUTH_URL = os.getenv("AUTH_REDIRECT")
POST_TOKEN = os.getenv("POST_TOKEN")
ADMINS = [int(admin) for admin in os.getenv("ADMINS").split(",")]
MAP_PATH = os.path.join(settings.STATIC_ROOT, "map.html")
LEADERBOARD_PATH = os.path.join(settings.STATIC_ROOT, "leaderboard.json")


def index(request):
    context = request.session.pop("context", None)

    return render(
        request,
        "index.html",
        {
            "data_telegram_login": DATA_TELEGRAM_LOGIN,
            "data_auth_url": DATA_AUTH_URL,
            "context": context,
            "race_is_live": get_status(),
        },
    )


@user_passes_test(lambda u: u.is_superuser)
def admin(request):
    return render(request, "admin.html")


def login(request):
    query = request.GET

    if not validate_login(query):
        return Http404

    telegram_id = query.get("id")

    logger.debug(f"Trying to log in with telegram id {telegram_id}.")

    mongo_user = MongoUser.objects(telegram_id=telegram_id).first()

    if not mongo_user:
        logger.warning(f"User with telegram id {telegram_id} not found in database.")
        request.session["context"] = "not_registered"
        return redirect("/")

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

    auth.login(request, user)

    logger.debug(f"User with telegram id {telegram_id} logged in.")

    request.session["context"] = "login"

    return redirect("/")


def logout(request):
    auth.logout(request)

    request.session["context"] = "logout"

    return redirect("/")


@csrf_exempt
def post(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    logger.debug("Received POST request.")

    post_token = request.headers.get("post-token")

    if post_token != POST_TOKEN:
        logger.warning(f"Invalid post token: {post_token}")
        return HttpResponse("Invalid post token", status=403)

    request_type = request.headers.get("request-type")

    logger.debug(f"Request type: {request_type}")

    if request_type == "leaderboard":
        leaderboard = json.loads(request.body)

        with open(LEADERBOARD_PATH, "w") as f:
            json.dump(leaderboard, f)

        logger.info(
            f"Received leaderboard with {len(leaderboard)} entries and saved it to {LEADERBOARD_PATH}."
        )

        return HttpResponse("Success")

    elif request_type == "race_stop":
        logger.info("Received request to stop the race, will delete files.")

        try:
            os.remove(MAP_PATH)
            logger.debug(f"Removed map from {MAP_PATH}.")
        except FileNotFoundError:
            logger.debug(f"Map not found at {MAP_PATH}.")
            pass

        try:
            os.remove(LEADERBOARD_PATH)
            logger.debug(f"Removed leaderboard from {LEADERBOARD_PATH}.")
        except FileNotFoundError:
            logger.debug(f"Leaderboard not found at {LEADERBOARD_PATH}.")
            pass

        return HttpResponse("Success")

    elif request_type == "map":
        logger.debug("Received map request.")

        map_html = request.body.decode("utf-8")

        logger.debug("Trying to receive map from request body.")

        with open(MAP_PATH, "w") as f:
            f.write(map_html)

        logger.info(f"Received map and saved it to {MAP_PATH}.")

        return HttpResponse("Success")

    return HttpResponse("Invalid request type", status=400)


def live(request):
    leaderboard = None
    if os.path.exists(LEADERBOARD_PATH):
        with open(LEADERBOARD_PATH, "r") as f:
            leaderboard = json.load(f)

    return render(
        request, "live.html", {"race_is_live": get_status(), "leaderboard": leaderboard}
    )


def race(request):
    return render(request, "race.html")


def races(request):
    return render(request, "races.html")


def get_status():
    if os.path.exists(MAP_PATH) and os.path.exists(LEADERBOARD_PATH):
        return True
    else:
        return False
