import logging

from flask import Flask, render_template

import globals as g

from flask_bootstrap import Bootstrap4

flask_log = logging.getLogger("werkzeug")
flask_log.disabled = True
app = Flask(__name__)
logger = g.Logger("webserver")
bootstrap = Bootstrap4(app)


@app.route("/", methods=["GET"])
def index():
    context = {
        "title": "Велогонки в Великом Новгороде",
        "description": "Заглушка для описания проекта",
        "comment": "Требуется Telegram",
        "main_button": "Запустить бота",
    }

    return render_template("index.html", context=context)


@app.route("/live", methods=["GET"])
def tds_map():
    context = {"title": "Тур де Селищи 2023"}
    leaderboard_all = racers_debug_data

    return render_template(
        "race_live.html", context=context, leaderboard_all=leaderboard_all
    )


def launch():
    port = 80
    logger.info(f"Starting webserver on port {port}.")
    app.run(port=port, host="0.0.0.0")
    logger.warning("Webserver stopped.")


###############################
####### * DEBUG DATA ##########
###############################


racers_debug_data = [
    {
        "row_number": 1,
        "distance": "23 км",
        "category": "CX / Gravel",
        "race_number": 202,
        "first_name": "Иван",
        "last_name": "Иванов",
    },
    {
        "row_number": 2,
        "distance": "21 км",
        "category": "Road",
        "race_number": 103,
        "first_name": "Петр",
        "last_name": "Петров",
    },
    {
        "row_number": 3,
        "distance": "19 км",
        "category": "MTB",
        "race_number": 304,
        "first_name": "Сидор",
        "last_name": "Сидоров",
    },
]
