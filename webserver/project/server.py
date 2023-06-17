from waitress import serve

from django.contrib.staticfiles.handlers import StaticFilesHandler

from project.wsgi import application

import globals as g

logger = g.Logger(__name__)
application = StaticFilesHandler(application)


if __name__ == "__main__":
    PORT = 80
    logger.info(f"Starting server on port {PORT}.")
    serve(application, port="80")
