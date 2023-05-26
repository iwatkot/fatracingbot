import logging
import json
import os

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
    if g.AppState.Race.info:
        context = {"title": g.AppState.Race.info.name}
        race_code = g.AppState.Race.info.code
    else:
        # ! Debug
        context = {"title": "Велогонки в Великом Новгороде"}
        race_code = "TEST"

    map_path = f"/static/{race_code}_map.html"
    json_path = os.path.join(g.JSON_DIR, f"{race_code}_leaderboard_all.json")

    if not os.path.exists(json_path):
        logger.warning(f"Leaderboard file {json_path} not found.")
        leaderboard_all = []
    else:
        with open(json_path, "r") as json_file:
            leaderboard_all = json.load(json_file)

    return render_template(
        "race_live.html",
        context=context,
        leaderboard_all=leaderboard_all,
        map_path=map_path,
    )


def launch():
    port = 80
    logger.info(f"Starting webserver on port {port}.")
    app.run(port=port, host="0.0.0.0")
    logger.warning("Webserver stopped.")
