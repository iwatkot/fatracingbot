import logging
import json
import os

from flask import Flask, render_template

from flask_bootstrap import Bootstrap4

import globals as g

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
def live():
    if not os.path.exists(g.JSON_RACE_INFO):
        logger.warning("JSON race info file wasn't found. No active races.")
        return render_template("race_not.html")
    else:
        with open(g.JSON_RACE_INFO, "r") as race_info_file:
            race_info = json.load(race_info_file)

    race_code = race_info["code"]
    context = {
        "title": race_info["name"],
    }

    logger.debug(f"Loaded JSON race info file. Race with code {race_code} is active.")

    map_path = f"/static/{race_code}_map.html"
    leaderboard_all_path = os.path.join(g.JSON_DIR, f"{race_code}_leaderboard_all.json")

    if not os.path.exists(leaderboard_all_path):
        logger.warning(f"Leaderboard file {leaderboard_all_path} not found.")
        leaderboard_all = []
    else:
        with open(leaderboard_all_path, "r") as json_file:
            leaderboard_all = json.load(json_file)

    logger.debug(f"Loaded leaderboard with {len(leaderboard_all)} entries.")

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
