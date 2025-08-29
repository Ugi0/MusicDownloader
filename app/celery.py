from . import create_app, celery as _celery

flask_app = create_app()
celery = _celery
