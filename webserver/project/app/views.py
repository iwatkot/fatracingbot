import json
import os

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .mongo import User as MongoUser
from .mongo import Race
from .mongo import create_race, get_races, create_participants_table
from .utils import validate_login
from .forms import NewRaceForm
import globals as g

logger = g.Logger(__name__)

DATA_TELEGRAM_LOGIN = os.getenv("AUTH_BOT_USERNAME")
DATA_AUTH_URL = os.getenv("AUTH_REDIRECT")
POST_TOKEN = os.getenv("POST_TOKEN")
ADMINS = [int(admin) for admin in os.getenv("ADMINS").split(",")]
MAP_PATH = os.path.join(settings.APP_STATIC_DIR, "map.html")


class AppState:
    def __init__(self):
        self.race_is_live = False
        self.leaderboard = []


APP_STATE = AppState()


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
def admin_events(request):
    context = request.session.pop("context", None)

    upcoming_races = get_races("upcoming")
    ended_races = get_races("ended")

    return render(
        request,
        "admin_events.html",
        {
            "context": context,
            "upcoming_races": upcoming_races,
            "ended_races": ended_races,
        },
    )


@user_passes_test(lambda u: u.is_superuser)
def admin_event_download(request, race_id: str):
    race = Race.objects(id=race_id).first()

    table = create_participants_table(race)

    response = FileResponse(
        open(table, "rb"), as_attachment=True, filename="participants.xlsx"
    )
    return response


@user_passes_test(lambda u: u.is_superuser)
def admin_new_event(request):
    if request.method != "POST":
        form = NewRaceForm()
    else:
        form = NewRaceForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            create_race(form_data)
            request.session["context"] = "created"
            return redirect("/admin/events")

    context = {"form": form}
    return render(request, "admin_new_event.html", context)


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

        APP_STATE.leaderboard = leaderboard

        logger.info(f"Received leaderboard: {leaderboard} and saved it in app state.")

        return HttpResponse("Success")

    elif request_type == "race_state":
        race_state = json.loads(request.body)
        logger.info(f"Received request to change race_state to: {race_state}.")

        if race_state == "start":
            APP_STATE.race_is_live = True

        elif race_state == "stop":
            APP_STATE.race_is_live = False
            try:
                os.remove(MAP_PATH)
                logger.debug(f"Removed map from {MAP_PATH}.")
            except FileNotFoundError:
                logger.debug(f"Map not found at {MAP_PATH}.")
                pass

        logger.debug(f"Race state is now: {APP_STATE.race_is_live}.")

        return HttpResponse("Success")

    elif request_type == "map":
        logger.debug("Received map request.")
        map_html = request.body.decode("utf-8")

        start_substring = "<!DOCTYPE html>"
        end_substring = "</html>"

        start_index = map_html.find(start_substring)
        end_index = map_html.find(end_substring)

        if start_index == -1:
            start_index = 0

        html_content = map_html[start_index : end_index + len(end_substring)]

        logger.debug("Trying to receive map from request body.")

        with open(MAP_PATH, "w") as f:
            f.write(html_content)

        logger.info(f"Received map and saved it to {MAP_PATH}.")

        return HttpResponse("Success")

    return HttpResponse("Invalid request type", status=400)


def live(request):
    return render(
        request,
        "live.html",
        {"race_is_live": get_status(), "leaderboard": APP_STATE.leaderboard},
    )


def tds(request):
    return render(request, "tds.html")


def tzar(request):
    return render(request, "tzar.html")


def get_status():
    if APP_STATE.race_is_live and APP_STATE.leaderboard and os.path.exists(MAP_PATH):
        return True
    else:
        return False
