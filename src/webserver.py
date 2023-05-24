import logging

from flask import Flask, render_template

import globals as g

# from flask_bootstrap import Bootstrap4

flask_log = logging.getLogger("werkzeug")
flask_log.disabled = True
app = Flask(__name__)
logger = g.Logger("webserver")
# bootstrap = Bootstrap4(app)


@app.route("/tds_map/", methods=["GET"])
def tds_map():
    return render_template("tds_race.html")


def launch():
    port = 80
    logger.info(f"Starting webserver on port {port}.")
    app.run(port=port, host="0.0.0.0")
    logger.warning("Webserver stopped.")
