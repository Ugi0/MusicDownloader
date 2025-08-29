from flask import Flask
from celery import Celery

celery = Celery(__name__)

def make_celery(app):
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    celery.Task = type(
        'ContextTask',
        (celery.Task,),
        {'run': lambda self, *args, **kwargs: app.app_context().__enter__() or self.run(*args, **kwargs)}
    )
    return celery

def create_app():
    flask = Flask(__name__)
    flask.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
    flask.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'

    from .routes.delete import delete_bp
    from .routes.download import download_bp
    from .routes.root import root_bp
    from .routes.start_download import start_download_bp
    from .routes.status import status_bp
    from .routes.login import login_bp
    from .routes.register import register_bp
    
    flask.register_blueprint(delete_bp)
    flask.register_blueprint(download_bp)
    flask.register_blueprint(root_bp)
    flask.register_blueprint(start_download_bp)
    flask.register_blueprint(status_bp)
    flask.register_blueprint(login_bp)
    flask.register_blueprint(register_bp)

    import app.tasks

    global celery
    celery = make_celery(flask)
    return flask
