from flask import Flask
from celery import Celery
import os

celery = Celery(__name__)

def make_celery(app):
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_BROKER_URL"]
    )
    celery.conf.update(app.config)
    celery.Task = type('ContextTask', (celery.Task,), {
        'run': lambda self, *args, **kwargs: app.app_context().__enter__() or self.run(*args, **kwargs)
    })
    return celery

def create_app():
    flask = Flask(__name__)
    flask.config["CELERY_BROKER_URL"] = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

    from .routes import app
    flask.register_blueprint(app)

    make_celery(flask)
    return flask
