from waitress import serve

from project.wsgi import application

import globals as g

logger = g.Logger(__name__)


if __name__ == "__main__":
    PORT = 80
    logger.info(f"Starting server on port {PORT}.")
    serve(application, port="80")
